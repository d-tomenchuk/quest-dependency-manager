import unittest
import os
import json
from fastapi.testclient import TestClient
from api_main import app 


API_TEST_SAVE_FILE = "data/api_test_quests.json"
SAMPLE_QUEST_FILE_FOR_API_TESTS = "data/api_sample_test_data.json"


class TestQuestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        
        cls.client = TestClient(app)
        
        sample_data = [
            {"id": "api_sample_0", "title": "API Sample Init", "description": "Loaded at start", "dependencies": [], "completed": False},
            {"id": "api_sample_1", "title": "API Sample Dep", "description": "Depends on 0", "dependencies": ["api_sample_0"], "completed": True}
        ]
        data_dir = os.path.dirname(SAMPLE_QUEST_FILE_FOR_API_TESTS)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        with open(SAMPLE_QUEST_FILE_FOR_API_TESTS, 'w') as f:
            json.dump(sample_data, f)


    @classmethod
    def tearDownClass(cls):
        
        if os.path.exists(API_TEST_SAVE_FILE):
            os.remove(API_TEST_SAVE_FILE)
        if os.path.exists(SAMPLE_QUEST_FILE_FOR_API_TESTS):
            os.remove(SAMPLE_QUEST_FILE_FOR_API_TESTS)
        data_dir = os.path.dirname(API_TEST_SAVE_FILE) 
        try:
            if os.path.exists(data_dir) and not os.listdir(data_dir):
                os.rmdir(data_dir)
        except OSError:
            pass 

    def setUp(self):
 
        response = self.client.post("/testing/reset")
        self.assertEqual(response.status_code, 200, "Failed to reset quest manager state for test.")


    def test_00_read_root(self):
        
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the Quest Dependency Manager API!"})

    def test_01_create_quest_success(self):
        
        quest_data = {"id": "q_api_1", "title": "API Quest 1", "description": "First API quest", "dependencies": []}
        response = self.client.post("/quests/", json=quest_data)
        self.assertEqual(response.status_code, 201) 
        data = response.json()
        self.assertEqual(data["id"], quest_data["id"])
        self.assertEqual(data["title"], quest_data["title"])
        self.assertFalse(data["completed"])

    def test_02_create_quest_duplicate_id(self):

        quest_data = {"id": "q_api_dup", "title": "API Dup Quest", "description": "Desc", "dependencies": []}
        response1 = self.client.post("/quests/", json=quest_data)
        self.assertEqual(response1.status_code, 201) 

        response2 = self.client.post("/quests/", json=quest_data) 
        self.assertEqual(response2.status_code, 400) 
        self.assertTrue("already exists" in response2.json()["detail"])

    def test_03_get_all_quests_empty(self):

        response = self.client.get("/quests/")
        self.assertEqual(response.status_code, 200)


    def test_04_get_one_quest(self):

        quest_data = {"id": "q_api_get1", "title": "API Get Quest", "description": "Desc", "dependencies": []}
        self.client.post("/quests/", json=quest_data)

        response = self.client.get(f"/quests/{quest_data['id']}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], quest_data["id"])

        response_not_found = self.client.get("/quests/non_existent_id")
        self.assertEqual(response_not_found.status_code, 404)
    
    def test_05_complete_quest_success_and_dependencies(self):
        """Test completing quests with and without dependencies."""
        q1_data = {"id": "q_api_c1", "title": "C1", "description": "D1"}
        q2_data = {"id": "q_api_c2", "title": "C2", "description": "D2", "dependencies": ["q_api_c1"]}
        self.client.post("/quests/", json=q1_data)
        self.client.post("/quests/", json=q2_data)

        response_q2_fail = self.client.post(f"/quests/{q2_data['id']}/complete")
        self.assertEqual(response_q2_fail.status_code, 403) 

        response_q1_ok = self.client.post(f"/quests/{q1_data['id']}/complete")
        self.assertEqual(response_q1_ok.status_code, 200)
        self.assertTrue(response_q1_ok.json()["completed"])

        response_q2_ok = self.client.post(f"/quests/{q2_data['id']}/complete")
        self.assertEqual(response_q2_ok.status_code, 200)
        self.assertTrue(response_q2_ok.json()["completed"])

    def test_06_get_available_quests(self):
        """Test listing available quests."""
        q1_data = {"id": "q_api_a1", "title": "A1", "description": "D1"}
        q2_data = {"id": "q_api_a2", "title": "A2", "description": "D2", "dependencies": ["q_api_a1"]}
        q3_data = {"id": "q_api_a3", "title": "A3", "description": "D3"} 
        self.client.post("/quests/", json=q1_data)
        self.client.post("/quests/", json=q2_data)
        self.client.post("/quests/", json=q3_data)

        response = self.client.get("/quests/available/")
        self.assertEqual(response.status_code, 200)
        available_ids = {q["id"] for q in response.json()}
        self.assertEqual(available_ids, {"q_api_a1", "q_api_a3"})

        self.client.post(f"/quests/q_api_a1/complete") 
        response_after_complete = self.client.get("/quests/available/")
        available_ids_after = {q["id"] for q in response_after_complete.json()}
        self.assertEqual(available_ids_after, {"q_api_a2", "q_api_a3"})


    def test_07_cycle_detection(self):
        """Test cycle detection endpoint."""
        q_cycle1 = {"id": "qc1", "title": "Cycle1", "description": "d", "dependencies": ["qc2"]}
        q_cycle2 = {"id": "qc2", "title": "Cycle2", "description": "d", "dependencies": ["qc1"]}
        self.client.post("/quests/", json=q_cycle1)
        self.client.post("/quests/", json=q_cycle2)

        response = self.client.get("/analysis/cycles")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["has_cycles"])

        self.client.post("/testing/reset")
        q_no_cycle = {"id": "qnc1", "title": "NoCycle", "description": "d"}
        self.client.post("/quests/", json=q_no_cycle)
        response_no_cycle = self.client.get("/analysis/cycles")
        self.assertEqual(response_no_cycle.status_code, 200)
        self.assertFalse(response_no_cycle.json()["has_cycles"])

    def test_08_completion_order(self):
        """Test completion order endpoint."""
        q1 = {"id": "co1", "title": "CO1", "description": "d"}
        q2 = {"id": "co2", "title": "CO2", "description": "d", "dependencies": ["co1"]}
        self.client.post("/quests/", json=q1)
        self.client.post("/quests/", json=q2)
        
        response = self.client.get("/analysis/completion_order")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["order"], ["co1", "co2"])

        self.client.post("/testing/reset")
        q_cycle1 = {"id": "qc1", "title": "Cycle1", "description": "d", "dependencies": ["qc2"]}
        q_cycle2 = {"id": "qc2", "title": "Cycle2", "description": "d", "dependencies": ["qc1"]}
        self.client.post("/quests/", json=q_cycle1)
        self.client.post("/quests/", json=q_cycle2)
        response_cycle = self.client.get("/analysis/completion_order")
        self.assertEqual(response_cycle.status_code, 409) 

    def test_09_save_and_load_via_api(self):

        q1_data = {"id": "api_sl1", "title": "SaveLoad1", "description": "SL1"}
        q2_data = {"id": "api_sl2", "title": "SaveLoad2", "description": "SL2", "dependencies": ["api_sl1"]}
        self.client.post("/quests/", json=q1_data)
        self.client.post("/quests/", json=q2_data)
        self.client.post(f"/quests/api_sl1/complete") 

        
        save_payload = {"filepath": API_TEST_SAVE_FILE}
        response_save = self.client.post("/data/save", json=save_payload)
        self.assertEqual(response_save.status_code, 200)
        self.assertTrue(os.path.exists(API_TEST_SAVE_FILE))

        
        self.client.post("/testing/reset")

        load_payload = {"filepath": API_TEST_SAVE_FILE}
        response_load = self.client.post("/data/load", json=load_payload)
        self.assertEqual(response_load.status_code, 200)
        self.assertTrue(response_load.json()["message"].startswith(f"Quests successfully loaded from {API_TEST_SAVE_FILE}"))

        
        response_get_all = self.client.get("/quests/")
        self.assertEqual(response_get_all.status_code, 200)
        loaded_quests_data = response_get_all.json()
        self.assertEqual(len(loaded_quests_data), 2)

        loaded_ids_map = {q["id"]: q for q in loaded_quests_data}
        self.assertTrue(loaded_ids_map["api_sl1"]["completed"])
        self.assertFalse(loaded_ids_map["api_sl2"]["completed"])
        self.assertIn("api_sl1", loaded_ids_map["api_sl2"]["dependencies"])

    def test_10_load_predefined_sample_file(self):

        load_payload = {"filepath": SAMPLE_QUEST_FILE_FOR_API_TESTS}
        response_load = self.client.post("/data/load", json=load_payload)
        self.assertEqual(response_load.status_code, 200)
        
        response_get_all = self.client.get("/quests/")
        loaded_quests_data = response_get_all.json()
        self.assertEqual(len(loaded_quests_data), 2)
        
        ids_map = {q['id']: q for q in loaded_quests_data}
        self.assertIn("api_sample_0", ids_map)
        self.assertIn("api_sample_1", ids_map)
        self.assertTrue(ids_map["api_sample_1"]["completed"]) 
        self.assertEqual(ids_map["api_sample_1"]["dependencies"], ["api_sample_0"])


if __name__ == '__main__':
    unittest.main(verbosity=2)