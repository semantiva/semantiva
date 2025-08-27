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

import re
import sys
import pathlib
import importlib

RST_DIR = pathlib.Path(__file__).resolve().parents[1] / "source"
PROC_RE = re.compile(r"^[ \t]*processor:\s*([A-Za-z0-9_\.]+)\s*$", re.M)


def iter_rst():
    for p in RST_DIR.rglob("*.rst"):
        yield p, p.read_text(encoding="utf-8")


def extract_processors(text):
    procs = []
    for block in re.findall(r"\.\. code-block:: yaml\n\n((?:[ \t].*\n)+)", text):
        procs += PROC_RE.findall(block)
    return procs


def try_import(fqcn):
    if "." not in fqcn:
        return True  # probably a registry short name; ignore
    mod, _, cls = fqcn.rpartition(".")
    try:
        m = importlib.import_module(mod)
        getattr(m, cls)
        return True
    except Exception:
        return False


def main():
    failed = []
    for path, text in iter_rst():
        for fqcn in extract_processors(text):
            if not try_import(fqcn):
                failed.append((str(path), fqcn))
    if failed:
        print("FAILED imports:")
        for path, fqcn in failed:
            print(f" - {path}: {fqcn}")
        sys.exit(1)
    print("OK: YAML processor imports")


if __name__ == "__main__":
    main()
