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

"""Tests for CLI version helpers."""

import pytest

import semantiva.cli as cli


def test_parse_version_text_supports_assignment() -> None:
    text = "__version__ = '1.2.3'\n"
    assert cli._parse_version_text(text) == "1.2.3"


def test_parse_version_text_supports_raw_line() -> None:
    text = "0.4.0\n"
    assert cli._parse_version_text(text) == "0.4.0"


def test_get_version_falls_back_to_version_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_pkg_version(_: str) -> str:
        raise cli.PackageNotFoundError  # force fallback

    monkeypatch.setattr(cli, "pkg_version", fake_pkg_version)

    version = cli._get_version()
    assert isinstance(version, str)
    assert version != "unknown"
