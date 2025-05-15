import unittest
from quest import Quest
from manager import QuestManager
import os
import json
import logging 
from datetime import datetime, timezone  


try:
    from enums.quest_enums import QuestStatus, QuestType
except ImportError:
    logging.warning("test_manager.py: Could not import QuestStatus and QuestType from enums.quest_enums. Using string fallbacks for tests.")
    QuestStatus = type("QuestStatus", (object,), {k: k.lower() for k in ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "FAILED"]})
    QuestType = type("QuestType", (object,), {k: k.lower() for k in ["MAIN", "SIDE", "OPTIONAL", "REPEATABLE", "TIMED"]})


class TestQuestManager(unittest.TestCase):

    def setUp(self):
        self.manager = QuestManager()

        self.q_not_started = Quest(id="q_ns", title="Not Started Quest", description="NS quest desc")
        self.q_dep_on_ns = Quest(id="q_dep_ns", title="Depends on NS", description="Dep NS desc", dependencies=["q_ns"])
        
        self.q_main = Quest(id="q_main", title="Main Quest", description="Main story", quest_type=QuestType.MAIN)
        self.q_side_completed = Quest(id="q_side_done", title="Side Completed", description="Side done", 
                                      status=QuestStatus.COMPLETED, quest_type=QuestType.SIDE)


    def test_add_quest_valid(self):
        self.manager.add_quest(self.q_not_started)
        self.assertIn(self.q_not_started.id, self.manager._quests)
        self.assertEqual(self.manager.get_quest(self.q_not_started.id), self.q_not_started)

        self.assertNotIn(self.q_not_started.id, self.manager._completed_quest_ids)

        self.manager.add_quest(self.q_side_completed) 
        self.assertIn(self.q_side_completed.id, self.manager._quests)

        self.assertIn(self.q_side_completed.id, self.manager._completed_quest_ids)


    def test_add_quest_duplicate_id(self):
        self.manager.add_quest(self.q_not_started)
        q_dup = Quest(id=self.q_not_started.id, title="Duplicate", description="This should fail.")
        with self.assertRaisesRegex(ValueError, f"Quest with ID '{self.q_not_started.id}' already exists."):
            self.manager.add_quest(q_dup)

    def test_get_quest(self):
        self.manager.add_quest(self.q_main)
        self.assertEqual(self.manager.get_quest(self.q_main.id), self.q_main)
        self.assertIsNone(self.manager.get_quest("non_existent_id"))

    def test_start_quest_success(self):
        q1 = Quest(id="q1_start", title="Startable", description="Can start")
        q2_timed = Quest(id="q2_timed_start", title="Timed Startable", description="Can start timed", quest_type=QuestType.TIMED)
        self.manager.add_quest(q1)
        self.manager.add_quest(q2_timed)

        self.manager.start_quest(q1.id)
        self.assertEqual(q1.status, QuestStatus.IN_PROGRESS)
        self.assertIsNone(q1.start_time) 

        self.manager.start_quest(q2_timed.id)
        self.assertEqual(q2_timed.status, QuestStatus.IN_PROGRESS)
        self.assertIsNotNone(q2_timed.start_time)
        self.assertTrue(isinstance(q2_timed.start_time, datetime))

    def test_start_quest_failures(self):
        q_started = Quest(id="q_started", title="Already Started", description="desc", status=QuestStatus.IN_PROGRESS)
        q_completed = Quest(id="q_completed", title="Already Completed", description="desc", status=QuestStatus.COMPLETED)
        q_no_deps_met = Quest(id="q_no_deps", title="Deps not met", description="desc", dependencies=["missing_dep"])
        
        self.manager.add_quest(q_started)
        self.manager.add_quest(q_completed)
        self.manager.add_quest(q_no_deps_met)

        with self.assertRaisesRegex(PermissionError, "is not in NOT_STARTED state"):
            self.manager.start_quest(q_started.id)
        with self.assertRaisesRegex(PermissionError, "is not in NOT_STARTED state"):
            self.manager.start_quest(q_completed.id)
        
        with self.assertRaisesRegex(PermissionError, "Dependencies not met: \\['missing_dep'\\]"):
            self.manager.start_quest(q_no_deps_met.id)
            
        with self.assertRaisesRegex(ValueError, "not found, cannot start"):
            self.manager.start_quest("non_existent_quest_id")

    def test_complete_quest_success_flow(self):
        q1 = Quest(id="q1_flow", title="Part 1", description="d")
        q2 = Quest(id="q2_flow", title="Part 2", description="d", dependencies=["q1_flow"])
        self.manager.add_quest(q1)
        self.manager.add_quest(q2)


        self.manager.start_quest(q1.id)
        self.assertEqual(q1.status, QuestStatus.IN_PROGRESS)
        

        self.manager.complete_quest(q1.id)
        self.assertEqual(q1.status, QuestStatus.COMPLETED)
        self.assertIn(q1.id, self.manager._completed_quest_ids)


        self.manager.start_quest(q2.id)
        self.assertEqual(q2.status, QuestStatus.IN_PROGRESS)


        self.manager.complete_quest(q2.id)
        self.assertEqual(q2.status, QuestStatus.COMPLETED)
        self.assertIn(q2.id, self.manager._completed_quest_ids)


    def test_complete_quest_failures(self):
        q_not_started = Quest(id="q_ns_comp", title="Not Started For Completion", description="d")
        q_already_completed = Quest(id="q_ac_comp", title="Already Completed For Completion", description="d", status=QuestStatus.COMPLETED)
        self.manager.add_quest(q_not_started)
        self.manager.add_quest(q_already_completed)

        with self.assertRaisesRegex(PermissionError, "Current status: not_started \\(expected IN_PROGRESS\\)"):
            self.manager.complete_quest(q_not_started.id)
        
        try:
            self.manager.complete_quest(q_already_completed.id)
        except Exception as e:
            self.fail(f"Completing an already completed quest raised an unexpected exception: {e}")
        self.assertEqual(q_already_completed.status, QuestStatus.COMPLETED)

        with self.assertRaisesRegex(ValueError, "not found for completion"):
            self.manager.complete_quest("non_existent_quest_id_for_completion")


    def test_fail_quest_success_and_edge_cases(self):
        q_ns = Quest(id="q_ns_fail", title="NS Fail", description="d")
        q_ip = Quest(id="q_ip_fail", title="IP Fail", description="d")
        q_comp = Quest(id="q_c_fail", title="COMP Fail", description="d", status=QuestStatus.COMPLETED)
        
        self.manager.add_quest(q_ns)
        self.manager.add_quest(q_ip)
        self.manager.add_quest(q_comp)
        self.manager._completed_quest_ids.add(q_comp.id) 


        self.manager.start_quest(q_ip.id)

        self.manager.fail_quest(q_ns.id)
        self.assertEqual(q_ns.status, QuestStatus.FAILED)
        self.assertNotIn(q_ns.id, self.manager._completed_quest_ids)

        self.manager.fail_quest(q_ip.id)
        self.assertEqual(q_ip.status, QuestStatus.FAILED)
        self.assertNotIn(q_ip.id, self.manager._completed_quest_ids)

        initial_completed_ids = self.manager._completed_quest_ids.copy()
        self.manager.fail_quest(q_comp.id)
        self.assertEqual(q_comp.status, QuestStatus.COMPLETED) 
        self.assertEqual(self.manager._completed_quest_ids, initial_completed_ids) 

        with self.assertRaisesRegex(ValueError, "not found, cannot fail"):
            self.manager.fail_quest("non_existent_quest_id_for_fail")


    def test_reset_repeatable_quest(self):
        q_repeat = Quest(id="q_rep", title="Repeatable", description="d", quest_type=QuestType.REPEATABLE)
        q_not_repeat = Quest(id="q_not_rep", title="Not Repeatable", description="d", quest_type=QuestType.SIDE)
        
        self.manager.add_quest(q_repeat)
        self.manager.add_quest(q_not_repeat)
        self.manager.start_quest(q_repeat.id)
        self.manager.complete_quest(q_repeat.id)
        self.assertEqual(q_repeat.status, QuestStatus.COMPLETED)
        self.assertIn(q_repeat.id, self.manager._completed_quest_ids)

        if q_repeat.quest_type == QuestType.TIMED and q_repeat.start_time is None: 
             q_repeat.set_start_time(datetime.utcnow())



        self.manager.reset_repeatable_quest(q_repeat.id)
        self.assertEqual(q_repeat.status, QuestStatus.NOT_STARTED)
        self.assertNotIn(q_repeat.id, self.manager._completed_quest_ids)
        self.assertIsNone(q_repeat.start_time) 


        with self.assertRaisesRegex(PermissionError, "is not REPEATABLE"):
            self.manager.reset_repeatable_quest(q_not_repeat.id)
        
        q_repeat_not_completed = Quest(id="q_rep_ns", title="Rep NS", description="d", quest_type=QuestType.REPEATABLE)
        self.manager.add_quest(q_repeat_not_completed)
        with self.assertRaisesRegex(PermissionError, "is not COMPLETED"):
            self.manager.reset_repeatable_quest(q_repeat_not_completed.id) 

        with self.assertRaisesRegex(ValueError, "not found, cannot reset"):
            self.manager.reset_repeatable_quest("non_existent_for_reset")


    def test_list_available_quests(self):
        q1 = Quest(id="q1_avail", title="A1", description="d") 
        q2_dep_q1 = Quest(id="q2_dep_avail", title="A2", description="d", dependencies=["q1_avail"]) 
        q3_initially_available = Quest(id="q3_ia_avail", title="A3", description="d") 
        q4_initially_available = Quest(id="q4_ia_avail", title="A4", description="d") 
        q5_no_deps = Quest(id="q5_avail", title="A5", description="d") 

        self.manager.add_quest(q1)
        self.manager.add_quest(q2_dep_q1)
        self.manager.add_quest(q3_initially_available)
        self.manager.add_quest(q4_initially_available)
        self.manager.add_quest(q5_no_deps)

        
        available = self.manager.list_available_quests()
        self.assertIn(q1, available)
        self.assertIn(q3_initially_available, available)
        self.assertIn(q4_initially_available, available)
        self.assertIn(q5_no_deps, available)
        self.assertNotIn(q2_dep_q1, available) 
        self.assertEqual(len(available), 4)

       
        self.manager.start_quest(q3_initially_available.id)
        available = self.manager.list_available_quests()
        self.assertNotIn(q3_initially_available, available) 
        self.assertEqual(len(available), 3) 

        
        self.manager.start_quest(q4_initially_available.id)
        self.manager.complete_quest(q4_initially_available.id)
        available = self.manager.list_available_quests()
        self.assertNotIn(q4_initially_available, available) 
        self.assertEqual(len(available), 2) 
        
        
        self.manager.start_quest(q1.id)
        self.manager.complete_quest(q1.id)
        available_after_q1_done = self.manager.list_available_quests()
        self.assertIn(q2_dep_q1, available_after_q1_done) 
        self.assertIn(q5_no_deps, available_after_q1_done)
        self.assertNotIn(q1, available_after_q1_done) 
        self.assertEqual(len(available_after_q1_done), 2)
        
        
        self.manager.start_quest(q2_dep_q1.id) 
        self.manager.complete_quest(q2_dep_q1.id) 
        self.manager.start_quest(q5_no_deps.id) 
        self.manager.complete_quest(q5_no_deps.id) 
        self.assertEqual(self.manager.list_available_quests(), [])



    def test_save_and_load_quests_with_new_fields(self):
        test_filepath = "test_quests_new_fields.json"
        if os.path.exists(test_filepath): 
            os.remove(test_filepath)

        start_dt_q1 = datetime.now(timezone.utc)
        q1_save = Quest(id="s_q1", title="Save Q1", description="Desc Q1", 
                          status=QuestStatus.IN_PROGRESS, quest_type=QuestType.TIMED,
                          rewards=[{"r":1}], start_time=start_dt_q1)
        q2_save = Quest(id="s_q2", title="Save Q2", description="Desc Q2", 
                          dependencies=["s_q1"], status=QuestStatus.COMPLETED,
                          consequences=[{"c":1}])
        q3_save = Quest(id="s_q3", title="Save Q3", description="Desc Q3",
                          status=QuestStatus.NOT_STARTED)
        
        self.manager.add_quest(q1_save)
        self.manager.add_quest(q2_save)
        self.manager.add_quest(q3_save)
                                  
        self.manager.save_quests(test_filepath)
        self.assertTrue(os.path.exists(test_filepath))
        
        new_manager = QuestManager()
        new_manager.load_quests(test_filepath)

        self.assertEqual(len(new_manager._quests), 3)
        
        loaded_q1 = new_manager.get_quest("s_q1")
        loaded_q2 = new_manager.get_quest("s_q2")
        loaded_q3 = new_manager.get_quest("s_q3")

        self.assertIsNotNone(loaded_q1)
        self.assertEqual(loaded_q1.title, "Save Q1")
        self.assertEqual(loaded_q1.status, QuestStatus.IN_PROGRESS)
        self.assertEqual(loaded_q1.quest_type, QuestType.TIMED)
        self.assertEqual(loaded_q1.rewards, [{"r":1}])
        self.assertEqual(loaded_q1.start_time.replace(microsecond=0), start_dt_q1.replace(microsecond=0)) 
        self.assertNotIn("s_q1", new_manager._completed_quest_ids) 

        self.assertIsNotNone(loaded_q2)
        self.assertEqual(loaded_q2.title, "Save Q2")
        self.assertEqual(loaded_q2.status, QuestStatus.COMPLETED)
        self.assertEqual(loaded_q2.dependencies, {"s_q1"})
        self.assertEqual(loaded_q2.consequences, [{"c":1}])
        self.assertIn("s_q2", new_manager._completed_quest_ids) 

        self.assertIsNotNone(loaded_q3)
        self.assertEqual(loaded_q3.status, QuestStatus.NOT_STARTED)
        self.assertNotIn("s_q3", new_manager._completed_quest_ids)

        if os.path.exists(test_filepath): 
            os.remove(test_filepath)

    def test_has_cycles_no_cycle(self):
        q1 = Quest(id="cyc_q1", title="Q1", description="d")
        q2 = Quest(id="cyc_q2", title="Q2", description="d", dependencies=["cyc_q1"])
        self.manager.add_quest(q1)
        self.manager.add_quest(q2)
        self.assertFalse(self.manager.has_cycles())

    def test_has_cycles_simple_direct_cycle(self):
        qc1 = Quest(id="cyc_qc1", title="Cycle 1", description="Part of cycle", dependencies=["cyc_qc2"])
        qc2 = Quest(id="cyc_qc2", title="Cycle 2", description="Part of cycle", dependencies=["cyc_qc1"])
        self.manager.add_quest(qc1)
        self.manager.add_quest(qc2)
        self.assertTrue(self.manager.has_cycles())
    
    def test_get_completion_order_no_cycle(self):
        q1 = Quest(id="ord_q1", title="Q1", description="d")
        q2 = Quest(id="ord_q2", title="Q2", description="d", dependencies=["ord_q1"])
        q_ind = Quest(id="ord_q_ind", title="Ind", description="d")
        
        self.manager.add_quest(q1)
        self.manager.add_quest(q2)
        self.manager.add_quest(q_ind)
        
        order = self.manager.get_completion_order()
        self.assertEqual(len(order), 3)
        self.assertIn("ord_q1", order)
        self.assertIn("ord_q2", order)
        self.assertIn("ord_q_ind", order)
        self.assertLess(order.index("ord_q1"), order.index("ord_q2"))

    def test_get_completion_order_with_cycle(self):
        qc1 = Quest(id="ord_qc1", title="Cycle 1", description="Part of cycle", dependencies=["ord_qc2"])
        qc2 = Quest(id="ord_qc2", title="Cycle 2", description="Part of cycle", dependencies=["ord_qc1"])
        self.manager.add_quest(qc1)
        self.manager.add_quest(qc2)
        with self.assertRaisesRegex(ValueError, "Cannot determine completion order: graph contains cycles."):
            self.manager.get_completion_order()

    def tearDown(self):
        test_files_to_remove = [
            "test_quests_new_fields.json", 
            "test_quests.json",
            "test_invalid_format.json",
            "test_decode_error.json",
            "test_missing_keys.json",
            "test_sample_like.json",

        ]
        for test_file in test_files_to_remove:
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except OSError as e:

                    logging.warning(f"Warning: Could not remove test file {test_file} in tearDown: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)