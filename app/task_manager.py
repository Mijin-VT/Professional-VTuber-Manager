"""Task manager for VT Manager.
Handles loading, saving, and managing task lists.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class TaskItem:
    def __init__(self, title: str, priority: str = "medium", completed: bool = False, created_at: str = None):
        self.title = title
        self.priority = priority
        self.completed = completed
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "priority": self.priority,
            "completed": self.completed,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TaskItem":
        return cls(
            title=d.get("title", ""),
            priority=d.get("priority", "medium"),
            completed=d.get("completed", False),
            created_at=d.get("created_at")
        )

class TaskManager:
    """Manages reading and writing task items to json persistence."""
    
    def __init__(self, config):
        self.config = config
        self.tasks_file = Path(__file__).parent.parent / "data" / "tasks.json"
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        self.tasks: List[TaskItem] = []
        self.load_tasks()

    def load_tasks(self) -> List[TaskItem]:
        self.tasks = []
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.tasks = [TaskItem.from_dict(d) for d in data]
            except Exception as e:
                print(f"[TaskManager] Error loading tasks: {e}")
        return self.tasks

    def save_tasks(self):
        try:
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in self.tasks], f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[TaskManager] Error saving tasks: {e}")

    def add_task(self, title: str, priority: str = "medium") -> TaskItem:
        task = TaskItem(title=title, priority=priority)
        self.tasks.append(task)
        self.save_tasks()
        return task

    def delete_task(self, idx: int) -> bool:
        if 0 <= idx < len(self.tasks):
            self.tasks.pop(idx)
            self.save_tasks()
            return True
        return False

    def toggle_task(self, idx: int) -> bool:
        if 0 <= idx < len(self.tasks):
            self.tasks[idx].completed = not self.tasks[idx].completed
            self.save_tasks()
            return True
        return False
