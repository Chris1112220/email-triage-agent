from typing import TypedDict, Optional

class EmailState(TypedDict):
    email_id: str
    sender: str
    subject: str
    body: str
    category: Optional[str]
    label: Optional[str]
    draft: Optional[str]
    approved: bool