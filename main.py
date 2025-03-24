import math
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import colorama
from colorama import Fore, Back, Style
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box

# Initialize colorama for cross-platform colored terminal output
colorama.init(autoreset=True)


class TokenType(Enum):
    # Keywords
    FUNCTION = auto()
    EXTERN = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    FOR = auto()
    IN = auto()
    
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    IDENTIFIER = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    POWER = auto()
    
    # Comparison operators
    LESS = auto()
    GREATER = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    
    # Punctuation
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    COMMA = auto()
    SEMICOLON = auto()
    
    # Special
    EOF = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
    
    def __str__(self) -> str:
        return f"Token(type={self.type.name}, value='{self.value}', position=({self.line}, {self.column}))"

    def colored_str(self) -> str:
        """Return a colored string representation based on token type."""
        type_colors = {
            # Keywords - cyan
            TokenType.FUNCTION: Fore.CYAN,
            TokenType.EXTERN: Fore.CYAN,
            TokenType.IF: Fore.CYAN,
            TokenType.THEN: Fore.CYAN,
            TokenType.ELSE: Fore.CYAN,
            TokenType.FOR: Fore.CYAN,
            TokenType.IN: Fore.CYAN,
            
            # Literals - green
            TokenType.INTEGER: Fore.GREEN,
            TokenType.FLOAT: Fore.GREEN,
            TokenType.IDENTIFIER: Fore.WHITE,
            
            # Operators - yellow
            TokenType.PLUS: Fore.YELLOW,
            TokenType.MINUS: Fore.YELLOW,
            TokenType.MULTIPLY: Fore.YELLOW,
            TokenType.DIVIDE: Fore.YELLOW,
            TokenType.MODULO: Fore.YELLOW,
            TokenType.POWER: Fore.YELLOW,
            
            # Comparison - magenta
            TokenType.LESS: Fore.MAGENTA,
            TokenType.GREATER: Fore.MAGENTA,
            TokenType.EQUAL: Fore.MAGENTA,
            TokenType.NOT_EQUAL: Fore.MAGENTA,
            
            # Punctuation - blue
            TokenType.LEFT_PAREN: Fore.BLUE,
            TokenType.RIGHT_PAREN: Fore.BLUE,
            TokenType.COMMA: Fore.BLUE,
            TokenType.SEMICOLON: Fore.BLUE,
            
            # Special
            TokenType.EOF: Fore.RED,
            TokenType.UNKNOWN: Fore.RED,
        }
        color = type_colors.get(self.type, Fore.WHITE)
        return f"{color}Token(type={Style.BRIGHT}{self.type.name}{Style.NORMAL}, " \
               f"value='{self.value}', " \
               f"position=({self.line}, {self.column})){Style.RESET_ALL}"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
        # Optimized keyword lookup
        self.keywords = {
            "def": TokenType.FUNCTION, "extern": TokenType.EXTERN,
            "if": TokenType.IF, "then": TokenType.THEN, "else": TokenType.ELSE,
            "for": TokenType.FOR, "in": TokenType.IN
        }

        self.single_char_tokens = {
            "+": TokenType.PLUS, "-": TokenType.MINUS, "*": TokenType.MULTIPLY,
            "/": TokenType.DIVIDE, "%": TokenType.MODULO, "^": TokenType.POWER,
            "<": TokenType.LESS, ">": TokenType.GREATER, "=": TokenType.EQUAL,
            "(": TokenType.LEFT_PAREN, ")": TokenType.RIGHT_PAREN,
            ",": TokenType.COMMA, ";": TokenType.SEMICOLON,
        }
        
        # Pre-compile regular expressions for better performance
        self.identifier_regex = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
        self.number_regex = re.compile(r'\d+(\.\d+)?')

    def is_at_end(self) -> bool:
        return self.position >= len(self.source)

    def advance(self) -> str:
        if self.is_at_end():
            return ''
        char = self.source[self.position]
        self.position += 1
        self.column += 1

        if char == '\n':
            self.line += 1
            self.column = 1

        return char

    def peek(self) -> str:
        return self.source[self.position] if not self.is_at_end() else ''

    def peek_next(self) -> str:
        return self.source[self.position + 1] if self.position + 1 < len(self.source) else ''

    def match(self, expected: str) -> bool:
        if self.is_at_end() or self.source[self.position] != expected:
            return False
        self.position += 1
        self.column += 1
        return True

    def add_token(self, token_type: TokenType, value: str = ""):
        self.tokens.append(Token(token_type, value or token_type.name, self.line, self.column - len(value)))

    def scan_tokens(self) -> List[Token]:
        start_time = time.time()
        
        while not self.is_at_end():
            self.scan_token()
        
        self.add_token(TokenType.EOF)
        end_time = time.time()
        scan_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return self.tokens, scan_time

    def scan_token(self):
        char = self.advance()

        if char.isspace():
            return
        elif char == '#':  # Comment handling
            while self.peek() not in '\n' and not self.is_at_end():
                self.advance()
            return
        elif char in self.single_char_tokens:
            if char == '!' and self.match('='):
                self.add_token(TokenType.NOT_EQUAL, "!=")
            else:
                self.add_token(self.single_char_tokens[char], char)
            return
        elif char.isalpha() or char == '_':
            self.identifier()
            return
        elif char.isdigit() or (char == '.' and self.peek().isdigit()):
            self.number()
            return

        self.add_token(TokenType.UNKNOWN, char)

    def identifier(self):
        # Start from previous position as we've already advanced
        match = self.identifier_regex.match(self.source[self.position - 1:])
        if match:
            identifier = match.group(0)
            # Adjust position (account for the first character we've already advanced)
            self.position = self.position - 1 + len(identifier)
            self.column = self.column - 1 + len(identifier)
            token_type = self.keywords.get(identifier, TokenType.IDENTIFIER)
            self.add_token(token_type, identifier)

    def number(self):
        match = self.number_regex.match(self.source[self.position - 1:])
        if match:
            num_str = match.group(0)
            # Adjust position (account for the first character we've already advanced)
            self.position = self.position - 1 + len(num_str)
            self.column = self.column - 1 + len(num_str)
            self.add_token(TokenType.FLOAT if '.' in num_str else TokenType.INTEGER, num_str)


