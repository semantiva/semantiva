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

import argparse
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from semantiva import Pipeline, load_pipeline_from_yaml
from semantiva.tools.pipeline_inspector import PipelineInspector

app = FastAPI()


def build_pipeline_json(pipeline: Pipeline) -> dict:
    # Get parameter resolution information using PipelineInspector
    param_resolutions = PipelineInspector.get_node_parameter_resolutions(pipeline)

    # Create a lookup dictionary for parameter resolutions
    # Note: param_resolutions uses 0-indexed IDs, so we don't need to adjust them
    resolution_lookup = {
        item["id"]: item["parameter_resolution"] for item in param_resolutions
    }

    nodes = []
    edges = []
    for idx, node in enumerate(pipeline.nodes):
        meta = node.get_metadata()
        info = {
            "id": idx,
            "label": node.processor.__class__.__name__,
            "component_type": meta.get("component_type"),
            "input_type": (
                (typ := getattr(node, "input_data_type", lambda: None)())
                and typ.__name__
            ),
            "output_type": (
                (typ := getattr(node, "output_data_type", lambda: None)())
                and typ.__name__
            ),
            "docstring": (
                node.processor.__class__.__doc__.strip()
                if node.processor.__class__.__doc__
                else "No description available."
            ),
            "parameters": node.processor_config,
            "parameter_resolution": resolution_lookup.get(idx, {}),
            "created_keys": (
                node.get_created_keys() if hasattr(node, "get_created_keys") else []
            ),
            "required_keys": (
                node.get_required_keys() if hasattr(node, "get_required_keys") else []
            ),
            "suppressed_keys": (
                node.get_suppressed_keys()
                if hasattr(node, "get_suppressed_keys")
                else []
            ),
        }
        nodes.append(info)
        if idx < len(pipeline.nodes) - 1:
            edges.append({"source": idx, "target": idx + 1})
    return {"nodes": nodes, "edges": edges}


@app.get("/pipeline")
def get_pipeline():
    if not hasattr(app.state, "pipeline") or app.state.pipeline is None:
        raise HTTPException(
            status_code=404, detail="Pipeline not found. Please load a pipeline first."
        )
    return build_pipeline_json(app.state.pipeline)


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "web_gui" / "index.html")


@app.get("/debug")
def debug():
    return FileResponse(Path(__file__).parent / "web_gui" / "debug.html")


def main():
    parser = argparse.ArgumentParser(description="Semantiva Pipeline GUI server")
    parser.add_argument("yaml", help="Path to pipeline YAML")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # Load the pipeline
    config = load_pipeline_from_yaml(args.yaml)
    app.state.pipeline = Pipeline(config)

    # Print inspection information
    from semantiva.tools.pipeline_inspector import PipelineInspector

    print("Pipeline Inspector:", PipelineInspector.inspect_pipeline(app.state.pipeline))
    print("-" * 40)
    print(
        "Extended Pipeline Inspection:",
        PipelineInspector.inspect_pipeline_extended(app.state.pipeline),
    )

    static_dir = Path(__file__).parent / "web_gui"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
