# email_slicer.py

def email_slicer(email):
    try:
        # Split email into username and domain
        username, domain = email.split('@')
        
        # Split domain into domain name and extension
        domain_name, extension = domain.split('.')
        
        print(f"Username      : {username}")
        print(f"Domain Name   : {domain_name}")
        print(f"Extension     : {extension}")
    
    except ValueError:
        print("Invalid email format. Please enter a valid email.")

# Main program
if __name__ == "__main__":
    email_input = input("Enter your email: ").strip()
    email_slicer(email_input)
