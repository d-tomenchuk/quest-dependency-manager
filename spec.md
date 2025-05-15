📄 Specification — Quest Dependency Manager

**Purpose & Use Cases**

The Quest Dependency Manager is a Python-based system designed for creating, managing, and tracking tasks (or "quests") and their interdependencies. It ensures logical progression by preventing tasks from starting before their prerequisites are met, supports various quest statuses and types, allows defining outcomes, detects cyclical dependencies, and can determine an optimal completion order.

This system is versatile and can be applied in various domains, including:
* **Game Development**: Managing complex questlines and storylines with different types of quests (main, side, repeatable, timed), detailed statuses, and defined rewards or consequences.
* **Project Management**: Breaking down projects into dependent tasks, tracking detailed task statuses, and identifying critical paths.
* **Educational Platforms**: Structuring learning modules where access to new content depends on completing prior lessons, with different types of assignments.
* **Workflow Management**: Modeling and automating business processes with sequential and conditional steps, and tracking their state.
* **General Task Planning**: Organizing any set of tasks where order, prerequisites, types, and statuses are crucial.

Project Overview

This project implements a console-based and API-driven quest dependency system using Python. It allows users to define quests with various attributes (including types, rewards, consequences, failure conditions), specify dependencies between them, manage their lifecycle (not started, in progress, completed, failed), check for valid quest progression, detect cycles, and determine a topological order of quest completion. The system supports both interactive command-line usage and RESTful API interaction via FastAPI.

🎯 Goals

* Represent quests with dependencies on other quests and expanded attributes.
* Manage a detailed lifecycle for quests (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`).
* Prevent starting a quest unless its prerequisites are completed.
* Detect cyclic dependencies in the quest graph.
* Provide a valid quest completion order via topological sorting.
* Ensure core functionality is covered by unit tests.
* Provide a RESTful API for integration.

📦 Features

1.  **Quest Structure**

    Each quest contains the following fields:

    * `id` (str): A unique identifier.
    * `title` (str): A human-readable name.
    * `description` (str): A short quest summary.
    * `dependencies` (List[str]): A list of quest IDs that must be completed first.
    * `status` (Enum: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`): The current state of the quest. (Default: `NOT_STARTED`)
    * `quest_type` (Enum: `MAIN`, `SIDE`, `OPTIONAL`, `REPEATABLE`, `TIMED`): The category of the quest. (Default: `SIDE`)
    * `rewards` (List[Dict[str, Any]]): A list of rewards for completing the quest (e.g., `[{"type": "xp", "amount": 100}]`). (Default: `[]`)
    * `consequences` (List[Dict[str, Any]]): A list of consequences for failing the quest. (Default: `[]`)
    * `failure_conditions` (List[Dict[str, Any]]): A list of criteria for quest failure. (Default: `[]`)
    * `start_time` (Optional[datetime]): Timestamp for when a `TIMED` quest was started. (Default: `None`)

2.  **Functionalities**

    * Add new quests with optional dependencies and various attributes.
    * Manage quest lifecycle:
        * Start a quest (changes status to `IN_PROGRESS`).
        * Complete a quest (changes status to `COMPLETED`, only if prerequisites are satisfied and quest is in progress).
        * Fail a quest (changes status to `FAILED`).
        * Reset a repeatable quest (changes status from `COMPLETED` back to `NOT_STARTED`).
    * List available (unlocked and not started) quests.
    * List all quests with their current details.
    * Detect cycles in the dependency graph.
    * Return a valid quest execution order using topological sorting.
    * Save and load quest data using JSON files, preserving all attributes.

3.  **Command-Line Interface (CLI)**

    An interactive CLI with the following options:

    1.  Add new quest (with type and simplified rewards input)
    2.  Start quest
    3.  Complete quest
    4.  Fail quest
    5.  Reset repeatable quest
    6.  List available quests (not started, dependencies met)
    7.  List all quests (with details)
    8.  Check system for cyclic dependencies
    9.  Get recommended quest completion order
    10. Save quests to JSON file
    11. Load quests from JSON file
    0.  Exit

4.  **RESTful API (FastAPI)**

    Key endpoints:

    * `POST /quests/`: Create a new quest (supports all new attributes).
    * `GET /quests/`: List all quests (returns new attributes).
    * `GET /quests/{quest_id}`: Get a specific quest (returns new attributes).
    * `GET /quests/available/`: Get available (unlocked and not started) quests.
    * `POST /quests/{quest_id}/start`: Start a quest.
    * `POST /quests/{quest_id}/complete`: Complete a quest.
    * `POST /quests/{quest_id}/fail`: Fail a quest.
    * `POST /quests/{quest_id}/reset`: Reset a repeatable quest.
    * `GET /analysis/cycles`: Check for cycles in the dependency graph.
    * `GET /analysis/completion_order`: Get topological quest order.
    * `POST /data/save`: Save quest data to a file.
    * `POST /data/load`: Load quest data from a file.

