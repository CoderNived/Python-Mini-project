# Random_Password_ListGenerator.py

import random
import string

def generate_password(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


def generate_password_list(count, length):
    passwords = []
    
    for _ in range(count):
        passwords.append(generate_password(length))
    
    return passwords


# Main program
if __name__ == "__main__":
    try:
        count = int(input("How many passwords to generate? "))
        length = int(input("Enter length of each password: "))
        
        if count <= 0 or length <= 0:
            print("Please enter positive numbers.")
        else:
            password_list = generate_password_list(count, length)
            
            print("\nGenerated Passwords:")
            for i, pwd in enumerate(password_list, start=1):
                print(f"{i}. {pwd}")
    
    except ValueError:
        print("Please enter valid numbers.")
