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

from scripts.add_license import insert_header, HEADER
from scripts.check_license_headers import has_header


def test_insert_header_no_extra_blank_line(tmp_path):
    file_path = tmp_path / "__init__.py"
    file_path.write_text("")
    insert_header(str(file_path))
    assert file_path.read_text() == HEADER.strip() + "\n"


def test_check_file_has_header(tmp_path):
    good = tmp_path / "good.py"
    good.write_text(HEADER.strip() + "\n")
    bad = tmp_path / "bad.py"
    bad.write_text("print('hi')\n")
    assert has_header(str(good))
    assert not has_header(str(bad))
