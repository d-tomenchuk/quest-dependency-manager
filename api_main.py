import logging
import sys
import os
from fastapi import FastAPI, HTTPException, Body, status, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from typing import List, Dict, Optional 

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, .env file will not be loaded.")

LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

from quest import Quest 

try:
    from enums.quest_enums import QuestStatus, QuestType
except ImportError:
    logger.critical("CRITICAL: Core enums QuestStatus, QuestType from enums.quest_enums could not be imported in api_main.py.")
    QuestStatus = object() 
    QuestType = object()


from manager import QuestManager
from api_models import ( 
    QuestCreateSchema,
    QuestResponseSchema,
    FilePathSchema,
    CycleCheckResponseSchema,
    CompletionOrderResponseSchema,
    QuestOperationSuccessResponse, 
    APIQuestStatus 
)

app = FastAPI(
    title="Quest Dependency Manager API",
    description="API for managing quest dependencies, completion, and analysis. Some write operations require API Key authentication via X-API-Key header.",
    version="1.1.0" 
)

quest_manager = QuestManager()
DEFAULT_QUEST_FILE = "data/quest_data.json" 

try:
    if os.path.exists(DEFAULT_QUEST_FILE):
        logger.info(f"Attempting to load initial quests from {DEFAULT_QUEST_FILE}...")
        quest_manager.load_quests(DEFAULT_QUEST_FILE)
    else:
        logger.info(f"Default quest file {DEFAULT_QUEST_FILE} not found. Starting with an empty quest list.")
except Exception as e:
    logger.warning(f"Could not load initial quests from {DEFAULT_QUEST_FILE}. Error: {e}", exc_info=True)

API_KEY_NAME = "X-API-Key"
api_key_header_auth_scheme = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

VALID_API_KEYS_ENV = os.getenv("VALID_API_KEYS", "entwicklungsschluessel") 
VALID_API_KEYS = {key.strip() for key in VALID_API_KEYS_ENV.split(',') if key.strip()}

if not VALID_API_KEYS:
    logger.critical("SECURITY CRITICAL: No VALID_API_KEYS configured.")
elif "entwicklungsschluessel" in VALID_API_KEYS and len(VALID_API_KEYS) == 1:
    logger.warning("SECURITY WARNING: Using default development API key.")

async def get_api_key(api_key_header: Optional[str] = Security(api_key_header_auth_scheme)):
    if api_key_header is None:
        logger.warning("API Key missing from request header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: API Key is missing in X-API-Key header."
        )
    if api_key_header in VALID_API_KEYS:
        logger.debug(f"Valid API Key received (ends with ...{api_key_header[-4:] if len(api_key_header) > 3 else '***'}).")
        return api_key_header
    else:
        logger.warning(f"Invalid API Key received (ends with ...{api_key_header[-4:] if len(api_key_header) > 3 else '***'}). Access denied.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Invalid API Key."
        )

