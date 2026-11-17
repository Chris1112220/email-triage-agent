"""Category list, labels, and drafts stay in sync."""
from app import nodes


def test_every_category_has_a_label():
    assert set(nodes.LABELS) == set(nodes.CATEGORIES)


def test_unknown_category_goes_to_other():
    assert nodes.label({"category": "banana"}) == {"label": "Other"}


def test_no_draft_for_automated_categories():
    for category in ("alert", "receipt", "account", "bill", "promo", "spam", "other"):
        state = {"sender": "Real Person <pat@example.com>", "subject": "Hi", "category": category}
        assert nodes.draft(state) == {"draft": None}


def test_draft_for_real_people():
    state = {"sender": "Pat <pat@example.com>", "subject": "Quote for invoice bot", "category": "client"}
    assert nodes.draft(state)["draft"]


def test_keyword_fallback_knows_alerts_and_receipts():
    base = {"sender": "Acme <info@acme.com>", "body": ""}
    assert nodes.keyword_classify({**base, "subject": "New login to your account"}) == "alert"
    assert nodes.keyword_classify({**base, "subject": "Here's your receipt"}) == "receipt"