from quest import Quest
from manager import QuestManager
from typing import List
import os


DEFAULT_SAVE_FILENAME = "data/quest_data.json"

def print_quests(quests: List[Quest]):
    if not quests:
        print("No quests to display.")
        return
    for quest in quests:
        print(f"  - {quest}") 

def main():
    manager = QuestManager()
    print("Welcome to the Quest Dependency Manager!")

    # --- Optional: Auto-load quests on startup ---
    try:
        
        if os.path.exists(DEFAULT_SAVE_FILENAME):
            print(f"Attempting to auto-load quests from {DEFAULT_SAVE_FILENAME}...")
            manager.load_quests(DEFAULT_SAVE_FILENAME)
            
        else:
            print(f"Default save file {DEFAULT_SAVE_FILENAME} not found. Starting with an empty quest list.")
    except Exception as e: 
        print(f"Could not auto-load quests: {e}")
    # --- End Optional: Auto-load ---

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
                    print("Error: Quest ID cannot be empty.")
                    continue
                title = input("Enter quest title: ").strip()
                if not title:
                    print("Error: Quest title cannot be empty.")
                    continue
                description = input("Enter quest description: ")
                dependencies_str = input("Enter dependency quest IDs separated by comma (leave empty if none): ")
                
                dependencies = []
                if dependencies_str.strip():
                    dependencies = [dep_id.strip() for dep_id in dependencies_str.split(',') if dep_id.strip()]

                try:
                    new_quest = Quest(id=q_id, title=title, description=description, dependencies=dependencies)
                    manager.add_quest(new_quest)
                    print(f"Quest '{title}' (ID: {q_id}) added successfully.")
                except ValueError as e:
                    print(f"Error adding quest: {e}")

            elif choice == '2':
                q_id = input("Enter ID of the quest to complete: ").strip()
                if not q_id:
                    print("Error: Quest ID cannot be empty.")
                    continue
                try:
                    manager.complete_quest(q_id)
                except (ValueError, PermissionError) as e:
                    print(f"Error completing quest: {e}")

            elif choice == '3':
                print("\nAvailable quests:")
                available = manager.list_available_quests()
                print_quests(available)

            elif choice == '4':
                if manager.has_cycles():
                    print("Warning: Cyclic dependencies detected in the system!")
                else:
                    print("No cyclic dependencies detected.")

            elif choice == '5':
                try:
                    order = manager.get_completion_order()
                    if not order and not manager._quests: 
                         print("No quests available to order.")
                    elif order: 
                        print("\nRecommended quest completion order (by ID):")
                        for i, q_id in enumerate(order):
                            quest = manager.get_quest(q_id)
                            title_str = f" ({quest.title})" if quest else ""
                            print(f"  {i+1}. {q_id}{title_str}")
                    
                except ValueError as e: 
                    print(f"Error: {e}")
                except RuntimeError as e: 
                    print(f"Critical error determining order: {e}")
            
            elif choice == '6': 
                filepath_input = input(f"Enter filepath to save quests (default: {DEFAULT_SAVE_FILENAME}): ").strip()
                filepath_to_save = filepath_input if filepath_input else DEFAULT_SAVE_FILENAME
                try:
                    manager.save_quests(filepath_to_save)
                    
                except (IOError, TypeError) as e:
                    print(f"Error saving quests: {e}")

            elif choice == '7': 
                filepath_input = input(f"Enter filepath to load quests (default: {DEFAULT_SAVE_FILENAME}): ").strip()
                filepath_to_load = filepath_input if filepath_input else DEFAULT_SAVE_FILENAME
                
                if manager._quests: 
                    confirm_load = input(
                        "Loading will replace current quest data. Unsaved changes will be lost. Proceed? (yes/no): "
                    ).strip().lower()
                    if confirm_load != 'yes':
                        print("Load operation cancelled.")
                        continue
                try:
                    manager.load_quests(filepath_to_load)
                    
                except (FileNotFoundError, IOError, ValueError) as e:
                    print(f"Error loading quests: {e}")
            
            elif choice == '0':

                # --- Optional: Save quests on exit ---
                if manager._quests: 
                   save_on_exit = input(
                       f"Save current quests to {DEFAULT_SAVE_FILENAME} before exiting? (yes/no): "
                   ).strip().lower()
                   if save_on_exit == 'yes':
                       try:
                           manager.save_quests(DEFAULT_SAVE_FILENAME)
                       except (IOError, TypeError) as e:
                           print(f"Error saving quests on exit: {e}")
                # --- End Optional: Save on exit ---

                print("Exiting program.")
                break
            else:
                print("Invalid choice. Please enter a number between 0 and 7.") 

        except Exception as e:
            
            print(f"An unexpected error occurred in the application: {e}")


if __name__ == "__main__":
    main()