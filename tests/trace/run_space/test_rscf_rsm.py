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

from dataclasses import asdict

from semantiva.trace.runtime import RunSpaceIdentityService
from semantiva.configurations.schema import RunBlock, RunSpaceV1Config


def _spec_with_blocks(blocks: list[RunBlock]) -> dict:
    cfg = RunSpaceV1Config(blocks=blocks)
    return asdict(cfg)


def test_rscf_v1_key_order_irrelevant():
    block_a = RunBlock(mode="by_position", context={"alpha": [1, 2], "beta": [3, 4]})
    spec1 = _spec_with_blocks([block_a])
    block_b = RunBlock(mode="by_position", context={"beta": [3, 4], "alpha": [1, 2]})
    spec2 = _spec_with_blocks([block_b])

    service = RunSpaceIdentityService()
    ids1 = service.compute(spec1)
    ids2 = service.compute(spec2)

    assert ids1.spec_id == ids2.spec_id
    assert ids1.inputs_id == ids2.inputs_id


def test_rsm_v1_changes_on_fingerprint_digest_change(tmp_path):
    data_file = tmp_path / "runs.csv"
    data_file.write_text("value\n1\n", encoding="utf-8")

    block = RunBlock(mode="by_position", context={"value": [1]}, source=None)
    # asdict omits None sources; build spec manually to include fingerprint metadata
    spec_dict = asdict(RunSpaceV1Config(blocks=[block]))
    spec_dict["blocks"][0]["source"] = {
        "format": "csv",
        "path": str(data_file),
        "select": None,
        "rename": {},
        "mode": "zip",
    }

    service = RunSpaceIdentityService()
    first = service.compute(spec_dict, base_dir=tmp_path)

    data_file.write_text("value\n2\n", encoding="utf-8")
    second = service.compute(spec_dict, base_dir=tmp_path)

    assert first.inputs_id != second.inputs_id
    assert first.fingerprints[0].digest_sha256 != second.fingerprints[0].digest_sha256
