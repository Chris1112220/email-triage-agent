"""Snapshot the newest emails into evals/eval_set.json so every eval runs on the SAME emails."""
import json
import os

from app.gmail_client import fetch_emails

OUT = os.path.join("evals", "eval_set.json")


def main():
    os.makedirs("evals", exist_ok=True)
    emails = fetch_emails(n=10)
    rows = [
        {
            "email_id": e["email_id"],
            "sender": e["sender"],
            "subject": e["subject"],
            "body": e["body"][:1000],
            "expected": "",  # Chris fills this in: the RIGHT answer (ground truth)
        }
        for e in emails
    ]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(rows)} emails to {OUT}")


if __name__ == "__main__":
    main()
