import io
import contextlib
import ast


class CodeExecutionTool:
    def execute(self, code: str):
        tree = ast.parse(code, mode="exec")
        disallowed = (
            ast.Import,
            ast.ImportFrom,
            ast.With,
            ast.AsyncWith,
            ast.Try,
            ast.Raise,
            ast.Global,
            ast.Nonlocal,
            ast.Lambda,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Attribute,
            ast.Subscript,
            ast.Delete,
        )
        for node in ast.walk(tree):
            if isinstance(node, disallowed):
                raise ValueError(f"Disallowed syntax in sandboxed execution: {type(node).__name__}")
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in {"print", "len", "range", "str", "int"}:
                    raise ValueError("Only safe builtins are allowed in sandboxed execution")
        output = io.StringIO()
        sandbox_globals = {"__builtins__": {"print": print, "len": len, "range": range, "str": str, "int": int}}
        with contextlib.redirect_stdout(output):
            exec(compile(tree, "<sandbox>", "exec"), sandbox_globals, {})
        return {"stdout": output.getvalue()}
