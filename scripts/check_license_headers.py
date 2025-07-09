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

"""Verify that all project files contain the license header and summarize failures."""

import os
import sys

from scripts import HEADER_PATTERN, INCLUDE_DIRS, EXTENSIONS


def has_header(filepath: str) -> bool:
    with open(filepath, "r", encoding="utf-8") as f:
        return bool(HEADER_PATTERN.search(f.read()))


def main() -> None:
    missing_files = []

    for dirpath in INCLUDE_DIRS:
        for root, _, files in os.walk(dirpath):
            for filename in files:
                if any(filename.endswith(ext) for ext in EXTENSIONS):
                    fullpath = os.path.join(root, filename)
                    if not has_header(fullpath):
                        print(f"❌ Missing header: {fullpath}")
                        missing_files.append(fullpath)
                    else:
                        print(f"✅ Header found: {fullpath}")

    print("\n✅ License check complete.")
    print(f"Total files missing header: {len(missing_files)}")
    if missing_files:
        print("List of files without header:")
        for path in missing_files:
            print(f" - {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
