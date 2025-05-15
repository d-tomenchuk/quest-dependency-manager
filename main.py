import logging
import sys
import os
from typing import List
import json

from quest import Quest
from manager import QuestManager

try:
    from enums.quest_enums import QuestStatus, QuestType
except ImportError:
    logging.critical("CRITICAL: Could not import QuestStatus and QuestType from enums.quest_enums in main.py.")
    QuestStatus = type("QuestStatus", (object,), {s: s.lower() for s in ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "FAILED"]})
    QuestType = type("QuestType", (object,), {t: t.lower() for t in ["MAIN", "SIDE", "OPTIONAL", "REPEATABLE", "TIMED"]})


LOG_LEVEL_STR_CLI = os.getenv("CLI_LOG_LEVEL", "INFO").upper()
LOG_LEVEL_CLI = getattr(logging, LOG_LEVEL_STR_CLI, logging.INFO)

logging.basicConfig(
    level=LOG_LEVEL_CLI,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_SAVE_FILENAME = "data/quest_data.json"

def print_quests(quests: List[Quest]):
    if not quests:
        print("No quests to display.")
        return
    for quest in quests:
        print(f"  - {str(quest)}")

def main():
    manager = QuestManager()
    
    print("\nWelcome to the Quest Dependency Manager!")

    try:
        if os.path.exists(DEFAULT_SAVE_FILENAME):
            logger.info(f"Attempting to auto-load quests from {DEFAULT_SAVE_FILENAME}...")
            manager.load_quests(DEFAULT_SAVE_FILENAME)
        else:
            logger.info(f"Default save file {DEFAULT_SAVE_FILENAME} not found. Starting with an empty quest list.")
    except Exception as e:
        logger.error(f"Could not auto-load quests: {e}", exc_info=True)

    while True:
        print("\nSelect an action:")
        print(" 1. Add new quest")
        print(" 2. Start quest")
        print(" 3. Complete quest")
        print(" 4. Fail quest")
        print(" 5. Reset repeatable quest")
        print(" 6. List available quests (not started, dependencies met)")
        print(" 7. List all quests (with details)")
        print(" 8. Check system for cyclic dependencies")
        print(" 9. Get recommended quest completion order")
        print("10. Save quests to JSON file")
        print("11. Load quests from JSON file")
        print(" 0. Exit")

        choice = input("Enter your choice: ").strip()

        try:
            if choice == '1':
                q_id = input("Enter quest ID: ").strip()
                if not q_id:
                    logger.warning("Quest ID cannot be empty.")
                    print("Error: Quest ID cannot be empty.")
                    continue
                title = input("Enter quest title: ").strip()
                if not title:
                    logger.warning("Quest title cannot be empty.")
                    print("Error: Quest title cannot be empty.")
                    continue
                description = input("Enter quest description: ")
                dependencies_str = input("Enter dependency quest IDs separated by comma (leave empty if none): ")
                
                dependencies = []
                if dependencies_str.strip():
                    dependencies = [dep_id.strip() for dep_id in dependencies_str.split(',') if dep_id.strip()]

                print("Available quest types:")
                for i, member in enumerate(QuestType):
                    print(f"  {i+1}. {member.name} ({member.value})")
                type_choice_str = input(f"Choose quest type (number or value, default: {QuestType.SIDE.value}): ").strip()
                quest_q_type = QuestType.SIDE
                if type_choice_str:
                    try:
                        if type_choice_str.isdigit():
                            type_index = int(type_choice_str) - 1
                            if 0 <= type_index < len(list(QuestType)):
                                quest_q_type = list(QuestType)[type_index]
                            else:
                                print(f"Invalid number. Using default type {quest_q_type.value}.")
                        else:
                            quest_q_type = QuestType(type_choice_str.lower())
                    except ValueError:
                        print(f"Invalid type value. Using default type {quest_q_type.value}.")
                        logger.warning(f"Invalid quest type input: '{type_choice_str}'. Defaulting to {quest_q_type.value}")
                
                rewards_str = input("Enter rewards as JSON string (e.g., '[{\"type\":\"xp\", \"amount\":100}]') or leave empty: ").strip()
                rewards_list = []
                if rewards_str:
                    try:
                        rewards_list = json.loads(rewards_str)
                        if not isinstance(rewards_list, list):
                            print("Error: Rewards must be a list. Rewards not set.")
                            rewards_list = []
                    except json.JSONDecodeError:
                        print("Error: Invalid JSON format for rewards. Rewards not set.")
                
                try:
                    new_quest = Quest(
                        id=q_id, 
                        title=title, 
                        description=description, 
                        dependencies=dependencies,
                        quest_type=quest_q_type,
                        rewards=rewards_list
                    )
                    manager.add_quest(new_quest)
                    print(f"Quest '{title}' (ID: {q_id}) added with type '{quest_q_type.value}'.")
                    logger.info(f"CLI: Quest '{title}' (ID: {q_id}) submitted for addition.")
                except ValueError as e:
                    print(f"Error adding quest: {e}")
                    logger.error(f"CLI: Error adding quest: {e}")

            elif choice == '2':
                q_id = input("Enter ID of the quest to start: ").strip()
                if not q_id:
                    print("Error: Quest ID cannot be empty.")
                    continue
                try:
                    manager.start_quest(q_id)
                    quest = manager.get_quest(q_id)
                    print(f"Quest '{quest.title if quest else q_id}' (ID: {q_id}) started.")
                    logger.info(f"CLI: Submitted request to start quest '{q_id}'.")
                except (ValueError, PermissionError) as e:
                    print(f"Error starting quest '{q_id}': {e}")
                    logger.error(f"CLI: Error starting quest '{q_id}': {e}")
            
            elif choice == '3':
                q_id = input("Enter ID of the quest to complete: ").strip()
                if not q_id:
                    print("Error: Quest ID for completion cannot be empty.")
                    continue
                try:
                    manager.complete_quest(q_id)
                    quest = manager.get_quest(q_id)
                    print(f"Quest '{quest.title if quest else q_id}' (ID: {q_id}) completed.")
                    logger.info(f"CLI: Submitted request to complete quest '{q_id}'.")
                except (ValueError, PermissionError) as e:
                    print(f"Error completing quest '{q_id}': {e}")
                    logger.error(f"CLI: Error completing quest '{q_id}': {e}")
            
            elif choice == '4':
                q_id = input("Enter ID of the quest to fail: ").strip()
                if not q_id:
                    print("Error: Quest ID cannot be empty.")
                    continue
                try:
                    manager.fail_quest(q_id)
                    quest = manager.get_quest(q_id)
                    print(f"Quest '{quest.title if quest else q_id}' (ID: {q_id}) failed.")
                    logger.info(f"CLI: Submitted request to fail quest '{q_id}'.")
                except (ValueError, PermissionError) as e:
                    print(f"Error failing quest '{q_id}': {e}")
                    logger.error(f"CLI: Error failing quest '{q_id}': {e}")

            elif choice == '5':
                q_id = input("Enter ID of the repeatable quest to reset: ").strip()
                if not q_id:
                    print("Error: Quest ID cannot be empty.")
                    continue
                try:
                    manager.reset_repeatable_quest(q_id)
                    quest = manager.get_quest(q_id)
                    print(f"Quest '{quest.title if quest else q_id}' (ID: {q_id}) reset.")
                    logger.info(f"CLI: Submitted request to reset quest '{q_id}'.")
                except (ValueError, PermissionError) as e:
                    print(f"Error resetting quest '{q_id}': {e}")
                    logger.error(f"CLI: Error resetting quest '{q_id}': {e}")

            elif choice == '6':
                print("\nAvailable quests (NOT_STARTED, dependencies met):")
                available = manager.list_available_quests()
                print_quests(available)
                logger.info(f"CLI: Displayed {len(available)} available quests.")

            elif choice == '7':
                print("\nAll quests in the system:")
                all_quests = list(manager._quests.values())
                if all_quests:
                    print_quests(sorted(all_quests, key=lambda q: q.id))
                else:
                    print("No quests in the system.")
                logger.info(f"CLI: Displayed all {len(all_quests)} quests.")

            elif choice == '8':
                logger.info("CLI: Checking for cycles.")
                if manager.has_cycles():
                    print("Warning: Cyclic dependencies detected in the system!")
                else:
                    print("No cyclic dependencies detected.")

            elif choice == '9':
                logger.info("CLI: Requesting completion order.")
                try:
                    order = manager.get_completion_order()
                    if not order and not manager._quests:
                        print("No quests available to order.")
                    elif order:
                        print("\nRecommended quest completion order (by ID):")
                        for i, q_id_ordered in enumerate(order):
                            quest = manager.get_quest(q_id_ordered)
                            print(f"  {i+1}. {str(quest) if quest else q_id_ordered}")
                except ValueError as e:
                    print(f"Error: {e}")
                    logger.error(f"CLI: Error determining completion order: {e}")
                except RuntimeError as e:
                    print(f"Critical error: {e}")
                    logger.critical(f"CLI: Critical error determining order: {e}", exc_info=True)
            
            elif choice == '10':
                filepath_input = input(f"Enter filepath to save quests (default: {DEFAULT_SAVE_FILENAME}): ").strip()
                filepath_to_save = filepath_input if filepath_input else DEFAULT_SAVE_FILENAME
                logger.info(f"CLI: Attempting to save quests to {filepath_to_save}.")
                try:
                    manager.save_quests(filepath_to_save)
                    print(f"Quests saved to {filepath_to_save}")
                except (IOError, TypeError) as e:
                    print(f"Error saving quests: {e}")
                    logger.error(f"CLI: Error saving quests to {filepath_to_save}: {e}", exc_info=True)

            elif choice == '11':
                filepath_input = input(f"Enter filepath to load quests (default: {DEFAULT_SAVE_FILENAME}): ").strip()
                filepath_to_load = filepath_input if filepath_input else DEFAULT_SAVE_FILENAME
                
                logger.info(f"CLI: Preparing to load quests from {filepath_to_load}.")
                if manager._quests:
                    confirm_load = input(
                        "Loading will replace current quest data. Unsaved changes will be lost. Proceed? (yes/no): "
                    ).strip().lower()
                    if confirm_load != 'yes':
                        logger.info("CLI: Load operation cancelled by user.")
                        print("Load operation cancelled.")
                        continue
                try:
                    manager.load_quests(filepath_to_load)
                    print(f"Quests loaded from {filepath_to_load}")
                except (FileNotFoundError, IOError, ValueError) as e:
                    print(f"Error loading quests: {e}")
                    logger.error(f"CLI: Error loading quests from {filepath_to_load}: {e}", exc_info=True)
            
            elif choice == '0':
                logger.info("CLI: User initiated exit.")
                if manager._quests:
                    save_on_exit = input(
                        f"Save current quests to {DEFAULT_SAVE_FILENAME} before exiting? (yes/no): "
                    ).strip().lower()
                    if save_on_exit == 'yes':
                        logger.info(f"CLI: Attempting to save quests to {DEFAULT_SAVE_FILENAME} on exit.")
                        try:
                            manager.save_quests(DEFAULT_SAVE_FILENAME)
                            print(f"Quests saved to {DEFAULT_SAVE_FILENAME}.")
                        except (IOError, TypeError) as e:
                            print(f"Error saving quests on exit: {e}")
                            logger.error(f"CLI: Error saving quests on exit to {DEFAULT_SAVE_FILENAME}: {e}", exc_info=True)
                
                logger.info("CLI: Exiting program.")
                print("Exiting program.")
                break
            else:
                logger.warning(f"CLI: Invalid choice entered: '{choice}'.")
                print("Invalid choice. Please enter a valid number from the menu.")

        except Exception as e:
            logger.critical(f"CLI: An unexpected error occurred in the application main loop: {e}", exc_info=True)
            print(f"An unexpected critical error occurred: {e}")

if __name__ == "__main__":
    main()