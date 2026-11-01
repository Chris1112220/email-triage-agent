import sys

from app.gmail_client import fetch_emails
from app.graph import graph

# Windows console defaults to cp1252, which can't print emojis. Use UTF-8.
sys.stdout.reconfigure(encoding="utf-8")


def main():
    for email in fetch_emails(n=10):
        result = graph.invoke(email)
        print("-" * 60)
        print("Subject: ", result["subject"])
        print("Category:", result["category"])
        print("Label:   ", result["label"])
        print("Draft:   ", "yes" if result["draft"] else "no")
        print("Approved:", result["approved"])


if __name__ == "__main__":
    main()