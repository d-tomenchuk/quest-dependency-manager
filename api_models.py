from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class APIQuestStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class APIQuestType(str, Enum):
    MAIN = "main"
    SIDE = "side"
    OPTIONAL = "optional"
    REPEATABLE = "repeatable"
    TIMED = "timed"

class QuestCreateSchema(BaseModel):
    id: str = Field(..., min_length=1, description="Unique quest identifier")
    title: str = Field(..., min_length=1, description="Quest title")
    description: str = Field(default="", description="Quest description")
    dependencies: Optional[List[str]] = Field(default_factory=list, description="List of dependency quest IDs")

    quest_type: Optional[APIQuestType] = Field(default=APIQuestType.SIDE, description="Type of quest")
    rewards: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of rewards upon completion")
    consequences: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of consequences on failure")
    failure_conditions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of failure conditions for the quest")

class QuestResponseSchema(BaseModel):
    id: str
    title: str
    description: str
    dependencies: List[str]

    status: APIQuestStatus
    quest_type: APIQuestType
    rewards: List[Dict[str, Any]]
    consequences: List[Dict[str, Any]]
    failure_conditions: List[Dict[str, Any]]
    start_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class FilePathSchema(BaseModel):
    filepath: str = Field(..., description="Path to the file for saving/loading data")

class CycleCheckResponseSchema(BaseModel):
    has_cycles: bool
    message: str

class CompletionOrderResponseSchema(BaseModel):
    order: List[str]
    message: str

class QuestOperationSuccessResponse(BaseModel):
    message: str
    quest_id: str
    new_status: Optional[APIQuestStatus] = None
