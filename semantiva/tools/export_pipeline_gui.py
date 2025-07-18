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
import json
from pathlib import Path

from semantiva import Pipeline, load_pipeline_from_yaml
from semantiva.tools.serve_pipeline_gui import build_pipeline_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a standalone HTML page visualizing a pipeline"
    )
    parser.add_argument("yaml", help="Path to pipeline YAML")
    parser.add_argument("output", help="Destination HTML file")
    args = parser.parse_args()

    config = load_pipeline_from_yaml(args.yaml)
    pipeline = Pipeline(config)
    data = build_pipeline_json(pipeline)

    template_path = Path(__file__).parent / "web_gui" / "index.html"
    html = template_path.read_text()

    injection = (
        "<script>\n"
        f"window.PIPELINE_DATA = {json.dumps(data)};\n"
        "window.fetch = ((orig) => (url, options) => {\n"
        "  if (url === '/pipeline') {\n"
        "    return Promise.resolve({ok: true, json: () => Promise.resolve(window.PIPELINE_DATA)});\n"
        "  }\n"
        "  return orig(url, options);\n"
        "})(window.fetch);\n"
        "</script>"
    )

    html = html.replace("<body>", f"<body>\n{injection}", 1)

    Path(args.output).write_text(html)
    print(f"Standalone GUI written to {args.output}")


if __name__ == "__main__":
    main()
