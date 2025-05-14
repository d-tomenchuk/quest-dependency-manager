# 📄 Specification — Quest Dependency Manager

## Project Overview

This project implements a console-based quest dependency system using Python. It allows users to define quests, specify dependencies between them, check for valid quest progression, detect cycles, and get a topological order of completion.

---

## 🎯 Goals

- Represent quests with dependencies on other quests.
- Prevent starting a quest unless its prerequisites are completed.
- Detect cyclic dependencies.
- Provide a valid quest completion order.
- Include unit testing for core functionality.

---

## 📦 Features

### 1. Quest Structure
Each quest contains:
- `id` (str): unique identifier
- `title` (str): human-readable name
- `description` (str): short quest text
- `dependencies` (List[str]): list of quest IDs that must be completed first

### 2. Functionalities
- Add new quests with optional dependencies.
- Mark quests as completed.
- List available (unlocked) quests.
- Detect cycles in the dependency graph.
- Return a valid quest execution order using topological sorting.

### 3. Command-Line Interface
The program should provide an interactive CLI with options:
- `1` - Add new quest
- `2` - Complete quest
- `3` - List available quests
- `4` - Check for cycles
- `5` - Get completion order
- `0` - Exit

---

## 🧪 Testing Requirements

Unit tests must cover:
- Quest addition
- Quest availability logic
- Completion marking
- Cycle detection
- Topological sorting logic

Use Python’s built-in `unittest` framework. Tests should be located in `tests/test_quest.py`.

---

## 🧰 Tools & Technologies

- Python 3.10+
- `unittest` for testing
- Optionally: `json` module for serialization

---

## 🚀 Future Extensions (Optional)

- Data persistence in JSON or SQLite
- Visualization of dependencies using `networkx` or `graphviz`
- Web UI via Flask/FastAPI
- Integration with Unity/Unreal for in-game quest control





