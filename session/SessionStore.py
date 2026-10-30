import datetime
import json
from typing import Self
from uuid import uuid4
import os


class SessionError(Exception):
    """Session Error"""


class Session:

    def __init__(self) -> None:
        self.id = uuid4()
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        self.messages: list[dict[str, str]] = []

    # def _init_session(self):
    #     init_session = {
    #         "id": str(self.id),
    #         "created_at": self.created_at.__str__(),
    #         "updated_at": self.updated_at.__str__(),
    #         "messages": self.messages,
    #     }
    #     session_file_path = os.path.join(self.workspace, f"{self.id.hex}.json")
    #     if not os.path.exists(session_file_path):
    #         raise SessionError(f"{session_file_path} not found")
    #     with open(os.path.join(self.workspace, f"{self.id.hex}.json"), "w") as f:
    #         json.dump(init_session, f)

    # def _init_workspace(self):
    #     current_path = os.path.join(*__path__)
    #     self.workspace = os.path.join(current_path, ".agentl", self.id.hex)

    def get_session(self):
        return {
            "id": str(self.id),
            "created_at": self.created_at.__str__(),
            "updated_at": self.updated_at.__str__(),
            "messages": self.messages,
        }


class SessionStore:

    def load(self, session: Session):
        self.session = session

    def save(self):
        if not os.path.exists(self.session.workspace):
            os.path.join(self.session.workspace)

        session_file_path = os.path.join(self.session.workspace, f"{self.session.id.hex}.json")
        with open(session_file_path, "w") as f:
            json.dump(self.session.get_session(), f)

    def list(self): ...

    def delete(self): ...


class FilesystemSessionStore:
    def __init__(self, session: SessionStore):
        self.session = session

    def save_file(self): ...