🧪 Testing Requirements

* Use Python’s built-in `unittest` framework.
* Unit tests must cover:
    * Quest creation with all attributes and their validation.
    * Quest status transitions and lifecycle management.
    * Determining available quests based on new status logic.
    * Marking quests as started, completed, failed, and reset.
    * Detecting cycles.
    * Topological sorting.
    * Serialization and deserialization of all quest attributes (including Enums and datetime).
* Test files are located in:
    ```
    tests/
    ├── __init__.py
    ├── test_quest.py   # Unit tests for Quest class logic
    ├── test_manager.py # Unit tests for QuestManager class logic
    └── test_api.py     # Unit tests for API endpoints
    ```

🧰 Tools & Technologies

* Python 3.10+
* `unittest` (testing)
* `json` module (data serialization)
* `datetime` module (for `start_time`)
* `enum` module (for `QuestStatus`, `QuestType`)
* `fastapi`, `uvicorn`, `httpx` (API functionality and testing)
* `python-dotenv` (environment variable management)

💡 Potential Enhancements & Future Features

This section outlines potential improvements and new features that could be added to the Quest Dependency Manager.
(✅ = Implemented; ✔️ = Partially implemented or good foundation exists; ➡️ = To be developed)

1.  **Core Logic & Data Model:**
    * ✔️ **Stricter Validation**: Good validation exists; can be expanded (e.g., ID formats, self-dependencies more explicitly, validation of `rewards`/`consequences` structure).
    * ✅ **Expanded Quest Attributes**:
        * ✅ Rewards/Consequences: Structures defined and stored. *Active application logic is external.*
        * ✅ Quest Types: Categorize quests (e.g., main, side, optional, repeatable, timed).
        * ✅ Detailed Statuses: Extended to `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`.
        * ✅ Failure Conditions: Structures defined and stored. *Active checking logic is external.*
    * ➡️ **Advanced Dependencies**:
        * ➡️ "OR" Dependencies: Allow quests to be unlocked if one of several prerequisite sets is met.
        * ➡️ Incompatible Quests: Specify quests that cannot be active or completed simultaneously.
    * ✔️ **Time-Limited Quests**: `TIMED` type and `start_time` attribute exist. *Active timeout logic is external.*
    * ✔️ **Configuration Management**: Default filenames used; could be centralized further.

2.  **API Enhancements (FastAPI):**
    * ➡️ **Pagination**: Implement for endpoints returning lists (`/quests/`, `/quests/available/`).
    * ➡️ **Filtering & Sorting**: Allow filtering and sorting of quest lists by various attributes (status, type, etc.).
    * ➡️ **Partial Updates (PATCH)**: Add an endpoint for modifying specific quest fields without sending the whole object.
    * ✔️ **Structured Error Responses**: FastAPI provides good structure; can be customized for more detail.
    * ➡️ **Asynchronous Operations**: Consider making file I/O operations in `QuestManager` asynchronous if performance with large datasets becomes a concern.

3.  **CLI Improvements:**
    * ➡️ **Interactive Editing**: Allow modification of existing quests field by field.
    * ✔️ **Input for Complex Fields**: Basic JSON string input for rewards; can be made more user-friendly.
    * ➡️ **Text-Based Graph Visualization**: Display quest dependencies in a simple visual format.
    * ➡️ **Quest Search**: Implement search functionality by ID, title, or description.

4.  **New Systems & Integrations:**
    * ➡️ **Active Outcome Processing**: Integrate logic to actually process rewards/consequences.
    * ➡️ **Active Failure Condition Checking**: Integrate logic for time limits or other failure conditions.
    * ➡️ **Webhook/Event System**: Notify external systems (via webhooks) upon quest state changes.
    * ✔️ **Data Versioning/Backup**: Manual via saving to different files; could be automated.
    * ➡️ **Internationalization (i18n)**: Add support for multiple languages in CLI/API messages.

5.  **Operational & Security Enhancements:**
    * ✔️ **Enhanced Logging Configuration**: Good foundation with `getenv` for log levels; format and output could be more configurable.
    * ✔️ **Stricter API Key Handling**: Default key warning exists; could add "production mode" enforcement.

Last updated: May 15, 2025