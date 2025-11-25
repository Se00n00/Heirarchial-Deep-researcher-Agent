import unittest
import asyncio
from python_intrepeter import PythonInterpreterTool

class TestPythonInterpreter(unittest.TestCase):
    def setUp(self):
        self.interpreter = PythonInterpreterTool()

    def run_code(self, code):
        # Helper method to run code and get result
        return asyncio.run(self.interpreter.forward(code))

    def test_basic_calculation(self):
        # Test basic mathematical operations
        result = self.run_code("2 + 2")
        self.assertEqual(result.output, "Stdout:\n\nOutput: 4")

    def test_print_statement(self):
        # Test print statement capture
        result = self.run_code("print('Hello, World!')")
        self.assertEqual(result.output, "Stdout:\nHello, World!\nOutput: None")

    def test_multiple_lines(self):
        # Test multiple lines of code
        code = """
x = 5
y = 3
print(f"Sum is: {x + y}")
x * y"""
        result = self.run_code(code)
        self.assertEqual(result.output, "Stdout:\nSum is: 8\nOutput: 15")

    def test_unauthorized_import(self):
        # Test that unauthorized imports raise an error
        result = self.run_code("import os; os.getcwd()")
        self.assertIsNotNone(result.error)

    def test_syntax_error(self):
        # Test syntax error handling
        result = self.run_code("print('Hello'")
        self.assertIsNotNone(result.error)

    def test_runtime_error(self):
        # Test runtime error handling
        result = self.run_code("1/0")
        self.assertIsNotNone(result.error)

    def test_complex_calculation(self):
        # Test more complex mathematical operations
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

print(f"Factorial of 7 is: {factorial(7)}")
factorial(7)
"""
        result = self.run_code(code)
        self.assertEqual(result.output, "Stdout:\nFactorial of 7 is: 5040\nOutput: 5040")

if __name__ == '__main__':
    unittest.main()