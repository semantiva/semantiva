# Semantiva CLI

The `semantiva` command executes Semantiva pipelines defined in YAML.

## Usage

```bash
semantiva run <pipeline.yaml> [--dry-run] [--validate] [--set k=v ...] [-v|--verbose] [-q|--quiet]
```

## Options

- `--dry-run`: build the pipeline graph without executing nodes.
- `--validate`: parse and validate configuration only.
- `--set key=value`: override configuration values using dotted paths. Can be used multiple times.
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
