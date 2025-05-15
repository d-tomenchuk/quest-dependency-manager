📄 Specification — Quest Dependency Manager

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


Last updated: May 15, 2025