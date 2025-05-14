from fastapi import FastAPI, HTTPException, Body, status
from typing import List, Dict


from quest import Quest
from manager import QuestManager
from api_models import (
    QuestCreateSchema, 
    QuestResponseSchema, 
    FilePathSchema,
    CycleCheckResponseSchema,
    CompletionOrderResponseSchema
)

app = FastAPI(
    title="Quest Dependency Manager API",
    description="API for managing quest dependencies, completion, and analysis.",
    version="1.0.0"
)

quest_manager = QuestManager()


DEFAULT_QUEST_FILE = "data/quest_data.json" 

try:
    import os
    if os.path.exists(DEFAULT_QUEST_FILE):
        print(f"Attempting to load initial quests from {DEFAULT_QUEST_FILE}...")
        quest_manager.load_quests(DEFAULT_QUEST_FILE)
except Exception as e:
    print(f"Warning: Could not load initial quests from {DEFAULT_QUEST_FILE}. Error: {e}")



@app.post("/quests/", response_model=QuestResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Quests"])
async def create_quest(quest_data: QuestCreateSchema):

    try:

        new_quest = Quest(
            id=quest_data.id,
            title=quest_data.title,
            description=quest_data.description,
            dependencies=quest_data.dependencies
            
        )
        quest_manager.add_quest(new_quest)

        return QuestResponseSchema.model_validate(new_quest) # Pydantic V2
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e: # Общий обработчик
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/quests/", response_model=List[QuestResponseSchema], tags=["Quests"])
async def get_all_quests():

    response_quests = [QuestResponseSchema.model_validate(q) for q in quest_manager._quests.values()]
    return response_quests

@app.get("/quests/available/", response_model=List[QuestResponseSchema], tags=["Quests"])
async def get_available_quests():
    """
    Lists all quests that are currently available (unlocked and not completed).
    """
    available_quests_objects = quest_manager.list_available_quests()
    response_quests = [QuestResponseSchema.model_validate(q) for q in available_quests_objects]
    return response_quests

@app.post("/quests/{quest_id}/complete", response_model=QuestResponseSchema, tags=["Quests"])
async def complete_quest_endpoint(quest_id: str):

    try:
        quest_manager.complete_quest(quest_id) 
                                             
        completed_quest = quest_manager.get_quest(quest_id)
        if not completed_quest: 
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quest '{quest_id}' completed but then not found.")
        return QuestResponseSchema.model_validate(completed_quest)
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/quests/{quest_id}", response_model=QuestResponseSchema, tags=["Quests"])
async def get_quest_by_id(quest_id: str):
    """
    Retrieves details for a specific quest by its ID.
    """
    quest = quest_manager.get_quest(quest_id)
    if not quest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quest with ID '{quest_id}' not found.")
    return QuestResponseSchema.model_validate(quest)


@app.get("/analysis/cycles", response_model=CycleCheckResponseSchema, tags=["Analysis"])
async def check_for_cycles():
    """
    Checks if there are any cyclic dependencies in the quest graph.
    """
    has_cycles = quest_manager.has_cycles()
    message = "Cyclic dependencies detected." if has_cycles else "No cyclic dependencies detected."
    return CycleCheckResponseSchema(has_cycles=has_cycles, message=message)

@app.get("/analysis/completion_order", response_model=CompletionOrderResponseSchema, tags=["Analysis"])
async def get_completion_order_api():

    try:
        order = quest_manager.get_completion_order()
        return CompletionOrderResponseSchema(order=order, message="Successfully retrieved completion order.")
    except ValueError as e: 
        
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



@app.post("/data/save", status_code=status.HTTP_200_OK, tags=["Data Management"])
async def save_quests_to_file(payload: FilePathSchema):

    try:
        quest_manager.save_quests(payload.filepath)
        return {"message": f"Quests successfully saved to {payload.filepath}"}
    except (IOError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error saving quests: {str(e)}")

@app.post("/data/load", status_code=status.HTTP_200_OK, tags=["Data Management"])
async def load_quests_from_file(payload: FilePathSchema):

    try:
        quest_manager.load_quests(payload.filepath)
        
        return {"message": f"Quests successfully loaded from {payload.filepath}. Total: {len(quest_manager._quests)}."}
    except (FileNotFoundError, IOError, ValueError) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, FileNotFoundError) else \
                      status.HTTP_400_BAD_REQUEST if isinstance(e, ValueError) else \
                      status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=f"Error loading quests: {str(e)}")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Quest Dependency Manager API!"}



@app.post("/testing/reset", tags=["Testing"], include_in_schema=False) 
async def reset_state_testing():
    """
    Resets the QuestManager to its initial empty state.
    Loads default quests if DEFAULT_QUEST_FILE exists.
    USE ONLY FOR TESTING PURPOSES.
    """
    global quest_manager 
    quest_manager = QuestManager() 
    print(f"QuestManager state has been reset for testing.")
    try:
        import os
        if os.path.exists(DEFAULT_QUEST_FILE): 
            print(f"Attempting to load initial quests from {DEFAULT_QUEST_FILE} after reset...")
            quest_manager.load_quests(DEFAULT_QUEST_FILE)
    except Exception as e:
        print(f"Warning: Could not load initial quests from {DEFAULT_QUEST_FILE} after reset. Error: {e}")
    return {"message": "QuestManager state has been reset."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)