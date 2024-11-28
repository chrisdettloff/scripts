import os
import shutil
import subprocess
from datetime import datetime

OBSIDIAN_BLOGS_FOLDER = '/path/to/obsidian/blogs'
PUBLISH_FOLDER = os.path.join(OBSIDIAN_BLOGS_FOLDER, 'publish')
PUBLISHED_FOLDER = os.path.join(PUBLISH_FOLDER, 'published')
BLOG_REPO_FOLDER = '/path/to/blog/repo'
BLOG_POSTS_FOLDER = os.path.join(BLOG_REPO_FOLDER, '/path/to/blog/folder')

def generate_frontmatter(title):
    # Strip .md extension and convert dashes/underscores to spaces for title
    title = title.replace('.md', '').replace('-', ' ').replace('_', ' ')
    today = datetime.now().strftime('%b %-d %Y')
    
    frontmatter = f"""---
title: '{title}'
description: ''
pubDate: '{today}'
---

"""
    return frontmatter

def add_frontmatter_to_file(source_path, dest_path):
    # Read original content
    with open(source_path, 'r') as file:
        content = file.read()
    
    # Generate frontmatter using filename as title
    filename = os.path.basename(source_path)
    frontmatter = generate_frontmatter(filename)
    
    # Write new content with frontmatter
    with open(dest_path, 'w') as file:
        file.write(frontmatter + content)

def copy_markdown_files():
    # Create published folder if it doesn't exist
    os.makedirs(PUBLISHED_FOLDER, exist_ok=True)
    
    md_files = [f for f in os.listdir(PUBLISH_FOLDER) if f.endswith('.md')]
    
    if not md_files:
        print("No Markdown files found in the publish folder.")
        return False, []
    
    copied_files = []
    for md_file in md_files:
        src = os.path.join(PUBLISH_FOLDER, md_file)
        dest = os.path.join(BLOG_POSTS_FOLDER, md_file)
        published_dest = os.path.join(PUBLISHED_FOLDER, md_file)
        
        # Add frontmatter and copy to blog repository
        add_frontmatter_to_file(src, dest)
        print(f"Copied '{md_file}' with frontmatter to the blog repository.")

        shutil.move(src, published_dest)
        print(f"Moved '{md_file}' to published folder.")
        copied_files.append(md_file)
    
    return True, copied_files

def commit_and_push_changes(files):
    os.chdir(BLOG_REPO_FOLDER)
    subprocess.run(['git', 'add', '.'])
    
    # Create commit message with file names
    commit_message = "Added blog post(s): " + ", ".join(files)
    subprocess.run(['git', 'commit', '-m', commit_message])
    print("Committed the changes to git.")
    
    subprocess.run(['git', 'push'])
    print("Pushed the changes to the remote repository.")

def main():
    success, copied_files = copy_markdown_files()
    
    if success:
        commit_and_push_changes(copied_files)
        print("Changes were committed and pushed to the remote repository.")
    else:
        print("No files were copied. Exiting.")

if __name__ == "__main__":
    main()
