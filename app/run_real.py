import sys

from app.gmail_client import fetch_emails
from app.graph import graph
from app.nodes import BATCH_SIZE, classify_batch

# Windows console defaults to cp1252, which can't print emojis. Use UTF-8.
sys.stdout.reconfigure(encoding="utf-8")


def main():
    emails = fetch_emails(n=10)
    for i in range(0, len(emails), BATCH_SIZE):  # 0, 5 -> two batches of 5
        batch = emails[i : i + BATCH_SIZE]
        categories = classify_batch(batch)  # ONE Gemini call for the whole batch
        for email, category in zip(batch, categories):
            email["category"] = category  # pre-fill so the classify node skips Gemini
            result = graph.invoke(email)
            print("-" * 60)
            print("Subject: ", result["subject"])
            print("Category:", result["category"])
            print("Label:   ", result["label"])
            print("Draft:   ", "yes" if result["draft"] else "no")
            print("Approved:", result["approved"])


if __name__ == "__main__":
    main()
