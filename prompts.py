from textwrap import dedent


def make_translation_prompt(src_lang: str, tgt_lang: str, src_code: str) -> str:
    """
    First-pass translation prompt.
    """
    return dedent(f"""
    You are a programming language translator.

    Task:
    Translate the following source code into {tgt_lang}.
    Keep the behavior 100% identical.
    Do not invent new helper functions, libraries, classes, or types that are not present or standard in {tgt_lang}.
    Preserve comments and docstrings.
    Keep function and variable names the same when legal in {tgt_lang}.

    Requirements:
    1. The output must be valid, runnable {tgt_lang} code with no syntax errors.
    2. Do not add explanations. Output ONLY the translated code.
    3. If something cannot be expressed directly, add a comment in the code explaining the limitation instead of guessing.

    Source language: {src_lang}
    Target language: {tgt_lang}

    Code to translate:
    ```{src_lang}
    {src_code}
    ```
    """).strip()


def make_fix_prompt(tgt_lang: str, current_code: str, error_log: str) -> str:
    """
    Repair prompt.

    NOTE: We deliberately put the *current code* LAST in a fenced block.
    Our dummy call_llm_fix() will grab the last fenced block and return it.
    """
    return dedent(f"""
    I tried to compile/run the {tgt_lang} code you generated, and it failed.

    The error log was:
    ```text
    {error_log}
    ```

    Please fix ONLY what is required to eliminate these errors.
    Do not change the program's behavior.
    Do not add new features.
    Return ONLY the full corrected {tgt_lang} code, with no commentary.

    Here is the current {tgt_lang} code that needs fixing:
    {current_code}
    """).strip()
