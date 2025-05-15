import unittest
from quest import Quest 
from manager import QuestManager
import os
import json
import logging

class TestQuest(unittest.TestCase):

    def test_quest_creation_valid(self):
        quest1 = Quest(id="q1", title="Title 1", description="Desc 1")
        self.assertEqual(quest1.id, "q1")
        self.assertEqual(quest1.title, "Title 1")
        self.assertEqual(quest1.description, "Desc 1")
        self.assertEqual(quest1.dependencies, set())
        self.assertFalse(quest1.completed)

        quest2 = Quest(id="q2", title="Title 2", description="Desc 2", dependencies=["q1"])
        self.assertEqual(quest2.id, "q2")
        self.assertEqual(quest2.dependencies, {"q1"})
        self.assertFalse(quest2.completed)

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
        # Description can be empty, but not None
        Quest(id="q1", title="Title", description="") # Should be fine
        with self.assertRaisesRegex(ValueError, "Quest description must be a string."):
            Quest(id="q1", title="Title", description=None)

    def test_mark_as_completed_pending(self):
        quest = Quest(id="q1", title="Title", description="Desc")
        self.assertFalse(quest.completed)
        quest.mark_as_completed()
        self.assertTrue(quest.completed)
        quest.mark_as_pending()
        self.assertFalse(quest.completed)

    def test_add_remove_dependency(self):
        quest = Quest(id="q1", title="Title", description="Desc")
        quest.add_dependency("dep1")
        self.assertEqual(quest.dependencies, {"dep1"})
        quest.add_dependency("dep2")
        self.assertEqual(quest.dependencies, {"dep1", "dep2"})
        quest.add_dependency("dep1") # Adding same dependency should not change the set
        self.assertEqual(quest.dependencies, {"dep1", "dep2"})

        with self.assertRaisesRegex(ValueError, "Dependency quest ID must be a non-empty string."):
            quest.add_dependency("")
        with self.assertRaisesRegex(ValueError, "Dependency quest ID must be a non-empty string."):
            quest.add_dependency(None)

        quest.remove_dependency("dep1")
        self.assertEqual(quest.dependencies, {"dep2"})
        quest.remove_dependency("non_existent_dep") # Should not raise error
        self.assertEqual(quest.dependencies, {"dep2"})
        quest.remove_dependency("dep2")
        self.assertEqual(quest.dependencies, set())

    def test_is_unlocked(self):
        quest_no_deps = Quest(id="q_no_deps", title="T", description="D")
        quest_with_deps = Quest(id="q_deps", title="T", description="D", dependencies=["dep1", "dep2"])

        self.assertTrue(quest_no_deps.is_unlocked(set()))
        self.assertTrue(quest_no_deps.is_unlocked({"dep1", "another_dep"})) # Extra completed quests don't matter

        self.assertFalse(quest_with_deps.is_unlocked(set()))
        self.assertFalse(quest_with_deps.is_unlocked({"dep1"}))
        self.assertTrue(quest_with_deps.is_unlocked({"dep1", "dep2"}))
        self.assertTrue(quest_with_deps.is_unlocked({"dep1", "dep2", "dep3"})) # Superset of dependencies

    def test_quest_str_repr(self):
        quest = Quest(id="q1", title="My Quest", description="Desc", dependencies=["dep0"])
        self.assertTrue("q1" in str(quest))
        self.assertTrue("My Quest" in str(quest))
        self.assertTrue("PENDING" in str(quest))
        self.assertTrue("dep0" in str(quest))
        
        quest.mark_as_completed()
        self.assertTrue("DONE" in str(quest))

        self.assertTrue("Quest(id='q1'" in repr(quest))
        self.assertTrue("title='My Quest'" in repr(quest))
        self.assertTrue("dependencies=['dep0']" in repr(quest) or "dependencies={'dep0'}" in repr(quest)) # Order in set for repr might vary
        self.assertTrue("completed=True" in repr(quest))


