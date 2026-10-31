from app.graph import graph
from app.fake_emails import FAKE_EMAILS

def run(email):
    return graph.invoke({**email, "category": None, "label": None, "draft": None, "approved": False})

def test_nothing_is_ever_approved():
    for email in FAKE_EMAILS:
        assert run(email)["approved"] is False

def test_phishing_is_spam_with_no_draft():
    result = run(FAKE_EMAILS[3])
    assert result["category"] == "spam"
    assert result["draft"] is None

def test_recruiter_is_job():
    assert run(FAKE_EMAILS[0])["category"] == "job"