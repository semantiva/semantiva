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

"""
Unit tests for SequentialSemantivaExecutor, the default synchronous executor
in Semantiva's processing runtime. This executor runs each task immediately
in the calling thread and returns a completed Future, enabling uniform
handling of both sync and async executors in the orchestration code.

Key behaviors under test:
  - submit(fn, *args, **kwargs) returns a Future whose result() yields fn's return value.
  - Exceptions raised by fn propagate out of submit() immediately, since execution is synchronous.
"""

import pytest
from semantiva.execution.executor import SequentialSemantivaExecutor
from concurrent.futures import Future


def test_submit_returns_future_and_result():
    """
    Verify that submit() returns a Future and that Future.result()
    contains the correct return value of the provided function.
    """
    executor = SequentialSemantivaExecutor()

    # Submit a simple addition lambda
    fut = executor.submit(lambda a, b: a + b, 2, 3)

    # The returned object must be a Future
    assert isinstance(fut, Future)

    # Since execution is immediate, result() should be available and equal to 5
    assert fut.result() == 5


def test_submit_captures_exceptions():
    """
    Verify that exceptions raised by the submitted function propagate
    immediately from submit(), because SequentialSemantivaExecutor executes
    synchronously rather than deferring into a worker thread.
    """
    executor = SequentialSemantivaExecutor()

    def explode():
        raise RuntimeError("boom")

    # Because submit() calls fn() directly, a RuntimeError should be thrown here
    with pytest.raises(RuntimeError):
        executor.submit(explode)
