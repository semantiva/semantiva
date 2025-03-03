"""
This script is a test that checks if the code snippets in the README.md file can be executed without errors.
"""

import os
import re


def test_readme_code_runs():
    # Construct the path to the README.md file (assumed to be in the repository root)
    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Extract all python code blocks from the README.md file
    code_blocks = re.findall(r"```python(.*?)```", readme_content, re.DOTALL)

    # Execute each code block in a fresh namespace
    for block in code_blocks:
        code = block.strip()
        if code:
            exec(compile(code, "<string>", "exec"), {})
