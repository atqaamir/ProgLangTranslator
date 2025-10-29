def build_error_log(exec_result: dict) -> str:
    """
    Turn executor result into a readable error log string
    that we can feed into the FixAgent prompt.
    """
    return (
        "STDERR:\n" + exec_result["stderr"] +
        "\nSTDOUT:\n" + exec_result["stdout"] +
        f"\nEXIT CODE: {exec_result['exit_code']}\n"
    )
