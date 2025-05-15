from typing import List, Set, Optional, Dict, Any
from datetime import datetime
import logging 

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    
    from enums.quest_enums import QuestStatus, QuestType
else:
    
    try:
        from enums.quest_enums import QuestStatus, QuestType
    except ImportError:
        logging.warning("Could not import QuestStatus and QuestType from enums.quest_enums. Using string fallbacks.")
        QuestStatus = str
        QuestType = str


class Quest:
    def __init__(self,
                 id: str,
                 title: str,
                 description: str,
                 dependencies: Optional[List[str]] = None,
                 
                 status: QuestStatus = QuestStatus.NOT_STARTED,
                 quest_type: QuestType = QuestType.SIDE, 
                 rewards: Optional[List[Dict[str, Any]]] = None,
                 consequences: Optional[List[Dict[str, Any]]] = None,
                 failure_conditions: Optional[List[Dict[str, Any]]] = None,
                 start_time: Optional[datetime] = None):

        if not id or not isinstance(id, str):
            raise ValueError("Quest ID must be a non-empty string.")
        if not title or not isinstance(title, str):
            raise ValueError("Quest title must be a non-empty string.")
        if not isinstance(description, str):
            raise ValueError("Quest description must be a string.")

        
        if isinstance(status, str) and hasattr(QuestStatus, status.upper()):
             status = QuestStatus[status.upper()]
        elif not isinstance(status, QuestStatus) and status != QuestStatus.NOT_STARTED: 
             try: 
                 status = QuestStatus(status)
             except ValueError:
                 raise ValueError(f"Invalid quest status: {status}. Must be a QuestStatus enum member or a valid string representation.")

        if isinstance(quest_type, str) and hasattr(QuestType, quest_type.upper()):
            quest_type = QuestType[quest_type.upper()]
        elif not isinstance(quest_type, QuestType) and quest_type != QuestType.SIDE: 
            try: 
                quest_type = QuestType(quest_type)
            except ValueError:
                raise ValueError(f"Invalid quest type: {quest_type}. Must be a QuestType enum member or a valid string representation.")

        if rewards is not None and not isinstance(rewards, list):
            raise ValueError("Rewards must be a list of dictionaries.")
        if consequences is not None and not isinstance(consequences, list):
            raise ValueError("Consequences must be a list of dictionaries.")
        if failure_conditions is not None and not isinstance(failure_conditions, list):
            raise ValueError("Failure conditions must be a list of dictionaries.")
        if start_time is not None and not isinstance(start_time, datetime):
            raise ValueError("Start time must be a datetime object.")


        self.id: str = id
        self.title: str = title
        self.description: str = description
        self.dependencies: Set[str] = set(dependencies) if dependencies else set()
        
        self.status: QuestStatus = status
        self.quest_type: QuestType = quest_type
        self.rewards: List[Dict[str, Any]] = rewards if rewards is not None else []
        self.consequences: List[Dict[str, Any]] = consequences if consequences is not None else []
        self.failure_conditions: List[Dict[str, Any]] = failure_conditions if failure_conditions is not None else []
        self.start_time: Optional[datetime] = start_time
        

    @property
    def completed(self) -> bool:
        return self.status == QuestStatus.COMPLETED

    def __repr__(self) -> str:
        return (f"Quest(id='{self.id}', title='{self.title}', "
                f"description='{self.description}', "
                f"dependencies={sorted(list(self.dependencies)) if self.dependencies else []}, "
                f"status='{str(self.status)}', quest_type='{str(self.quest_type)}', "
                f"rewards={self.rewards}, consequences={self.consequences}, "
                f"failure_conditions={self.failure_conditions}, "
                f"start_time={repr(self.start_time)})")

    def __str__(self) -> str:
        deps_list = sorted(list(self.dependencies))
        deps = f", depends_on={deps_list}" if deps_list else ""
        start_time_str = f", started_at={self.start_time.isoformat()}" if self.start_time else ""
        return (f"<{self.id}: \"{self.title}\" [{str(self.status).upper()}|{str(self.quest_type).upper()}]{deps}{start_time_str}>")


    def update_status(self, new_status: QuestStatus) -> None:
        if not isinstance(new_status, QuestStatus):
            
            try:
                new_status = QuestStatus(new_status)
            except ValueError:
                raise ValueError(f"Invalid status value: {new_status}. Must be a QuestStatus enum member.")
        self.status = new_status



    def set_start_time(self, time: datetime) -> None:
        if not isinstance(time, datetime):
            raise ValueError("Time must be a datetime object.")
        self.start_time = time
    
    def clear_start_time(self) -> None:
        self.start_time = None

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "dependencies": sorted(list(self.dependencies)),
            "status": str(self.status), 
            "quest_type": str(self.quest_type),
            "rewards": self.rewards,
            "consequences": self.consequences,
            "failure_conditions": self.failure_conditions,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Quest':
        required_keys = ["id", "title", "description"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key in quest data: '{key}'")

        quest_id = data["id"]
        title = data["title"]
        description = data["description"]
        dependencies = data.get("dependencies", [])
        
        
        status_str = data.get("status", QuestStatus.NOT_STARTED.value) 
        try:
            status = QuestStatus(status_str)
        except ValueError:
            raise ValueError(f"Invalid status value '{status_str}' in data for quest ID '{quest_id}'")

        
        type_str = data.get("quest_type", QuestType.SIDE.value) 
        try:
            quest_type = QuestType(type_str)
        except ValueError:
            raise ValueError(f"Invalid quest_type value '{type_str}' in data for quest ID '{quest_id}'")

        rewards = data.get("rewards", [])
        consequences = data.get("consequences", [])
        failure_conditions = data.get("failure_conditions", [])
        
        start_time_str = data.get("start_time")
        start_time = None
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid start_time format '{start_time_str}' for quest ID '{quest_id}'. Must be ISO format.")

     
        if not isinstance(quest_id, str) or not quest_id.strip():
            raise ValueError(f"Invalid ID in data: '{quest_id}' for quest data {data}")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"Invalid title in data: '{title}' for quest ID '{quest_id}'")
        if not isinstance(description, str):
             raise ValueError(f"Invalid description in data for quest ID '{quest_id}'")
        if not isinstance(dependencies, list):
            raise ValueError(f"Dependencies must be a list in data for quest ID '{quest_id}'")
        if not isinstance(rewards, list):
            raise ValueError(f"Rewards must be a list in data for quest ID '{quest_id}'")
        if not isinstance(consequences, list):
            raise ValueError(f"Consequences must be a list in data for quest ID '{quest_id}'")
        if not isinstance(failure_conditions, list):
            raise ValueError(f"Failure conditions must be a list in data for quest ID '{quest_id}'")
        



        return Quest(
            id=quest_id,
            title=title,
            description=description,
            dependencies=dependencies,
            status=status,
            quest_type=quest_type,
            rewards=rewards,
            consequences=consequences,
            failure_conditions=failure_conditions,
            start_time=start_time
            
        )