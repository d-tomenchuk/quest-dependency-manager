# Quest Dependency Manager

A console-based quest dependency management system written in Python. This application allows users to define quests, specify dependencies between them, check for valid quest progression by preventing the start of quests whose prerequisites are not met, detect cyclical dependencies, and determine a valid topological order for quest completion. It also supports saving and loading quest data via JSON files.

## Overview

The Quest Dependency Manager provides a robust way to model and manage complex questlines, ensuring logical progression and preventing common issues like cyclic dependencies. It's an ideal tool for game developers, writers, or anyone needing to manage a set of tasks with interdependencies. The system is interacted with via a simple command-line interface.

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
* **Command-Line Interface:** An interactive CLI for easy management of quests and system functions.
* **Unit Tested:** Core functionalities are covered by unit tests using Python's `unittest` framework.

## Requirements

* Python 3.10 or newer.

## Getting Started

### Prerequisites

Ensure you have Python 3.10+ installed on your system. You can download it from [python.org](https://www.python.org/).

### File Structure

The project has the following key files:

quest-dependency-manager/
├── .gitignore          # Specifies intentionally untracked files that Git should ignore
├── quest.py            # Defines the Quest data model
├── manager.py          # Contains the QuestManager class for all quest logic
├── main.py             # The main executable for the CLI application
├── data/
│   ├── sample.json     # Sample quest definitions (without completion status)
│   └── quest\_data.json # Default file for saving/loading active quest data (created on save)
├── tests/
│   ├── init.py     # Makes the 'tests' directory a Python package
│   └── test\_quest.py   # Unit tests for the system
├── README.md           # This file
└── spec.md             # Project specification document

### Running the Application

1. Navigate to the root directory of the project (`quest-dependency-manager/`).
2. Run the command-line interface using:

   ```bash
   python main.py
   ```

   (or `python3 main.py` depending on your system's Python alias).

### Running Tests

To ensure the application is working correctly, you can run the unit tests:

1. Navigate to the root directory of the project (`quest-dependency-manager/`).
2. Run the tests using Python's `unittest` module:

   ```bash
   python -m unittest discover tests
   ```

   Alternatively, you can run a specific test file:

   ```bash
   python -m unittest tests.test_quest
   ```

   All tests should pass with an `OK` status.

## Command-Line Interface (CLI) Usage

Once the application is running (`python main.py`), you will be presented with the following menu:

* **1. Add new quest:** Prompts for quest ID, title, description, and a comma-separated list of dependency IDs.
* **2. Complete quest:** Prompts for the ID of the quest to mark as completed. Prerequisites must be met.
* **3. List available quests:** Shows quests that are not yet completed and whose dependencies have been satisfied.
* **4. Check for cycles:** Reports if any cyclic dependencies are present in the quest graph.
* **5. Get completion order:** Displays a valid topological sort of quest IDs, if no cycles exist.
* **6. Save quests to JSON file:** Prompts for a filepath (defaults to `data/quest_data.json`) and saves the current quest data.
* **7. Load quests from JSON file:** Prompts for a filepath (defaults to `data/quest_data.json`) and loads quest data, replacing any current data. Warns before overwriting unsaved changes.
* **0. Exit:** Exits the application.

## Data Storage

### Quest Data Format

Quests are saved and loaded in JSON format. Each quest is represented as an object with the following fields:

```json
[
  {
    "id": "string_unique_quest_id",
    "title": "string_quest_title",
    "description": "string_quest_description",
    "dependencies": ["list_of_string_dependency_ids"],
    "completed": boolean_completion_status
  }
  // ... more quest objects
]
```

* `id`: (String) A unique identifier for the quest.
* `title`: (String) The human-readable name of the quest.
* `description`: (String) A short description of the quest.
* `dependencies`: (List of Strings) A list of quest IDs that must be completed before this quest can be started. An empty list means no dependencies.
* `completed`: (Boolean) `true` if the quest is completed, `false` otherwise.

### Default Save/Load File

* The application uses `data/quest_data.json` as the default file for saving and loading quest progress. This file will be created in the `data/` directory when you first save.

### Sample Data

* The file `data/sample.json` provides a set of sample quest definitions. This file does **not** initially contain the `"completed"` field for quests. When loaded, these quests will default to an uncompleted status. You can load this file using option `7` in the CLI and specifying `data/sample.json` as the filepath.
