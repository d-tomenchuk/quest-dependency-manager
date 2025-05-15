import unittest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timezone 

from api_main import app, API_KEY_NAME 

from api_models import APIQuestStatus, APIQuestType, QuestOperationSuccessResponse


API_TEST_SAVE_FILE = "data/api_test_quests.json"
SAMPLE_QUEST_FILE_FOR_API_TESTS = "data/api_sample_test_data_v2.json" 

VALID_TEST_API_KEY = os.getenv("VALID_API_KEYS", "entwicklungsschluessel").split(',')[0].strip()
INVALID_TEST_API_KEY = "invalid_dummy_key_12345"


class TestQuestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.auth_headers = {API_KEY_NAME: VALID_TEST_API_KEY}

        sample_data_v2 = [
            {
                "id": "api_sample_0", 
                "title": "API Sample Init V2", 
                "description": "Loaded at start, not started", 
                "dependencies": [], 
                "status": APIQuestStatus.NOT_STARTED.value, 
                "quest_type": APIQuestType.MAIN.value,
                "rewards": [{"type": "xp", "amount": 50}],
                "consequences": [],
                "failure_conditions": [],
                "start_time": None
            },
            {
                "id": "api_sample_1", 
                "title": "API Sample Dep V2", 
                "description": "Depends on 0, completed", 
                "dependencies": ["api_sample_0"], 
                "status": APIQuestStatus.COMPLETED.value, 
                "quest_type": APIQuestType.SIDE.value,
                "rewards": [],
                "consequences": [{"type": "npc_dislike", "target": "merchant"}],
                "failure_conditions": [],
                "start_time": datetime.now(timezone.utc).isoformat() 
            }
        ]
        data_dir = os.path.dirname(SAMPLE_QUEST_FILE_FOR_API_TESTS)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        with open(SAMPLE_QUEST_FILE_FOR_API_TESTS, 'w', encoding='utf-8') as f:
            json.dump(sample_data_v2, f, indent=2)

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
        response = self.client.post("/testing/reset", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Failed to reset quest manager state. Response: {response.text}")
        self.assertIn("QuestManager state has been reset", response.json()["message"])


    def test_00_read_root_public(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the Quest Dependency Manager API!"})

    def test_01_create_quest_success_auth_with_new_fields(self):
        quest_data_payload = {
            "id": "q_api_new_1", 
            "title": "API Quest New 1", 
            "description": "First API quest with new fields", 
            "dependencies": [],
            "quest_type": APIQuestType.MAIN.value, 
            "rewards": [{"type": "gold", "amount": 100}],
            "consequences": [],
            "failure_conditions": []
        }
        response = self.client.post("/quests/", json=quest_data_payload, headers=self.auth_headers)
        self.assertEqual(response.status_code, 201, response.text)
        data = response.json()
        
        self.assertEqual(data["id"], quest_data_payload["id"])
        self.assertEqual(data["title"], quest_data_payload["title"])
        self.assertEqual(data["status"], APIQuestStatus.NOT_STARTED.value) 
        self.assertEqual(data["quest_type"], quest_data_payload["quest_type"])
        self.assertEqual(data["rewards"], quest_data_payload["rewards"])
        self.assertIsNone(data["start_time"]) 


    def test_02_create_quest_duplicate_id_auth(self):
        quest_data = {"id": "q_api_dup", "title": "API Dup Quest", "description": "Desc"}
        self.client.post("/quests/", json=quest_data, headers=self.auth_headers) 
        response2 = self.client.post("/quests/", json=quest_data, headers=self.auth_headers) 
        self.assertEqual(response2.status_code, 400)
        self.assertIn("already exists", response2.json()["detail"])

    def test_03_get_all_quests_public_check_new_schema(self):
        q_data = {
            "id": "q_get_all_1", "title": "For Get All", "description": "D",
            "quest_type": APIQuestType.SIDE.value, "rewards": [{"item":"potion"}]
        }
        self.client.post("/quests/", json=q_data, headers=self.auth_headers)
        
        response = self.client.get("/quests/")
        self.assertEqual(response.status_code, 200)
        quests_list = response.json()
        self.assertTrue(len(quests_list) >= 1) 
        found_quest = next((q for q in quests_list if q["id"] == "q_get_all_1"), None)
        self.assertIsNotNone(found_quest)
        self.assertEqual(found_quest["title"], "For Get All")
        self.assertEqual(found_quest["status"], APIQuestStatus.NOT_STARTED.value)
        self.assertEqual(found_quest["quest_type"], APIQuestType.SIDE.value)
        self.assertEqual(found_quest["rewards"], [{"item":"potion"}])


    def test_04_get_one_quest_public_check_new_schema(self):
        start_time_val = datetime.now(timezone.utc)
        quest_data_payload = {
            "id": "q_api_get_one", "title": "API Get One Quest", "description": "Desc",
            "quest_type": APIQuestType.TIMED.value, "rewards": [{"xp":500}]
        }
        create_response = self.client.post("/quests/", json=quest_data_payload, headers=self.auth_headers)
        self.assertEqual(create_response.status_code, 201)
        start_response = self.client.post(f"/quests/{quest_data_payload['id']}/start", headers=self.auth_headers)
        self.assertEqual(start_response.status_code, 200)
        
        response = self.client.get(f"/quests/{quest_data_payload['id']}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], quest_data_payload["id"])
        self.assertEqual(data["status"], APIQuestStatus.IN_PROGRESS.value) 
        self.assertEqual(data["quest_type"], APIQuestType.TIMED.value)
        self.assertIsNotNone(data["start_time"]) 

        response_not_found = self.client.get("/quests/non_existent_id_for_get_one")
        self.assertEqual(response_not_found.status_code, 404)

    def test_05_full_quest_lifecycle_start_complete_auth(self):
        q1_data = {"id": "q_api_lc1", "title": "Lifecycle1", "description": "D1"}
        q2_data = {"id": "q_api_lc2", "title": "Lifecycle2", "description": "D2", "dependencies": ["q_api_lc1"]}
        
        self.client.post("/quests/", json=q1_data, headers=self.auth_headers)
        self.client.post("/quests/", json=q2_data, headers=self.auth_headers)


        response_q2_start_fail = self.client.post(f"/quests/{q2_data['id']}/start", headers=self.auth_headers)
        self.assertEqual(response_q2_start_fail.status_code, 403) 

        response_q1_start = self.client.post(f"/quests/{q1_data['id']}/start", headers=self.auth_headers)
        self.assertEqual(response_q1_start.status_code, 200)
        self.assertEqual(response_q1_start.json()["status"], APIQuestStatus.IN_PROGRESS.value)

        response_q1_complete = self.client.post(f"/quests/{q1_data['id']}/complete", headers=self.auth_headers)
        self.assertEqual(response_q1_complete.status_code, 200)
        self.assertEqual(response_q1_complete.json()["status"], APIQuestStatus.COMPLETED.value)

        response_q2_start_ok = self.client.post(f"/quests/{q2_data['id']}/start", headers=self.auth_headers)
        self.assertEqual(response_q2_start_ok.status_code, 200)
        self.assertEqual(response_q2_start_ok.json()["status"], APIQuestStatus.IN_PROGRESS.value)
    
        response_q2_complete_ok = self.client.post(f"/quests/{q2_data['id']}/complete", headers=self.auth_headers)
        self.assertEqual(response_q2_complete_ok.status_code, 200)
        self.assertEqual(response_q2_complete_ok.json()["status"], APIQuestStatus.COMPLETED.value)

    def test_05a_fail_quest_auth(self):
        q_fail_data = {"id": "q_api_fail", "title": "To Be Failed", "description": "D"}
        self.client.post("/quests/", json=q_fail_data, headers=self.auth_headers)
        response_fail_not_started = self.client.post(f"/quests/{q_fail_data['id']}/fail", headers=self.auth_headers)
        self.assertEqual(response_fail_not_started.status_code, 200)
        self.assertEqual(response_fail_not_started.json()["status"], APIQuestStatus.FAILED.value)
        self.client.post("/testing/reset", headers=self.auth_headers)
        self.client.post("/quests/", json=q_fail_data, headers=self.auth_headers)
        self.client.post(f"/quests/{q_fail_data['id']}/start", headers=self.auth_headers) 
        
        response_fail_in_progress = self.client.post(f"/quests/{q_fail_data['id']}/fail", headers=self.auth_headers)
        self.assertEqual(response_fail_in_progress.status_code, 200)
        self.assertEqual(response_fail_in_progress.json()["status"], APIQuestStatus.FAILED.value)

    def test_05b_reset_quest_auth(self):
        q_repeat_data = {
            "id": "q_api_repeat", "title": "To Be Reset", "description": "D", 
            "quest_type": APIQuestType.REPEATABLE.value
        }
        self.client.post("/quests/", json=q_repeat_data, headers=self.auth_headers)
        self.client.post(f"/quests/{q_repeat_data['id']}/start", headers=self.auth_headers)
        self.client.post(f"/quests/{q_repeat_data['id']}/complete", headers=self.auth_headers)

        response_reset = self.client.post(f"/quests/{q_repeat_data['id']}/reset", headers=self.auth_headers)
        self.assertEqual(response_reset.status_code, 200)
        data = response_reset.json()
        self.assertEqual(data["status"], APIQuestStatus.NOT_STARTED.value)
        self.assertIsNone(data["start_time"]) 
        q_not_repeat_data = {"id": "q_not_rep_api", "title": "Not Repeat", "quest_type": APIQuestType.SIDE.value}
        self.client.post("/quests/", json=q_not_repeat_data, headers=self.auth_headers)
        self.client.post(f"/quests/{q_not_repeat_data['id']}/start", headers=self.auth_headers)
        self.client.post(f"/quests/{q_not_repeat_data['id']}/complete", headers=self.auth_headers)
        response_reset_fail = self.client.post(f"/quests/{q_not_repeat_data['id']}/reset", headers=self.auth_headers)
        self.assertEqual(response_reset_fail.status_code, 403) 


    def test_06_get_available_quests_public_updated_logic(self):
        q1 = {"id": "q_api_avail1", "title": "Avail1", "description": "D1"} 
        q2 = {"id": "q_api_avail2", "title": "Avail2", "description": "D2", "dependencies": ["q_api_avail1"]} 
        q3 = {"id": "q_api_avail3", "title": "Avail3", "description": "D3"} 
        
        self.client.post("/quests/", json=q1, headers=self.auth_headers)
        self.client.post("/quests/", json=q2, headers=self.auth_headers)
        self.client.post("/quests/", json=q3, headers=self.auth_headers)

        response = self.client.get("/quests/available/")
        self.assertEqual(response.status_code, 200)
        available_ids = {q["id"] for q in response.json()}
        self.assertEqual(available_ids, {"q_api_avail1", "q_api_avail3"})

        # Начинаем и Завершаем q1
        self.client.post(f"/quests/q_api_avail1/start", headers=self.auth_headers)
        self.client.post(f"/quests/q_api_avail1/complete", headers=self.auth_headers)
        
        response_after_complete = self.client.get("/quests/available/")
        available_ids_after = {q["id"] for q in response_after_complete.json()}
        self.assertEqual(available_ids_after, {"q_api_avail2", "q_api_avail3"})

    def test_07_cycle_detection_public(self):

        q_cycle1 = {"id": "qc1_api", "title": "Cycle1", "description": "d", "dependencies": ["qc2_api"]}
        q_cycle2 = {"id": "qc2_api", "title": "Cycle2", "description": "d", "dependencies": ["qc1_api"]}
        self.client.post("/quests/", json=q_cycle1, headers=self.auth_headers)
        self.client.post("/quests/", json=q_cycle2, headers=self.auth_headers)

        response = self.client.get("/analysis/cycles")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["has_cycles"])
        self.client.post("/testing/reset", headers=self.auth_headers) 

    def test_08_completion_order_public(self):

        q1 = {"id": "co1_api", "title": "CO1", "description": "d"}
        q2 = {"id": "co2_api", "title": "CO2", "description": "d", "dependencies": ["co1_api"]}
        self.client.post("/quests/", json=q1, headers=self.auth_headers)
        self.client.post("/quests/", json=q2, headers=self.auth_headers)

        response = self.client.get("/analysis/completion_order")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["order"], ["co1_api", "co2_api"])
        self.client.post("/testing/reset", headers=self.auth_headers)


    def test_09_save_and_load_via_api_auth_check_new_fields(self):
        q1_data = {"id": "api_sl1", "title": "SaveLoad1", "description": "SL1", "quest_type": APIQuestType.MAIN.value}
        q2_data = {"id": "api_sl2", "title": "SaveLoad2", "description": "SL2", "dependencies": ["api_sl1"], "rewards":[{"xp":10}]}
        
        self.client.post("/quests/", json=q1_data, headers=self.auth_headers)
        self.client.post("/quests/", json=q2_data, headers=self.auth_headers)
        self.client.post(f"/quests/api_sl1/start", headers=self.auth_headers)
        self.client.post(f"/quests/api_sl1/complete", headers=self.auth_headers)

        save_payload = {"filepath": API_TEST_SAVE_FILE}
        response_save = self.client.post("/data/save", json=save_payload, headers=self.auth_headers)
        self.assertEqual(response_save.status_code, 200)
        self.assertTrue(os.path.exists(API_TEST_SAVE_FILE))

        self.client.post("/testing/reset", headers=self.auth_headers)

        load_payload = {"filepath": API_TEST_SAVE_FILE}
        response_load = self.client.post("/data/load", json=load_payload, headers=self.auth_headers)
        self.assertEqual(response_load.status_code, 200)
        self.assertIn("successfully loaded", response_load.json()["message"].lower())

        response_get_all = self.client.get("/quests/")
        self.assertEqual(response_get_all.status_code, 200)
        loaded_quests_data = response_get_all.json()
        self.assertEqual(len(loaded_quests_data), 2)
        loaded_ids_map = {q["id"]: q for q in loaded_quests_data}
        self.assertEqual(loaded_ids_map["api_sl1"]["status"], APIQuestStatus.COMPLETED.value)
        self.assertEqual(loaded_ids_map["api_sl1"]["quest_type"], APIQuestType.MAIN.value)
        
        self.assertEqual(loaded_ids_map["api_sl2"]["status"], APIQuestStatus.NOT_STARTED.value) 
        self.assertEqual(loaded_ids_map["api_sl2"]["rewards"], [{"xp":10}])


    def test_10_load_predefined_sample_file_auth_v2(self):

        load_payload = {"filepath": SAMPLE_QUEST_FILE_FOR_API_TESTS}
        response_load = self.client.post("/data/load", json=load_payload, headers=self.auth_headers)
        self.assertEqual(response_load.status_code, 200)

        response_get_all = self.client.get("/quests/")
        loaded_quests_data = response_get_all.json()
        self.assertEqual(len(loaded_quests_data), 2)
        
        ids_map = {q['id']: q for q in loaded_quests_data}
        self.assertEqual(ids_map["api_sample_0"]["status"], APIQuestStatus.NOT_STARTED.value)
        self.assertEqual(ids_map["api_sample_0"]["quest_type"], APIQuestType.MAIN.value)
        self.assertEqual(ids_map["api_sample_0"]["rewards"], [{"type": "xp", "amount": 50}])
        
        self.assertEqual(ids_map["api_sample_1"]["status"], APIQuestStatus.COMPLETED.value)
        self.assertEqual(ids_map["api_sample_1"]["quest_type"], APIQuestType.SIDE.value)
        self.assertIsNotNone(ids_map["api_sample_1"]["start_time"]) 


    def test_11_protected_endpoint_no_api_key(self):
        response = self.client.post("/quests/some_id/start") 
        self.assertIn(response.status_code, [401, 403]) 
        self.assertIn("Not authenticated", response.json()["detail"])

    def test_12_protected_endpoint_invalid_api_key(self):
        invalid_headers = {API_KEY_NAME: INVALID_TEST_API_KEY}
        response = self.client.post("/quests/some_id/fail", headers=invalid_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Invalid API Key", response.json()["detail"])

    def test_13_testing_reset_endpoint_auth_checks(self):
        response_no_key = self.client.post("/testing/reset")
        self.assertIn(response_no_key.status_code, [401, 403])

        response_invalid_key = self.client.post("/testing/reset", headers={API_KEY_NAME: INVALID_TEST_API_KEY})
        self.assertEqual(response_invalid_key.status_code, 403)

        response_valid_key = self.client.post("/testing/reset", headers=self.auth_headers)
        self.assertEqual(response_valid_key.status_code, 200)
        
        self.assertIn("message", response_valid_key.json())
        self.assertIn("quest_id", response_valid_key.json()) 

if __name__ == '__main__':
    unittest.main(verbosity=2)