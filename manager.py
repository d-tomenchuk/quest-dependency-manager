# manager.py

from typing import Dict, List, Optional, Set
from collections import deque
import json 
import os   


from quest import Quest

class QuestManager:
    def __init__(self):
        self._quests: Dict[str, Quest] = {}
        self._completed_quest_ids: Set[str] = set() 

    def add_quest(self, quest: Quest) -> None:
        if quest.id in self._quests:
            raise ValueError(f"Quest with ID '{quest.id}' already exists.")
        
        
        for dep_id in quest.dependencies:
            if not isinstance(dep_id, str) or not dep_id.strip():
                raise ValueError(f"Invalid dependency ID '{dep_id}' for quest '{quest.id}'. Must be a non-empty string.")

        self._quests[quest.id] = quest

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        return self._quests.get(quest_id)

    def complete_quest(self, quest_id: str) -> None:
        quest = self.get_quest(quest_id)
        if not quest:
            raise ValueError(f"Quest with ID '{quest_id}' not found.")
        if quest.completed:
            print(f"Quest '{quest.title}' (ID: {quest_id}) is already completed.")
            return

        if not quest.is_unlocked(self._completed_quest_ids):

            unmet_deps = sorted(list(d_id for d_id in quest.dependencies if d_id not in self._completed_quest_ids))
            raise PermissionError(f"Cannot complete quest '{quest.title}' (ID: {quest_id}). "
                                  f"Dependencies not met: {unmet_deps}")

        quest.mark_as_completed()
        self._completed_quest_ids.add(quest_id)
        print(f"Quest '{quest.title}' (ID: {quest_id}) marked as completed.")


    def list_available_quests(self) -> List[Quest]:
        available = []
        for quest in self._quests.values():
            if not quest.completed and quest.is_unlocked(self._completed_quest_ids):
                available.append(quest)
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
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()

        for quest_id in list(self._quests.keys()): 
            if quest_id not in visited:
                if self._is_cyclic_util(quest_id, visited, recursion_stack):
                    return True
        return False

    def get_completion_order(self) -> List[str]:
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

            for v_id in adj[u]: # v_id это ID квеста, который зависит от u
                in_degree[v_id] -= 1
                if in_degree[v_id] == 0:
                    queue.append(v_id)
        
        if len(topological_order) != len(self._quests):

            raise RuntimeError("Topological sort failed: not all quests were included in the order. "
                               "This might indicate an unexpected graph structure or remaining cycle.")

        return topological_order

    def save_quests(self, filepath: str) -> None:
       
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True) 
            except OSError as e:
                
                raise IOError(f"Could not create directory {directory}: {e}")

        
        quests_data_to_save = [quest.to_dict() for quest in self._quests.values()]
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(quests_data_to_save, f, indent=4, ensure_ascii=False)
            print(f"Quests successfully saved to {filepath}")
        except IOError as e:
            
            raise IOError(f"Could not write to file {filepath}: {e}")
        except TypeError as e:
            
            raise TypeError(f"Error serializing quests to JSON: {e}")


    def load_quests(self, filepath: str) -> None:
        """Loads quests from a JSON file, replacing current quests and completion statuses."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
        except IOError as e:
            raise IOError(f"Could not read file {filepath}: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from file {filepath}: {e}")

        if not isinstance(loaded_data, list):
            raise ValueError(f"Invalid format: Expected a list of quests in {filepath}, but got {type(loaded_data).__name__}.")

        
        self._quests.clear()
        self._completed_quest_ids.clear()
        
        temp_quests_to_add: List[Quest] = []
        quest_ids_from_file: Set[str] = set()

        for i, quest_data_entry in enumerate(loaded_data):
            if not isinstance(quest_data_entry, dict):
                print(f"Warning: Item #{i+1} in JSON is not a dictionary, skipping: {quest_data_entry}")
                continue
            try:
                quest = Quest.from_dict(quest_data_entry)
                if quest.id in quest_ids_from_file:
                    print(f"Warning: Duplicate quest ID '{quest.id}' found in file. Using first instance.")
                    continue 
                quest_ids_from_file.add(quest.id)
                temp_quests_to_add.append(quest)
            except ValueError as e: 
                print(f"Warning: Skipping quest data entry #{i+1} due to error: {e}. Data: {quest_data_entry}")
        
        
        for quest in temp_quests_to_add:
            
            self._quests[quest.id] = quest
            if quest.completed:
                self._completed_quest_ids.add(quest.id)
        
        
        for quest_id, quest_obj in self._quests.items():
            for dep_id in list(quest_obj.dependencies): 
                if dep_id not in self._quests:
                    print(f"Warning: Quest '{quest_obj.title}' (ID: {quest_id}) has a dependency on a non-existent quest ID '{dep_id}'. Removing this dependency.")
                    quest_obj.remove_dependency(dep_id) 

        print(f"Quests successfully loaded from {filepath}. Total quests in manager: {len(self._quests)}. Completed: {len(self._completed_quest_ids)}.")