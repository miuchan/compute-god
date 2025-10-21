"""Computable function limit language implementation."""

from __future__ import annotations

import ast
import math
import operator
import re
from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, Mapping, Sequence, Tuple

__all__ = [
    "ComputableFunction",
    "DomainSpec",
    "LimitApproach",
    "LimitProgram",
    "LimitResult",
    "LimitStatement",
    "parse_limit_language",
]


# ---------------------------------------------------------------------------
# Data structures representing the DSL
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LimitApproach:
    """Description of how a variable approaches a limit."""

    kind: str
    value: float | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"value", "infinity", "-infinity"}:
            raise ValueError(f"Unsupported limit approach kind: {self.kind!r}")
        if self.kind == "value" and self.value is None:
            raise ValueError("Finite approaches require an explicit value")
        if self.kind != "value" and self.value is not None:
            raise ValueError("Infinite approaches cannot specify a value")

    @property
    def is_infinite(self) -> bool:
        return self.kind in {"infinity", "-infinity"}


@dataclass(frozen=True)
class DomainSpec:
    """Domain over which uniform convergence must hold."""

    variable: str
    lower: float
    upper: float
    samples: int = 5

    def __post_init__(self) -> None:
        if self.samples <= 0:
            raise ValueError("Domain sample count must be positive")
        if not math.isfinite(self.lower) or not math.isfinite(self.upper):
            raise ValueError("Domain bounds must be finite numbers")

    def sample_points(self) -> Tuple[float, ...]:
        if self.samples == 1 or math.isclose(self.lower, self.upper):
            return (self.lower,)
        step = (self.upper - self.lower) / (self.samples - 1)
        return tuple(self.lower + step * index for index in range(self.samples))

    def with_samples(self, samples: int) -> "DomainSpec":
        if samples <= 0:
            raise ValueError("Domain sample count must be positive")
        return replace(self, samples=samples)


@dataclass(frozen=True)
class ComputableFunction:
    """Function definition used by the limit language."""

    name: str
    parameters: Tuple[str, ...]
    expression: str
    line: int | None = None
    _ast: ast.AST = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if len(set(self.parameters)) != len(self.parameters):
            raise ValueError(f"Function '{self.name}' has duplicate parameters")
        object.__setattr__(self, "_ast", ast.parse(self.expression, mode="eval").body)


