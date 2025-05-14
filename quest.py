from typing import List, Set, Optional, Dict

class Quest:
    def __init__(self, id: str, title: str, description: str, dependencies: Optional[List[str]] = None, completed: bool = False):
        if not id or not isinstance(id, str):
            raise ValueError("Quest ID must be a non-empty string.")
        if not title or not isinstance(title, str):
            raise ValueError("Quest title must be a non-empty string.")
        if not isinstance(description, str): 
            raise ValueError("Quest description must be a string.")
        if not isinstance(completed, bool):
            raise ValueError("Completed status must be a boolean.")

        self.id: str = id
        self.title: str = title
        self.description: str = description
        self.dependencies: Set[str] = set(dependencies) if dependencies else set()
        self.completed: bool = completed

    def __repr__(self) -> str:
        return (f"Quest(id='{self.id}', title='{self.title}', "
                f"description='{self.description}', "
                f"dependencies={sorted(list(self.dependencies)) if self.dependencies else []}, "
                f"completed={self.completed})")

    def __str__(self) -> str:
        status = "DONE" if self.completed else "PENDING"
        deps_list = sorted(list(self.dependencies))
        deps = f", depends_on={deps_list}" if deps_list else ""
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

    def to_dict(self) -> Dict:
       
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "dependencies": sorted(list(self.dependencies)), 
            "completed": self.completed
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Quest':
        
        required_keys = ["id", "title", "description"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key in quest data: '{key}'")
        
        
        quest_id = data["id"]
        title = data["title"]
        description = data["description"]
        dependencies = data.get("dependencies", [])
        completed = data.get("completed", False)

        if not isinstance(quest_id, str) or not quest_id.strip(): 
            raise ValueError(f"Invalid ID in data: '{quest_id}' for quest data {data}")
        if not isinstance(title, str) or not title.strip(): 
            raise ValueError(f"Invalid title in data: '{title}' for quest ID '{quest_id}'")
        if not isinstance(description, str):
             raise ValueError(f"Invalid description in data for quest ID '{quest_id}'")
        if not isinstance(dependencies, list):
            raise ValueError(f"Dependencies must be a list in data for quest ID '{quest_id}'")
        if not isinstance(completed, bool):
            raise ValueError(f"Completed status must be a boolean in data for quest ID '{quest_id}'")


        return Quest(
            id=quest_id,
            title=title,
            description=description,
            dependencies=dependencies,
            completed=completed
        )