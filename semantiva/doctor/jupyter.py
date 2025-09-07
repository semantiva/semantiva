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
"""Jupyter magic for running Semantiva Doctor on classes in a notebook."""

from __future__ import annotations

from typing import Dict, List

from IPython.core.magic import needs_local_scope, register_line_magic

from semantiva.contracts.expectations import Diagnostic, validate_components


@register_line_magic
@needs_local_scope
def semantiva_doctor(line: str, local_ns=None):
    """Validate Semantiva component contracts in the current notebook.

    Parameters
    ----------
    line:
        Optional space-separated class names. If omitted, all classes in the
        cell's local namespace are validated.
    local_ns:
        Provided by IPython; mapping of local variables.
    """

    ns = local_ns or {}
    names = [n for n in line.split() if n.strip()]
    classes: List[type] = []
    if names:
        for n in names:
            obj = ns.get(n)
            if isinstance(obj, type):
                classes.append(obj)
    else:
        classes = [v for v in ns.values() if isinstance(v, type)]

    diags = validate_components(classes)
    by_comp: Dict[str, List[Diagnostic]] = {}
    for d in diags:
        by_comp.setdefault(d.component, []).append(d)

    for comp, ds in sorted(by_comp.items()):
        print(f"\n{comp}")
        for d in ds:
            loc = f"{d.location[0]}:{d.location[1]}" if d.location else "<unknown>"
            print(f"  {d.severity.upper()} {d.code} @ {loc}")
            print(f"    {d.message}")

    return None
