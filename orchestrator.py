from prompts import make_translation_prompt, make_fix_prompt
from llm_client import call_llm_translate, call_llm_fix
from executor import get_executor
from utils import build_error_log


def translate_and_repair(source_lang: str,
                         target_lang: str,
                         source_code: str,
                         max_attempts: int = 5):
    """
    Orchestrates:
    1. Initial translation via LLM.
    2. Compile/run loop with self-repair.
    Stops early if we get a clean run.
    """

    # 1. initial translation
    initial_prompt = make_translation_prompt(
        src_lang=source_lang,
        tgt_lang=target_lang,
        src_code=source_code,
    )
    current_code = call_llm_translate(initial_prompt)

    run_fn = get_executor(target_lang)

    last_error_log = ""

    for attempt in range(max_attempts):
        result = run_fn(current_code)

        if result["ok"]:
            # success, return immediately
            return {
                "success": True,
                "code": current_code,
                "stdout": result["stdout"],
            }

        # not ok
        last_error_log = build_error_log(result)

        # Build a fix prompt
        fix_prompt = make_fix_prompt(
            tgt_lang=target_lang,
            current_code=current_code,
            error_log=last_error_log,
        )

        # Ask "LLM" to fix code
        current_code = call_llm_fix(fix_prompt)

    # ran out of attempts
    return {
        "success": False,
        "code": current_code,
        "error": last_error_log,
        "stdout": "",
    }