@dataclass(frozen=True)
class LimitStatement:
    """Limit statement to be verified."""

    variable: str
    approach: LimitApproach
    function: str
    argument_expressions: Tuple[str, ...]
    target_expression: str
    mode: str = "pointwise"
    domain: DomainSpec | None = None
    tolerance: float = 1e-6
    max_steps: int = 32
    line: int | None = None
    _target_ast: ast.AST = field(init=False, repr=False)
    _argument_ast: Tuple[ast.AST, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.mode not in {"pointwise", "uniform"}:
            raise ValueError(f"Unsupported convergence mode: {self.mode!r}")
        if self.tolerance <= 0:
            raise ValueError("Tolerance must be positive")
        if self.max_steps <= 0:
            raise ValueError("Iteration budget must be positive")
        object.__setattr__(self, "_target_ast", ast.parse(self.target_expression, mode="eval").body)
        object.__setattr__(
            self,
            "_argument_ast",
            tuple(ast.parse(expr, mode="eval").body for expr in self.argument_expressions),
        )

    @property
    def samples(self) -> int:
        return self.domain.samples if self.domain else 1


@dataclass(frozen=True)
class LimitResult:
    """Result returned when verifying a limit statement."""

    statement: LimitStatement
    converged: bool
    max_error: float
    steps_used: int
    samples_evaluated: int


# ---------------------------------------------------------------------------
# Expression evaluation helpers
# ---------------------------------------------------------------------------


_ALLOWED_FUNCTIONS: Dict[str, object] = {
    "abs": abs,
    "max": max,
    "min": min,
    "pow": pow,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "exp": math.exp,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "sqrt": math.sqrt,
    "floor": math.floor,
    "ceil": math.ceil,
    "erf": math.erf,
    "erfc": math.erfc,
    "gamma": math.gamma,
    "lgamma": math.lgamma,
    "hypot": math.hypot,
}

_ALLOWED_CONSTANTS: Dict[str, float | bool | None] = {
    "pi": math.pi,
    "tau": math.tau,
    "e": math.e,
    "inf": math.inf,
    "infinity": math.inf,
    "nan": math.nan,
    "true": True,
    "false": False,
    "none": None,
}

_BINARY_OPERATORS: Dict[type[ast.AST], object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS: Dict[type[ast.AST], object] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}


class _MathModuleProxy:
    """Restricted proxy for :mod:`math` exposed to expressions."""

    __slots__ = ()

    def __getattr__(self, name: str) -> object:
        func = _ALLOWED_FUNCTIONS.get(name)
        if func is None:
            raise AttributeError(name)
        return func


class _FunctionProxy:
    __slots__ = ("_evaluator", "_function")

    def __init__(self, evaluator: "_ExpressionEvaluator", function: ComputableFunction) -> None:
        self._evaluator = evaluator
        self._function = function

    def __call__(self, *args: float) -> float:
        return self._evaluator.call_function(self._function, args)


class _ExpressionEvaluator(ast.NodeVisitor):
    """Safe evaluator for arithmetic expressions."""

    __slots__ = ("program", "variables", "call_stack")

    def __init__(
        self,
        program: "LimitProgram",
        variables: Mapping[str, float | bool | None],
        call_stack: Tuple[str, ...] = (),
    ) -> None:
        self.program = program
        self.variables = dict(variables)
        self.call_stack = call_stack

    # Public helpers -----------------------------------------------------
    def evaluate(self, node: ast.AST) -> float | bool | None:
        return self.visit(node)

    def with_variables(self, extra: Mapping[str, float | bool | None]) -> "_ExpressionEvaluator":
        merged = dict(self.variables)
        merged.update(extra)
        return _ExpressionEvaluator(self.program, merged, self.call_stack)

    def call_function(self, function: ComputableFunction, args: Sequence[float]) -> float:
        if len(args) != len(function.parameters):
            raise ValueError(
                f"Function '{function.name}' expects {len(function.parameters)} arguments, "
                f"received {len(args)}"
            )
        if function.name in self.call_stack:
            raise ValueError("Recursive function definitions are not supported")
        merged = dict(self.variables)
        merged.update(zip(function.parameters, args))
        evaluator = _ExpressionEvaluator(
            self.program,
            merged,
            self.call_stack + (function.name,),
        )
        result = evaluator.evaluate(function._ast)
        if isinstance(result, bool):
            return float(result)
        if isinstance(result, (int, float)):
            return float(result)
        raise TypeError(f"Function '{function.name}' must return a numeric value")

    # Node visitors -------------------------------------------------------
    def visit_Constant(self, node: ast.Constant) -> float | bool | None:
        if isinstance(node.value, (int, float, bool)) or node.value is None:
            return node.value
        raise TypeError(f"Unsupported constant {node.value!r}")

    def visit_Name(self, node: ast.Name) -> float | bool | None | object:
        identifier = node.id
        if identifier in self.variables:
            return self.variables[identifier]
        lowered = identifier.lower()
        if lowered in _ALLOWED_CONSTANTS:
            return _ALLOWED_CONSTANTS[lowered]
        if lowered == "math":
            return _MathModuleProxy()
        function = self.program.functions.get(identifier)
        if function is not None:
            return _FunctionProxy(self, function)
        func = _ALLOWED_FUNCTIONS.get(lowered)
        if func is not None:
            return func
        raise NameError(f"Unknown identifier '{identifier}' in expression")

    def visit_BinOp(self, node: ast.BinOp) -> float | bool:
        operator_fn = _BINARY_OPERATORS.get(type(node.op))
        if operator_fn is None:
            raise TypeError(f"Unsupported binary operator {ast.dump(node.op)}")
        left = self.visit(node.left)
        right = self.visit(node.right)
        return operator_fn(left, right)  # type: ignore[arg-type]

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float | bool:
        operator_fn = _UNARY_OPERATORS.get(type(node.op))
        if operator_fn is None:
            raise TypeError(f"Unsupported unary operator {ast.dump(node.op)}")
        operand = self.visit(node.operand)
        return operator_fn(operand)  # type: ignore[arg-type]

    def visit_BoolOp(self, node: ast.BoolOp) -> bool:
        values = [self.visit(value) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise TypeError("Unsupported boolean operator")

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for operator_node, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            if not self._compare(operator_node, left, right):
                return False
            left = right
        return True

    def _compare(self, operator_node: ast.cmpop, left: object, right: object) -> bool:
        if isinstance(operator_node, ast.Lt):
            return left < right  # type: ignore[operator]
        if isinstance(operator_node, ast.LtE):
            return left <= right  # type: ignore[operator]
        if isinstance(operator_node, ast.Gt):
            return left > right  # type: ignore[operator]
        if isinstance(operator_node, ast.GtE):
            return left >= right  # type: ignore[operator]
        if isinstance(operator_node, ast.Eq):
            return left == right
        if isinstance(operator_node, ast.NotEq):
            return left != right
        raise TypeError(f"Unsupported comparison operator {ast.dump(operator_node)}")

    def visit_Call(self, node: ast.Call) -> float | bool | None:
        if node.keywords:
            raise TypeError("Keyword arguments are not supported")
        func = self.visit(node.func)
        args = [self.visit(arg) for arg in node.args]
        if callable(func):
            return func(*args)
        raise TypeError("Attempted to call a non-callable object")

    def visit_IfExp(self, node: ast.IfExp) -> float | bool | None:
        condition = self.visit(node.test)
        branch = node.body if condition else node.orelse
        return self.visit(branch)

    def visit_Tuple(self, node: ast.Tuple) -> Tuple[object, ...]:
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_List(self, node: ast.List) -> Tuple[object, ...]:
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_Attribute(self, node: ast.Attribute) -> object:
        base = self.visit(node.value)
        if isinstance(base, _MathModuleProxy):
            return getattr(base, node.attr)
        raise TypeError("Only math.* attributes are allowed")

    def generic_visit(self, node: ast.AST):  # type: ignore[override]
        raise TypeError(f"Unsupported expression node: {ast.dump(node)}")


# ---------------------------------------------------------------------------
# Parsing utilities
# ---------------------------------------------------------------------------


_FUNCTION_RE = re.compile(
    r"^(?:function|函数)\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*=\s*(.+)$"
)

_LIMIT_RE = re.compile(
    r"^(?:limit|极限)\s+([A-Za-z_][\w]*)\s*(?:->|→)\s*([^\s]+)\s+(?:of|的)\s+"
    r"([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*=\s*(.+)$"
)

_OPTION_TRIGGER_RE = re.compile(
    r"\b(" "uniform|uniformly|pointwise|mode|domain|samples|steps|tolerance|" "一致|逐点|模式|范围|域|采样|步数|容差" ")\b"
)


def parse_limit_language(source: Iterable[str] | str) -> "LimitProgram":
    """Parse *source* into a :class:`LimitProgram`."""

    lines = source.splitlines() if isinstance(source, str) else list(source)
    functions: Dict[str, ComputableFunction] = {}
    statements: list[LimitStatement] = []

    for line_no, raw_line in enumerate(lines, start=1):
        stripped = raw_line.split("#", 1)[0].strip()
        if not stripped:
            continue

        function_match = _FUNCTION_RE.match(stripped)
        if function_match:
            name, params_text, expression = function_match.groups()
            parameters = _parse_parameters(params_text)
            if name in functions:
                raise ValueError(f"Function '{name}' defined multiple times (line {line_no})")
            functions[name] = ComputableFunction(name, parameters, expression, line=line_no)
            continue

        limit_match = _LIMIT_RE.match(stripped)
        if limit_match:
            variable, approach_text, function_name, args_text, remainder = limit_match.groups()
            function = functions.get(function_name)
            if function is None:
                raise ValueError(
                    f"Limit on line {line_no} references unknown function '{function_name}'"
                )
            argument_expressions = _parse_arguments(args_text)
            if len(argument_expressions) != len(function.parameters):
                raise ValueError(
                    f"Limit on line {line_no} provides {len(argument_expressions)} arguments "
                    f"for function '{function_name}' which expects {len(function.parameters)}"
                )
            target_text, option_texts = _split_options(remainder)
            approach = _parse_approach(approach_text)
            mode, domain, tolerance, steps = _parse_options(
                option_texts,
                argument_expressions,
                variable,
            )
            statements.append(
                LimitStatement(
                    variable=variable,
                    approach=approach,
                    function=function_name,
                    argument_expressions=argument_expressions,
                    target_expression=target_text,
                    mode=mode,
                    domain=domain,
                    tolerance=tolerance,
                    max_steps=steps,
                    line=line_no,
                )
            )
            continue

        raise ValueError(f"Unrecognised statement on line {line_no}: {raw_line}")

    return LimitProgram(functions=functions, limits=tuple(statements))


def _parse_parameters(params_text: str) -> Tuple[str, ...]:
    params = []
    for token in (part.strip() for part in params_text.split(",")):
        if not token:
            continue
        params.append(token)
    return tuple(params)


def _parse_arguments(args_text: str) -> Tuple[str, ...]:
    if not args_text.strip():
        return ()
    return tuple(part.strip() for part in args_text.split(","))


def _split_options(text: str) -> Tuple[str, list[str]]:
    parts: list[str] = []
    buffer: list[str] = []
    depth = 0
    for char in text:
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        if char == ";" and depth == 0:
            parts.append("".join(buffer).strip())
            buffer = []
            continue
        buffer.append(char)
    if buffer:
        parts.append("".join(buffer).strip())

    if not parts:
        raise ValueError("Limit statement must include a target expression")

    target = parts[0]
    options = [part for part in parts[1:] if part]

    match = _OPTION_TRIGGER_RE.search(target)
    if match:
        option_text = target[match.start() :].strip()
        target = target[: match.start()].strip()
        if option_text:
            options.insert(0, option_text)

    if not target:
        raise ValueError("Limit statement target expression cannot be empty")

    return target, options


def _parse_approach(text: str) -> LimitApproach:
    lowered = text.strip().lower()
    if lowered in {"inf", "infinity", "+inf", "+infinity", "∞"}:
        return LimitApproach("infinity")
    if lowered in {"-inf", "-infinity", "-∞"}:
        return LimitApproach("-infinity")
    value = _parse_scalar_expression(text.strip())
    return LimitApproach("value", value=value)


def _parse_options(
    options: Sequence[str],
    argument_expressions: Tuple[str, ...],
    limit_variable: str,
) -> Tuple[str, DomainSpec | None, float, int]:
    mode = "pointwise"
    tolerance = 1e-6
    steps = 32
    domain: DomainSpec | None = None
    pending_samples: int | None = None
    default_domain_var = _infer_default_domain_variable(argument_expressions, limit_variable)

    for raw_option in options:
        option = _normalize_option(raw_option)
        lowered = option.lower()

        if lowered in {"uniform", "uniformly"}:
            mode = "uniform"
            continue
        if lowered.startswith("uniform"):
            mode = "uniform"
            tail = option[len("uniform"):].strip()
            if tail.startswith("ly"):
                tail = tail[2:].strip()
            if tail.startswith("on"):
                tail = tail[len("on"):].strip()
            if tail:
                domain = _parse_domain(tail, default_domain_var, pending_samples)
                pending_samples = None
            continue
        if lowered in {"pointwise"}:
            mode = "pointwise"
            continue
        if lowered.startswith("mode="):
            value = option[5:].strip().lower()
            if value in {"uniform"}:
                mode = "uniform"
            elif value in {"pointwise"}:
                mode = "pointwise"
            else:
                raise ValueError(f"Unknown convergence mode '{value}'")
            continue
        if lowered.startswith("domain="):
            domain = _parse_domain(option[7:].strip(), default_domain_var, pending_samples)
            pending_samples = None
            continue
        if lowered.startswith("samples="):
            pending_samples = int(float(option[8:].strip()))
            if domain is not None:
                domain = domain.with_samples(pending_samples)
                pending_samples = None
            continue
        if lowered.startswith("steps="):
            steps = int(float(option[6:].strip()))
            continue
        if lowered.startswith("tolerance="):
            tolerance = float(option[10:].strip())
            continue

        raise ValueError(f"Unrecognised option '{raw_option}' in limit statement")

    if domain is not None and pending_samples is not None:
        domain = domain.with_samples(pending_samples)

    return mode, domain, tolerance, steps


def _normalize_option(option: str) -> str:
    replacements = {
        "一致收敛": "uniform",
        "一致": "uniform",
        "逐点": "pointwise",
        "模式": "mode",
        "方式": "mode",
        "域": "domain",
        "范围": "domain",
        "采样": "samples",
        "样本": "samples",
        "步数": "steps",
        "迭代": "steps",
        "容差": "tolerance",
        "误差": "tolerance",
    }
    normalised = option.strip()
    for source, target in replacements.items():
        normalised = normalised.replace(source, target)
    return normalised


def _infer_default_domain_variable(
    argument_expressions: Tuple[str, ...], limit_variable: str
) -> str | None:
    for expr in argument_expressions:
        candidate = expr.strip()
        if candidate.isidentifier() and candidate != limit_variable:
            return candidate
    return None


_DOMAIN_RE = re.compile(
    r"^(?:([A-Za-z_][\w]*)\s*[:=])?\s*(?:([A-Za-z_][\w]*)\s*(?:in|∈)\s*)?" r"\[([^,]+),\s*([^\]]+)\]$"
)


def _parse_domain(text: str, default_var: str | None, pending_samples: int | None) -> DomainSpec:
    match = _DOMAIN_RE.match(text.strip())
    if not match:
        if default_var is None:
            raise ValueError(f"Domain specification '{text}' is not understood")
        interval = text.strip()
        bounds = _parse_interval(interval)
        samples = pending_samples if pending_samples is not None else 5
        return DomainSpec(variable=default_var, lower=bounds[0], upper=bounds[1], samples=samples)

    prefix, named_var, lower_text, upper_text = match.groups()
    variable = prefix or named_var or default_var
    if variable is None:
        raise ValueError("Domain specification must provide a variable name")
    lower_value = _parse_scalar_expression(lower_text.strip())
    upper_value = _parse_scalar_expression(upper_text.strip())
    samples = pending_samples if pending_samples is not None else 5
    return DomainSpec(variable=variable, lower=lower_value, upper=upper_value, samples=samples)


def _parse_interval(text: str) -> Tuple[float, float]:
    stripped = text.strip()
    if not stripped.startswith("[") or not stripped.endswith("]"):
        raise ValueError(f"Unsupported interval format: {text}")
    content = stripped[1:-1]
    lower_text, _, upper_text = content.partition(",")
    if not upper_text:
        raise ValueError(f"Unsupported interval format: {text}")
    lower = _parse_scalar_expression(lower_text.strip())
    upper = _parse_scalar_expression(upper_text.strip())
    return lower, upper


def _parse_scalar_expression(text: str) -> float:
    lowered = text.lower()
    if lowered in {"inf", "+inf", "infinity", "+infinity", "∞"}:
        return math.inf
    if lowered in {"-inf", "-infinity", "-∞"}:
        return -math.inf
    tree = ast.parse(text, mode="eval")
    return float(_ScalarEvaluator().visit(tree.body))


class _ScalarEvaluator(ast.NodeVisitor):
    """Restricted evaluator for scalar expressions used in options."""

    def visit_Constant(self, node: ast.Constant) -> float:
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise TypeError("Only numeric constants are allowed in scalar expressions")

    def visit_Name(self, node: ast.Name) -> float:
        lowered = node.id.lower()
        if lowered in _ALLOWED_CONSTANTS and isinstance(_ALLOWED_CONSTANTS[lowered], (int, float)):
            return float(_ALLOWED_CONSTANTS[lowered])
        raise NameError(f"Unknown name '{node.id}' in scalar expression")

    def visit_BinOp(self, node: ast.BinOp) -> float:
        operator_fn = _BINARY_OPERATORS.get(type(node.op))
        if operator_fn is None:
            raise TypeError("Unsupported operator in scalar expression")
        left = self.visit(node.left)
        right = self.visit(node.right)
        return float(operator_fn(left, right))

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        operator_fn = _UNARY_OPERATORS.get(type(node.op))
        if operator_fn is None:
            raise TypeError("Unsupported unary operator in scalar expression")
        operand = self.visit(node.operand)
        return float(operator_fn(operand))

    def visit_Call(self, node: ast.Call) -> float:
        if node.keywords:
            raise TypeError("Scalar expressions do not support keyword arguments")
        func_name = getattr(node.func, "id", None)
        if func_name is None:
            raise TypeError("Only simple function calls are supported in scalar expressions")
        func = _ALLOWED_FUNCTIONS.get(func_name.lower())
        if func is None:
            raise NameError(f"Unknown function '{func_name}' in scalar expression")
        args = [self.visit(arg) for arg in node.args]
        return float(func(*args))

    def generic_visit(self, node: ast.AST):  # type: ignore[override]
        raise TypeError(f"Unsupported scalar expression component: {ast.dump(node)}")


# ---------------------------------------------------------------------------
# Program execution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LimitProgram:
    """Collection of computable functions and limit statements."""

    functions: Dict[str, ComputableFunction]
    limits: Tuple[LimitStatement, ...]

    def evaluate_function(self, name: str, **variables: float) -> float:
        function = self.functions[name]
        missing = [param for param in function.parameters if param not in variables]
        if missing:
            raise ValueError(
                f"Missing values for parameters {', '.join(missing)} when calling '{name}'"
            )
        evaluator = _ExpressionEvaluator(self, variables)
        return evaluator.call_function(function, [variables[param] for param in function.parameters])

    def verify(self, *, tolerance: float | None = None, max_steps: int | None = None) -> Tuple[LimitResult, ...]:
        results = []
        for statement in self.limits:
            local_tolerance = tolerance if tolerance is not None else statement.tolerance
            local_steps = max_steps if max_steps is not None else statement.max_steps
            results.append(self._verify_statement(statement, local_tolerance, local_steps))
        return tuple(results)

    # Internal helpers -------------------------------------------------
    def _verify_statement(
        self, statement: LimitStatement, tolerance: float, steps: int
    ) -> LimitResult:
        step_values = self._approach_steps(statement.approach, steps)
        if not step_values:
            return LimitResult(statement, False, math.inf, 0, 0)

        domain_contexts, target_values = self._prepare_domain(statement)
        samples = len(domain_contexts)

        if statement.mode == "uniform":
            best_error = math.inf
            for index, values in enumerate(step_values, start=1):
                step_error = 0.0
                for domain_index, base_context in enumerate(domain_contexts):
                    evaluator = _ExpressionEvaluator(self, base_context)
                    for var_value in values:
                        eval_with_var = evaluator.with_variables({statement.variable: var_value})
                        value = self._evaluate_function_call(
                            statement,
                            eval_with_var,
                        )
                        error = abs(value - target_values[domain_index])
                        step_error = max(step_error, error)
                best_error = min(best_error, step_error)
                if step_error <= tolerance:
                    return LimitResult(statement, True, step_error, index, samples)
            return LimitResult(statement, False, best_error, len(step_values), samples)

        # Pointwise convergence
        max_error = 0.0
        max_step = 0
        for base_context, target in zip(domain_contexts, target_values, strict=True):
            evaluator = _ExpressionEvaluator(self, base_context)
            satisfied_at: int | None = None
            best_local = math.inf
            for index, values in enumerate(step_values, start=1):
                step_error = 0.0
                for var_value in values:
                    eval_with_var = evaluator.with_variables({statement.variable: var_value})
                    value = self._evaluate_function_call(statement, eval_with_var)
                    step_error = max(step_error, abs(value - target))
                best_local = min(best_local, step_error)
                if step_error <= tolerance:
                    satisfied_at = index
                    max_error = max(max_error, step_error)
                    max_step = max(max_step, index)
                    break
            if satisfied_at is None:
                return LimitResult(statement, False, best_local, len(step_values), samples)
        return LimitResult(statement, True, max_error, max_step or len(step_values), samples)

    def _prepare_domain(
        self, statement: LimitStatement
    ) -> Tuple[Tuple[Dict[str, float], ...], Tuple[float, ...]]:
        if statement.domain is None:
            contexts: list[Dict[str, float]] = [dict()]
        else:
            contexts = [
                {statement.domain.variable: value}
                for value in statement.domain.sample_points()
            ]
        targets = []
        for context in contexts:
            evaluator = _ExpressionEvaluator(self, context)
            target_value = evaluator.evaluate(statement._target_ast)
            if isinstance(target_value, bool):
                target_value = float(target_value)
            targets.append(float(target_value))
        return tuple(contexts), tuple(targets)

    def _evaluate_function_call(
        self, statement: LimitStatement, evaluator: _ExpressionEvaluator
    ) -> float:
        function = self.functions[statement.function]
        args = [
            float(evaluator.evaluate(arg_ast))
            for arg_ast in statement._argument_ast
        ]
        return evaluator.call_function(function, args)

    def _approach_steps(self, approach: LimitApproach, steps: int) -> Tuple[Tuple[float, ...], ...]:
        if steps <= 0:
            return ()
        if approach.kind == "infinity":
            current = 1.0
            result = []
            for _ in range(steps):
                result.append((current,))
                current *= 2.0
            return tuple(result)
        if approach.kind == "-infinity":
            current = -1.0
            result = []
            for _ in range(steps):
                result.append((current,))
                current *= 2.0
            return tuple(result)

        base = approach.value if approach.value is not None else 0.0
        delta = 1.0
        values: list[Tuple[float, float]] = []
        for _ in range(steps):
            delta /= 2.0
            values.append((base - delta, base + delta))
        return tuple(values)


