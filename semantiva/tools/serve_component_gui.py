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

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from rdflib import Graph, RDF, RDFS, OWL, Namespace

app = FastAPI()


def build_component_json(ttl_path: str) -> Dict[str, Any]:
    g = Graph()
    g.parse(ttl_path, format="turtle")
    SMTV = Namespace("http://semantiva.org/semantiva#")

    nodes: list[Dict[str, Any]] = []
    mapping: dict[Any, int] = {}
    for cls in g.subjects(RDF.type, OWL.Class):
        label = g.value(cls, RDFS.label) or str(cls).split("#")[-1]
        node_id = len(nodes)
        node = {
            "id": node_id,
            "label": str(label),
            "component_type": str(g.value(cls, SMTV.componentType) or ""),
            "docstring": str(g.value(cls, SMTV.docString) or ""),
            "input_type": str(g.value(cls, SMTV.inputDataType) or ""),
            "output_type": str(g.value(cls, SMTV.outputDataType) or ""),
            "parameters": str(g.value(cls, SMTV.inputParameters) or ""),
        }
        mapping[cls] = node_id
        nodes.append(node)

    edges: list[Dict[str, int]] = []
    for cls in g.subjects(RDF.type, OWL.Class):
        parent = g.value(cls, RDFS.subClassOf)
        if parent in mapping:
            edges.append({"source": mapping[parent], "target": mapping[cls]})

    return {"nodes": nodes, "edges": edges}


@app.get("/components")
def get_components() -> Dict[str, Any]:
    if not hasattr(app.state, "ttl_path"):
        raise HTTPException(status_code=404, detail="Ontology not loaded")
    return build_component_json(app.state.ttl_path)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(Path(__file__).parent / "web_gui" / "components.html")


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantiva Component GUI server")
    parser.add_argument("ttl", help="Path to ontology TTL file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    app.state.ttl_path = args.ttl

    static_dir = Path(__file__).parent / "web_gui"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
