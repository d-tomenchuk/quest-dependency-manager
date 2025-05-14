import unittest
from quest import Quest 
from manager import QuestManager
import os

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
        with self.assertRaisesRegex(PermissionError, "Cannot complete quest 'q2'. Dependencies not met: \\['q1'\\]"):
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


if __name__ == '__main__':

    
    if not os.path.exists('tests'):
        os.makedirs('tests')

    unittest.main(verbosity=2)