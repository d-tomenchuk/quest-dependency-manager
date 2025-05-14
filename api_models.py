from pydantic import BaseModel, Field
from typing import List, Optional


class QuestCreateSchema(BaseModel):
    id: str
    title: str
    description: str
    dependencies: Optional[List[str]] = Field(default_factory=list)



class QuestResponseSchema(BaseModel):
    id: str
    title: str
    description: str
    dependencies: List[str]
    completed: bool


    class Config:
        from_attributes = True 
        


class FilePathSchema(BaseModel):
    filepath: str


class CycleCheckResponseSchema(BaseModel):
    has_cycles: bool
    message: str


class CompletionOrderResponseSchema(BaseModel):
    order: List[str]
    message: str
    