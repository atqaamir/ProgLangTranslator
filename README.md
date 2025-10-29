ProgLangTranslator
==================

ProgLangTranslator is an offline AI-powered programming language translator and self-repairing transpiler.

It takes code in one language (for example Python or C++) and asks a local large language model (LLM) to:
1. Translate it to a target language.
2. Try to compile/run the translated code.
3. If it fails, send the error log and the code back to the model.
4. Get a fixed version of the code.
5. Repeat until it compiles/runs.

No OpenAI API is required. The pipeline runs locally using an open source code model (Qwen2.5-Coder).


Main Features
-------------
- Translate between languages, e.g.:
  - C++ → Python
  - Python → C++
- Automatically compile or run the translated code.
- Automatic self-repair loop:
  - Compiler/runtime errors are fed back into the model.
  - The model returns a corrected version of the code.
- Saves:
  - final translated code,
  - logs,
  - run output
  to disk.
- Fully offline:
  - Uses Qwen/Qwen2.5-Coder-1.5B-Instruct locally via Hugging Face Transformers.
  - No API key, no internet calls after first model download.


Project Layout
--------------
main.py                CLI entry point. Parses args and saves outputs to disk.
orchestrator.py        Orchestrates translation + run + repair loop.
executor.py            Knows how to run/compile different target languages.
prompts.py             Builds prompts for translate and fix.
llm_client.py          Loads the local model (Qwen2.5-Coder) and generates code.
utils.py               Helper utilities for error logs.
examples/              Example input code you can try.
outputs/               Generated files will be written here (translated code, logs, run output).


Requirements
-----------
You need:
- Python 3.9+ (3.10+ recommended)
- g++ (for C++ compilation)
- venv (Python virtual environment)
- Enough RAM / VRAM to run a ~1.5B parameter model (Qwen2.5-Coder-1.5B-Instruct).
  - This model can usually run on CPU. It's slower, but works.

Python packages:
- torch
- transformers>=4.37.0
- accelerate
- safetensors
- bitsandbytes   (optional; helps with GPU / low VRAM)

All of these are installed in the steps below.


Setup
-----

1. Go to the project directory
   cd /path/to/ProgLangTranslator

2. Create and activate a virtual environment

   macOS / Linux:
   python3 -m venv venv
   source venv/bin/activate

   Windows (PowerShell):
   python -m venv venv
   venv\Scripts\activate

3. Upgrade pip
   pip install --upgrade pip

4. Install base requirements
   pip install -r requirements.txt

   (Your requirements.txt should include torch, transformers>=4.37.0, accelerate, safetensors, bitsandbytes)

   If bitsandbytes fails on your machine (Mac CPU-only for example), re-run without it:
   pip install torch transformers>=4.37.0 accelerate safetensors

5. First run will download the model
   The file llm_client.py loads:
   Qwen/Qwen2.5-Coder-1.5B-Instruct
   via Hugging Face Transformers:
       tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
       model = AutoModelForCausalLM.from_pretrained(_MODEL_NAME, ...)

   That download happens once and is cached locally.
   After that, you are offline.


How It Works (Pipeline)
-----------------------

1. main.py
   - Parses CLI args:
     --input         path to source code file
     --source        source language (e.g. "cpp", "python")
     --target        target language (e.g. "python", "cpp")
     --max-attempts  how many repair loops to allow
     --output-dir    where to save results
   - Calls translate_and_repair(...) in orchestrator.py
   - Writes:
     - <name>_translated.<ext>
     - <name>_log.txt
     - <name>_run_output.txt
     into the output directory.

2. orchestrator.translate_and_repair(...)
   - Reads the source file.
   - Builds a translation prompt using make_translation_prompt(...) from prompts.py.
   - Calls call_llm_translate(...) in llm_client.py to get first target-language code.
   - Runs that code using the proper executor for the target language.
   - If run/compile fails:
        * build_error_log(...) packages stderr/stdout
        * make_fix_prompt(...) builds a "please fix this" prompt
        * call_llm_fix(...) asks the model for a corrected full version of the code
        * retry
   - Returns structured data (final code, last error log, etc.) back to main.py.

