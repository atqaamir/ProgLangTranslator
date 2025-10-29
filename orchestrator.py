import os
from prompts import make_translation_prompt, make_fix_prompt
from llm_client import call_llm_translate, call_llm_fix
from executor import get_executor
from utils import build_error_log


def translate_and_repair(
    source_lang: str,
    target_lang: str,
    input_path: str,
    max_attempts: int = 5
):
    """
    End-to-end pipeline:

    1. Read the source code from disk.
    2. Ask the LLM to translate it into target_lang.
    3. Try to compile/run the translated code with the appropriate executor.
    4. If it fails, feed the error log + code back into the LLM to repair.
    5. Repeat until success or max_attempts.

    Returns a dict ready for main.py to write to disk:
        {
            "best_code": <final translated code string>,
            "last_error_log": <str>,
            "status_message": <str>,
            "program_output": <last exec_result dict>,
        }
    """

    # 0. read source file
    with open(input_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # 1. initial translation prompt for LLM
    initial_prompt = make_translation_prompt(
        src_lang=source_lang,
        tgt_lang=target_lang,
        src_code=source_code,
    )

    # 2. first translated candidate from LLM
    current_code = call_llm_translate(initial_prompt)

    # 3. pick executor for the *target* language
    run_fn = get_executor(target_lang)

    last_error_log = ""
    exec_result = {
        "ok": False,
        "stdout": "",
        "stderr": "",
        "exit_code": None,
    }

    for attempt in range(max_attempts):
        exec_result = run_fn(current_code)

        if exec_result["ok"]:
            # success path
            status_message = (
                "[OK] Translation succeeded with no runtime/compile errors."
            )

            return {
                "best_code": current_code,
                "last_error_log": "No errors.",
                "status_message": status_message,
                "program_output": exec_result,
            }

        # not ok: build error log we'll feed back
        last_error_log = build_error_log(exec_result)

        # Build a repair prompt for the LLM
        fix_prompt = make_fix_prompt(
            tgt_lang=target_lang,
            current_code=current_code,
            error_log=last_error_log,
        )

        # Ask LLM to return a fixed full version of the code
        current_code = call_llm_fix(fix_prompt)

    # if we exit loop without success:
    status_message = (
        "[WARN] Could not get a clean run/compile after attempts."
    )

    return {
        "best_code": current_code,
        "last_error_log": last_error_log,
        "status_message": status_message,
        "program_output": exec_result,
    }
