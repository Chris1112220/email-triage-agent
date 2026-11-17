import argparse
import sys

from app.gmail_client import fetch_emails, get_service
from app.gmail_labels import NEW_EMAILS_QUERY, apply_labels
from app.graph import graph
from app.nodes import BATCH_SIZE, classify_batch

# Windows console defaults to cp1252, which can't print emojis. Use UTF-8.
sys.stdout.reconfigure(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Triage new Gmail emails.")
    parser.add_argument("--apply", action="store_true", help="actually add labels in Gmail (default: dry run)")
    parser.add_argument("--max", type=int, default=25, help="most emails to handle in one run")
    args = parser.parse_args()

    emails = fetch_emails(n=args.max, query=NEW_EMAILS_QUERY)  # only emails not yet marked Triage/Done
    print("MODE:", "APPLY (adding labels in Gmail)" if args.apply else "DRY RUN (add --apply to label in Gmail)")
    if not emails:
        print("No new emails.")
        return

    service = get_service() if args.apply else None
    cache = {}  # label name -> id, so we look labels up once per run
    for i in range(0, len(emails), BATCH_SIZE):
        batch = emails[i : i + BATCH_SIZE]
        categories = classify_batch(batch)  # ONE Gemini call for the whole batch
        for email, category in zip(batch, categories):
            email["category"] = category  # pre-fill so the classify node skips Gemini
            result = graph.invoke(email)
            print("-" * 60)
            print("Subject: ", result["subject"])
            print("Category:", result["category"])
            print("Draft:   ", "yes" if result["draft"] else "no")
            print("Approved:", result["approved"])
            if args.apply:
                apply_labels(service, email["email_id"], result["label"], cache)
                print("Labeled:  Triage/" + result["label"])
            else:
                print("Would label: Triage/" + result["label"])


if __name__ == "__main__":
    main()