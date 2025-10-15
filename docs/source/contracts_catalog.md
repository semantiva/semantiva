| Semantiva Validation Assertions (SVA) enumerate contract checks enforced by ``semantiva dev lint``. |
| Code | Severity | Applies To | Summary | Trigger | Hint |
|------|----------|------------|---------|---------|------|
| SVA001 | error | Any class defining input_data_type | input_data_type must be @classmethod | Method exists; inspect.getattr_static not classmethod | Add @classmethod and use cls |
| SVA002 | error | Any class defining output_data_type | output_data_type must be @classmethod | Method exists; inspect.getattr_static not classmethod | Add @classmethod and use cls |
| SVA003 | error | Any class defining *_data_type | *_data_type must be @classmethod | Name matches .*_data_type$ | Add @classmethod and use cls |
| SVA004 | error | Any class defining *_data_type | *_data_type returns a type | Return is non-type or call raises | Return a type (e.g., MyType) |
| SVA100 | error | All components | _define_metadata/get_metadata return dict | Returned value not dict or raised | Return dict |
| SVA101 | error | All components | Required metadata keys present | Missing any of class_name, docstring, component_type | Add missing keys |
| SVA102 | warn | All components | Docstring too long | len(docstring) > LIMIT | Shorten summary |
| SVA103 | error | All components (if parameters present) | parameters shape | Not in {dict, list, 'None', {}} | Normalize params |
| SVA104 | error | All components (if present) | injected_context_keys list[str] unique | Not list of unique strings | Fix list |
| SVA105 | error | All components (if present) | suppressed_context_keys list[str] unique | Not list of unique strings | Fix list |
| SVA106 | warn | All components (if both present) | Injected vs suppressed overlap | set(injected) ∩ set(suppressed) non-empty | Reconcile keys |
| SVA107 | error | All components | Registry/category coherence | Not present under its component_type in registry | Fix registration |
| SVA200 | error | DataSource / PayloadSource (component) | Require output_data_type | Metadata lacks output_data_type | Add method/meta |
| SVA201 | warn | DataSource / PayloadSource (component) | Forbid input_data_type | Metadata has input_data_type | Remove it |
| SVA210 | error | DataSink / PayloadSink (component) | Require input_data_type | Metadata lacks input_data_type | Add method/meta |
| SVA211 | warn | DataSink / PayloadSink (component) | Forbid output_data_type | Metadata has output_data_type | Remove it |
| SVA220 | error | DataOperation (component) | Require both input & output | One or both missing | Add both |
| SVA221 | error | DataOperation (component) | Parameters shape valid | Same validator as SVA103 | Fix params |
| SVA230 | error | DataProbe (component) | Require input_data_type | Missing input | Add method/meta |
| SVA231 | warn | DataProbe (component) | Discourage output_data_type | Has output | Remove it (node enforces pass-through) |
| SVA232 | error | DataProbe (component) | Parameters shape valid | Same validator as SVA103 | Fix params |
| SVA240 | info | ContextProcessor (component) | No IO req; classmethod rules still apply if present | — | — |
| SVA300 | error | DataSourceNode / PayloadSourceNode (node) | Node input is NoDataType | Node metadata input != NoDataType | Set to NoDataType |
| SVA301 | error | DataSourceNode / PayloadSourceNode (node) | Node out == processor out | If processor available, mismatch | Mirror processor |
| SVA310 | error | DataSinkNode / PayloadSinkNode (node) | Node input==output (pass-through) | Mismatch | Make equal |
| SVA311 | error | DataSinkNode / PayloadSinkNode (node) | Node I/O == processor input | If processor available, mismatch | Mirror processor |
| SVA320 | error | Probe Nodes (node) | Node input==output (pass-through) | Mismatch | Make equal |
| SVA321 | error | Probe Nodes (node) | Node I/O == processor input | If processor available, mismatch | Mirror processor |