class TestQuestManager(unittest.TestCase):

    def setUp(self):
        """Set up a new QuestManager and some common quests for each test."""
        self.manager = QuestManager()
        self.q1 = Quest(id="q1", title="Quest 1", description="First quest, no deps.")
        self.q2 = Quest(id="q2", title="Quest 2", description="Depends on q1.", dependencies=["q1"])
        self.q3 = Quest(id="q3", title="Quest 3", description="Depends on q1 and q2.", dependencies=["q1", "q2"])
        self.q_independent = Quest(id="q_ind", title="Independent", description="No dependencies.")
        # For cycle tests
        self.qc1 = Quest(id="qc1", title="Cycle 1", description="Part of cycle", dependencies=["qc2"])
        self.qc2 = Quest(id="qc2", title="Cycle 2", description="Part of cycle", dependencies=["qc1"]) # Simple A->B, B->A
        self.qc3 = Quest(id="qc3", title="Cycle 3", description="Completes cycle", dependencies=["qc1"]) # A->B, B->C, C->A (if qc2 dep on qc3)

    def test_add_quest_valid(self):
        self.manager.add_quest(self.q1)
        self.assertIn("q1", self.manager._quests)
        self.assertEqual(self.manager.get_quest("q1"), self.q1)

    def test_add_quest_duplicate_id(self):
        self.manager.add_quest(self.q1)
        q_dup = Quest(id="q1", title="Duplicate Quest", description="This should fail.")
        with self.assertRaisesRegex(ValueError, "Quest with ID 'q1' already exists."):
            self.manager.add_quest(q_dup)

    def test_get_quest(self):
        self.manager.add_quest(self.q1)
        self.assertEqual(self.manager.get_quest("q1"), self.q1)
        self.assertIsNone(self.manager.get_quest("non_existent_id"))

    def test_complete_quest_valid_no_deps(self):
        self.manager.add_quest(self.q1)
        self.manager.complete_quest("q1")
        self.assertTrue(self.q1.completed)
        self.assertIn("q1", self.manager._completed_quest_ids)

    def test_complete_quest_valid_with_deps(self):
        self.manager.add_quest(self.q1)
        self.manager.add_quest(self.q2) # q2 depends on q1
        
        self.manager.complete_quest("q1") # Complete q1 first
        self.manager.complete_quest("q2") # Now q2 can be completed
        self.assertTrue(self.q2.completed)
        self.assertIn("q2", self.manager._completed_quest_ids)

    def test_complete_quest_not_found(self):
        with self.assertRaisesRegex(ValueError, "Quest with ID 'non_existent' not found."):
            self.manager.complete_quest("non_existent")

    def test_complete_quest_already_completed(self):
        self.manager.add_quest(self.q1)
        self.manager.complete_quest("q1")
        # Should not raise an error, just print a message (tested via lack of exception and state)
        try:
            self.manager.complete_quest("q1") 
        except Exception as e:
            self.fail(f"Completing an already completed quest raised an unexpected exception: {e}")
        self.assertTrue(self.q1.completed) # Still completed

    def test_complete_quest_dependencies_not_met(self):
        self.manager.add_quest(self.q1)
        self.manager.add_quest(self.q2) # q2 depends on q1
        expected_error_regex = "Cannot complete quest 'Quest 2' \\(ID: q2\\). Dependencies not met: \\['q1'\\]"
        with self.assertRaisesRegex(PermissionError, expected_error_regex):
            self.manager.complete_quest("q2")
        self.assertFalse(self.q2.completed)

    def test_list_available_quests(self):
        self.assertEqual(self.manager.list_available_quests(), []) # No quests added

        self.manager.add_quest(self.q1) # No deps
        self.manager.add_quest(self.q2) # Depends on q1
        self.manager.add_quest(self.q_independent) # No deps

        available = self.manager.list_available_quests()
        self.assertIn(self.q1, available)
        self.assertIn(self.q_independent, available)
        self.assertNotIn(self.q2, available)
        self.assertEqual(len(available), 2)

        self.manager.complete_quest("q1")
        available_after_q1_done = self.manager.list_available_quests()
        self.assertIn(self.q2, available_after_q1_done) # q2 now available
        self.assertIn(self.q_independent, available_after_q1_done)
        self.assertNotIn(self.q1, available_after_q1_done) # q1 is completed
        self.assertEqual(len(available_after_q1_done), 2)
        
        self.manager.complete_quest("q2")
        self.manager.complete_quest("q_ind")
        self.assertEqual(self.manager.list_available_quests(), [])


    def test_has_cycles_no_cycle(self):
        self.manager.add_quest(self.q1)
        self.manager.add_quest(self.q2) # q1 -> q2
        self.manager.add_quest(self.q3) # q1 -> q3, q2 -> q3
        self.assertFalse(self.manager.has_cycles())

    def test_has_cycles_simple_direct_cycle(self):
        # qc1 -> qc2, qc2 -> qc1
        self.manager.add_quest(self.qc1)
        self.manager.add_quest(self.qc2)
        self.assertTrue(self.manager.has_cycles())

    def test_has_cycles_longer_cycle(self):
        # q_a -> q_b -> q_c -> q_a
        q_a = Quest("qa", "A", "desc", ["qc"])
        q_b = Quest("qb", "B", "desc", ["qa"])
        q_c = Quest("qc", "C", "desc", ["qb"])
        self.manager.add_quest(q_a)
        self.manager.add_quest(q_b)
        self.manager.add_quest(q_c)
        self.assertTrue(self.manager.has_cycles())
        
    def test_has_cycles_unrelated_paths_with_cycle(self):
        self.manager.add_quest(self.q1) # q1 (no cycle part)
        self.manager.add_quest(self.qc1) # qc1 -> qc2
        self.manager.add_quest(self.qc2) # qc2 -> qc1 (cycle part)
        self.assertTrue(self.manager.has_cycles())

    def test_has_cycles_dependency_on_non_existent_quest(self):
        q_dep_non_exist = Quest("q_non", "Non", "desc", ["non_existent_id"])
        self.manager.add_quest(q_dep_non_exist)
        self.assertFalse(self.manager.has_cycles()) # A non-existent dependency is not a cycle itself


    def test_get_completion_order_no_cycle(self):
        self.manager.add_quest(self.q1)
        self.manager.add_quest(self.q2) # q1 -> q2
        self.manager.add_quest(self.q_independent)
        
        order = self.manager.get_completion_order()
        self.assertEqual(len(order), 3)
        self.assertIn("q1", order)
        self.assertIn("q2", order)
        self.assertIn("q_ind", order)
        
        # q1 must come before q2
        self.assertLess(order.index("q1"), order.index("q2"))
        # q_independent can be anywhere relative to q1/q2 as long as q1 is before q2

    def test_get_completion_order_complex_dag(self):
        # A -> B, A -> C, B -> D, C -> D
        qA = Quest("A", "A", "", [])
        qB = Quest("B", "B", "", ["A"])
        qC = Quest("C", "C", "", ["A"])
        qD = Quest("D", "D", "", ["B", "C"])
        qE = Quest("E", "E", "", []) 
        
        self.manager.add_quest(qA)
        self.manager.add_quest(qB)
        self.manager.add_quest(qC)
        self.manager.add_quest(qD)
        self.manager.add_quest(qE)
        
        order = self.manager.get_completion_order()
        self.assertEqual(len(order), 5)
        self.assertLess(order.index("A"), order.index("B"))
        self.assertLess(order.index("A"), order.index("C"))
        self.assertLess(order.index("B"), order.index("D"))
        self.assertLess(order.index("C"), order.index("D"))

    def test_get_completion_order_with_cycle(self):
        self.manager.add_quest(self.qc1) # qc1 -> qc2
        self.manager.add_quest(self.qc2) # qc2 -> qc1
        with self.assertRaisesRegex(ValueError, "Cannot determine completion order: graph contains cycles."):
            self.manager.get_completion_order()

    def test_get_completion_order_empty_manager(self):
        order = self.manager.get_completion_order()
        self.assertEqual(order, [])

    def test_get_completion_order_dependency_on_non_existent_quest(self):
        q_dep_non_exist = Quest("q_non", "Non", "desc", ["non_existent_id"])
        self.manager.add_quest(q_dep_non_exist)
        self.manager.add_quest(self.q1) 
        
        order = self.manager.get_completion_order()
        self.assertEqual(len(order), 2)
        self.assertIn("q_non", order)
        self.assertIn("q1", order)

    def tearDown(self):

        test_files_to_remove = [
            "test_quests.json",
            "test_invalid_format.json",
            "test_decode_error.json",
            "test_missing_keys.json",
            "test_sample_like.json",
            os.path.join("data_test_save", "nested_quests.json")
        ]
        for test_file in test_files_to_remove:
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except OSError as e:
                    print(f"Warning: Could not remove test file {test_file}: {e}")
        
        
        data_dir_for_tests = "data_test_save"
        if os.path.exists(data_dir_for_tests):
            try:
                if not os.listdir(data_dir_for_tests): 
                    os.rmdir(data_dir_for_tests)
            except OSError as e:
                 print(f"Warning: Could not remove test directory {data_dir_for_tests}: {e}")


    def test_save_and_load_quests(self):
        test_filepath = "test_quests.json"
        if os.path.exists(test_filepath): 
            os.remove(test_filepath)

 
        q1 = Quest(id="s_q1", title="Save Q1", description="Desc Q1", completed=False)
        q2 = Quest(id="s_q2", title="Save Q2", description="Desc Q2", dependencies=["s_q1"], completed=True)
        
        self.manager.add_quest(q1)
        self.manager.add_quest(q2)
                                  
        self.manager.save_quests(test_filepath)
        self.assertTrue(os.path.exists(test_filepath))

        
        new_manager = QuestManager()
        new_manager.load_quests(test_filepath)

        self.assertEqual(len(new_manager._quests), 2)
        
        loaded_q1 = new_manager.get_quest("s_q1")
        loaded_q2 = new_manager.get_quest("s_q2")

        self.assertIsNotNone(loaded_q1)
        self.assertEqual(loaded_q1.title, "Save Q1")
        self.assertFalse(loaded_q1.completed, "Loaded q1 should not be completed")
        self.assertNotIn("s_q1", new_manager._completed_quest_ids, "s_q1 should not be in completed_ids set")

        self.assertIsNotNone(loaded_q2)
        self.assertEqual(loaded_q2.title, "Save Q2")
        self.assertTrue(loaded_q2.completed, "Loaded q2 should be completed as per saved data")
        self.assertEqual(loaded_q2.dependencies, {"s_q1"})
        self.assertIn("s_q2", new_manager._completed_quest_ids, "s_q2 should be in completed_ids set after load")

    def test_save_quests_creates_directory(self):
        
        nested_filepath = os.path.join("data_test_save", "nested_quests.json")
        if os.path.exists(nested_filepath): os.remove(nested_filepath)
        if os.path.exists(os.path.dirname(nested_filepath)): os.rmdir(os.path.dirname(nested_filepath))
        
        
        self.manager.add_quest(Quest(id="q_temp", title="Temp", description="Temp quest"))
        
        self.manager.save_quests(nested_filepath)
        self.assertTrue(os.path.exists(nested_filepath))
        


    def test_load_quests_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.load_quests("non_existent_file_definitely.json")

    def test_load_quests_invalid_json_structure_not_a_list(self):
        test_filepath = "test_invalid_format.json"
        with open(test_filepath, 'w', encoding='utf-8') as f:
            f.write('{"not": "a list"}') 
        
        with self.assertRaisesRegex(ValueError, "Invalid format: Expected a list of quests"):
            self.manager.load_quests(test_filepath)
        

    def test_load_quests_json_decode_error(self):
        test_filepath = "test_decode_error.json"
        with open(test_filepath, 'w', encoding='utf-8') as f:
            f.write('this is not valid json {')
        
        with self.assertRaisesRegex(ValueError, "Error decoding JSON"):
            self.manager.load_quests(test_filepath)
        

    def test_load_quests_missing_required_keys_in_quest_data(self):
        test_filepath = "test_missing_keys.json"
        
        data_with_missing_key = [
            {"id": "q_ok", "title":"OK Quest", "description":"This is fine", "dependencies":[], "completed":False},
            {"id": "q_bad", "description": "desc only no title"}
        ]
        with open(test_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_with_missing_key, f)
        
        self.manager.load_quests(test_filepath)
        self.assertEqual(len(self.manager._quests), 1, "Only one quest should be loaded")
        self.assertIsNotNone(self.manager.get_quest("q_ok"))
        self.assertIsNone(self.manager.get_quest("q_bad"))


    def test_load_from_sample_json_like_structure_no_completed_field(self):

        sample_like_filepath = "test_sample_like.json"
        sample_data = [
            {"id": "sample_0", "title": "Hero's Awakening", "description": "Desc", "dependencies": []},
            {"id": "sample_1", "title": "Find Sword", "description": "Desc", "dependencies": ["sample_0"]}
        ] 
        with open(sample_like_filepath, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f)

        self.manager.load_quests(sample_like_filepath)
        self.assertEqual(len(self.manager._quests), 2)
        
        q0 = self.manager.get_quest("sample_0")
        self.assertIsNotNone(q0)
        self.assertFalse(q0.completed, "Quest loaded without 'completed' field should default to False")
        self.assertNotIn("sample_0", self.manager._completed_quest_ids)

        q1 = self.manager.get_quest("sample_1")
        self.assertIsNotNone(q1)
        self.assertFalse(q1.completed)
        self.assertEqual(q1.dependencies, {"sample_0"})
        self.assertNotIn("sample_1", self.manager._completed_quest_ids)
        

    def test_load_quests_duplicate_ids_in_file(self):
        test_filepath = "test_duplicate_ids_in_file.json"
        duplicate_id_data = [
            {"id": "dup1", "title": "First Dup", "description": "Desc1", "completed": False},
            {"id": "dup1", "title": "Second Dup", "description": "Desc2", "completed": True}, 
            {"id": "uniq1", "title": "Unique", "description": "DescUniq", "completed": False}
        ]
        with open(test_filepath, 'w', encoding='utf-8') as f:
            json.dump(duplicate_id_data, f)

        self.manager.load_quests(test_filepath)
        self.assertEqual(len(self.manager._quests), 2)
        
        loaded_dup1 = self.manager.get_quest("dup1")
        self.assertIsNotNone(loaded_dup1)
        self.assertEqual(loaded_dup1.title, "First Dup") 
        self.assertFalse(loaded_dup1.completed)
        self.assertNotIn("dup1", self.manager._completed_quest_ids) 

        self.assertIsNotNone(self.manager.get_quest("uniq1"))
        

    def test_load_quests_removes_dangling_dependencies(self):
        test_filepath = "test_dangling_deps.json"
        data_with_dangling_dep = [
            {"id": "q_valid", "title": "Valid Quest", "description": "Desc", "dependencies": ["non_existent_dep_id"], "completed": False},
            {"id": "q_another", "title": "Another", "description": "Desc", "dependencies": [], "completed": True}
        ]
        with open(test_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_with_dangling_dep, f)

        self.manager.load_quests(test_filepath)
        self.assertEqual(len(self.manager._quests), 2)

        loaded_q_valid = self.manager.get_quest("q_valid")
        self.assertIsNotNone(loaded_q_valid)
        self.assertEqual(loaded_q_valid.dependencies, set(), "Dangling dependency should have been removed")

        loaded_q_another = self.manager.get_quest("q_another")
        self.assertIsNotNone(loaded_q_another)
        self.assertTrue(loaded_q_another.completed)
        self.assertIn("q_another", self.manager._completed_quest_ids)
    
    def test_load_quests_logs_warning_for_bad_entry_in_file(self):
            
            bad_data_filepath = "test_bad_data_for_log_check.json"
            test_data = [
                {"id": "log_q1", "title": "Log Quest 1", "description": "Correct entry"}, 
                {"id": "log_q2"}  
            ]
            with open(bad_data_filepath, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            with self.assertLogs(logger='manager', level='WARNING') as cm:
                self.manager.load_quests(bad_data_filepath) 
                

            
            self.assertTrue(len(cm.records) > 0, "No WARNING messages were logged.")

            found_expected_log = False
            for record in cm.output: 
                if "Skipping quest data entry" in record and "log_q2" in record:
                    found_expected_log = True
                    break
            self.assertTrue(found_expected_log, "Expected warning log for bad quest entry was not found.")


            self.assertIsNotNone(self.manager.get_quest("log_q1"))
            self.assertIsNone(self.manager.get_quest("log_q2")) 

            if os.path.exists(bad_data_filepath):
                os.remove(bad_data_filepath)
        

if __name__ == '__main__':

    
    if not os.path.exists('tests'):
        os.makedirs('tests')

    unittest.main(verbosity=2)