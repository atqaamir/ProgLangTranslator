import subprocess
import tempfile
import os
import shutil




def _run_subprocess(cmd_list, timeout=5, cwd=None):
    """
    Run a subprocess and capture stdout/stderr/exit code.
    """
    try:
        proc = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        exit_code = proc.returncode
        return stdout, stderr, exit_code
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 124
    except FileNotFoundError as e:
        # e.g. "node" or "python3" not found on system
        return "", f"EXECUTOR ERROR: {str(e)}", 127


def run_python(python_code: str):
    """
    1. Write code to temp.py
    2. python3 -m py_compile temp.py  (syntax check)
    3. python3 temp.py                (runtime check)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "candidate.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(python_code)

        # syntax check
        stdout_c, stderr_c, exit_c = _run_subprocess(
            ["python3", "-m", "py_compile", file_path],
            cwd=tmpdir,
        )

        if exit_c != 0:
            return {
                "ok": False,
                "stdout": stdout_c,
                "stderr": stderr_c,
                "exit_code": exit_c,
            }

        # runtime check
        stdout_r, stderr_r, exit_r = _run_subprocess(
            ["python3", file_path],
            cwd=tmpdir,
        )

        return {
            "ok": (exit_r == 0),
            "stdout": stdout_r,
            "stderr": stderr_r,
            "exit_code": exit_r,
        }


def run_javascript(js_code: str):
    """
    1. Write code to candidate.js
    2. node candidate.js
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "candidate.js")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(js_code)

        stdout_r, stderr_r, exit_r = _run_subprocess(
            ["node", file_path],
            cwd=tmpdir,
        )

        return {
            "ok": (exit_r == 0),
            "stdout": stdout_r,
            "stderr": stderr_r,
            "exit_code": exit_r,
        }


def run_cpp_just_compile(cpp_code: str):
    """
    This is here mostly as an example if you ever want to test C++ output.
    Currently we assume target is Python by default, but let's keep this.

    Steps:
    - Write candidate.cpp
    - g++ candidate.cpp -o candidate.out
    - run ./candidate.out

    NOTE: requires g++ to exist.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        cpp_path = os.path.join(tmpdir, "candidate.cpp")
        out_path = os.path.join(tmpdir, "candidate.out")

        with open(cpp_path, "w", encoding="utf-8") as f:
            f.write(cpp_code)

        # compile
        stdout_c, stderr_c, exit_c = _run_subprocess(
            ["g++", "-std=c++17", cpp_path, "-o", out_path],
            cwd=tmpdir,
        )

        if exit_c != 0:
            return {
                "ok": False,
                "stdout": stdout_c,
                "stderr": stderr_c,
                "exit_code": exit_c,
            }

        # run
        stdout_r, stderr_r, exit_r = _run_subprocess(
            [out_path],
            cwd=tmpdir,
        )

        return {
            "ok": (exit_r == 0),
            "stdout": stdout_r,
            "stderr": stderr_r,
            "exit_code": exit_r,
        }


def get_executor(target_lang: str):
    """
    Pick the executor (runner) function based on the chosen target language.
    By default, we assume you want C++ -> Python, so Python executor is default.
    """

    # normalize
    lang = target_lang.strip().lower()

    # Python target
    if lang in ["python", "py", "python3"]:
        return run_python

    # JavaScript / Node target
    if lang in ["javascript", "js", "node", "nodejs"]:
        return run_javascript

    # C++ target (compile with g++)
    if lang in ["c++", "cpp", "cxx"]:
        return run_cpp_just_compile

    # If we don't know how to run it, fallback to "always fail"
    def unsupported_executor(_code: str):
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"No executor available for target language '{target_lang}'",
            "exit_code": 1,
        }

    return unsupported_executor
