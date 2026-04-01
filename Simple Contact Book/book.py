# simple_contact_book.py

contacts = {}

def add_contact():
    name = input("Enter name: ").strip()
    phone = input("Enter phone number: ").strip()
    
    contacts[name] = phone
    print("Contact added successfully!\n")


def view_contacts():
    if not contacts:
        print("No contacts found.\n")
        return
    
    print("\nContact List:")
    for name, phone in contacts.items():
        print(f"{name} : {phone}")
    print()


def search_contact():
    name = input("Enter name to search: ").strip()
    
    if name in contacts:
        print(f"{name} : {contacts[name]}\n")
    else:
        print("Contact not found.\n")


def delete_contact():
    name = input("Enter name to delete: ").strip()
    
    if name in contacts:
        del contacts[name]
        print("Contact deleted successfully!\n")
    else:
        print("Contact not found.\n")


def main():
    while True:
        print("==== Contact Book ====")
        print("1. Add Contact")
        print("2. View Contacts")
        print("3. Search Contact")
        print("4. Delete Contact")
        print("5. Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            add_contact()
        elif choice == "2":
            view_contacts()
        elif choice == "3":
            search_contact()
        elif choice == "4":
            delete_contact()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.\n")


# Run program
if __name__ == "__main__":
    main()
