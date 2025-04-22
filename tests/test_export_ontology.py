import subprocess
import os
from pathlib import Path


def test_export_framework_ontology_script():
    """
    Test the ontology exporter script by mimicking a command-line call.
    """
    # Define the output file path
    output_file = "__test_ontology_exporter__.ttl"

    # Ensure the output file does not already exist
    if os.path.exists(output_file):
        os.remove(output_file)

    # Call the script using subprocess
    result = subprocess.run(
        [
            "python",
            "semantiva/tools/export_ontology.py",
            "-o",
            output_file,
            "-p",
            "semantiva",
        ],
        capture_output=True,
        text=True,
    )

    # Check that the script executed successfully
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"

    # Check that the output file was created
    assert os.path.exists(output_file), "Output file was not created."

    # Check that the output file is not empty
    assert Path(output_file).stat().st_size > 0, "Output file is empty."

    # Clean up the generated file
    os.remove(output_file)
