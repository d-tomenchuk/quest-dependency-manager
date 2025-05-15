import unittest
from quest import Quest 
from manager import QuestManager
import os
import json
import logging

from datetime import datetime, timezone

from quest import Quest
try:
    from enums.quest_enums import QuestStatus, QuestType
except ImportError:
    logging.basicConfig(level=logging.WARNING)
    logging.warning("test_quest.py: Could not import QuestStatus and QuestType from enums.quest_enums. Using string fallbacks for tests.")
    QuestStatus = type("QuestStatus", (object,), {k: k.lower() for k in ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "FAILED"]})
    QuestType = type("QuestType", (object,), {k: k.lower() for k in ["MAIN", "SIDE", "OPTIONAL", "REPEATABLE", "TIMED"]})


class TestQuest(unittest.TestCase):

    def test_quest_creation_valid_defaults(self):
        quest1 = Quest(id="q1", title="Title 1", description="Desc 1")
        self.assertEqual(quest1.id, "q1")
        self.assertEqual(quest1.title, "Title 1")
        self.assertEqual(quest1.description, "Desc 1")
        self.assertEqual(quest1.dependencies, set())
        
        self.assertEqual(quest1.status, QuestStatus.NOT_STARTED)
        self.assertEqual(quest1.quest_type, QuestType.SIDE)
        self.assertEqual(quest1.rewards, [])
        self.assertEqual(quest1.consequences, [])
        self.assertEqual(quest1.failure_conditions, [])
        self.assertIsNone(quest1.start_time)
        self.assertFalse(quest1.completed) 

    def test_quest_creation_valid_all_fields(self):
        deps = ["dep1"]
        rewards_data = [{"type": "xp", "amount": 100}]
        consequences_data = [{"type": "lose_item", "item_id": "key"}]
        failure_data = [{"condition": "timeout"}]
        start_dt = datetime.now(timezone.utc)

        quest2 = Quest(
            id="q2", 
            title="Title 2", 
            description="Desc 2", 
            dependencies=deps,
            status=QuestStatus.IN_PROGRESS,
            quest_type=QuestType.MAIN,
            rewards=rewards_data,
            consequences=consequences_data,
            failure_conditions=failure_data,
            start_time=start_dt
        )
        self.assertEqual(quest2.id, "q2")
        self.assertEqual(quest2.dependencies, set(deps))
        self.assertEqual(quest2.status, QuestStatus.IN_PROGRESS)
        self.assertEqual(quest2.quest_type, QuestType.MAIN)
        self.assertEqual(quest2.rewards, rewards_data)
        self.assertEqual(quest2.consequences, consequences_data)
        self.assertEqual(quest2.failure_conditions, failure_data)
        self.assertEqual(quest2.start_time, start_dt)
        self.assertFalse(quest2.completed) 


        quest_completed = Quest(id="q3", title="T3", description="D3", status=QuestStatus.COMPLETED)
        self.assertTrue(quest_completed.completed)


    def test_quest_creation_invalid_id(self):
        with self.assertRaisesRegex(ValueError, "Quest ID must be a non-empty string."):
            Quest(id="", title="Title", description="Desc")
        with self.assertRaisesRegex(ValueError, "Quest ID must be a non-empty string."):
            Quest(id=None, title="Title", description="Desc")

    def test_quest_creation_invalid_title(self):
        with self.assertRaisesRegex(ValueError, "Quest title must be a non-empty string."):
            Quest(id="q1", title="", description="Desc")
        with self.assertRaisesRegex(ValueError, "Quest title must be a non-empty string."):
            Quest(id="q1", title=None, description="Desc")
            
    def test_quest_creation_invalid_description(self):
        Quest(id="q1", title="Title", description="") 
        with self.assertRaisesRegex(ValueError, "Quest description must be a string."):
            Quest(id="q1", title="Title", description=None)

    def test_quest_creation_invalid_enums_and_types(self):
        with self.assertRaisesRegex(ValueError, "Invalid quest status: invalid_status"):
            Quest(id="q_s", title="T", description="D", status="invalid_status")
        with self.assertRaisesRegex(ValueError, "Invalid quest type: invalid_type"):
            Quest(id="q_t", title="T", description="D", quest_type="invalid_type")

        with self.assertRaisesRegex(ValueError, "Rewards must be a list of dictionaries."):
            Quest(id="q_r", title="T", description="D", rewards={"not_a_list": True})
        with self.assertRaisesRegex(ValueError, "Consequences must be a list of dictionaries."):
            Quest(id="q_c", title="T", description="D", consequences="not_a_list")
        with self.assertRaisesRegex(ValueError, "Failure conditions must be a list of dictionaries."):
            Quest(id="q_f", title="T", description="D", failure_conditions=123)
        with self.assertRaisesRegex(ValueError, "Start time must be a datetime object."):
            Quest(id="q_st", title="T", description="D", start_time="not_a_datetime")


    def test_update_status(self):
        quest = Quest(id="q1", title="Title", description="Desc")
        self.assertEqual(quest.status, QuestStatus.NOT_STARTED)
        self.assertFalse(quest.completed)

        quest.update_status(QuestStatus.IN_PROGRESS)
        self.assertEqual(quest.status, QuestStatus.IN_PROGRESS)
        self.assertFalse(quest.completed)

        quest.update_status(QuestStatus.COMPLETED)
        self.assertEqual(quest.status, QuestStatus.COMPLETED)
        self.assertTrue(quest.completed)

        quest.update_status(QuestStatus.FAILED)
        self.assertEqual(quest.status, QuestStatus.FAILED)
        self.assertFalse(quest.completed)

        quest.update_status("not_started") 
        self.assertEqual(quest.status, QuestStatus.NOT_STARTED)

        with self.assertRaisesRegex(ValueError, "Invalid status value: very_invalid_status"):
            quest.update_status("very_invalid_status")


    def test_set_and_clear_start_time(self):
        quest = Quest(id="q1", title="T", description="D")
        self.assertIsNone(quest.start_time)
        
        dt1 = datetime.now(timezone.utc)
        quest.set_start_time(dt1)
        self.assertEqual(quest.start_time, dt1)

        quest.clear_start_time()
        self.assertIsNone(quest.start_time)

        with self.assertRaisesRegex(ValueError, "Time must be a datetime object."):
            quest.set_start_time("not_a_datetime_object")


    def test_add_remove_dependency(self):
        quest = Quest(id="q1", title="Title", description="Desc")
        quest.add_dependency("dep1")
        self.assertEqual(quest.dependencies, {"dep1"})
        quest.add_dependency("dep2")
        self.assertEqual(quest.dependencies, {"dep1", "dep2"})
        quest.add_dependency("dep1") 
        self.assertEqual(quest.dependencies, {"dep1", "dep2"})

        with self.assertRaisesRegex(ValueError, "Dependency quest ID must be a non-empty string."):
            quest.add_dependency("")
        with self.assertRaisesRegex(ValueError, "Dependency quest ID must be a non-empty string."):
            quest.add_dependency(None)

        quest.remove_dependency("dep1")
        self.assertEqual(quest.dependencies, {"dep2"})
        quest.remove_dependency("non_existent_dep") 
        self.assertEqual(quest.dependencies, {"dep2"})
        quest.remove_dependency("dep2")
        self.assertEqual(quest.dependencies, set())

    def test_is_unlocked(self):
        quest_no_deps = Quest(id="q_no_deps", title="T", description="D")
        quest_with_deps = Quest(id="q_deps", title="T", description="D", dependencies=["dep1", "dep2"])

        self.assertTrue(quest_no_deps.is_unlocked(set()))
        self.assertTrue(quest_no_deps.is_unlocked({"dep1", "another_dep"})) 

        self.assertFalse(quest_with_deps.is_unlocked(set()))
        self.assertFalse(quest_with_deps.is_unlocked({"dep1"}))
        self.assertTrue(quest_with_deps.is_unlocked({"dep1", "dep2"}))
        self.assertTrue(quest_with_deps.is_unlocked({"dep1", "dep2", "dep3"})) 

    def test_quest_str_repr(self):
        quest = Quest(id="q1", title="My Quest", description="D", dependencies=["dep0"], quest_type=QuestType.MAIN)
        s_initial = str(quest)
        r_initial = repr(quest) 

        self.assertIn("q1", s_initial)
        self.assertIn("My Quest", s_initial)
        self.assertIn(str(QuestStatus.NOT_STARTED).upper(), s_initial)
        self.assertIn(str(QuestType.MAIN).upper(), s_initial)
        self.assertIn("dep0", s_initial)
        
        self.assertIn("Quest(id='q1'", r_initial)
        self.assertIn("title='My Quest'", r_initial)
        self.assertIn(f"status='{str(QuestStatus.NOT_STARTED)}'", r_initial)
        self.assertIn(f"quest_type='{str(QuestType.MAIN)}'", r_initial)
        self.assertIn("dependencies=['dep0']", r_initial) 
        self.assertIn(f"rewards={[]}", r_initial) 
        self.assertIn(f"start_time=None", r_initial)
        
        quest.update_status(QuestStatus.COMPLETED)
        s_completed = str(quest)
        r_completed = repr(quest) 

        self.assertIn(str(QuestStatus.COMPLETED).upper(), s_completed)
        
        self.assertIn(f"status='{str(QuestStatus.COMPLETED)}'", r_completed)
        self.assertIn("Quest(id='q1'", r_completed)
        self.assertIn("title='My Quest'", r_completed)
        self.assertIn("dependencies=['dep0']", r_completed) 

    def test_to_dict_conversion(self):
        start_dt = datetime(2024, 5, 15, 12, 30, 0, tzinfo=timezone.utc)
        rewards_data = [{"item": "gold", "amount": 10}]
        quest = Quest(
            id="q_dict", 
            title="To Dict Test", 
            description="Testing to_dict",
            dependencies=["dep_d"],
            status=QuestStatus.IN_PROGRESS,
            quest_type=QuestType.TIMED,
            rewards=rewards_data,
            consequences=[{"effect": "anger"}],
            failure_conditions=[{"time": 300}],
            start_time=start_dt
        )
        
        d = quest.to_dict()
        
        self.assertEqual(d["id"], "q_dict")
        self.assertEqual(d["title"], "To Dict Test")
        self.assertEqual(d["description"], "Testing to_dict")
        self.assertEqual(d["dependencies"], ["dep_d"])
        self.assertEqual(d["status"], str(QuestStatus.IN_PROGRESS)) 
        self.assertEqual(d["quest_type"], str(QuestType.TIMED))  
        self.assertEqual(d["rewards"], rewards_data)
        self.assertEqual(d["consequences"], [{"effect": "anger"}])
        self.assertEqual(d["failure_conditions"], [{"time": 300}])
        self.assertEqual(d["start_time"], start_dt.isoformat()) 

    def test_from_dict_conversion(self):
        start_iso = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat()
        data = {
            "id": "q_from_dict",
            "title": "From Dict Test",
            "description": "Testing from_dict",
            "dependencies": ["dep_fd"],
            "status": str(QuestStatus.COMPLETED), 
            "quest_type": str(QuestType.OPTIONAL),
            "rewards": [{"item": "potion"}],
            "consequences": [],
            "failure_conditions": [{"reason": "too_slow"}],
            "start_time": start_iso
        }
        
        quest = Quest.from_dict(data)
        
        self.assertEqual(quest.id, "q_from_dict")
        self.assertEqual(quest.title, "From Dict Test")
        self.assertEqual(quest.status, QuestStatus.COMPLETED) 
        self.assertEqual(quest.quest_type, QuestType.OPTIONAL) 
        self.assertEqual(quest.rewards, [{"item": "potion"}])
        self.assertEqual(quest.dependencies, {"dep_fd"})
        self.assertTrue(quest.completed) 
        self.assertEqual(quest.start_time, datetime.fromisoformat(start_iso))

    def test_from_dict_defaults_and_missing_fields(self):
        data = {
            "id": "q_min",
            "title": "Minimal",
            "description": "Minimal data"
            
        }
        quest = Quest.from_dict(data)
        self.assertEqual(quest.status, QuestStatus.NOT_STARTED) 
        self.assertEqual(quest.quest_type, QuestType.SIDE)    
        self.assertEqual(quest.rewards, [])
        self.assertIsNone(quest.start_time)

    def test_from_dict_invalid_data(self):
        with self.assertRaisesRegex(ValueError, "Missing required key in quest data: 'title'"):
            Quest.from_dict({"id": "q_no_title", "description": "d"})
        
        with self.assertRaisesRegex(ValueError, "Invalid status value 'bad_status'"):
            Quest.from_dict({"id": "q", "title": "t", "description": "d", "status": "bad_status"})
        
        with self.assertRaisesRegex(ValueError, "Invalid quest_type value 'bad_type'"):
            Quest.from_dict({"id": "q", "title": "t", "description": "d", "quest_type": "bad_type"})

        with self.assertRaisesRegex(ValueError, "Invalid start_time format 'not_iso_date'"):
            Quest.from_dict({"id": "q", "title": "t", "description": "d", "start_time": "not_iso_date"})
        
        with self.assertRaisesRegex(ValueError, "Rewards must be a list"): 
            Quest.from_dict({"id": "q", "title": "t", "description": "d", "rewards": "not_a_list"})

if __name__ == '__main__':

    
    if not os.path.exists('tests'):
        os.makedirs('tests')

    unittest.main(verbosity=2)