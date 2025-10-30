# This file defines a function to sum two numbers

def multiply_numbers(a: float, b: float, c:float) -> float:
    """
    Sum two numbers.

    Args:
    a (float): The first number.
    b (float): The second number.

    Returns:
    float: The sum of a and b.
    """
    return a * b * c

# Example usage:
if __name__ == "__main__":
    num1 = 5.5
    num2 = 4.5
    num3 = 3.5
    result = multiply_numbers(num1, num2, num3)
    print(f"The sum of {num1}, {num2}, and {num3} is {result}")
    