import re

class Calculator:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        # Map of supported functions and their implementations
        self.functions = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log10,
            "ln": math.log,
            "abs": abs,
            "pow": pow
        }

    def calculate(self) -> Tuple[Optional[float], float]:
        start_time = time.time()
        result = self.expression()
        end_time = time.time()
        calc_time = (end_time - start_time) * 1000  # Convert to milliseconds
        return result, calc_time

    def expression(self):
        return self.term()

    def term(self):
        left = self.factor()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos].type in [TokenType.PLUS, TokenType.MINUS]:
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.factor()
            
            if op.type == TokenType.PLUS:
                left += right
            elif op.type == TokenType.MINUS:
                left -= right
                
        return left

    def factor(self):
        left = self.power()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos].type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO]:
            op = self.tokens[self.pos]
            self.pos += 1
            right = self.power()
            
            if op.type == TokenType.MULTIPLY:
                left *= right
            elif op.type == TokenType.DIVIDE:
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                left /= right
            elif op.type == TokenType.MODULO:
                if right == 0:
                    raise ZeroDivisionError("Modulo by zero")
                left %= right
                
        return left

    def power(self):
        left = self.primary()
        
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.POWER:
            self.pos += 1
            right = self.power()  # Right associative
            return left ** right
            
        return left

    def primary(self):
        if self.pos >= len(self.tokens):
            raise SyntaxError("Unexpected end of expression")
            
        token = self.tokens[self.pos]
        self.pos += 1
        
        if token.type == TokenType.INTEGER:
            return int(token.value)
        elif token.type == TokenType.FLOAT:
            return float(token.value)
        elif token.type == TokenType.IDENTIFIER:
            # Handle functions
            if token.value in self.functions:
                if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.LEFT_PAREN:
                    self.pos += 1
                    
                    # Handle special case for pow function which takes two arguments
                    if token.value == "pow":
                        arg1 = self.expression()
                        
                        # Expect a comma
                        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.COMMA:
                            self.pos += 1
                            arg2 = self.expression()
                            
                            # Expect closing parenthesis
                            if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.RIGHT_PAREN:
                                self.pos += 1
                                return self.functions[token.value](arg1, arg2)
                            else:
                                raise SyntaxError(f"Expected closing parenthesis after second pow argument at position {self.pos}")
                        else:
                            raise SyntaxError(f"Expected comma separator in pow function at position {self.pos}")
                    
                    # Handle single argument functions
                    else:
                        arg = self.expression()
                        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.RIGHT_PAREN:
                            self.pos += 1
                            return self.functions[token.value](arg)
                        else:
                            raise SyntaxError(f"Expected closing parenthesis after function argument at position {self.pos}")
                else:
                    raise SyntaxError(f"Expected opening parenthesis after function name at position {self.pos}")
            else:
                raise NameError(f"Unknown identifier '{token.value}' at position {self.pos}")