@app.post("/quests/", response_model=QuestResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Quests Management (Protected)"], dependencies=[Depends(get_api_key)])
async def create_quest_api(quest_data: QuestCreateSchema):
    logger.debug(f"Authenticated request to create quest with id: {quest_data.id}")
    try:
        
        new_quest_params = {
            "id": quest_data.id,
            "title": quest_data.title,
            "description": quest_data.description,
            "dependencies": quest_data.dependencies or [], 
            "quest_type": quest_data.quest_type.value if quest_data.quest_type else QuestType.SIDE.value, 
            "rewards": quest_data.rewards or [],
            "consequences": quest_data.consequences or [],
            "failure_conditions": quest_data.failure_conditions or []
            
        }

        new_quest = Quest(**new_quest_params)
        
        quest_manager.add_quest(new_quest)
        logger.info(f"Quest '{new_quest.id}' titled '{new_quest.title}' created successfully by authenticated client.")
        return QuestResponseSchema.model_validate(new_quest)
    except ValueError as e:
        logger.warning(f"Failed to create quest (ID: {quest_data.id}) by authenticated client: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating quest (ID: {quest_data.id}) by authenticated client: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the quest.")


@app.post("/quests/{quest_id}/start", response_model=QuestResponseSchema, tags=["Quests Management (Protected)"], dependencies=[Depends(get_api_key)])
async def start_quest_api(quest_id: str):
    logger.debug(f"Authenticated request to start quest: {quest_id}")
    try:
        quest_manager.start_quest(quest_id)
        started_quest = quest_manager.get_quest(quest_id)
        if not started_quest: 
            logger.error(f"Quest '{quest_id}' reported as started by manager but then not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quest '{quest_id}' not found after attempting to start.")
        logger.info(f"Quest '{quest_id}' (title: '{started_quest.title}') started successfully.")
        return QuestResponseSchema.model_validate(started_quest)
    except ValueError as e: 
        logger.warning(f"Failed to start quest '{quest_id}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e: 
        logger.warning(f"Permission denied to start quest '{quest_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error starting quest '{quest_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while starting quest '{quest_id}'.")


@app.post("/quests/{quest_id}/complete", response_model=QuestResponseSchema, tags=["Quests Management (Protected)"], dependencies=[Depends(get_api_key)])
async def complete_quest_api(quest_id: str):
    logger.debug(f"Authenticated request to complete quest: {quest_id}")
    try:
        quest_manager.complete_quest(quest_id)
        completed_quest = quest_manager.get_quest(quest_id) 
        if not completed_quest:
            logger.error(f"Quest '{quest_id}' reported as completed by manager but then not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quest '{quest_id}' not found after completion attempt.")
        logger.info(f"Quest '{quest_id}' (title: '{completed_quest.title}') marked as completed successfully.")
        return QuestResponseSchema.model_validate(completed_quest)
    except ValueError as e:
        logger.warning(f"Attempt to complete quest '{quest_id}' failed, quest not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Attempt to complete quest '{quest_id}' failed due to unmet dependencies or wrong status: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error completing quest '{quest_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while completing quest '{quest_id}'.")


@app.post("/quests/{quest_id}/fail", response_model=QuestResponseSchema, tags=["Quests Management (Protected)"], dependencies=[Depends(get_api_key)])
async def fail_quest_api(quest_id: str):
    logger.debug(f"Authenticated request to fail quest: {quest_id}")
    try:
        quest_manager.fail_quest(quest_id)
        failed_quest = quest_manager.get_quest(quest_id)
        if not failed_quest:
            logger.error(f"Quest '{quest_id}' reported as failed by manager but then not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quest '{quest_id}' not found after attempting to fail.")
        logger.info(f"Quest '{quest_id}' (title: '{failed_quest.title}') marked as failed successfully.")
        return QuestResponseSchema.model_validate(failed_quest)
    except ValueError as e:
        logger.warning(f"Failed to fail quest '{quest_id}', quest not found: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied to fail quest '{quest_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error failing quest '{quest_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while failing quest '{quest_id}'.")


@app.post("/quests/{quest_id}/reset", response_model=QuestResponseSchema, tags=["Quests Management (Protected)"], dependencies=[Depends(get_api_key)])
async def reset_quest_api(quest_id: str):
    logger.debug(f"Authenticated request to reset repeatable quest: {quest_id}")
    try:
        quest_manager.reset_repeatable_quest(quest_id)
        reset_quest = quest_manager.get_quest(quest_id)
        if not reset_quest:
            logger.error(f"Quest '{quest_id}' reported as reset by manager but then not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quest '{quest_id}' not found after attempting to reset.")
        logger.info(f"Quest '{quest_id}' (title: '{reset_quest.title}') reset successfully (if repeatable).")
        return QuestResponseSchema.model_validate(reset_quest)
    except ValueError as e: 
        logger.warning(f"Failed to reset quest '{quest_id}': {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e: 
        logger.warning(f"Permission denied to reset quest '{quest_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error resetting quest '{quest_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while resetting quest '{quest_id}'.")

@app.post("/data/save", response_model=QuestOperationSuccessResponse, status_code=status.HTTP_200_OK, tags=["Data Management (Protected)"], dependencies=[Depends(get_api_key)])
async def save_quests_to_file_api(payload: FilePathSchema):
    logger.info(f"Authenticated request to save quests to file: {payload.filepath}")
    try:
        quest_manager.save_quests(payload.filepath)
        logger.info(f"Quests successfully saved to {payload.filepath} via authenticated API call.")
        return QuestOperationSuccessResponse(message=f"Quests successfully saved to {payload.filepath}", quest_id="N/A")
    except (IOError, TypeError) as e:
        logger.error(f"Error saving quests to {payload.filepath} (authenticated): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error saving quests: {str(e)}")

@app.post("/data/load", response_model=QuestOperationSuccessResponse, status_code=status.HTTP_200_OK, tags=["Data Management (Protected)"], dependencies=[Depends(get_api_key)])
async def load_quests_from_file_api(payload: FilePathSchema):
    logger.info(f"Authenticated request to load quests from file: {payload.filepath}")
    try:
        quest_manager.load_quests(payload.filepath)
        message = f"Quests successfully loaded from {payload.filepath}. Total in manager: {len(quest_manager._quests)}."
        logger.info(message + " (Authenticated request)")
        return QuestOperationSuccessResponse(message=message, quest_id="N/A") 
    except FileNotFoundError as e:
        logger.warning(f"File not found for loading quests (authenticated): {payload.filepath}. Error: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Error loading quests: {str(e)}")
    except (IOError, ValueError) as e:
        logger.error(f"Error loading quests from {payload.filepath} (authenticated): {e}", exc_info=True)
        status_code = status.HTTP_400_BAD_REQUEST if isinstance(e, ValueError) else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=f"Error loading quests: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error loading quests from {payload.filepath} (authenticated): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while loading quests: {str(e)}")
    
@app.post("/testing/reset", response_model=QuestOperationSuccessResponse, tags=["Testing (Protected)"], include_in_schema=False, dependencies=[Depends(get_api_key)])
async def reset_state_testing_api():
    global quest_manager 
    quest_manager = QuestManager()
    logger.info("QuestManager state has been reset for testing via authenticated API call.")
    try:
        if os.path.exists(DEFAULT_QUEST_FILE):
            logger.info(f"Attempting to load initial quests from {DEFAULT_QUEST_FILE} after reset (authenticated call)...")
            quest_manager.load_quests(DEFAULT_QUEST_FILE)
        else:
            logger.info(f"Default quest file {DEFAULT_QUEST_FILE} not found after reset (authenticated call). Manager is empty.")
    except Exception as e:
        logger.warning(f"Could not load initial quests from {DEFAULT_QUEST_FILE} after reset (authenticated call). Error: {e}", exc_info=True)
    return QuestOperationSuccessResponse(message="QuestManager state has been reset.", quest_id="N/A")

@app.get("/quests/", response_model=List[QuestResponseSchema], tags=["Quests (Public)"])
async def get_all_quests_public():
    logger.debug("Public request to fetch all quests.")
    response_quests = [QuestResponseSchema.model_validate(q) for q in quest_manager._quests.values()]
    return response_quests

@app.get("/quests/available/", response_model=List[QuestResponseSchema], tags=["Quests (Public)"])
async def get_available_quests_public():
    logger.debug("Public request to fetch available quests.")
    available_quests_objects = quest_manager.list_available_quests()
    response_quests = [QuestResponseSchema.model_validate(q) for q in available_quests_objects]
    return response_quests

@app.get("/quests/{quest_id}", response_model=QuestResponseSchema, tags=["Quests (Public)"])
async def get_quest_by_id_public(quest_id: str):
    logger.debug(f"Public request to fetch quest by ID: {quest_id}")
    quest = quest_manager.get_quest(quest_id)
    if not quest:
        logger.warning(f"Quest with ID '{quest_id}' not found during public API call.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quest with ID '{quest_id}' not found.")
    return QuestResponseSchema.model_validate(quest)

@app.get("/analysis/cycles", response_model=CycleCheckResponseSchema, tags=["Analysis (Public)"])
async def check_for_cycles_public():
    logger.debug("Public request to check for cycles.")
    has_cycles = quest_manager.has_cycles()
    message = "Cyclic dependencies detected." if has_cycles else "No cyclic dependencies detected."
    logger.info(f"Cycle check result (public): {message}")
    return CycleCheckResponseSchema(has_cycles=has_cycles, message=message)

@app.get("/analysis/completion_order", response_model=CompletionOrderResponseSchema, tags=["Analysis (Public)"])
async def get_completion_order_public_api():
    logger.debug("Public request to get completion order.")
    try:
        order = quest_manager.get_completion_order()
        logger.info("Successfully retrieved completion order (public).")
        return CompletionOrderResponseSchema(order=order, message="Successfully retrieved completion order.")
    except ValueError as e: 
        logger.warning(f"Cannot get completion order (public), graph contains cycles: {e}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e: 
        logger.error(f"Runtime error getting completion order (public): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/", tags=["Root (Public)"])
async def read_root_public():
    logger.info("Root endpoint accessed (public).")
    return {"message": "Welcome to the Quest Dependency Manager API!"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server directly from script (for development only).")
    uvicorn.run(app, host="0.0.0.0", port=8000)