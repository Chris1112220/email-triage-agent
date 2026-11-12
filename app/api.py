"""FastAPI wrapper: send an email in, get the agent's decision back. Never sends anything."""
from fastapi import FastAPI
from pydantic import BaseModel

from app.graph import graph

app = FastAPI(title="Email Triage Agent")


class EmailIn(BaseModel):
    # What the caller must send. FastAPI rejects bad requests automatically (422 error).
    sender: str
    subject: str
    body: str = ""


class TriageOut(BaseModel):
    # What we promise to send back.
    category: str
    label: str
    draft: str | None
    approved: bool


@app.get("/health")
def health():
    # Quick "is it alive?" check, like pinging a robot in Orchestrator.
    return {"status": "ok"}


@app.post("/triage", response_model=TriageOut)
def triage(email: EmailIn):
    state = {
        "email_id": "api",
        "sender": email.sender,
        "subject": email.subject,
        "body": email.body,
        "category": None,
        "label": None,
        "draft": None,
        "approved": False,
    }
    result = graph.invoke(state)  # same graph as run_real: classify -> label -> draft -> approve
    return TriageOut(
        category=result["category"],
        label=result["label"],
        draft=result["draft"],
        approved=result["approved"],
    )
