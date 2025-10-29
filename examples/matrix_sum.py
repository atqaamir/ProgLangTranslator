def matrix_sum(a, b):
    """Add two 2D matrices."""
    rows = len(a)
    cols = len(a[0])
    result = [[a[i][j] + b[i][j] for j in range(cols)] for i in range(rows)]
    return result

def main():
    A = [[1, 2, 3], [4, 5, 6]]
    B = [[6, 5, 4], [3, 2, 1]]
    C = matrix_sum(A, B)
    for row in C:
        print(row)

if __name__ == "__main__":
    main()

# python3 main.py --source python --target cpp --input examples/matrix_sum.py
