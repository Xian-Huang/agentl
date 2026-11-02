import datetime
import json
import shutil
from uuid import uuid4
import os
from pathlib import Path
from agentl.core.config import ROOT_DIR


class SessionError(Exception):
    """Session Error"""


class Session:
    def __init__(self, session_id: str | None = None) -> None:
        self.id: str = session_id or uuid4().hex
        self.created_at: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.updated_at: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.messages: list[dict[str, str]] = []

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        session = cls(session_id=data["id"])
        session.created_at = datetime.datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.datetime.fromisoformat(data["updated_at"])
        session.messages = data.get("messages", [])
        return session


class SessionStore:

    def load(self, id: str):
        session_json_path = ROOT_DIR.joinpath("sessions", id, f"{id}.json")
        if session_json_path.exists():
            json_data = json.loads(session_json_path.read_text())
            return Session.from_dict(json_data)
        else:
            raise SessionError(f"Session with id {id} does not exist.")

    def save(self, session: Session):
        session_workspace = ROOT_DIR.joinpath("sessions", session.id)
        if not session_workspace.exists():
            os.makedirs(session_workspace)

        session_file_path = os.path.join(session_workspace, f"{session.id}.json")
        with open(session_file_path, "w") as f:
            json.dump(session.to_dict(), f)

    def list(self) -> list[Session]:
        sessions = []
        for session_workspace in os.listdir(ROOT_DIR.joinpath("sessions")):
            session_json_path = os.path.join(session_workspace, f"{session_workspace}.json")
            if os.path.exists(session_json_path):
                sessions.append(Session.from_dict(json.loads(open(session_json_path).read())))
        return sessions

    def delete(self, session: Session):
        session_workspace = ROOT_DIR.joinpath("sessions", session.id)
        if session_workspace.exists():
            shutil.rmtree(session_workspace)
            return True
        return False
