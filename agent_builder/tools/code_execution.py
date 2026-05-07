import io
import contextlib


class CodeExecutionTool:
    def execute(self, code: str):
        output = io.StringIO()
        sandbox_globals = {"__builtins__": {"print": print, "len": len, "range": range, "str": str, "int": int}}
        with contextlib.redirect_stdout(output):
            exec(code, sandbox_globals, {})
        return {"stdout": output.getvalue()}
