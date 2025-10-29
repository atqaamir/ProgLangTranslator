from textwrap import dedent


def make_translation_prompt(src_lang: str, tgt_lang: str, src_code: str) -> str:
    """
    Builds a first-pass translation prompt.
    Automatically adds special instructions for certain target languages
    (e.g., C++), so the output is a complete, compilable program.
    """

    base_prompt = dedent(f"""
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

    # Add extra guidance for specific target languages
    tgt = tgt_lang.lower().strip()

    if tgt in ["c++", "cpp", "cxx"]:
        extra_cpp = dedent("""
        Additional requirements for C++ targets:
        4. The output MUST be a single, self-contained program that compiles
           with `g++ -std=c++17` without external dependencies.
        5. Include necessary standard headers (e.g., <iostream>, <vector>, etc.).
        6. Define an `int main()` function that demonstrates or calls the translated logic.
        7. Do not include explanations or comments outside the code block.
        """)
        base_prompt += "\n\n" + extra_cpp

    elif tgt in ["java"]:
        extra_java = dedent("""
        Additional requirements for Java targets:
        4. The output must be a single compilable Java file with a `public class`
           containing a `main` method.
        5. Use only standard Java libraries.
        """)
        base_prompt += "\n\n" + extra_java

    return base_prompt



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
