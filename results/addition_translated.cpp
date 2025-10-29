#include <iostream>

int add(int a, int b) {
    // Return the sum of two numbers.
    return a + b;
}

int main() {
    int x = 5;
    int y = 7;
    int result = add(x, y);
    std::cout << "The sum of " << x << " and " << y << " is " << result << std::endl;

    return 0;
}
