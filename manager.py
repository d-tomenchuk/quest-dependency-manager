from typing import Dict, List, Optional, Set
from collections import deque
import json
import os
import logging
from datetime import datetime, timezone  

logger = logging.getLogger(__name__)

from quest import Quest

try:

    from enums.quest_enums import QuestStatus, QuestType

except ImportError:
    logger.critical("CRITICAL: Could not import QuestStatus and QuestType from enums.quest_enums. "
                    "QuestManager may not function correctly. Ensure enums package is correct.")

    QuestStatus = type("QuestStatus", (object,), {
        "NOT_STARTED": "not_started",
        "IN_PROGRESS": "in_progress",
        "COMPLETED": "completed",
        "FAILED": "failed"
    })
    QuestType = type("QuestType", (object,), {
        "MAIN": "main",
        "SIDE": "side",
        "OPTIONAL": "optional",
        "REPEATABLE": "repeatable",
        "TIMED": "timed"
    })

class QuestManager:
    def __init__(self):
        self._quests: Dict[str, Quest] = {}
        self._completed_quest_ids: Set[str] = set()
        logger.debug("QuestManager initialized.")

    def add_quest(self, quest: Quest) -> None:

        logger.debug(f"Attempting to add quest with ID: {quest.id}")
        if quest.id in self._quests:
            msg = f"Quest with ID '{quest.id}' already exists."
            logger.warning(msg)
            raise ValueError(msg)

        
        for dep_id in quest.dependencies:
            if not isinstance(dep_id, str) or not dep_id.strip():
                msg = f"Invalid dependency ID '{dep_id}' for quest '{quest.id}'. Must be a non-empty string."
                logger.error(msg)
                raise ValueError(msg)

        self._quests[quest.id] = quest
        
        
        if quest.status == QuestStatus.COMPLETED:
            self._completed_quest_ids.add(quest.id)
            logger.debug(f"Quest '{quest.title}' (ID: {quest.id}) added as already completed.")
        
        logger.info(f"Quest '{quest.title}' (ID: {quest.id}, Status: {quest.status}, Type: {quest.quest_type}) added to manager.")

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        logger.debug(f"Attempting to get quest with ID: {quest_id}")
        return self._quests.get(quest_id)
    
    def start_quest(self, quest_id: str) -> None:
        logger.debug(f"Attempting to start quest with ID: {quest_id}")
        quest = self.get_quest(quest_id)
        if not quest:
            msg = f"Quest with ID '{quest_id}' not found, cannot start."
            logger.warning(msg)
            raise ValueError(msg)

        if quest.status != QuestStatus.NOT_STARTED:
            msg = f"Quest '{quest.title}' (ID: {quest_id}) is not in NOT_STARTED state (current: {quest.status}). Cannot start."
            logger.warning(msg)
            raise PermissionError(msg)

        if not quest.is_unlocked(self._completed_quest_ids):
            unmet_deps = sorted(list(d_id for d_id in quest.dependencies if d_id not in self._completed_quest_ids))
            msg = (f"Cannot start quest '{quest.title}' (ID: {quest_id}). "
                   f"Dependencies not met: {unmet_deps}")
            logger.warning(msg)
            raise PermissionError(msg)

        quest.update_status(QuestStatus.IN_PROGRESS)
        if quest.quest_type == QuestType.TIMED:
            quest.set_start_time(datetime.now(timezone.utc))
            logger.info(f"Quest '{quest.title}' (ID: {quest_id}, Type: TIMED) started at {quest.start_time}.")
        else:
            logger.info(f"Quest '{quest.title}' (ID: {quest_id}) status changed to IN_PROGRESS.")


    def complete_quest(self, quest_id: str) -> None:
        
        logger.debug(f"Attempting to complete quest with ID: {quest_id}")
        quest = self.get_quest(quest_id)
        if not quest:
            msg = f"Quest with ID '{quest_id}' not found for completion."
            logger.warning(msg)
            raise ValueError(msg)
        
        if quest.status == QuestStatus.COMPLETED:
            logger.info(f"Quest '{quest.title}' (ID: {quest_id}) is already completed. No action taken.")
            return
        
        if quest.status != QuestStatus.IN_PROGRESS:
            msg = f"Quest '{quest.title}' (ID: {quest_id}) cannot be completed. Current status: {quest.status} (expected IN_PROGRESS)."
            logger.warning(msg)
            raise PermissionError(msg)
        
        if not quest.is_unlocked(self._completed_quest_ids):
            unmet_deps = sorted(list(d_id for d_id in quest.dependencies if d_id not in self._completed_quest_ids))
            msg = (f"Cannot complete quest '{quest.title}' (ID: {quest_id}). "
                   f"Dependencies not met: {unmet_deps}. This check is a safeguard.")
            logger.warning(msg)
            raise PermissionError(msg)

        quest.update_status(QuestStatus.COMPLETED)
        self._completed_quest_ids.add(quest_id)
        logger.info(f"Quest '{quest.title}' (ID: {quest_id}) marked as COMPLETED in manager.")

    def fail_quest(self, quest_id: str) -> None:

        logger.debug(f"Attempting to fail quest with ID: {quest_id}")
        quest = self.get_quest(quest_id)
        if not quest:
            msg = f"Quest with ID '{quest_id}' not found, cannot fail."
            logger.warning(msg)
            raise ValueError(msg)

        if quest.status == QuestStatus.FAILED or quest.status == QuestStatus.COMPLETED:
            logger.info(f"Quest '{quest.title}' (ID: {quest_id}) is already FAILED or COMPLETED. No action taken.")
            return
        
        if quest.status not in [QuestStatus.NOT_STARTED, QuestStatus.IN_PROGRESS]:
            msg = f"Quest '{quest.title}' (ID: {quest_id}) cannot be failed. Current status: {quest.status}."
            logger.warning(msg)
            raise PermissionError(msg)

        quest.update_status(QuestStatus.FAILED)
        if quest_id in self._completed_quest_ids:
            self._completed_quest_ids.discard(quest_id)
            logger.warning(f"Quest '{quest.title}' (ID: {quest_id}) was in completed_ids but is now FAILED. Removed from completed_ids.")
        
        logger.info(f"Quest '{quest.title}' (ID: {quest_id}) marked as FAILED.")
    
    def reset_repeatable_quest(self, quest_id: str) -> None:

        logger.debug(f"Attempting to reset repeatable quest with ID: {quest_id}")
        quest = self.get_quest(quest_id)
        if not quest:
            msg = f"Quest with ID '{quest_id}' not found, cannot reset."
            logger.warning(msg)
            raise ValueError(msg)

        if quest.quest_type != QuestType.REPEATABLE:
            msg = f"Quest '{quest.title}' (ID: {quest_id}) is not REPEATABLE. Cannot reset."
            logger.warning(msg)
            raise PermissionError(msg)

        if quest.status != QuestStatus.COMPLETED: 
            msg = (f"Repeatable quest '{quest.title}' (ID: {quest_id}) is not COMPLETED (current: {quest.status}). "
                   "Cannot reset until completed first.")
            logger.warning(msg)
            raise PermissionError(msg)
        
        quest.update_status(QuestStatus.NOT_STARTED)
        quest.clear_start_time() 
        
        if quest_id in self._completed_quest_ids:
            self._completed_quest_ids.discard(quest_id)
        
        logger.info(f"Repeatable quest '{quest.title}' (ID: {quest_id}) has been reset to NOT_STARTED.")



    def list_available_quests(self) -> List[Quest]:
        
        logger.debug("Listing available quests (status NOT_STARTED and dependencies met).")
        available = []
        for quest in self._quests.values():
            if quest.status == QuestStatus.NOT_STARTED and quest.is_unlocked(self._completed_quest_ids):
                available.append(quest)
        logger.debug(f"Found {len(available)} available quests.")
        return sorted(available, key=lambda q: q.title)

    def _is_cyclic_util(self, current_quest_id: str, visited: Set[str], recursion_stack: Set[str]) -> bool:

        visited.add(current_quest_id)
        recursion_stack.add(current_quest_id)

        quest = self._quests.get(current_quest_id)
        if not quest:
            recursion_stack.remove(current_quest_id)
            return False

        for dependency_id in quest.dependencies:
            if dependency_id not in self._quests:
                continue
            if dependency_id not in visited:
                if self._is_cyclic_util(dependency_id, visited, recursion_stack):
                    return True
            elif dependency_id in recursion_stack:
                
                return True
        
        recursion_stack.remove(current_quest_id)
        return False

    def has_cycles(self) -> bool:
        logger.debug("Performing cycle detection.")
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()
        for quest_id in list(self._quests.keys()):
            if quest_id not in visited:
                if self._is_cyclic_util(quest_id, visited, recursion_stack):
                    logger.info("Cycle detection: Cycles found in the graph.")
                    return True
        logger.info("Cycle detection: No cycles found in the graph.")
        return False


    def get_completion_order(self) -> List[str]:
        logger.debug("Attempting to get completion order (topological sort).")
        if self.has_cycles(): 
            raise ValueError("Cannot determine completion order: graph contains cycles.")
        
        in_degree: Dict[str, int] = {qid: 0 for qid in self._quests}
        adj: Dict[str, List[str]] = {qid: [] for qid in self._quests}

        for quest_id, quest_obj in self._quests.items():
            for dep_id in quest_obj.dependencies:
                if dep_id in self._quests:
                    adj[dep_id].append(quest_id)
                    in_degree[quest_id] += 1
        
        queue = deque([qid for qid, degree in in_degree.items() if degree == 0])
        topological_order: List[str] = []

        while queue:
            u = queue.popleft()
            topological_order.append(u)
            for v_id in adj[u]:
                in_degree[v_id] -= 1
                if in_degree[v_id] == 0:
                    queue.append(v_id)
        
        if len(topological_order) != len(self._quests):
            msg = ("Topological sort failed: not all quests were included in the order. "
                   "This might indicate an unexpected graph structure or remaining cycle.")
            logger.error(msg) 
            raise RuntimeError(msg)
        logger.info(f"Completion order generated successfully with {len(topological_order)} quests.")
        return topological_order


    def save_quests(self, filepath: str) -> None:

        logger.info(f"Attempting to save quests to: {filepath}")
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"Created directory for saving: {directory}")
            except OSError as e:
                logger.error(f"Could not create directory {directory}: {e}", exc_info=True)
                raise IOError(f"Could not create directory {directory}: {e}")
        
        quests_data_to_save = [quest.to_dict() for quest in self._quests.values()]
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(quests_data_to_save, f, indent=4, ensure_ascii=False)
            logger.info(f"Quests successfully saved to {filepath}. Total quests saved: {len(quests_data_to_save)}.")
        except IOError as e:
            logger.error(f"IOError while writing to file {filepath}: {e}", exc_info=True)
            raise IOError(f"Could not write to file {filepath}: {e}")
        except TypeError as e:
            logger.error(f"TypeError during JSON serialization for {filepath}: {e}", exc_info=True)
            raise TypeError(f"Error serializing quests to JSON: {e}")

    def load_quests(self, filepath: str) -> None:

        logger.info(f"Attempting to load quests from: {filepath}")
        if not os.path.exists(filepath):
            logger.warning(f"File not found for loading: {filepath}")
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
        except IOError as e:
            logger.error(f"IOError while reading file {filepath}: {e}", exc_info=True)
            raise IOError(f"Could not read file {filepath}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError while decoding file {filepath}: {e}", exc_info=True)
            raise ValueError(f"Error decoding JSON from file {filepath}: {e}")

        if not isinstance(loaded_data, list):
            msg = f"Invalid format: Expected a list of quests in {filepath}, but got {type(loaded_data).__name__}."
            logger.error(msg)
            raise ValueError(msg)
        
        logger.debug(f"Clearing current quest data before loading from {filepath}.")
        self._quests.clear()
        self._completed_quest_ids.clear() 
        
        temp_quests_to_add: List[Quest] = []
        quest_ids_from_file: Set[str] = set()

        for i, quest_data_entry in enumerate(loaded_data):
            if not isinstance(quest_data_entry, dict):
                logger.warning(f"Item #{i+1} in JSON from {filepath} is not a dictionary, skipping: {quest_data_entry}")
                continue
            try:
                quest = Quest.from_dict(quest_data_entry)
                if quest.id in quest_ids_from_file:
                    logger.warning(f"Duplicate quest ID '{quest.id}' found in file {filepath}. Using first instance, skipping subsequent.")
                    continue
                quest_ids_from_file.add(quest.id)
                temp_quests_to_add.append(quest)
            except ValueError as e:
                logger.warning(f"Skipping quest data entry #{i+1} from {filepath} due to validation error: {e}. Data: {quest_data_entry}")
        
        for quest in temp_quests_to_add:
            self._quests[quest.id] = quest

        for quest_id, quest_obj in self._quests.items():
            if quest_obj.status == QuestStatus.COMPLETED:
                self._completed_quest_ids.add(quest_id)
            logger.debug(f"Loaded quest '{quest_obj.title}' (ID: {quest_id}, Status: {quest_obj.status}, Type: {quest_obj.quest_type}) from {filepath}.")
        
        dangling_deps_removed_count = 0
        for quest_id, quest_obj in self._quests.items():
            original_deps_count = len(quest_obj.dependencies)

            for dep_id in list(quest_obj.dependencies): 
                if dep_id not in self._quests:
                    logger.warning(f"Quest '{quest_obj.title}' (ID: {quest_id}) from {filepath} has a dependency on a non-existent quest ID '{dep_id}'. Removing this dependency.")
                    quest_obj.remove_dependency(dep_id)
            if len(quest_obj.dependencies) < original_deps_count:
                dangling_deps_removed_count += (original_deps_count - len(quest_obj.dependencies))
        
        if dangling_deps_removed_count > 0:
            logger.info(f"Removed {dangling_deps_removed_count} dangling dependencies after loading from {filepath}.")

        logger.info(f"Quests successfully loaded from {filepath}. Total quests in manager: {len(self._quests)}. "
                    f"Completed (status COMPLETED): {len(self._completed_quest_ids)}.")
