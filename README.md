# Quest Dependency Manager

A console-based quest dependency management system written in Python. This application allows users to define quests, specify dependencies between them, check for valid quest progression by preventing the start of quests whose prerequisites are not met, detect cyclical dependencies, and determine a valid topological order for quest completion. It also supports saving and loading quest data via JSON files.

## Overview

The Quest Dependency Manager provides a robust way to model and manage complex questlines, ensuring logical progression and preventing common issues like cyclic dependencies. It's an ideal tool for game developers, writers, or anyone needing to manage a set of tasks with interdependencies. The system is interacted with via a simple command-line interface and a RESTful HTTP API.

## Features

* **Quest Representation:** Define quests with unique IDs, titles, descriptions, and a list of prerequisite quest IDs.
* **Dependency Management:**

  * Add new quests with optional dependencies.
  * Mark quests as completed.
  * Strictly enforces prerequisites: a quest cannot be marked as completed unless all its dependencies are met.
* **Graph Analysis:**

  * Detect cycles within the quest dependency graph.
  * Provide a valid quest completion order using topological sorting.
* **Data Persistence:**

  * Save the current state of all quests (including completion status) to a JSON file.
  * Load quest data from a JSON file, replacing the current state.
* **Interfaces:**

  * **Command-Line Interface (CLI):** An interactive CLI for easy local management and debugging of quests.
  * **HTTP API (FastAPI):** A RESTful API for programmatic interaction with the quest system, suitable for integration with other applications (e.g., game engines).
* **Logging:** Integrated logging for both CLI and API operations for better traceability and debugging.
* **Unit Tested:** Core functionalities and API endpoints are covered by unit tests using Python's `unittest` framework.

## Requirements

* Python 3.10 or newer.
* External packages (install via `pip install -r requirements.txt`):

  * `fastapi`
  * `uvicorn[standard]`
  * `httpx` (for API tests)

## Getting Started

### Prerequisites

1. Ensure you have Python 3.10+ installed on your system. You can download it from [python.org](https://www.python.org/).
2. It is highly recommended to use a Python virtual environment for this project.

   ```bash
   # Create a virtual environment (e.g., named .venv)
   python -m venv .venv
   # Activate it:
   # On Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # On Windows (cmd.exe):
   .\.venv\Scripts\activate.bat
   # On Linux/macOS:
   source .venv/bin/activate
   ```
3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### File Structure

```text
quest-dependency-manager/
├── .gitignore          # Specifies intentionally untracked files
├── quest.py            # Defines the Quest data model
├── manager.py          # Contains the QuestManager class for core logic
├── main.py             # Executable for the CLI application
├── api_main.py         # Executable for the FastAPI application
├── api_models.py       # Pydantic models for the API
├── requirements.txt    # Project dependencies
├── data/
│   ├── sample.json     # Sample quest definitions
│   └── quest_data.json # Default file for saving/loading active quest data
├── tests/
│   ├── __init__.py     # Makes 'tests' a Python package
│   ├── test_quest.py   # Unit tests for core logic (Quest, QuestManager)
│   └── test_api.py     # Unit tests for the FastAPI application
├── README.md           # This file
└── spec.md             # Project specification document
```

## Running the Applications

### 1. Command-Line Interface (CLI)

Navigate to the root directory of the project (`quest-dependency-manager/`).
Ensure your virtual environment is activated.
Run the CLI using:

```bash
python main.py
```

(or `python3 main.py` depending on your system's Python alias).

### 2. HTTP API (FastAPI)

Navigate to the root directory of the project.
Ensure your virtual environment is activated.
Run the FastAPI server using Uvicorn:

```bash
uvicorn api_main:app --reload --port 8000 --log-level debug
```

* `--reload`: Enables auto-reload on code changes (for development).
* `--port 8000`: Specifies the port number.
* `--log-level debug`: Sets Uvicorn's logging level.

Once the server is running, you can access:

* Interactive API documentation (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Alternative API documentation (ReDoc): [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Running Tests

To ensure the application is working correctly, you can run all unit tests:

```bash
python -m unittest discover tests
```

All tests should pass with an `OK` status.

## Command-Line Interface (CLI) Usage

When you run `python main.py`, you will be presented with this menu:

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

Follow the on-screen prompts for each option.

## API Endpoints Overview

The API provides endpoints for programmatic interaction. Key endpoints include:

* `POST /quests/`: Create a new quest.
* `GET /quests/`: Get all quests.
* `GET /quests/available/`: Get available quests.
* `GET /quests/{quest_id}`: Get a specific quest.
* `POST /quests/{quest_id}/complete`: Mark a quest as completed.
* `GET /analysis/cycles`: Check for cyclic dependencies.
* `GET /analysis/completion_order`: Get the topological completion order.
* `POST /data/save`: Save quests to a specified file.
* `POST /data/load`: Load quests from a specified file.

Refer to the API documentation at `/docs` or `/redoc` for detailed information on request/response schemas and trying out the endpoints.

## Data Storage

### Quest Data Format

Quests are saved and loaded in JSON format. The data is an array of quest objects:

```json
[
  {
    "id": "string_unique_quest_id",
    "title": "string_quest_title",
    "description": "string_quest_description",
    "dependencies": ["list_of_string_dependency_ids"],
    "completed": true
  }
]
```

**Field Descriptions:**

* `id`: (String) A unique identifier for the quest.
* `title`: (String) The human-readable name of the quest.
* `description`: (String) A short description of the quest.
* `dependencies`: (List of Strings) A list of quest IDs that must be completed before this quest can be started. An empty list means no dependencies.
* `completed`: (Boolean) `true` if the quest is completed, `false` otherwise.

### Default Save/Load File

The application (both CLI and API, unless specified otherwise) can use `data/quest_data.json` as a default file for saving and loading quest progress. This file will be created in the `data/` directory when you first save.

### Sample Data

The file `data/sample.json` provides a set of sample quest definitions. This file does not initially contain the `"completed"` field for quests. When loaded, these quests will default to an uncompleted status. You can load this file using option `7` in the CLI or the `/data/load` API endpoint by specifying `data/sample.json` as the filepath.

## License

This project is licensed under the terms specified in the LICENSE file.

---

*Last updated: May 15, 2025*
