from quest import Quest
from manager import QuestManager
from typing import List

def print_quests(quests: List[Quest]):
    if not quests:
        print("No quests available.")
        return
    for quest in quests:
        print(f"  - {quest}") 

def main():
    manager = QuestManager()
    print("Welcome to the Quest Dependency Manager!")

    while True:
        print("\nSelect an action:")
        print("1. Add new quest")
        print("2. Complete quest")
        print("3. List available quests (pending, dependencies met)")
        print("4. Check system for cyclic dependencies")
        print("5. Get recommended quest completion order")
        print("0. Exit")

        choice = input("Enter your choice: ")

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
                    elif not order and manager.has_cycles(): 
                       
                        print("Cannot determine completion order due to cycles.")
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


            elif choice == '0':
                print("Exiting program.")
                break
            else:
                print("Invalid choice. Please enter a number between 0 and 5.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()