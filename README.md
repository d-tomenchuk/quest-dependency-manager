# 🧭 Quest Dependency Manager

A Python-based system for managing tasks (or **"quests"**) with complex dependencies and lifecycles. Designed with flexibility and clarity in mind, this tool supports everything from RPG questlines to workflow automation.

---

## 🚀 Overview

The **Quest Dependency Manager** enables you to define, track, and progress through quests with attributes like:

- Type (`MAIN`, `SIDE`, `REPEATABLE`, `TIMED`)
- Status (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`)
- Dependencies & prerequisites
- Rewards, consequences, failure conditions

Supports **cycle detection**, **topological sorting**, **data persistence**, and offers:

- 🖥️ Command-Line Interface (CLI)
- 🌐 FastAPI-powered HTTP API with authentication

---

## 🧠 Use Cases

| Domain               | Use Example                                                                 |
|----------------------|------------------------------------------------------------------------------|
| 🎮 Game Development  | Manage complex questlines with branching paths, time limits, and rewards.     |
| 🗂️ Project Management | Break down tasks into dependencies, enforce progression, track status.        |
| 📚 E-learning         | Unlock lessons/modules based on prerequisites.                              |
| ⚙️ Workflow Automation | Model business processes and execute dependent steps reliably.               |
| 📖 Storytelling       | Drive narrative progression via quest outcomes.                              |
| 🧑‍💼 Personal Planning | Track progress on personal goals or learning paths using a dependency system. |

---

## ✨ Features

### ✅ Quest Model
- Unique ID, title, description
- Dependencies on other quests
- Types: `MAIN`, `SIDE`, `OPTIONAL`, `REPEATABLE`, `TIMED`
- Status: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`
- Rewards, consequences, failure conditions
- Timed quest tracking (`start_time`)

### 🔄 Lifecycle Management
- Add, start, complete, fail, or reset quests
- Prerequisite enforcement: no skipping allowed!
- Repeatable quest handling

### 🧩 Dependency Graph
- Automatic cycle detection
- Generate valid quest completion order (topological sort)

### 💾 Persistence
- Save/load quests in structured JSON format

### 🧰 Interfaces
- **CLI**: Interactively manage quests locally
- **FastAPI API**: Programmatic access with API key protection
- Unified logging and automated tests included

---

## 📦 Requirements

* Python 3.10+
* Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
* Required packages:
    * `fastapi`
    * `uvicorn[standard]`
    * `httpx`
    * `python-dotenv`

## Getting Started

### Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\Scripts\Activate.ps1  # Windows PowerShell
   ```
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` file for API keys:

   ```env
   VALID_API_KEYS="your_secret_key_1,another_key"
   LOG_LEVEL="DEBUG"
   ```

   Add `.env` to `.gitignore` to keep it private.

## Project Structure

```
quest-dependency-manager/
├── .env
├── .gitignore
├── quest.py
├── manager.py
├── main.py
├── api_main.py
├── api_models.py
├── requirements.txt
├── data/
│   ├── sample.json
│   └── quest_data.json
├── tests/
│   ├── __init__.py
│   ├── test_quest.py
│   └── test_api.py
├── README.md
└── spec.md
```

## Running the Applications

### CLI

```bash
python main.py
```

### API (FastAPI)

```bash
uvicorn api_main:app --reload --port 8000 --log-level debug
```

* Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Running Tests

```bash
python -m unittest discover tests
```

All tests should pass.

## CLI Menu

```
Select an action:
1. Add new quest
2. Complete quest
3. List available quests (pending, dependencies met)
4. Check system for cyclic dependencies
5. Get recommended quest completion order
6. Save quests to JSON file
7. Load quests from JSON file
0. Exit
```

## API Endpoints

**Read-Only:**

* `GET /quests/`
* `GET /quests/available/`
* `GET /quests/{quest_id}`
* `GET /analysis/cycles`
* `GET /analysis/completion_order`

**Protected (requires `X-API-Key`):**

* `POST /quests/`
* `POST /quests/{quest_id}/complete`
* `POST /data/save`
* `POST /data/load`
* `POST /testing/reset`

## Authentication

Use `X-API-Key` header. Keys are configured via `VALID_API_KEYS` in `.env`. If not set, fallback is `"entwicklungsschluessel"` (with warning).

## Data Format

### Quest JSON Structure

```json
[
  {
    "id": "quest_1",
    "title": "Find the Sword",
    "description": "Retrieve the ancient sword from the cave.",
    "dependencies": [],
    "completed": false
  }
]
```

### Fields

* `id`: Unique string ID
* `title`: Quest title
* `description`: Short text
* `dependencies`: List of required quest IDs
* `completed`: Boolean

### Default File

* `data/quest_data.json`

### Sample Data

* `data/sample.json` — no `completed` field by default

## License

See LICENSE file. Consider using MIT or similar if open source.

*Last updated: May 15, 2025*
