from app.state import EmailState


def classify(state: EmailState) -> dict:
    text = (state["subject"] + " " + state["body"]).lower()
    sender = state["sender"].lower()

    if "urgent" in text and "password" in text:
        category = "spam"
    elif "recruiter" in sender or "hr@" in sender:
        category = "job"
    elif "bill" in text or "payment" in text:
        category = "bill"
    elif "deals@" in sender or "newsletter" in sender or "noreply" in sender:
        category = "promo"
    else:
        category = "needs_reply"

    return {"category": category}

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