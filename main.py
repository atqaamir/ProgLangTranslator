import argparse
from orchestrator import translate_and_repair


def parse_args():
    parser = argparse.ArgumentParser(
        description="LLM-powered code translator with auto-fix loop."
    )

    parser.add_argument(
        "--source",
        "-s",
        default="cpp",
        help="Source language name (default: cpp)",
    )

    parser.add_argument(
        "--target",
        "-t",
        default="python",
        help="Target language name (default: python)",
    )

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to the source code file you want to translate.",
    )

    parser.add_argument(
        "--max-attempts",
        "-m",
        type=int,
        default=5,
        help="Maximum repair attempts before giving up (default: 5).",
    )

    return parser.parse_args()


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    args = parse_args()
    source_lang = args.source
    target_lang = args.target
    source_code = read_file(args.input)
    max_attempts = args.max_attempts

    result = translate_and_repair(
        source_lang=source_lang,
        target_lang=target_lang,
        source_code=source_code,
        max_attempts=max_attempts,
    )

    print("========== RESULT ==========")
    if result["success"]:
        print("[OK] Translation succeeded with no runtime/compile errors.\n")
        print("----- Translated Code -----")
        print(result["code"])
        print("----- Program Output -----")
        print(result["stdout"])
    else:
        print("[WARN] Could not get a clean run/compile after attempts.\n")
        print("----- Best Effort Code -----")
        print(result["code"])
        print("----- Last Error Log -----")
        print(result["error"])

    print("===========================")


if __name__ == "__main__":
    main()
