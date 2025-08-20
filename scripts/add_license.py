#!/usr/bin/env python3
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

"""Utility to prepend Apache 2.0 license headers to project files,
and report a summary of changes."""

import os
from scripts import HEADER, HEADER_PATTERN, INCLUDE_DIRS, EXTENSIONS


def insert_header(filepath: str) -> bool:
    """Insert license header if missing.
    Returns True if the file was modified."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if HEADER_PATTERN.search(content):
        print(f"✅ Already has header: {filepath}")
        return False

    print(f"⚙️  Adding header: {filepath}")
    header = HEADER.strip() + "\n"
    new_content = header + ("\n" + content if content else "")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def main() -> None:
    changed_files = []

    for dirpath in INCLUDE_DIRS:
        for root, _, files in os.walk(dirpath):
            for filename in files:
                if any(filename.endswith(ext) for ext in EXTENSIONS):
                    fullpath = os.path.join(root, filename)
                    if insert_header(fullpath):
                        changed_files.append(fullpath)

    print("\n✅ Done inserting headers.")
    print(f"Total files updated: {len(changed_files)}")
    if changed_files:
        print("List of changed files:")
        for path in changed_files:
            print(f" - {path}")


if __name__ == "__main__":
    main()
