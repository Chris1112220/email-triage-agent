# Tests for the model fallback chain in classify().
# No real Gemini calls: we swap in fakes, so no API key, no cost, same result every time.
from app import nodes

EMAIL = {
    "sender": "Jane <jane@example.com>",
    "subject": "Quick question",
    "body": "Can you send me the report?",
    "category": None,
}


def test_quota_error_moves_to_next_model(monkeypatch):
    # First model hits its quota (429); the second model answers.
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    tried = []

    def fake_gemini(state, model):
        tried.append(model)
        if model == nodes.MODELS[0]:
            raise Exception("429 RESOURCE_EXHAUSTED. quota exceeded")
        return "job"

    monkeypatch.setattr(nodes, "gemini_classify", fake_gemini)
    assert nodes.classify(EMAIL) == {"category": "job"}
    assert tried == [nodes.MODELS[0], nodes.MODELS[1]]  # stopped after the model that worked


def test_all_models_fail_uses_keyword_rules(monkeypatch):
    # Every model is down (503). The agent must not crash; keyword rules take over.
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    tried = []

    def fake_gemini(state, model):
        tried.append(model)
        raise Exception("503 UNAVAILABLE. model overloaded")

    monkeypatch.setattr(nodes, "gemini_classify", fake_gemini)
    result = nodes.classify(EMAIL)
    assert tried == list(nodes.MODELS)  # tried every model in order
    assert result == {"category": nodes.keyword_classify(EMAIL)}


def test_junk_answer_becomes_needs_reply(monkeypatch):
    # Gemini answers with something that isn't a category. Safe default: a human sees it.
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    class FakeResponse:
        text = "banana"

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    monkeypatch.setattr(nodes.genai, "Client", FakeClient)
    assert nodes.gemini_classify(EMAIL, nodes.MODELS[0]) == "needs_reply"
