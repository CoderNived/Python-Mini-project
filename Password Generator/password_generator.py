# password_generator.py

import random
import string

def generate_password(length):
    # Combine all character sets
    characters = string.ascii_letters + string.digits + string.punctuation
    
    # Generate random password
    password = ''.join(random.choice(characters) for _ in range(length))
    
    return password


# Main program
if __name__ == "__main__":
    try:
        length = int(input("Enter password length: "))
        
        if length <= 0:
            print("Please enter a positive number.")
        else:
            password = generate_password(length)
            print(f"Generated Password: {password}")
    
    except ValueError:
        print("Please enter a valid number.")
