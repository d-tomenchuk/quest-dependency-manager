# Quest Dependency Manager

A console-based quest dependency management system written in Python. This application allows users to define quests, specify dependencies between them, check for valid quest progression by preventing the start of quests whose prerequisites are not met, detect cyclical dependencies, and determine a valid topological order for quest completion. It also supports saving and loading quest data via JSON files. An HTTP API is provided for programmatic interaction, with sensitive operations protected by API key authentication.

## Overview

The Quest Dependency Manager provides a robust way to model and manage complex questlines, ensuring logical progression and preventing common issues like cyclic dependencies. It's an ideal tool for game developers, writers, or anyone needing to manage a set of tasks with interdependencies. The system can be interacted with via a simple command-line interface for local management and a RESTful HTTP API for integration with other applications.

## Features

* **Quest Representation:** Define quests with unique IDs, titles, descriptions, and a list of prerequisite quest IDs.
* **Dependency Management:**

  * Add new quests with optional dependencies.
  * Mark quests as completed.
  * Enforce prerequisites strictly: quests cannot be completed unless all dependencies are fulfilled.
* **Graph Analysis:**

  * Detect cycles in the quest graph.
  * Provide valid completion order via topological sorting.
* **Data Persistence:**

  * Save/load quest state in JSON format.
* **Interfaces:**

  * **Command-Line Interface (CLI):** Local quest management and debugging.
  * **HTTP API (FastAPI):** RESTful interface with API key protection for write operations.
* **Logging:** Unified logging for CLI and API.
* **Testing:** Core and API logic tested via `unittest`.

## Requirements

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
