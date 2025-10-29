"""
llm_client.py (offline / Hugging Face)
--------------------------------------

This version runs an open-source code LLM locally:
Qwen/Qwen2.5-Coder-1.5B-Instruct  (Apache-2.0 licensed)  :contentReference[oaicite:7]{index=7}

It replaces the OpenAI API calls with local inference using transformers.

What it does:
- call_llm_translate(prompt) -> first-pass code translation
- call_llm_fix(prompt) -> repair pass using compiler/runtime errors

Both return ONLY code (no markdown fences), so the rest of the pipeline
can write it to a file and execute it.

Hardware note:
- 1.5B model can usually run on CPU (slow) or small GPU.
- For larger Qwen2.5-Coder (7B+), you'll want a GPU or quantization.

You MUST have installed:
    pip install torch transformers>=4.37.0 accelerate safetensors bitsandbytes
"""

import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# You can switch to bigger models later, e.g. "Qwen/Qwen2.5-Coder-7B-Instruct"
_MODEL_NAME = "Qwen/Qwen2.5-Coder-1.5B-Instruct"


# ----------------------------
# Model load (happens once)
# ----------------------------
# device_map="auto" will try to use GPU if available, otherwise CPU.
# torch_dtype="auto" will pick a reasonable precision automatically.
tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    _MODEL_NAME,
    torch_dtype="auto",
    device_map="auto",
)


def _strip_code_fences(text: str) -> str:
    """
    If the model wraps code in ```...``` or adds a stray language name
    (like 'python' or 'cpp') at the top, return just the actual code.
    """
    fence = "```"
    if fence in text:
        parts = text.split(fence)
        # pick the last chunk that looks like code
        for chunk in reversed(parts):
            chunk_stripped = chunk.strip()
            if "\n" in chunk_stripped or "def " in chunk_stripped or ";" in chunk_stripped:
                text = chunk_stripped
                break
        else:
            text = parts[-1]

    # Remove any leading language label like "python", "cpp", etc.
    lines = text.strip().splitlines()
    if lines and re.fullmatch(r"[A-Za-z0-9_+\-#]+", lines[0].strip().lower()):
        # first line is just a language name
        lines = lines[1:]
    return "\n".join(lines).strip()



def _generate_response(messages, max_new_tokens=512, temperature=0.0):
    """
    messages: list of { "role": "system"|"user"|"assistant", "content": str }
    Returns: generated text (string) from the assistant.

    We follow Qwen's chat template approach. :contentReference[oaicite:8]{index=8}
    """
    # Build chat text using Qwen chat template
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True  # tell model "your turn"
    )

    # Tokenize for model
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=(temperature > 0.0),
            temperature=temperature,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # We only want the newly generated part, not the full prompt
    generated_ids = output_ids[0][inputs["input_ids"].shape[-1]:]
    out_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

    return out_text.strip()


def _make_system_instruction_translate():
    """
    System message for translation.
    """
    return (
        "You are a code translation assistant. "
        "Your job is to translate code from a source language to a target language. "
        "You MUST output ONLY the translated code in the target language. "
        "Do not include explanations, markdown fences, or commentary."
    )


def _make_system_instruction_fix():
    """
    System message for repair.
    """
    return (
        "You are a code repair assistant. "
        "You receive code plus compiler/runtime errors. "
        "Return ONLY the corrected full code. "
        "No explanations, no comments outside the code, no markdown fences."
    )


def call_llm_translate(prompt: str) -> str:
    """
    FIRST PASS TRANSLATION.
    We feed the prompt we built in make_translation_prompt(...) to the local model.
    We wrap it with a system instruction telling it to ONLY output code.
    """

    messages = [
        {"role": "system", "content": _make_system_instruction_translate()},
        {"role": "user", "content": prompt},
    ]

    raw = _generate_response(messages, max_new_tokens=1024, temperature=0.0)
    cleaned = _strip_code_fences(raw)
    return cleaned.strip() + "\n"


def call_llm_fix(prompt: str) -> str:
    """
    REPAIR PASS.
    We feed the fix prompt we built in make_fix_prompt(...), which includes:
    - error log
    - current broken code
    We tell the model: ONLY output corrected code.
    """

    messages = [
        {"role": "system", "content": _make_system_instruction_fix()},
        {"role": "user", "content": prompt},
    ]

    raw = _generate_response(messages, max_new_tokens=1024, temperature=0.0)
    cleaned = _strip_code_fences(raw)
    return cleaned.strip() + "\n"
