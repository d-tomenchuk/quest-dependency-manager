import unittest
import os
import json
from fastapi.testclient import TestClient

from api_main import app, API_KEY_NAME

API_TEST_SAVE_FILE = "data/api_test_quests.json"
SAMPLE_QUEST_FILE_FOR_API_TESTS = "data/api_sample_test_data.json"

VALID_TEST_API_KEY = os.getenv("VALID_API_KEYS", "entwicklungsschluessel").split(',')[0].strip()
INVALID_TEST_API_KEY = "invalid_dummy_key_12345"


class TestQuestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.auth_headers = {API_KEY_NAME: VALID_TEST_API_KEY}

        sample_data = [
            {"id": "api_sample_0", "title": "API Sample Init", "description": "Loaded at start", "dependencies": [], "completed": False},
            {"id": "api_sample_1", "title": "API Sample Dep", "description": "Depends on 0", "dependencies": ["api_sample_0"], "completed": True}
        ]
        data_dir = os.path.dirname(SAMPLE_QUEST_FILE_FOR_API_TESTS)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        with open(SAMPLE_QUEST_FILE_FOR_API_TESTS, 'w', encoding='utf-8') as f:
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
        response = self.client.post("/testing/reset", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Failed to reset quest manager state. Response: {response.text}")

    def test_00_read_root_public(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the Quest Dependency Manager API!"})

    def test_01_create_quest_success_auth(self):
        quest_data = {"id": "q_api_1", "title": "API Quest 1", "description": "First API quest", "dependencies": []}
        response = self.client.post("/quests/", json=quest_data, headers=self.auth_headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["id"], quest_data["id"])
        self.assertFalse(data["completed"])

    def test_02_create_quest_duplicate_id_auth(self):
        quest_data = {"id": "q_api_dup", "title": "API Dup Quest", "description": "Desc"}
        self.client.post("/quests/", json=quest_data, headers=self.auth_headers)
        response2 = self.client.post("/quests/", json=quest_data, headers=self.auth_headers)
        self.assertEqual(response2.status_code, 400)
        self.assertIn("already exists", response2.json()["detail"])

    def test_03_get_all_quests_public(self):
        response = self.client.get("/quests/")
        self.assertEqual(response.status_code, 200)

    def test_04_get_one_quest_public(self):
        quest_data = {"id": "q_api_get1", "title": "API Get Quest", "description": "Desc"}
        create_response = self.client.post("/quests/", json=quest_data, headers=self.auth_headers)
        self.assertEqual(create_response.status_code, 201)

        response = self.client.get(f"/quests/{quest_data['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], quest_data["id"])

        response_not_found = self.client.get("/quests/non_existent_id")
        self.assertEqual(response_not_found.status_code, 404)

    def test_05_complete_quest_auth(self):
        q1_data = {"id": "q_api_c1", "title": "C1", "description": "D1"}
        q2_data = {"id": "q_api_c2", "title": "C2", "description": "D2", "dependencies": ["q_api_c1"]}
        self.client.post("/quests/", json=q1_data, headers=self.auth_headers)
        self.client.post("/quests/", json=q2_data, headers=self.auth_headers)

        response_q2_fail = self.client.post(f"/quests/{q2_data['id']}/complete", headers=self.auth_headers)
        self.assertEqual(response_q2_fail.status_code, 403)

        response_q1_ok = self.client.post(f"/quests/{q1_data['id']}/complete", headers=self.auth_headers)
        self.assertEqual(response_q1_ok.status_code, 200)
        self.assertTrue(response_q1_ok.json()["completed"])

        response_q2_ok = self.client.post(f"/quests/{q2_data['id']}/complete", headers=self.auth_headers)
        self.assertEqual(response_q2_ok.status_code, 200)
        self.assertTrue(response_q2_ok.json()["completed"])

    def test_06_get_available_quests_public(self):
        q1_data = {"id": "q_api_a1", "title": "A1", "description": "D1"}
        q2_data = {"id": "q_api_a2", "title": "A2", "description": "D2", "dependencies": ["q_api_a1"]}
        q3_data = {"id": "q_api_a3", "title": "A3", "description": "D3"}
        self.client.post("/quests/", json=q1_data, headers=self.auth_headers)
        self.client.post("/quests/", json=q2_data, headers=self.auth_headers)
        self.client.post("/quests/", json=q3_data, headers=self.auth_headers)

        response = self.client.get("/quests/available/")
        self.assertEqual(response.status_code, 200)
        available_ids = {q["id"] for q in response.json()}
        self.assertEqual(available_ids, {"q_api_a1", "q_api_a3"})

        self.client.post(f"/quests/q_api_a1/complete", headers=self.auth_headers)
        response_after_complete = self.client.get("/quests/available/")
        available_ids_after = {q["id"] for q in response_after_complete.json()}
        self.assertEqual(available_ids_after, {"q_api_a2", "q_api_a3"})

    def test_07_cycle_detection_public(self):
        q_cycle1 = {"id": "qc1", "title": "Cycle1", "description": "d", "dependencies": ["qc2"]}
        q_cycle2 = {"id": "qc2", "title": "Cycle2", "description": "d", "dependencies": ["qc1"]}
        self.client.post("/quests/", json=q_cycle1, headers=self.auth_headers)
        self.client.post("/quests/", json=q_cycle2, headers=self.auth_headers)

        response = self.client.get("/analysis/cycles")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["has_cycles"])

        self.client.post("/testing/reset", headers=self.auth_headers)
        q_no_cycle = {"id": "qnc1", "title": "NoCycle", "description": "d"}
        self.client.post("/quests/", json=q_no_cycle, headers=self.auth_headers)
        response_no_cycle = self.client.get("/analysis/cycles")
        self.assertEqual(response_no_cycle.status_code, 200)
        self.assertFalse(response_no_cycle.json()["has_cycles"])

    def test_08_completion_order_public(self):
        q1 = {"id": "co1", "title": "CO1", "description": "d"}
        q2 = {"id": "co2", "title": "CO2", "description": "d", "dependencies": ["co1"]}
        self.client.post("/quests/", json=q1, headers=self.auth_headers)
        self.client.post("/quests/", json=q2, headers=self.auth_headers)

        response = self.client.get("/analysis/completion_order")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["order"], ["co1", "co2"])

        self.client.post("/testing/reset", headers=self.auth_headers)
        q_cycle1 = {"id": "qc1_co", "title": "Cycle1CO", "description": "d", "dependencies": ["qc2_co"]}
        q_cycle2 = {"id": "qc2_co", "title": "Cycle2CO", "description": "d", "dependencies": ["qc1_co"]}
        self.client.post("/quests/", json=q_cycle1, headers=self.auth_headers)
        self.client.post("/quests/", json=q_cycle2, headers=self.auth_headers)
        response_cycle = self.client.get("/analysis/completion_order")
        self.assertEqual(response_cycle.status_code, 409)

    def test_09_save_and_load_via_api_auth(self):
        q1_data = {"id": "api_sl1", "title": "SaveLoad1", "description": "SL1"}
        q2_data = {"id": "api_sl2", "title": "SaveLoad2", "description": "SL2", "dependencies": ["api_sl1"]}
        self.client.post("/quests/", json=q1_data, headers=self.auth_headers)
        self.client.post("/quests/", json=q2_data, headers=self.auth_headers)
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
        self.assertTrue(loaded_ids_map["api_sl1"]["completed"])
        self.assertFalse(loaded_ids_map["api_sl2"]["completed"])

    def test_10_load_predefined_sample_file_auth(self):
        load_payload = {"filepath": SAMPLE_QUEST_FILE_FOR_API_TESTS}
        response_load = self.client.post("/data/load", json=load_payload, headers=self.auth_headers)
        self.assertEqual(response_load.status_code, 200)

        response_get_all = self.client.get("/quests/")
        loaded_quests_data = response_get_all.json()
        self.assertEqual(len(loaded_quests_data), 2)
        ids_map = {q['id']: q for q in loaded_quests_data}
        self.assertTrue(ids_map["api_sample_1"]["completed"])

    def test_11_protected_endpoint_no_api_key(self):
        quest_data = {"id": "q_no_key", "title": "No Key Quest", "description": "Test no key"}
        response = self.client.post("/quests/", json=quest_data)
        self.assertIn(response.status_code, [401, 403])
        self.assertIn("Not authenticated", response.json()["detail"])

    def test_12_protected_endpoint_invalid_api_key(self):
        quest_data = {"id": "q_invalid_key", "title": "Invalid Key Quest", "description": "Test invalid key"}
        invalid_headers = {API_KEY_NAME: INVALID_TEST_API_KEY}
        response = self.client.post("/quests/", json=quest_data, headers=invalid_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Invalid API Key", response.json()["detail"])

    def test_13_testing_reset_endpoint_auth_checks(self):
        response_no_key = self.client.post("/testing/reset")
        self.assertIn(response_no_key.status_code, [401, 403])
        self.assertIn("Not authenticated", response_no_key.json()["detail"])

        response_invalid_key = self.client.post("/testing/reset", headers={API_KEY_NAME: INVALID_TEST_API_KEY})
        self.assertEqual(response_invalid_key.status_code, 403)
        self.assertIn("Invalid API Key", response_invalid_key.json()["detail"])

        response_valid_key = self.client.post("/testing/reset", headers=self.auth_headers)
        self.assertEqual(response_valid_key.status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
