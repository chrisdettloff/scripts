import os
import re

def remove_first_line_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    with open(file_path, 'w') as file:
        file.writelines(lines[2:])

def parse_directory(directory):
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and item.endswith('.md'):
            remove_first_line_from_file(item_path)
        elif os.path.isdir(item_path):
            parse_directory(item_path)

directory_path = '/Users/christopherdettloff/notespace'

parse_directory(directory_path)