3. executor.py
   - run_python(): writes code to a temp .py, runs Python syntax check + python3 execution.
   - run_cpp_just_compile(): writes code to temp .cpp, compiles with g++ (optionally with -std=c++17), then runs the binary.
   - get_executor(target_lang): picks the correct runner based on --target.
   - The executor result (ok / stdout / stderr / exit_code) is what drives the repair loop.

4. llm_client.py (Offline)
   - Loads Qwen2.5-Coder-1.5B-Instruct via Hugging Face Transformers.
   - _generate_response(...) builds a chat-style prompt using tokenizer.apply_chat_template() and runs model.generate().
   - call_llm_translate(prompt):
        * Sends the "translate this code" instructions + source code.
        * Model responds with target-language code.
        * We strip fences and language labels so we only keep raw code.
   - call_llm_fix(prompt):
        * Sends current broken code + compiler/runtime error log.
        * Model returns a corrected full version of the code.
   - Both functions return pure code (no markdown, no "```", no "python" header line), so the executor can immediately try to run/compile it.

5. prompts.py
   - make_translation_prompt(source_lang, target_lang, source_code):
        * Tells the model: translate this code, keep behavior identical, produce ONLY code.
        * If target_lang is C++/cpp/cxx, it appends extra rules:
            - produce self-contained C++17 code,
            - include headers like <iostream>,
            - include int main() that demonstrates usage,
            - compile under g++ -std=c++17.
   - make_fix_prompt(target_lang, current_code, error_log):
        * "Here is the code that failed, and here is stderr/stdout. Fix only what's needed. Return full corrected code only."

   This is what powers the self-repair loop.


Usage
-----

Translate C++ → Python:
-----------------------
python3 main.py --input examples/hello.cpp --source cpp --target python --output-dir outputs

Translate Python → C++:
-----------------------
python3 main.py --input examples/addition.py --source python --target cpp --output-dir outputs

After running, look in the outputs/ directory (or whatever you passed to --output-dir).
You will see 3 files for each run:

1. <name>_translated.<ext>
   The final translated code after the last attempt.

2. <name>_log.txt
   Status summary and last error log (or "No errors." if success).

3. <name>_run_output.txt
   The stdout / stderr captured when we ran or compiled the translated code.


Example Input Files
-------------------

examples/hello.cpp
------------------
#include <iostream>
int main() {
    std::cout << "Hello from C++!" << std::endl;
    return 0;
}

examples/addition.py
--------------------
def add(a, b):
    """Return the sum of two numbers."""
    return a + b

def main():
    x = 5
    y = 7
    print(f"The sum of {x} and {y} is {add(x, y)}")

if __name__ == "__main__":
    main()


CLI Options
-----------
--input         Path to source code file (required)
--source        Source language (default: cpp)
--target        Target language (default: python)
--max-attempts  How many repair iterations before giving up (default: 5)
--output-dir    Directory where translated code and logs should be written (default: outputs)


What a Successful Run Looks Like
--------------------------------
The orchestrator will eventually mark success and you'll see something like:

best_code (translated file) might be:
    def main():
        print("Hello from C++!")

    if __name__ == "__main__":
        main()

log file (e.g. hello_log.txt):
    [OK] Translation succeeded with no runtime/compile errors.
    No errors.

run_output file (e.g. hello_run_output.txt):
    STDOUT:
    Hello from C++!

    STDERR:


Notes / Tips
------------
- If the model output starts with a stray language label like "python" or "cpp", llm_client.py strips it automatically.
- For Python → C++, the prompt tells the model:
  "make a full C++17 program with #include <iostream> and int main()".
  This helps g++ compile it directly.
- The executor uses g++ to compile C++ targets and python3 to run Python targets.
- You can increase --max-attempts if the code is complex.


You're Ready
------------
After setup, translating code and auto-fixing it is just:
python3 main.py --input YOUR_FILE --source SOURCE_LANG --target TARGET_LANG --output-dir outputs

Everything is offline. No API keys. No network calls at runtime.
