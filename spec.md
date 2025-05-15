📄 Specification — Quest Dependency Manager

**Purpose & Use Cases**

The Quest Dependency Manager is a Python-based system designed for creating, managing, and tracking tasks (or "quests") and their interdependencies. It ensures logical progression by preventing tasks from starting before their prerequisites are met, detects cyclical dependencies, and can determine an optimal completion order.

This system is versatile and can be applied in various domains, including:
* **Game Development**: Managing complex questlines and storylines in video games, especially RPGs.
* **Project Management**: Breaking down projects into dependent tasks, tracking progress, and identifying critical paths.
* **Educational Platforms**: Structuring learning modules where access to new content depends on completing prior lessons.
* **Workflow Management**: Modeling and automating business processes with sequential and conditional steps.
* **General Task Planning**: Organizing any set of tasks where order and prerequisites are crucial.

Project Overview

This project implements a console-based and API-driven quest dependency system using Python. It allows users to define quests, specify dependencies between them, check for valid quest progression, detect cycles, and determine a topological order of quest completion. The system supports both interactive command-line usage and RESTful API interaction via FastAPI.

🎯 Goals

Represent quests with dependencies on other quests.

Prevent starting a quest unless its prerequisites are completed.

Detect cyclic dependencies in the quest graph.

Provide a valid quest completion order via topological sorting.

Ensure core functionality is covered by unit tests.

Provide a RESTful API for integration.

📦 Features

1. Quest Structure

Each quest contains the following fields:

id (str): A unique identifier.

title (str): A human-readable name.

description (str): A short quest summary.

dependencies (List[str]): A list of quest IDs that must be completed first.

completed (bool): Completion status (default: false).

2. Functionalities

Add new quests with optional dependencies.

Mark quests as completed (only if prerequisites are satisfied).

List available (unlocked) quests.

Detect cycles in the dependency graph.

Return a valid quest execution order using topological sorting.

Save and load quest data using JSON files.

3. Command-Line Interface (CLI)

An interactive CLI with the following options:

1 - Add new quest
2 - Complete quest
3 - List available quests
4 - Check for cycles
5 - Get completion order
6 - Save quests to JSON file
7 - Load quests from JSON file
0 - Exit

4. RESTful API (FastAPI)

Key endpoints:

POST /quests/: Create a new quest.

GET /quests/: List all quests.

GET /quests/available/: Get available (unlocked) quests.

POST /quests/{quest_id}/complete: Complete a quest.

GET /analysis/cycles: Check for cycles in the dependency graph.

GET /analysis/completion_order: Get topological quest order.

POST /data/save: Save quest data to a file.

POST /data/load: Load quest data from a file.

🧪 Testing Requirements

Use Python’s built-in unittest framework.
Unit tests must cover:

Adding quests

Determining available quests

Marking quests as completed

Detecting cycles

Topological sorting

Test files are located in:

tests/
├── test_quest.py   # Unit tests for core logic
├── test_api.py     # Unit tests for API endpoints

🧰 Tools & Technologies

Python 3.10+

unittest (testing)

json module (data serialization)

fastapi, uvicorn, httpx (API functionality and testing)

💡 Potential Enhancements & Future Features

This section outlines potential improvements and new features that could be added to the Quest Dependency Manager.
(✔️ = Partially implemented or good foundation exists; ➡️ = To be developed)

1.  **Core Logic & Data Model:**
    * ✔️ **Stricter Validation**: Good validation exists in `Quest.from_dict` and `QuestManager.add_quest`; can be expanded (e.g., ID formats, self-dependencies more explicitly).
    * ➡️ **Expanded Quest Attributes**:
        * ➡️ Rewards/Consequences: Define outcomes for quest completion or failure.
        * ➡️ Quest Types: Categorize quests (e.g., main, side, optional).
        * ➡️ Detailed Statuses: Extend `completed` to states like `not_started`, `in_progress`, `failed`.
        * ➡️ Failure Conditions: Define criteria for quest failure.
    * ➡️ **Advanced Dependencies**:
        * ➡️ "OR" Dependencies: Allow quests to be unlocked if one of several prerequisite sets is met.
        * ➡️ Incompatible Quests: Specify quests that cannot be active or completed simultaneously.
        * ➡️ Time-Limited Quests: Add start/end availability times.
    * ✔️ **Configuration Management**: Default filenames used; could be centralized further.

2.  **API Enhancements (FastAPI):**
    * ➡️ **Pagination**: Implement for endpoints returning lists (`/quests/`, `/quests/available/`).
    * ➡️ **Filtering & Sorting**: Allow filtering and sorting of quest lists by various attributes.
    * ➡️ **Partial Updates (PATCH)**: Add an endpoint for modifying specific quest fields.
    * ✔️ **Structured Error Responses**: FastAPI provides some structure; can be customized for more detail.
    * ➡️ **Asynchronous Operations**: Consider making file I/O operations in `QuestManager` asynchronous if performance with large datasets becomes a concern. (Current operations are likely fast enough for typical use cases).

3.  **CLI Improvements:**
    * ➡️ **Interactive Editing**: Allow modification of existing quests field by field.
    * ➡️ **Text-Based Graph Visualization**: Display quest dependencies in a simple visual format.
    * ➡️ **Quest Search**: Implement search functionality by ID, title, or description.

4.  **New Systems & Integrations:**
    * ➡️ **Webhook/Event System**: Notify external systems (via webhooks) upon quest state changes.
    * ✔️ **Data Versioning/Backup**: Manual via saving to different files; could be automated.
    * ➡️ **Internationalization (i18n)**: Add support for multiple languages in CLI/API messages.

5.  **Operational & Security Enhancements:**
    * ✔️ **Enhanced Logging Configuration**: Good foundation with `getenv` for log levels; format and output could be more configurable.
    * ✔️ **Stricter API Key Handling**: Default key warning exists; could add "production mode" enforcement.

Last updated: May 15, 2025