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

import ast
from typing import Callable, Any


class ExpressionError(Exception):
    """Error raised for invalid expressions in ParametricSweep."""


class _SafeVisitor(ast.NodeVisitor):
    _ALLOWED_NODES = {
        ast.Expression,
        ast.Module,
        ast.Expr,
        ast.Load,
        ast.BinOp,
        ast.UnaryOp,
        ast.BoolOp,
        ast.Compare,
        ast.IfExp,
        ast.Call,
        ast.Name,
        ast.Constant,
        ast.Tuple,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.And,
        ast.Or,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
    }
    _ALLOWED_FUNCS = {"abs", "min", "max", "round", "float", "int", "str", "bool"}

    def __init__(self, allowed_names: set[str]):
        self.allowed_names = allowed_names

    def visit_Name(self, node: ast.Name) -> Any:  # pragma: no cover - trivial
        if node.id not in self.allowed_names:
            raise ExpressionError(f"Unknown variable '{node.id}' in expression.")

    def visit_Call(self, node: ast.Call) -> Any:  # pragma: no cover - trivial
        if (
            not isinstance(node.func, ast.Name)
            or node.func.id not in self._ALLOWED_FUNCS
        ):
            raise ExpressionError("Only simple calls to abs/min/max/round are allowed.")
        for arg in node.args:
            self.visit(arg)

    def generic_visit(self, node: ast.AST) -> Any:  # pragma: no cover - trivial
        if type(node) not in self._ALLOWED_NODES:
            raise ExpressionError(f"Disallowed syntax: {type(node).__name__}")
        super().generic_visit(node)


class ExpressionEvaluator:
    """Compile small mathematical expressions in a safe manner."""

    def __init__(self, allowed_funcs: dict[str, Callable] | None = None):
        env: dict[str, Callable] = {
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
            "float": float,
            "int": int,
            "str": str,
            "bool": bool,
        }
        if allowed_funcs:
            env.update(allowed_funcs)
        self.env = env

    def compile(self, expr: str, allowed_names: set[str]) -> Callable[..., Any]:
        """Compile ``expr`` ensuring only ``allowed_names`` are referenced."""
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as exc:  # pragma: no cover - simple propagation
            raise ExpressionError(f"Invalid expression syntax: {exc.msg}") from exc
        _SafeVisitor(allowed_names).visit(tree)
        code = compile(tree, filename="<expr>", mode="eval")

        def _fn(**kwargs: Any) -> Any:
            return eval(code, self.env, kwargs)

        return _fn