def print_tokens(tokens: List[Token], console: Console):
    """Print tokens in a visually appealing table format."""
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Type", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Line", style="yellow", justify="right")
    table.add_column("Column", style="yellow", justify="right")
    
    for token in tokens:
        if token.type != TokenType.EOF:  # Skip EOF for cleaner output
            table.add_row(
                token.type.name,
                token.value,
                str(token.line),
                str(token.column)
            )
    
    console.print(Panel(table, title="[bold blue]Tokens[/]", border_style="blue"))


def print_calculation_result(expression: str, result: float, tokens: List[Token], scan_time: float, calc_time: float, console: Console):
    """Print calculation result with detailed information."""
    # Expression panel
    syntax = Syntax(expression, "python", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="[bold green]Expression[/]", border_style="green"))
    
    # Create a visualization of the calculation process
    token_display = " ".join([f"[cyan]{t.value}[/]" if t.type in [TokenType.INTEGER, TokenType.FLOAT] 
                       else f"[yellow]{t.value}[/]" if t.type in [TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO, TokenType.POWER] 
                       else f"[magenta]{t.value}[/]" for t in tokens if t.type != TokenType.EOF])
    
    # Results table
    result_table = Table(show_header=False, box=box.SIMPLE_HEAD)
    result_table.add_column("Property", style="cyan", justify="right")
    result_table.add_column("Value", style="yellow")
    
    result_table.add_row("Expression", token_display)
    result_table.add_row("Result", str(result))  # Use Rich's styling instead
    result_table.add_row("Tokenization Time", f"{scan_time:.4f} ms")
    result_table.add_row("Calculation Time", f"{calc_time:.4f} ms")
    result_table.add_row("Total Processing Time", f"{scan_time + calc_time:.4f} ms")
    
    console.print(Panel(result_table, title="[bold yellow]Calculation Result[/]", border_style="yellow"))


def run_lexer_demo(source_code: str, console: Console):
    """Run a demonstration of the lexer with source code."""
    console.print(Panel(f"[bold]Lexer Demo[/]", border_style="green"))
    
    # Print the source code
    syntax = Syntax(source_code, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="[bold blue]Source Code[/]", border_style="blue"))
    
    # Scan tokens and print them
    lexer = Lexer(source_code)
    tokens, scan_time = lexer.scan_tokens()
    
    console.print(f"[bold cyan]Tokenization completed in[/] [yellow]{scan_time:.4f}[/] [bold cyan]ms[/]")
    print_tokens(tokens, console)


def run_calculator_demo(expression: str, console: Console):
    """Run a demonstration of the calculator with an expression."""
    console.print(Panel(f"[bold]Calculator Demo[/]", border_style="green"))
    
    # Create lexer and scan tokens
    lexer = Lexer(expression)
    tokens, scan_time = lexer.scan_tokens()
    
    # Print tokens
    print_tokens(tokens[:-1], console)  # Skip EOF token
    
    try:
        # Calculate result
        calculator = Calculator(tokens[:-1])  # Skip EOF token
        result, calc_time = calculator.calculate()
        
        # Print result
        print_calculation_result(expression, result, tokens[:-1], scan_time, calc_time, console)
    except Exception as e:
        console.print(Panel(f"[bold red]Error:[/] {str(e)}", title="[bold red]Calculation Error[/]", border_style="red"))


def main():
    console = Console()
    
    console.print(Panel.fit(
        "[bold yellow]Advanced Lexer & Calculator[/]",
        subtitle="[blue]© 2025[/]",
        padding=(2, 4),
        border_style="green"
    ))
    
    # Test the lexer with some example code
    sample = """
    # Define a function to calculate factorial
    def factorial(n)
        if n < 2 then
            1
        else
            n * factorial(n-1)
    
    # Call the function
    factorial(5)
    
    # Use some trigonometric functions
    extern sin(x);
    extern cos(x);
    
    # Calculate an expression with trigonometric functions
    3.14159 * sin(0.5) + 2 * cos(0)
    """
    
    run_lexer_demo(sample, console)
    
    console.print("\n")
    
    # Test simple expression calculation
    calc_samples = [
        "sin(1) - 1 + 3",
        "2 + 3 * 4 - 5 / 2",
        "sin(0.5) + cos(0)",
        "2 ^ 3 ^ 2",  # Test right associativity of power
        "sqrt(16) + pow(2, 3)"
    ]
    
    for sample in calc_samples:
        run_calculator_demo(sample, console)
        console.print("\n")


if __name__ == "__main__":
    main()
