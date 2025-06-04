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

import yaml
from typing import List, Dict


def load_pipeline_from_yaml(yaml_file: str) -> List[Dict]:
    """
    Loads a pipeline configuration from a YAML file.

    Args:
        yaml_file (str): Path to the YAML file.

    Returns:
        dict: Parsed pipeline configuration.
    """
    with open(yaml_file, "r", encoding="utf-8") as file:
        pipeline_config = yaml.safe_load(file)

    if "pipeline" not in pipeline_config or "nodes" not in pipeline_config["pipeline"]:
        raise ValueError(
            "Invalid pipeline configuration: Missing 'pipeline' or 'nodes' key."
        )

    return pipeline_config["pipeline"]["nodes"]
