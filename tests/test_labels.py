"""Prove the Gmail step only ever ADDS labels, using a fake Gmail (no internet)."""
from app.gmail_labels import DONE_LABEL, NEW_EMAILS_QUERY, apply_labels


class FakeGmail:
    """Pretends to be the Gmail API and records every call made to it."""

    def __init__(self, existing=None):
        self.calls = []
        self.store = dict(existing or {})

    # service.users().labels().list(...).execute() style chaining
    def users(self):
        return self

    def labels(self):
        return self

    def messages(self):
        return self

    def list(self, **kw):
        self.calls.append(("labels.list", kw))
        return _Result({"labels": [{"name": n, "id": i} for n, i in self.store.items()]})

    def create(self, **kw):
        self.calls.append(("labels.create", kw))
        new_id = f"id-{len(self.store)}"
        self.store[kw["body"]["name"]] = new_id
        return _Result({"id": new_id})

    def modify(self, **kw):
        self.calls.append(("messages.modify", kw))
        return _Result({})


class _Result:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


def test_adds_category_and_done_labels():
    gmail = FakeGmail()
    apply_labels(gmail, "msg1", "Bills", {})
    names = [c[1]["body"]["name"] for c in gmail.calls if c[0] == "labels.create"]
    assert names == ["Triage", "Triage/Bills", DONE_LABEL]
    modify = [c for c in gmail.calls if c[0] == "messages.modify"]
    assert len(modify) == 1 and modify[0][1]["id"] == "msg1"


def test_only_adds_never_removes_sends_or_deletes():
    gmail = FakeGmail()
    apply_labels(gmail, "msg1", "Needs Reply", {})
    for name, kw in gmail.calls:
        assert name in ("labels.list", "labels.create", "messages.modify")  # no send/trash/delete
        if name == "messages.modify":
            assert list(kw["body"].keys()) == ["addLabelIds"]  # never removeLabelIds


def test_reuses_existing_labels():
    gmail = FakeGmail({"Triage": "a", "Triage/Bills": "b", DONE_LABEL: "c"})
    ids = apply_labels(gmail, "msg1", "Bills", {})
    assert ids == ["b", "c"]
    assert not [c for c in gmail.calls if c[0] == "labels.create"]


def test_query_skips_already_done():
    assert "-label:triage-done" in NEW_EMAILS_QUERY