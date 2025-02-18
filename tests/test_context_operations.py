import pytest
from typing import List
from semantiva.context_operations.context_operations import (
    ContextOperation,
    ModelFittingContextOperation,
)
from semantiva.context_operations.context_types import ContextType
from semantiva.logger import Logger
from semantiva.workflows.fitting_model import FittingModel


class MockFittingModel(FittingModel):
    def fit(self, independent_variable, dependent_variable):
        return {"fit_results": "mock_results"}


class MockContextOperation(ContextOperation):
    def _operate_context(self, context: ContextType) -> ContextType:
        context.set_value("operation_result", "success")
        return context

    def get_required_keys(self) -> List[str]:
        return ["required_key"]

    def get_created_keys(self) -> List[str]:
        return ["operation_result"]

    def get_suppressed_keys(self) -> List[str]:
        return []


def test_mock_context_operation():
    context = ContextType({"required_key": "value"})
    operation = MockContextOperation()
    result_context = operation.operate_context(context)
    assert result_context.get_value("operation_result") == "success"


def test_model_fitting_context_operation():
    context = ContextType({"independent_var": [1, 2, 3], "dependent_var": [4, 5, 6]})
    fitting_model = MockFittingModel()
    operation = ModelFittingContextOperation(
        logger=Logger(),
        fitting_model=fitting_model,
        independent_var_key="independent_var",
        dependent_var_key="dependent_var",
        context_keyword="fit_results",
    )
    result_context = operation.operate_context(context)
    assert result_context.get_value("fit_results") == {"fit_results": "mock_results"}

    with pytest.raises(ValueError):
        incomplete_context = ContextType({"independent_var": [1, 2, 3]})
        operation.operate_context(incomplete_context)


if __name__ == "__main__":
    pytest.main()
