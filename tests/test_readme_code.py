# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
