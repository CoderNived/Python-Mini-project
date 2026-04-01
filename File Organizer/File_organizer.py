# file_organizer.py

import os
import shutil

def organize_files(folder_path):
    try:
        # Loop through all files in the folder
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)

            # Skip if it's a folder
            if os.path.isdir(file_path):
                continue

            # Get file extension
            _, extension = os.path.splitext(file)
            extension = extension[1:]  # remove dot

            if extension == "":
                extension = "others"

            # Create folder for extension if not exists
            dest_folder = os.path.join(folder_path, extension)
            os.makedirs(dest_folder, exist_ok=True)

            # Move file to respective folder
            shutil.move(file_path, os.path.join(dest_folder, file))

        print("Files organized successfully!")

    except Exception as e:
        print(f"Error: {e}")


# Main program
if __name__ == "__main__":
    path = input("Enter folder path: ").strip()
    organize_files(path)
