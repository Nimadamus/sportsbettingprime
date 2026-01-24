"""
Fix sportsbettingprime.com references to sportsbettingprime.com
The www subdomain doesn't work, so all references should be non-www.
"""

import os
import re

REPO_PATH = r"C:\Users\Nima\sportsbettingprime"

def fix_www_references():
    fixed_files = 0
    total_replacements = 0

    for root, dirs, files in os.walk(REPO_PATH):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if not filename.endswith(('.html', '.py', '.js', '.json', '.xml')):
                continue

            filepath = os.path.join(root, filename)

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Count occurrences before
                count_before = content.count('sportsbettingprime.com')

                if count_before > 0:
                    # Replace www with non-www
                    new_content = content.replace('sportsbettingprime.com', 'sportsbettingprime.com')

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    fixed_files += 1
                    total_replacements += count_before
                    print(f"Fixed {count_before} references in: {os.path.basename(filepath)}")

            except Exception as e:
                print(f"Error processing {filepath}: {e}")

    print(f"\n=== SUMMARY ===")
    print(f"Files fixed: {fixed_files}")
    print(f"Total replacements: {total_replacements}")

if __name__ == '__main__':
    fix_www_references()
