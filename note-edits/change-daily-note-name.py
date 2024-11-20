import os
import re

def rename_files_recursive(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path):
                match = re.match(r'(\d{4})\.(\d{2})\.(\d{2})\.md', filename)
                if match:
                    year, month, day = match.groups()
                    new_filename = f"{year}-{month}-{day}.md"
                    new_file_path = os.path.join(root, new_filename)
                    os.rename(file_path, new_file_path)
                    print(f"Renamed '{filename}' to '{new_filename}'")

# Change 'directory_path' to the path of the root directory
directory_path = '/Users/christopherdettloff/notespace'

rename_files_recursive(directory_path)
print("File names with date format changed from 'YYYY.MM.DD.md' to 'YYYY-MM-DD.md' recursively.")