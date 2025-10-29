def factorial(n):
    """Recursive factorial."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def main():
    nums = [3, 5, 7]
    results = [factorial(x) for x in nums]
    for x, y in zip(nums, results):
        print(f"{x}! = {y}")

if __name__ == "__main__":
    main()
