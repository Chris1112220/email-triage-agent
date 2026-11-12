import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.state import EmailState

load_dotenv()  # reads .env so GEMINI_API_KEY is available

CATEGORIES = ("job", "bill", "promo", "spam", "needs_reply")
# Fallback chain: try each model in order. Each has its own free daily quota.
MODELS = ("gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.7-flash")  # fastest first

# TODO (Chris): type the instruction Gemini follows. Tell it the 5 categories
# and to answer with ONE word only.
PROMPT = "Classify this email into exactly one category: job, bill, promo, spam, or needs_reply. Answer with one word only."  # single-email path; DEFINITIONS added below

# TODO (Chris): set this so the same email always gets the same answer.
TEMPERATURE = 0

BATCH_SIZE = 5  # emails per Gemini call: 20 free calls x 5 = 100 emails per model per day


def keyword_classify(state: EmailState) -> str:
    # Old rule-based version. Now the backup when Gemini is unavailable (tests, CI, no key).
    text = (state["subject"] + " " + state["body"]).lower()
    sender = state["sender"].lower()
    if "urgent" in text and "password" in text:
        return "spam"
    if "recruiter" in sender or "hr@" in sender:
        return "job"
    if "bill" in text or "payment" in text:
        return "bill"
    if "deals@" in sender or "newsletter" in sender or "noreply" in sender:
        return "promo"
    return "needs_reply"


def gemini_classify(state: EmailState, model: str) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    email = f"From: {state['sender']}\nSubject: {state['subject']}\n\n{state['body'][:2000]}"
    response = client.models.generate_content(
        model=model,
        contents=f"{PROMPT}\n\n{DEFINITIONS}\n\n{email}",
        config=types.GenerateContentConfig(temperature=TEMPERATURE),
    )
    raw = response.text or ""
    answer = raw.strip().lower().strip(".*`\"' ")  # clean "Promo." or "**promo**" down to "promo"
    if answer not in CATEGORIES:
        print(f"  [guardrail] Gemini said {raw!r}, not a category -> needs_reply")
        return "needs_reply"  # guardrail: unknown answer -> safe default
    return answer


def short_error(e: Exception) -> str:
    # "ClientError: 429 RESOURCE_EXHAUSTED. {...huge JSON...}" -> "ClientError: 429 RESOURCE_EXHAUSTED"
    return f"{type(e).__name__}: {str(e).split('.')[0]}"


def classify(state: EmailState) -> dict:
    if state.get("category"):  # already classified in a batch by run_real -> keep it
        return {"category": state["category"]}
    if not os.environ.get("GEMINI_API_KEY"):
        return {"category": keyword_classify(state)}
    for model in MODELS:  # like Retry Scope, but each retry uses the next model
        start = time.perf_counter()  # stopwatch: how long each call takes
        try:
            category = gemini_classify(state, model)
            print(f"  [gemini] {model}: {category} in {time.perf_counter() - start:.1f}s")
            return {"category": category}
        except Exception as e:
            print(f"  [skip] {model} failed after {time.perf_counter() - start:.1f}s: {short_error(e)}")
    print("  [fallback] all models failed -> keyword rules")
    return {"category": keyword_classify(state)}  # last resort, never crash


DEFINITIONS = (
    "Category definitions:\n"
    "- job: recruiters, interviews, job applications, offers\n"
    "- bill: an actual charge, invoice, receipt, or payment due\n"
    "- promo: marketing, newsletters, tips, and plan or product updates\n"
    "- spam: scams, phishing, or junk only\n"
    "- needs_reply: anything Chris must read or act on, including security alerts, "
    "new logins, and account changes"
)

BATCH_PROMPT = (
    "Classify each email below into exactly one category: job, bill, promo, spam, or needs_reply. "
    "Return ONLY a JSON list of category strings, one per email, in the same order. "
    'Example for 3 emails: ["promo", "bill", "needs_reply"]\n\n' + DEFINITIONS
)


def gemini_classify_batch(emails: list, model: str) -> list:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    blocks = [
        f"### Email {i}\nFrom: {e['sender']}\nSubject: {e['subject']}\n\n{e['body'][:1000]}"
        for i, e in enumerate(emails, start=1)
    ]
    response = client.models.generate_content(
        model=model,
        contents=BATCH_PROMPT + "\n\n" + "\n\n".join(blocks),
        config=types.GenerateContentConfig(
            temperature=TEMPERATURE,
            response_mime_type="application/json",  # forces Gemini to answer in JSON
        ),
    )
    answers = json.loads(response.text)  # '["promo","bill"]' -> ["promo", "bill"]
    if not isinstance(answers, list) or len(answers) != len(emails):
        raise ValueError(f"expected {len(emails)} answers, got {answers!r}")  # bad shape -> try next model
    cleaned = [str(a).strip().lower() for a in answers]
    return [a if a in CATEGORIES else "needs_reply" for a in cleaned]  # guardrail per email


def classify_batch(emails: list) -> list:
    # One Gemini call for the whole batch, with the same model fallback chain.
    if not os.environ.get("GEMINI_API_KEY"):
        return [keyword_classify(e) for e in emails]
    for model in MODELS:
        start = time.perf_counter()
        try:
            categories = gemini_classify_batch(emails, model)
            print(f"[batch] {model}: {len(emails)} emails in {time.perf_counter() - start:.1f}s")
            return categories
        except Exception as e:
            print(f"[batch skip] {model} failed after {time.perf_counter() - start:.1f}s: {short_error(e)}")
    print("[batch fallback] all models failed -> keyword rules")
    return [keyword_classify(e) for e in emails]


LABELS = {
    "job": "Job Applications",
    "bill": "Bills",
    "promo": "Promotions & Newsletters",
    "spam": "Spam",
    "needs_reply": "Needs Reply",
}


def label(state: EmailState) -> dict:
    return {"label": LABELS.get(state["category"], "Needs Reply")}


# Guardrail: never draft a reply to automated senders, no matter what classify says.
NO_REPLY_PATTERNS = ("no-reply", "noreply", "donotreply", "do-not-reply", "mailer-daemon")


def is_automated_sender(sender: str) -> bool:
    return any(p in sender.lower() for p in NO_REPLY_PATTERNS)


def draft(state: EmailState) -> dict:
    if is_automated_sender(state["sender"]):
        return {"draft": None}
    if state["category"] not in ("job", "needs_reply"):
        return {"draft": None}
    reply = f"Hi,\n\nThanks for your email about \"{state['subject']}\". I'll get back to you shortly.\n\nBest,\nChris"
    return {"draft": reply}


def approve(state: EmailState) -> dict:
    # Approval gate: the agent never approves or sends. A human flips this later.
    return {"approved": False}
