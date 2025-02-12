import yaml


def load_pipeline_from_yaml(yaml_file: str) -> dict:
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
