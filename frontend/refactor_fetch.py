import os
import re
import glob

PAGES_DIR = r"c:\Users\ADMIN\Desktop\GrapeHRM\frontend\src\pages"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Replace useAuth destructing
    content = re.sub(r'getAuthHeaders', 'authFetch', content)

    # 2. Replace simple fetch(url, { headers: authFetch() })
    content = re.sub(r"fetch\(([^,]+),\s*\{\s*headers:\s*authFetch\(\)\s*\}\)", r"authFetch(\1)", content)

    # 3. Replace fetch with options where headers: authFetch() is present.
    # Note: re.sub with a function
    def replacer(match):
        url = match.group(1)
        options = match.group(2)
        
        # Only modify if authFetch() is in the options
        if 'authFetch()' not in options:
            return match.group(0)
            
        # remove headers: authFetch()
        options = re.sub(r',\s*headers:\s*authFetch\(\)', '', options)
        options = re.sub(r'headers:\s*authFetch\(\)\s*,?\s*', '', options)
        
        # if options is just `{ }` or `{}`
        if options.strip() == '{}':
            return f"authFetch({url})"
        return f"authFetch({url}, {options})"

    # Match fetch(url, { ... }) where { ... } doesn't contain another fetch call ideally
    # We use a non-greedy match for the options block.
    # This might fail on nested brackets, but let's assume it's simple like { method: 'POST', body: ... }
    content = re.sub(r"fetch\(([^,]+),\s*(\{.*?\})\)", replacer, content, flags=re.DOTALL)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")

for filepath in glob.glob(os.path.join(PAGES_DIR, "*.jsx")):
    if os.path.basename(filepath) == "LoginPage.jsx":
        continue
    process_file(filepath)
