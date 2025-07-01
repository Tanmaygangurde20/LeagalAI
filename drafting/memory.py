"""
Session Memory Management for Conversational Legal Document Drafting Agent
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class SessionMemoryManager:
    """Manages session-based memory for the legal document drafting agent."""
    def __init__(self, storage_dir: str = "Experiments/session_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.default_session = {
            "session_id": "",
            "created_at": "",
            "last_updated": "",
            "document_type": "",
            "collected_info": {},
            "conversation_history": [],
            "current_question": "",
            "is_complete": False,
            "final_document": ""
        }

    def get_session_file_path(self, session_id: str) -> Path:
        return self.storage_dir / f"session_{session_id}.json"

    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_data = self.default_session.copy()
        session_data["session_id"] = session_id
        session_data["created_at"] = datetime.now().isoformat()
        session_data["last_updated"] = datetime.now().isoformat()
        self.save_session(session_id, session_data)
        return session_data

    def get_session(self, session_id: str) -> Dict[str, Any]:
        session_file = self.get_session_file_path(session_id)
        if not session_file.exists():
            return self.create_session(session_id)
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            session_data["last_updated"] = datetime.now().isoformat()
            self.save_session(session_id, session_data)
            return session_data
        except Exception:
            return self.create_session(session_id)

    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        session_file = self.get_session_file_path(session_id)
        session_data["last_updated"] = datetime.now().isoformat()
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        session_data = self.get_session(session_id)
        session_data.update(updates)
        self.save_session(session_id, session_data)
        return session_data

    def delete_session(self, session_id: str) -> bool:
        session_file = self.get_session_file_path(session_id)
        if session_file.exists():
            os.remove(session_file)
            return True
        return False

    def list_sessions(self) -> list:
        session_files = list(self.storage_dir.glob("session_*.json"))
        return [f.stem.replace("session_", "") for f in session_files] 