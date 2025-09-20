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

from queue import Empty

from semantiva.execution.job_queue.queue_orchestrator import QueueSemantivaOrchestrator
from semantiva.registry.bootstrap import RegistryProfile


class _DummyTransport:
    def connect(self):
        pass

    def close(self):
        pass

    def publish(self, *args, **kwargs):
        pass

    def subscribe(self, *args, **kwargs):
        class _DummySubscription:
            def __iter__(self):
                return iter(())

            def close(self):
                pass

        return _DummySubscription()


def test_enqueue_attaches_explicit_profile():
    orchestrator = QueueSemantivaOrchestrator(_DummyTransport())
    profile = RegistryProfile(
        load_defaults=True, modules=["x.y.z"], extensions=["demo"]
    )
    orchestrator.enqueue([{"processor": "delete:temp"}], registry_profile=profile)
    job_id, pipeline_cfg, data, context, profile_dict = (
        orchestrator.job_queue.get_nowait()
    )
    assert profile_dict == profile.as_dict()


def test_enqueue_attaches_current_profile_by_default():
    orchestrator = QueueSemantivaOrchestrator(_DummyTransport())
    orchestrator.enqueue([{"processor": "delete:temp"}])
    try:
        job = orchestrator.job_queue.get_nowait()
    except Empty:
        raise AssertionError("No job enqueued")
    assert job[-1] is not None
