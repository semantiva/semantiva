# Semantiva CLI

The `semantiva` command executes or inspects Semantiva pipelines defined in YAML.

## Usage

```bash
semantiva inspect <pipeline.yaml> [--extended] [-v|--verbose] [-q|--quiet]
semantiva run <pipeline.yaml> [--dry-run] [--validate] [--set k=v ...] [--context k=v ...] [-v|--verbose] [-q|--quiet]
```

## Inspecting a pipeline

- `semantiva inspect pipeline.yaml` prints a human-readable summary.
- `semantiva inspect --extended pipeline.yaml` includes detailed type and parameter information.

If a future `--json` flag is provided alongside `--extended`, JSON output takes precedence.

## Running a pipeline

- `--dry-run`: build the pipeline graph without executing nodes.
- `--validate`: parse and validate configuration only.
- `--set key=value`: override configuration values using dotted paths. Can be used multiple times.
- `--context key=value`: inject context key–value pairs at runtime. May be supplied multiple times; later flags override earlier ones.
- `-v`, `--verbose`: enable debug logging.
- `-q`, `--quiet`: show errors only.

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | success |
| 1 | CLI argument error |
| 2 | file not found |
| 3 | configuration or validation error |
| 4 | runtime execution error |
| 5 | keyboard interrupt |

## Examples

```bash
semantiva run semantiva/examples/simple_pipeline.yaml
semantiva run semantiva/examples/simple_pipeline.yaml --dry-run
python semantiva/semantiva.py run semantiva/examples/simple_pipeline.yaml
```
