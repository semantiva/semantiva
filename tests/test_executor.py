import pytest
from semantiva.execution_tools.executor import SequentialSemantivaExecutor
from concurrent.futures import Future


def test_submit_returns_future_and_result():
    executor = SequentialSemantivaExecutor()
    # Simple add
    fut = executor.submit(lambda a, b: a + b, 2, 3)
    # Should be a Future
    assert isinstance(fut, Future)
    # result() should return 5
    assert fut.result() == 5


def test_submit_captures_exceptions():
    executor = SequentialSemantivaExecutor()

    def explode():
        raise RuntimeError("boom")

    # Because SequentialSemantivaExecutor.submit calls fn synchronously,
    # exceptions propagate immediately (i.e. submit() itself raises).
    with pytest.raises(RuntimeError):
        executor.submit(explode)
