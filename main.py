import logging
import sys
import os
from typing import List

from quest import Quest
from manager import QuestManager


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
        
        print(f"  - {quest}")

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
        print("1. Add new quest")
        print("2. Complete quest")
        print("3. List available quests (pending, dependencies met)")
        print("4. Check system for cyclic dependencies")
        print("5. Get recommended quest completion order")
        print("6. Save quests to JSON file")
        print("7. Load quests from JSON file")
        print("0. Exit")

        choice = input("Enter your choice: ").strip()

        try:
            if choice == '1':
                q_id = input("Enter quest ID: ").strip()
                if not q_id:
                    logger.warning("Quest ID cannot be empty.")
                    continue
                title = input("Enter quest title: ").strip()
                if not title:
                    logger.warning("Quest title cannot be empty.")
                    continue
                description = input("Enter quest description: ")
                dependencies_str = input("Enter dependency quest IDs separated by comma (leave empty if none): ")
                
                dependencies = []
                if dependencies_str.strip():
                    dependencies = [dep_id.strip() for dep_id in dependencies_str.split(',') if dep_id.strip()]

                try:
                    new_quest = Quest(id=q_id, title=title, description=description, dependencies=dependencies)
                    manager.add_quest(new_quest) 
                    logger.info(f"CLI: Quest '{title}' (ID: {q_id}) submitted for addition.")
                except ValueError as e:
                    logger.error(f"CLI: Error adding quest: {e}")

            elif choice == '2':
                q_id = input("Enter ID of the quest to complete: ").strip()
                if not q_id:
                    logger.warning("Quest ID for completion cannot be empty.")
                    continue
                try:
                    manager.complete_quest(q_id) 
                    logger.info(f"CLI: Submitted request to complete quest '{q_id}'.")
                except (ValueError, PermissionError) as e:
                    logger.error(f"CLI: Error completing quest '{q_id}': {e}")

            elif choice == '3':
                
                print("\nAvailable quests:")
                available = manager.list_available_quests()
                print_quests(available) 
                logger.info(f"CLI: Displayed {len(available)} available quests.")

            elif choice == '4':
                logger.info("CLI: Checking for cycles.")
                if manager.has_cycles(): 
                    print("Warning: Cyclic dependencies detected in the system!") 
                else:
                    print("No cyclic dependencies detected.") 

            elif choice == '5':
                logger.info("CLI: Requesting completion order.")
                try:
                    order = manager.get_completion_order() 
                    if not order and not manager._quests:
                         
                        print("No quests available to order.")
                    elif order:
                        
                        print("\nRecommended quest completion order (by ID):")
                        for i, q_id_ordered in enumerate(order): 
                            quest = manager.get_quest(q_id_ordered)
                            title_str = f" ({quest.title})" if quest else ""
                            print(f"  {i+1}. {q_id_ordered}{title_str}")
                except ValueError as e:
                    logger.error(f"CLI: Error determining completion order: {e}")
                    print(f"Error: {e}") 
                except RuntimeError as e:
                    logger.critical(f"CLI: Critical error determining order: {e}", exc_info=True)
                    print(f"Critical error: {e}") 
            
            elif choice == '6':
                filepath_input = input(f"Enter filepath to save quests (default: {DEFAULT_SAVE_FILENAME}): ").strip()
                filepath_to_save = filepath_input if filepath_input else DEFAULT_SAVE_FILENAME
                logger.info(f"CLI: Attempting to save quests to {filepath_to_save}.")
                try:
                    manager.save_quests(filepath_to_save) 
                except (IOError, TypeError) as e:
                    logger.error(f"CLI: Error saving quests to {filepath_to_save}: {e}", exc_info=True)
                    print(f"Error saving quests: {e}") 

            elif choice == '7':
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
                except (FileNotFoundError, IOError, ValueError) as e:
                    logger.error(f"CLI: Error loading quests from {filepath_to_load}: {e}", exc_info=True)
                    print(f"Error loading quests: {e}") 
            
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
                        except (IOError, TypeError) as e:
                            logger.error(f"CLI: Error saving quests on exit to {DEFAULT_SAVE_FILENAME}: {e}", exc_info=True)
                            print(f"Error saving quests on exit: {e}") 
                
                logger.info("CLI: Exiting program.")
                print("Exiting program.") 
                break
            else:
                logger.warning(f"CLI: Invalid choice entered: '{choice}'.")
                print("Invalid choice. Please enter a number between 0 and 7.") 

        except Exception as e:
            logger.critical(f"CLI: An unexpected error occurred in the application main loop: {e}", exc_info=True)
            print(f"An unexpected error occurred: {e}") 

if __name__ == "__main__":
    main()