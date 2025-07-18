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

import pytest
from fastapi.testclient import TestClient

from semantiva.tools.serve_component_gui import app, build_component_json
from semantiva.examples.export_ontology import _export_framework_ontology


@pytest.fixture(scope="session")
def ontology_file(tmp_path_factory):
    path = tmp_path_factory.mktemp("ontology") / "components.ttl"
    _export_framework_ontology(str(path), ["semantiva"])
    return path


@pytest.fixture
def test_client(ontology_file):
    app.state.ttl_path = str(ontology_file)
    return TestClient(app)


def test_build_component_json(ontology_file):
    data = build_component_json(str(ontology_file))
    assert "nodes" in data and "edges" in data
    assert len(data["nodes"]) > 0


def test_get_components_endpoint(test_client):
    resp = test_client.get("/components")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data


def test_index_endpoint(test_client):
    response = test_client.get("/")
    assert response.status_code in (200, 404)
