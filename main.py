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


import argparse
import os
from orchestrator import translate_and_repair

def main():
    parser = argparse.ArgumentParser(description="Programming language translator with repair loop.")
    parser.add_argument("--input", required=True, help="Path to source code file.")
    parser.add_argument("--source", default="cpp", help="Source language (default: cpp).")
    parser.add_argument("--target", default="python", help="Target language (default: python).")
    parser.add_argument("--max-attempts", type=int, default=5, help="Maximum translation-repair attempts.")
    parser.add_argument("--output-dir", default="outputs", help="Directory to save results.")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    result = translate_and_repair(
        source_lang=args.source,
        target_lang=args.target,
        input_path=args.input,
        max_attempts=args.max_attempts,
    )

    # Build filenames
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    target_ext = "py" if args.target.lower() == "python" else "cpp"
    code_path = os.path.join(args.output_dir, f"{base_name}_translated.{target_ext}")
    log_path = os.path.join(args.output_dir, f"{base_name}_log.txt")
    runout_path = os.path.join(args.output_dir, f"{base_name}_run_output.txt")

    # Write translated code
    if "best_code" in result:
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(result["best_code"])

    # Write logs
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(result.get("last_error_log", "No errors.\n"))
        f.write("\n\n========== SUMMARY ==========\n")
        f.write(result.get("status_message", "Done.\n"))

    # Write runtime output (stdout/stderr)
    run_output = ""
    if "program_output" in result:
        run_output += "STDOUT:\n" + result["program_output"].get("stdout", "") + "\n"
        run_output += "STDERR:\n" + result["program_output"].get("stderr", "") + "\n"
    with open(runout_path, "w", encoding="utf-8") as f:
        f.write(run_output)

    # Print summary to terminal
    print("\n✅ Translation completed.")
    print(f"Code saved to: {code_path}")
    print(f"Logs saved to: {log_path}")
    print(f"Run output saved to: {runout_path}")

if __name__ == "__main__":
    main()
