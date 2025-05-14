from typing import List, Set, Optional

class Quest:
    def __init__(self, id: str, title: str, description: str, dependencies: Optional[List[str]] = None):
        if not id or not isinstance(id, str):
            raise ValueError("Quest ID must be a non-empty string.")
        if not title or not isinstance(title, str):
            raise ValueError("Quest title must be a non-empty string.")
        if not isinstance(description, str): # Description can be empty, but must be a string
            raise ValueError("Quest description must be a string.")

        self.id: str = id
        self.title: str = title
        self.description: str = description
        self.dependencies: Set[str] = set(dependencies) if dependencies else set()
        self.completed: bool = False

    def __repr__(self) -> str:
        return (f"Quest(id='{self.id}', title='{self.title}', "
                f"dependencies={list(self.dependencies) if self.dependencies else []}, "
                f"completed={self.completed})")

    def __str__(self) -> str:
        status = "DONE" if self.completed else "PENDING"
        deps = f", depends_on={sorted(list(self.dependencies))}" if self.dependencies else ""
        return f"<{self.id}: \"{self.title}\" [{status}]{deps}>"

    def mark_as_completed(self) -> None:
        self.completed = True

    def mark_as_pending(self) -> None:
        self.completed = False

    def add_dependency(self, quest_id: str) -> None:
        if not quest_id or not isinstance(quest_id, str):
            raise ValueError("Dependency quest ID must be a non-empty string.")
        self.dependencies.add(quest_id)

    def remove_dependency(self, quest_id: str) -> None:
        self.dependencies.discard(quest_id)

    def is_unlocked(self, completed_quest_ids: Set[str]) -> bool:
        
        if not self.dependencies:
            return True
        return self.dependencies.issubset(completed_quest_ids)