"""
calculator.py
=============
A beginner-friendly CLI calculator that supports addition, subtraction,
multiplication, and division with continuous input and graceful error handling.

Author  : You
Project : CLI Calculator (GitHub Beginner Project)
"""

# ──────────────────────────────────────────────
# 1.  OPERATION FUNCTIONS
# ──────────────────────────────────────────────

def add(a: float, b: float) -> float:
    """Return the sum of a and b."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return the difference of a and b."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Return the product of a and b."""
    return a * b


def divide(a: float, b: float) -> float | None:
    """
    Return the quotient of a divided by b.
    Returns None if b is zero to prevent ZeroDivisionError.
    """
    if b == 0:
        return None          # Caller is responsible for handling this case
    return a / b


# ──────────────────────────────────────────────
# 2.  INPUT HELPERS
# ──────────────────────────────────────────────

def get_number(prompt: str) -> float:
    """
    Repeatedly ask the user for a number until a valid float is entered.
    This prevents the program from crashing on bad input.
    """
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print(f"  ⚠  '{raw}' is not a valid number. Please try again.\n")


def get_menu_choice(options: list[str]) -> str:
    """
    Display a numbered menu and return the user's validated choice.
    Accepts both the number and the symbol (e.g. '1' or '+').
    """
    while True:
        choice = input("  Your choice : ").strip()
        if choice in options:
            return choice
        print(f"  ⚠  Invalid choice '{choice}'. Pick from {options}.\n")


# ──────────────────────────────────────────────
# 3.  DISPLAY HELPERS
# ──────────────────────────────────────────────

def print_header() -> None:
    """Print the application banner."""
    print("\n" + "=" * 42)
    print("        🧮  CLI CALCULATOR  🧮")
    print("=" * 42)


def print_menu(previous_result: float | None) -> None:
    """Print the operation menu and, if available, the previous result."""
    print("\n  Select an operation:")
    print("  ┌─────────────────────────────┐")
    print("  │  1  +   Addition            │")
    print("  │  2  -   Subtraction         │")
    print("  │  3  *   Multiplication      │")
    print("  │  4  /   Division            │")
    print("  │  0  q   Quit                │")
    print("  └─────────────────────────────┘")

    if previous_result is not None:
        # Show the last answer so users can chain calculations
        print(f"  💾  Previous result : {format_result(previous_result)}")


def format_result(value: float) -> str:
    """
    Return a clean string for a float result:
      - If the value is a whole number, show it as an integer (e.g. 6 not 6.0).
      - Otherwise, show up to 10 significant decimal places with trailing
        zeros stripped.
    """
    if value == int(value):
        return str(int(value))
    return f"{value:.10f}".rstrip("0")


def print_result(a: float, op: str, b: float, result: float) -> None:
    """Print a nicely formatted equation with the result."""
    print("\n" + "-" * 42)
    print(f"  {format_result(a)}  {op}  {format_result(b)}  =  {format_result(result)}")
    print("-" * 42)


# ──────────────────────────────────────────────
# 4.  MAIN LOOP
# ──────────────────────────────────────────────

def main() -> None:
    """
    Drive the calculator:
      1. Show the menu.
      2. Read the chosen operation.
      3. Collect two numbers.
      4. Compute and display the result.
      5. Repeat until the user quits.
    """
    print_header()

    # Maps menu keys → (symbol, function)
    operations: dict[str, tuple[str, callable]] = {
        "1": ("+", add),
        "+": ("+", add),
        "2": ("-", subtract),
        "-": ("-", subtract),
        "3": ("*", multiply),
        "*": ("*", multiply),
        "4": ("/", divide),
        "/": ("/", divide),
    }

    quit_keys   = {"0", "q", "Q"}
    valid_keys  = list(operations.keys()) + list(quit_keys)

    previous_result: float | None = None   # Stores the last answer

    while True:
        # ── Show menu ──────────────────────────────
        print_menu(previous_result)

        # ── Get operation choice ───────────────────
        choice = get_menu_choice(valid_keys)

        if choice in quit_keys:
            print("\n  👋  Thanks for using CLI Calculator. Goodbye!\n")
            break                           # Exit the loop → program ends

        symbol, operation_func = operations[choice]

        # ── Get first number ───────────────────────
        # Offer to reuse the previous result to allow chaining (e.g. 10 + 5 → 15 / 3)
        if previous_result is not None:
            reuse = input(
                f"\n  Use previous result ({format_result(previous_result)}) "
                f"as first number? [y/n] : "
            ).strip().lower()

            if reuse == "y":
                first = previous_result
                print(f"  ✔  First number set to {format_result(first)}")
            else:
                first = get_number("\n  Enter first number  : ")
        else:
            first = get_number("\n  Enter first number  : ")

        # ── Get second number ──────────────────────
        second = get_number("  Enter second number : ")

        # ── Compute result ─────────────────────────
        result = operation_func(first, second)

        if result is None:
            # Division by zero was attempted
            print("\n  ❌  Error: Cannot divide by zero. Please try again.")
            continue                        # Skip to next iteration; don't update previous_result

        # ── Display result ─────────────────────────
        print_result(first, symbol, second, result)
        previous_result = result            # Save for next iteration


# ──────────────────────────────────────────────
# 5.  ENTRY POINT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    main()