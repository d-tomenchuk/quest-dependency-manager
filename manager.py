from typing import Dict, List, Optional, Set
from collections import deque
from quest import Quest

class QuestManager:
    def __init__(self):
        self._quests: Dict[str, Quest] = {}
        self._completed_quest_ids: Set[str] = set()

    def add_quest(self, quest: Quest) -> None:

        if quest.id in self._quests:
            raise ValueError(f"Quest with ID '{quest.id}' already exists.")
        self._quests[quest.id] = quest

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        return self._quests.get(quest_id)

    def complete_quest(self, quest_id: str) -> None:
        quest = self.get_quest(quest_id)

        if not quest:
            raise ValueError(f"Quest with ID '{quest_id}' not found.")
        
        if quest.completed:
            print(f"Quest '{quest_id}' is already completed.")
            return

        if not quest.is_unlocked(self._completed_quest_ids):
            raise PermissionError(f"Cannot complete quest '{quest_id}'. Dependencies not met: "
                                  f"{sorted(list(quest.dependencies - self._completed_quest_ids))}")

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
        if quest: 
            
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

        for quest_id in self._quests:
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

            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        if len(topological_order) != len(self._quests):
            raise RuntimeError("Topological sort failed unexpectedly after cycle check.")

        return topological_order