"""Apply triage labels in Gmail.

Guardrail: the ONLY write this agent ever makes to Gmail is ADDING labels.
It never sends, deletes, trashes, archives, or removes labels.
"""

LABEL_PREFIX = "Triage"  # all labels live under Triage/ so they never mix with existing ones
DONE_LABEL = f"{LABEL_PREFIX}/Done"  # marks an email as already handled

# Gmail search: skip anything already marked Done, look back 7 days.
# (In Gmail search, "Triage/Done" is written as "triage-done".)
NEW_EMAILS_QUERY = "-label:triage-done newer_than:7d"


def get_or_create_label(service, name, cache):
    """Return the Gmail label id for name, creating the label if it doesn't exist yet."""
    if not cache:  # first call: load all existing labels once
        existing = service.users().labels().list(userId="me").execute().get("labels", [])
        cache.update({lab["name"]: lab["id"] for lab in existing})
    if name not in cache:
        created = service.users().labels().create(
            userId="me",
            body={"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"},
        ).execute()
        cache[name] = created["id"]
    return cache[name]


def apply_labels(service, email_id, label_name, cache):
    """Add Triage/<label_name> and Triage/Done to one email. Adds only, never removes."""
    get_or_create_label(service, LABEL_PREFIX, cache)  # parent, so Gmail nests the labels
    ids = [
        get_or_create_label(service, f"{LABEL_PREFIX}/{label_name}", cache),
        get_or_create_label(service, DONE_LABEL, cache),
    ]
    service.users().messages().modify(userId="me", id=email_id, body={"addLabelIds": ids}).execute()
    return ids