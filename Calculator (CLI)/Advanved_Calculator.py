"""
calculator_advanced.py
======================
A professional-grade CLI calculator featuring:
  • Full expression parser  (e.g. "3 + 4 * (2 - 1) ** 2")
  • Scientific functions     (sqrt, log, sin, cos, tan, …)
  • Built-in constants       (pi, e, tau, ans)
  • 5-slot memory system     (MS, MR, M+, M-, MC)
  • Timestamped history      with statistics & file export
  • Angle-mode toggle        (DEG / RAD)
  • ANSI colour terminal UI
  • Zero external dependencies (stdlib only)

Usage:
  python calculator_advanced.py
"""

# ─────────────────────────────────────────────────────────────────────────────
# STANDARD LIBRARY IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import math
import os
import csv
import sys
from datetime import datetime
from enum import Enum, auto
from typing import Optional


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 ─ ANSI COLOUR PALETTE
# Centralise all terminal-escape sequences so colours are changed in one place.
# ═════════════════════════════════════════════════════════════════════════════

class C:
    """ANSI colour / style constants."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"

    # Foreground colours
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # Bright variants
    BRED    = "\033[91m"
    BGREEN  = "\033[92m"
    BYELLOW = "\033[93m"
    BBLUE   = "\033[94m"
    BMAGENTA= "\033[95m"
    BCYAN   = "\033[96m"
    BWHITE  = "\033[97m"

    # Backgrounds
    BG_DARK = "\033[40m"
    BG_BLUE = "\033[44m"

    @staticmethod
    def strip_supported() -> bool:
        """Return True if the terminal likely supports ANSI codes."""
        return sys.stdout.isatty() and os.name != "nt" or (
            os.name == "nt" and "ANSICON" in os.environ
        )


# Disable colours on terminals that don't support them
if not C.strip_supported():
    for attr in vars(C):
        if not attr.startswith("_") and isinstance(getattr(C, attr), str):
            setattr(C, attr, "")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 ─ CALCULATOR MEMORY  (5-slot persistent memory bank)
# ═════════════════════════════════════════════════════════════════════════════

class CalculatorMemory:
    """
    Implements a 5-slot memory bank similar to physical calculators.

    Slots are numbered 1–5.  Standard operations:
      MS n value  – Memory Store   : save value in slot n
      MR n        – Memory Recall  : retrieve value from slot n
      M+ n value  – Memory Add    : add value to slot n
      M- n value  – Memory Sub    : subtract value from slot n
      MC n        – Memory Clear  : reset slot n to 0
      MCA         – Memory Clear All
    """

    SLOT_COUNT = 5

    def __init__(self) -> None:
        self._slots: list[float] = [0.0] * self.SLOT_COUNT

    # ── Validation ────────────────────────────────────────────────────────────
    def _check_slot(self, slot: int) -> None:
        if not (1 <= slot <= self.SLOT_COUNT):
            raise ValueError(f"Slot must be 1–{self.SLOT_COUNT}, got {slot}.")

    # ── Operations ────────────────────────────────────────────────────────────
    def store(self, slot: int, value: float) -> None:
        self._check_slot(slot)
        self._slots[slot - 1] = value

    def recall(self, slot: int) -> float:
        self._check_slot(slot)
        return self._slots[slot - 1]

    def add(self, slot: int, value: float) -> float:
        self._check_slot(slot)
        self._slots[slot - 1] += value
        return self._slots[slot - 1]

    def subtract(self, slot: int, value: float) -> float:
        self._check_slot(slot)
        self._slots[slot - 1] -= value
        return self._slots[slot - 1]

    def clear(self, slot: int) -> None:
        self._check_slot(slot)
        self._slots[slot - 1] = 0.0

    def clear_all(self) -> None:
        self._slots = [0.0] * self.SLOT_COUNT

    def snapshot(self) -> list[tuple[int, float]]:
        """Return a list of (slot_number, value) pairs for display."""
        return [(i + 1, v) for i, v in enumerate(self._slots)]


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 ─ HISTORY  (timestamped log with statistics & export)
# ═════════════════════════════════════════════════════════════════════════════

class HistoryEntry:
    """One immutable record in the calculation history."""
    __slots__ = ("expression", "result", "timestamp")

    def __init__(self, expression: str, result: float) -> None:
        self.expression: str      = expression
        self.result:     float    = result
        self.timestamp:  datetime = datetime.now()

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        return f"[{ts}]  {self.expression}  =  {fmt(self.result)}"


class CalculatorHistory:
    """
    Stores all calculations and provides statistical summaries and file export.
    """

    def __init__(self, max_entries: int = 100) -> None:
        self._entries: list[HistoryEntry] = []
        self._max: int = max_entries

    # ── Mutation ──────────────────────────────────────────────────────────────
    def add(self, expression: str, result: float) -> None:
        if len(self._entries) >= self._max:
            self._entries.pop(0)        # Drop oldest when full (FIFO)
        self._entries.append(HistoryEntry(expression, result))

    def clear(self) -> None:
        self._entries.clear()

    # ── Queries ───────────────────────────────────────────────────────────────
    def __len__(self) -> int:
        return len(self._entries)

    def recent(self, n: int = 10) -> list[HistoryEntry]:
        """Return the last n entries, newest first."""
        return list(reversed(self._entries[-n:]))

    def all_results(self) -> list[float]:
        return [e.result for e in self._entries]

    # ── Statistics ────────────────────────────────────────────────────────────
    def statistics(self) -> Optional[dict]:
        """Return a stats dict, or None if history is empty."""
        results = self.all_results()
        if not results:
            return None
        n = len(results)
        mean = sum(results) / n
        variance = sum((x - mean) ** 2 for x in results) / n
        return {
            "count":  n,
            "sum":    sum(results),
            "mean":   mean,
            "median": sorted(results)[n // 2],
            "min":    min(results),
            "max":    max(results),
            "std":    math.sqrt(variance),
        }

    # ── Export ────────────────────────────────────────────────────────────────
    def export_txt(self, filepath: str) -> int:
        """Write history as plain text. Returns number of lines written."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Calculator History — exported {datetime.now()}\n")
            f.write("=" * 55 + "\n")
            for entry in self._entries:
                f.write(str(entry) + "\n")
        return len(self._entries)

    def export_csv(self, filepath: str) -> int:
        """Write history as CSV. Returns number of rows written."""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "expression", "result"])
            for e in self._entries:
                writer.writerow([
                    e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    e.expression,
                    e.result,
                ])
        return len(self._entries)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 ─ EXPRESSION PARSER  (tokeniser + recursive-descent parser)
#
# Supports the full arithmetic grammar:
#   expr        →  additive
#   additive    →  multiplicative  ( ('+' | '-') multiplicative )*
#   multiplicative → power        ( ('*' | '/' | '//' | '%') power )*
#   power       →  unary          ( '**' unary )*          [right-assoc]
#   unary       →  ('-' | '+') unary  |  primary
#   primary     →  NUMBER | CONSTANT | FUNC '(' arglist ')' | '(' expr ')'
#
# Functions: sqrt, cbrt, abs, ceil, floor, round, log, log2, log10,
#            sin, cos, tan, asin, acos, atan, sinh, cosh, tanh,
#            degrees, radians, factorial, gcd, lcm, hypot, comb, perm
# Constants: pi, e, tau, phi, ans
# ═════════════════════════════════════════════════════════════════════════════

class TokenKind(Enum):
    NUMBER   = auto()
    IDENT    = auto()   # function name or constant
    PLUS     = auto()
    MINUS    = auto()
    STAR     = auto()
    SLASH    = auto()
    DSLASH   = auto()   # //
    PERCENT  = auto()
    DSTAR    = auto()   # **
    LPAREN   = auto()
    RPAREN   = auto()
    COMMA    = auto()
    EOF      = auto()


class Token:
    __slots__ = ("kind", "value")

    def __init__(self, kind: TokenKind, value=None) -> None:
        self.kind  = kind
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.kind.name}, {self.value!r})"


class Tokenizer:
    """Convert a raw expression string into a flat list of Token objects."""

    def __init__(self, text: str) -> None:
        self._text = text.strip()
        self._pos  = 0

    def _current(self) -> Optional[str]:
        return self._text[self._pos] if self._pos < len(self._text) else None

    def _advance(self) -> str:
        ch = self._text[self._pos]
        self._pos += 1
        return ch

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while (ch := self._current()) is not None:
            # Skip whitespace
            if ch.isspace():
                self._advance()
                continue

            # Numbers (integers and floats, including scientific notation)
            if ch.isdigit() or (ch == "." and self._peek_is_digit()):
                tokens.append(self._read_number())
                continue

            # Identifiers (function names and constants)
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_ident())
                continue

            # Two-character operators first
            two = self._text[self._pos : self._pos + 2]
            if two == "**":
                self._pos += 2
                tokens.append(Token(TokenKind.DSTAR))
                continue
            if two == "//":
                self._pos += 2
                tokens.append(Token(TokenKind.DSLASH))
                continue

            # Single-character operators / punctuation
            single_map = {
                "+": TokenKind.PLUS,
                "-": TokenKind.MINUS,
                "*": TokenKind.STAR,
                "/": TokenKind.SLASH,
                "%": TokenKind.PERCENT,
                "(": TokenKind.LPAREN,
                ")": TokenKind.RPAREN,
                ",": TokenKind.COMMA,
            }
            if ch in single_map:
                tokens.append(Token(single_map[self._advance()]))
                continue

            raise SyntaxError(
                f"Unexpected character '{ch}' at position {self._pos}."
            )

        tokens.append(Token(TokenKind.EOF))
        return tokens

    def _peek_is_digit(self) -> bool:
        return (
            self._pos + 1 < len(self._text)
            and self._text[self._pos + 1].isdigit()
        )

    def _read_number(self) -> Token:
        start = self._pos
        dot_seen = False
        while (ch := self._current()) is not None:
            if ch.isdigit():
                self._advance()
            elif ch == "." and not dot_seen:
                dot_seen = True
                self._advance()
            elif ch.lower() == "e" and self._pos > start:
                # Scientific notation: 1e10, 1.5e-3
                self._advance()
                if self._current() in ("+", "-"):
                    self._advance()
                if not (self._current() or "").isdigit():
                    raise SyntaxError("Malformed scientific notation.")
                while (self._current() or "").isdigit():
                    self._advance()
                break
            else:
                break
        return Token(TokenKind.NUMBER, float(self._text[start : self._pos]))

    def _read_ident(self) -> Token:
        start = self._pos
        while (ch := self._current()) is not None and (ch.isalnum() or ch == "_"):
            self._advance()
        return Token(TokenKind.IDENT, self._text[start : self._pos])


class ExpressionParser:
    """
    Recursive-descent parser.

    The `angle_mode` parameter controls whether trig functions expect degrees
    ('deg') or radians ('rad').  The `ans` parameter injects the last result
    as the constant `ans`.
    """

    # ── Built-in constants ────────────────────────────────────────────────────
    CONSTANTS: dict[str, float] = {
        "pi":  math.pi,
        "e":   math.e,
        "tau": math.tau,
        "phi": (1 + math.sqrt(5)) / 2,   # Golden ratio
        "inf": math.inf,
    }

    # ── Supported functions with their arities ────────────────────────────────
    # arity=1 → single argument;  arity=2 → two arguments
    FUNCTIONS: dict[str, dict] = {
        # Basic
        "sqrt":     {"arity": 1, "fn": math.sqrt},
        "cbrt":     {"arity": 1, "fn": lambda x: math.copysign(abs(x) ** (1/3), x)},
        "abs":      {"arity": 1, "fn": abs},
        "ceil":     {"arity": 1, "fn": math.ceil},
        "floor":    {"arity": 1, "fn": math.floor},
        "round":    {"arity": 1, "fn": round},
        # Logarithms
        "log":      {"arity": 1, "fn": math.log},
        "log2":     {"arity": 1, "fn": math.log2},
        "log10":    {"arity": 1, "fn": math.log10},
        "logb":     {"arity": 2, "fn": math.log},   # logb(x, base)
        # Trig (handled specially for angle-mode)
        "sin":      {"arity": 1, "trig": True},
        "cos":      {"arity": 1, "trig": True},
        "tan":      {"arity": 1, "trig": True},
        "asin":     {"arity": 1, "trig": True, "inverse": True},
        "acos":     {"arity": 1, "trig": True, "inverse": True},
        "atan":     {"arity": 1, "trig": True, "inverse": True},
        "atan2":    {"arity": 2, "fn": math.atan2},
        # Hyperbolic
        "sinh":     {"arity": 1, "fn": math.sinh},
        "cosh":     {"arity": 1, "fn": math.cosh},
        "tanh":     {"arity": 1, "fn": math.tanh},
        # Conversions
        "degrees":  {"arity": 1, "fn": math.degrees},
        "radians":  {"arity": 1, "fn": math.radians},
        # Combinatorics
        "factorial": {"arity": 1, "fn": lambda x: float(math.factorial(int(x)))},
        "gcd":      {"arity": 2, "fn": lambda a, b: float(math.gcd(int(a), int(b)))},
        "lcm":      {"arity": 2, "fn": lambda a, b: float(math.lcm(int(a), int(b)))},
        "comb":     {"arity": 2, "fn": lambda n, k: float(math.comb(int(n), int(k)))},
        "perm":     {"arity": 2, "fn": lambda n, k: float(math.perm(int(n), int(k)))},
        # Geometry
        "hypot":    {"arity": 2, "fn": math.hypot},
    }

    def __init__(
        self,
        tokens: list[Token],
        angle_mode: str = "deg",
        ans: float = 0.0,
        memory: Optional[CalculatorMemory] = None,
    ) -> None:
        self._tokens     = tokens
        self._pos        = 0
        self._angle_mode = angle_mode
        self._ans        = ans
        self._memory     = memory

    # ── Token navigation ──────────────────────────────────────────────────────
    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _consume(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, kind: TokenKind) -> Token:
        tok = self._consume()
        if tok.kind != kind:
            raise SyntaxError(
                f"Expected {kind.name}, got {tok.kind.name} ({tok.value!r})."
            )
        return tok

    # ── Grammar rules ─────────────────────────────────────────────────────────
    def parse(self) -> float:
        result = self._expr()
        if self._peek().kind != TokenKind.EOF:
            raise SyntaxError("Unexpected tokens after expression.")
        return result

    def _expr(self) -> float:
        """additive"""
        return self._additive()

    def _additive(self) -> float:
        left = self._multiplicative()
        while self._peek().kind in (TokenKind.PLUS, TokenKind.MINUS):
            op = self._consume().kind
            right = self._multiplicative()
            left = left + right if op == TokenKind.PLUS else left - right
        return left

    def _multiplicative(self) -> float:
        left = self._unary()
        while self._peek().kind in (
            TokenKind.STAR, TokenKind.SLASH,
            TokenKind.DSLASH, TokenKind.PERCENT,
        ):
            op = self._consume().kind
            right = self._power()
            if op == TokenKind.STAR:
                left *= right
            elif op == TokenKind.SLASH:
                if right == 0:
                    raise ZeroDivisionError("Division by zero.")
                left /= right
            elif op == TokenKind.DSLASH:
                if right == 0:
                    raise ZeroDivisionError("Floor-division by zero.")
                left = float(int(left) // int(right))
            elif op == TokenKind.PERCENT:
                if right == 0:
                    raise ZeroDivisionError("Modulo by zero.")
                left %= right
        return left

    def _power(self) -> float:
        # Right-associative: 2 ** 3 ** 2 == 2 ** (3 ** 2)
        # Base is _primary so that unary minus wraps the whole expression:
        #   -2 ** 2  →  -(2 ** 2)  = -4   (standard Python / math behaviour)
        #   (-2)**2  →  4          (explicit grouping still works)
        base = self._primary()
        if self._peek().kind == TokenKind.DSTAR:
            self._consume()
            exponent = self._unary()        # Exponent allows leading sign: 2**-1
            return base ** exponent
        return base

    def _unary(self) -> float:
        if self._peek().kind == TokenKind.MINUS:
            self._consume()
            return -self._unary()
        if self._peek().kind == TokenKind.PLUS:
            self._consume()
            return +self._unary()
        return self._power()                # Unary wraps _power, not _primary

    def _primary(self) -> float:
        tok = self._peek()

        # Parenthesised sub-expression
        if tok.kind == TokenKind.LPAREN:
            self._consume()
            val = self._expr()
            self._expect(TokenKind.RPAREN)
            return val

        # Numeric literal
        if tok.kind == TokenKind.NUMBER:
            self._consume()
            return tok.value

        # Identifier: constant, function, or 'ans' / 'mem'
        if tok.kind == TokenKind.IDENT:
            self._consume()
            name = tok.value.lower()

            # 'ans' → last result
            if name == "ans":
                return self._ans

            # Built-in constants
            if name in self.CONSTANTS:
                return self.CONSTANTS[name]

            # Memory recall shorthand:  mem1 … mem5
            if name.startswith("mem") and len(name) == 4 and name[3].isdigit():
                slot = int(name[3])
                if self._memory is None:
                    raise NameError("Memory not available.")
                return self._memory.recall(slot)

            # Function call
            if name in self.FUNCTIONS:
                return self._call_function(name)

            raise NameError(f"Unknown identifier '{name}'.")

        raise SyntaxError(f"Unexpected token: {tok!r}.")

    def _call_function(self, name: str) -> float:
        """Parse argument list and dispatch to the right math function."""
        meta = self.FUNCTIONS[name]
        self._expect(TokenKind.LPAREN)
        args = [self._expr()]
        while self._peek().kind == TokenKind.COMMA:
            self._consume()
            args.append(self._expr())
        self._expect(TokenKind.RPAREN)

        arity = meta["arity"]
        if len(args) != arity:
            raise TypeError(
                f"{name}() takes {arity} argument(s), got {len(args)}."
            )

        # Trig functions: apply degree ↔ radian conversion
        if meta.get("trig"):
            fn_map = {
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "asin": math.asin, "acos": math.acos, "atan": math.atan,
            }
            fn = fn_map[name]
            if meta.get("inverse"):
                result = fn(args[0])
                return math.degrees(result) if self._angle_mode == "deg" else result
            else:
                x = math.radians(args[0]) if self._angle_mode == "deg" else args[0]
                return fn(x)

        return meta["fn"](*args)


def evaluate(
    expression: str,
    angle_mode: str = "deg",
    ans: float = 0.0,
    memory: Optional[CalculatorMemory] = None,
) -> float:
    """Tokenise and parse an expression string, returning a float result."""
    tokens  = Tokenizer(expression).tokenize()
    parser  = ExpressionParser(tokens, angle_mode=angle_mode, ans=ans, memory=memory)
    return parser.parse()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 ─ DISPLAY  (all terminal-rendering helpers)
# ═════════════════════════════════════════════════════════════════════════════

WIDTH = 56   # Terminal column width for all panels


def fmt(value: float) -> str:
    """
    Smart number formatter:
      • Integers displayed without decimal point
      • Floats trimmed to 10 significant decimal places
      • ±inf / nan shown as words
    """
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "∞" if value > 0 else "-∞"
    if value == int(value) and abs(value) < 1e15:
        return f"{int(value):,}"
    formatted = f"{value:.10g}"
    if "e" in formatted.lower():
        return formatted                # Keep scientific notation as-is
    # Thousands separator for large floats
    parts = formatted.split(".")
    try:
        parts[0] = f"{int(parts[0]):,}"
    except ValueError:
        pass
    return ".".join(parts)


class Display:
    """All terminal-rendering helpers.  Nothing here does any calculation."""

    @staticmethod
    def clear() -> None:
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def rule(char: str = "─", color: str = C.DIM) -> None:
        print(f"{color}{char * WIDTH}{C.RESET}")

    @staticmethod
    def header(angle_mode: str, history_len: int, memory: CalculatorMemory) -> None:
        Display.clear()
        print()
        print(f"{C.BBLUE}{C.BOLD}{'':>4}⬛  ADVANCED CALCULATOR  ⬛{C.RESET}")
        Display.rule("═", C.BBLUE)

        # Status bar
        mode_tag  = (
            f"{C.BGREEN}● DEG{C.RESET}" if angle_mode == "deg"
            else f"{C.BMAGENTA}● RAD{C.RESET}"
        )
        hist_tag  = f"{C.DIM}History: {history_len}{C.RESET}"
        mem_vals  = [v for _, v in memory.snapshot() if v != 0.0]
        mem_tag   = f"{C.BYELLOW}MEM ●{C.RESET}" if mem_vals else f"{C.DIM}MEM ○{C.RESET}"

        print(f"  {mode_tag}    {hist_tag}    {mem_tag}")
        Display.rule()

    @staticmethod
    def prompt(ans: float) -> str:
        """Print the input prompt and return the stripped user input."""
        ans_str = f"  {C.DIM}ans = {fmt(ans)}{C.RESET}\n" if ans != 0.0 else ""
        if ans_str:
            print(ans_str, end="")
        raw = input(f"  {C.BCYAN}›{C.RESET} ").strip()
        return raw

    @staticmethod
    def result_panel(expression: str, result: float) -> None:
        Display.rule("─", C.DIM)
        print(f"  {C.DIM}{expression}{C.RESET}")
        print(f"  {C.BWHITE}{C.BOLD}= {C.BGREEN}{fmt(result)}{C.RESET}")
        Display.rule("─", C.DIM)

    @staticmethod
    def error(message: str) -> None:
        print(f"\n  {C.BRED}✖  {message}{C.RESET}\n")

    @staticmethod
    def info(message: str) -> None:
        print(f"\n  {C.BCYAN}ℹ  {message}{C.RESET}\n")

    @staticmethod
    def success(message: str) -> None:
        print(f"\n  {C.BGREEN}✔  {message}{C.RESET}\n")

    @staticmethod
    def memory_panel(memory: CalculatorMemory) -> None:
        print(f"\n  {C.BYELLOW}{C.BOLD}Memory Slots{C.RESET}")
        Display.rule("─", C.DIM)
        for slot, value in memory.snapshot():
            indicator = f"{C.BGREEN}●{C.RESET}" if value != 0.0 else f"{C.DIM}○{C.RESET}"
            print(f"  {indicator}  M{slot}  {fmt(value)}")
        Display.rule("─", C.DIM)

    @staticmethod
    def history_panel(history: CalculatorHistory, n: int = 10) -> None:
        print(f"\n  {C.BBLUE}{C.BOLD}Last {n} Calculations{C.RESET}")
        Display.rule("─", C.DIM)
        entries = history.recent(n)
        if not entries:
            print(f"  {C.DIM}No history yet.{C.RESET}")
        for i, entry in enumerate(entries, 1):
            ts  = entry.timestamp.strftime("%H:%M:%S")
            res = fmt(entry.result)
            print(
                f"  {C.DIM}{i:>2}. [{ts}]{C.RESET}  "
                f"{entry.expression}  "
                f"{C.BGREEN}= {res}{C.RESET}"
            )
        Display.rule("─", C.DIM)

    @staticmethod
    def stats_panel(stats: Optional[dict]) -> None:
        if stats is None:
            Display.info("No calculations to analyse yet.")
            return
        print(f"\n  {C.BMAGENTA}{C.BOLD}History Statistics{C.RESET}")
        Display.rule("─", C.DIM)
        rows = [
            ("Count",    str(stats["count"])),
            ("Sum",      fmt(stats["sum"])),
            ("Mean",     fmt(stats["mean"])),
            ("Median",   fmt(stats["median"])),
            ("Min",      fmt(stats["min"])),
            ("Max",      fmt(stats["max"])),
            ("Std Dev",  fmt(stats["std"])),
        ]
        for label, value in rows:
            print(f"  {C.DIM}{label:<10}{C.RESET}  {C.BWHITE}{value}{C.RESET}")
        Display.rule("─", C.DIM)

    @staticmethod
    def help_panel() -> None:
        sections = [
            ("Arithmetic Operators", [
                ("+ - * /",         "Basic four operations"),
                ("**",              "Exponentiation  (2 ** 8 = 256)"),
                ("//",              "Floor division   (7 // 2 = 3)"),
                ("%",               "Modulo           (10 % 3 = 1)"),
                ("( )",             "Grouping / precedence"),
            ]),
            ("Constants", [
                ("pi  e  tau  phi", "Mathematical constants"),
                ("ans",             "Previous result"),
                ("mem1 … mem5",     "Recall a memory slot"),
            ]),
            ("Scientific Functions", [
                ("sqrt(x)  cbrt(x)","Square / cube root"),
                ("abs(x)  ceil(x)  floor(x)", "Rounding"),
                ("log(x)  log2(x)  log10(x)", "Logarithms"),
                ("logb(x, b)",      "Log base b"),
                ("sin/cos/tan(x)",  "Trig (angle-mode aware)"),
                ("asin/acos/atan(x)","Inverse trig"),
                ("factorial(n)",    "n!  e.g. factorial(10)"),
                ("gcd(a,b)  lcm(a,b)", "GCD / LCM"),
                ("comb(n,k)  perm(n,k)","Combinations / Perms"),
                ("hypot(a,b)",      "Hypotenuse √(a²+b²)"),
            ]),
            ("Memory Commands", [
                ("ms n",            "Store ans in slot n (1–5)"),
                ("mr n",            "Recall slot n"),
                ("m+ n",            "Add ans to slot n"),
                ("m- n",            "Subtract ans from slot n"),
                ("mc n  |  mca",    "Clear slot n / all slots"),
            ]),
            ("App Commands", [
                ("help  h  ?",      "Show this help panel"),
                ("history  hist",   "Show recent calculations"),
                ("stats",           "Show result statistics"),
                ("mem",             "Show memory slots"),
                ("export txt|csv",  "Export history to file"),
                ("mode",            "Toggle DEG ↔ RAD"),
                ("clear  cls",      "Clear the screen"),
                ("reset",           "Clear history & memory"),
                ("exit  quit  q",   "Exit the calculator"),
            ]),
        ]
        print()
        for title, items in sections:
            print(f"  {C.BYELLOW}{C.BOLD}{title}{C.RESET}")
            Display.rule("─", C.DIM)
            for cmd, desc in items:
                print(
                    f"  {C.BCYAN}{cmd:<28}{C.RESET}"
                    f"  {C.DIM}{desc}{C.RESET}"
                )
            print()


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 ─ COMMAND HANDLER  (parses app commands that aren't expressions)
# ═════════════════════════════════════════════════════════════════════════════

def handle_command(
    raw: str,
    memory: CalculatorMemory,
    history: CalculatorHistory,
    ans: float,
    angle_mode: str,
) -> tuple[bool, str, float]:
    """
    Process a non-expression command.

    Returns:
        (handled, new_angle_mode, new_ans)
      • handled=True  means the input was a command and no expression eval needed
      • handled=False means the caller should try evaluating `raw` as an expression
    """
    cmd = raw.lower().strip()
    parts = cmd.split()

    # ── Navigation / display ──────────────────────────────────────────────────
    if cmd in ("help", "h", "?"):
        Display.help_panel()
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    if cmd in ("history", "hist"):
        Display.history_panel(history)
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    if cmd == "stats":
        Display.stats_panel(history.statistics())
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    if cmd == "mem":
        Display.memory_panel(memory)
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    if cmd in ("clear", "cls"):
        return True, angle_mode, ans       # Header re-draws on next loop

    # ── Mode toggle ───────────────────────────────────────────────────────────
    if cmd == "mode":
        new_mode = "rad" if angle_mode == "deg" else "deg"
        Display.success(f"Angle mode → {new_mode.upper()}")
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, new_mode, ans

    # ── Reset ─────────────────────────────────────────────────────────────────
    if cmd == "reset":
        history.clear()
        memory.clear_all()
        Display.success("History and memory cleared.")
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, 0.0

    # ── Export ────────────────────────────────────────────────────────────────
    if parts[0] == "export":
        fmt_arg = parts[1] if len(parts) > 1 else "txt"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if fmt_arg == "csv":
            path = f"calc_history_{timestamp}.csv"
            n    = history.export_csv(path)
        else:
            path = f"calc_history_{timestamp}.txt"
            n    = history.export_txt(path)
        Display.success(f"Exported {n} entries → {path}")
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    # ── Memory operations ─────────────────────────────────────────────────────
    if parts[0] == "ms" and len(parts) == 2:
        slot = int(parts[1])
        memory.store(slot, ans)
        Display.success(f"M{slot} ← {fmt(ans)}")
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    if parts[0] == "mr" and len(parts) == 2:
        slot = int(parts[1])
        val  = memory.recall(slot)
        Display.result_panel(f"MR{slot}", val)
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, val    # MR updates ans

    if parts[0] == "m+" and len(parts) == 2:
        slot = int(parts[1])
        val  = memory.add(slot, ans)
        Display.success(f"M{slot} += {fmt(ans)}  →  {fmt(val)}")
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    if parts[0] == "m-" and len(parts) == 2:
        slot = int(parts[1])
        val  = memory.subtract(slot, ans)
        Display.success(f"M{slot} -= {fmt(ans)}  →  {fmt(val)}")
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    if parts[0] == "mc":
        if len(parts) == 2:
            memory.clear(int(parts[1]))
            Display.success(f"M{parts[1]} cleared.")
        else:
            memory.clear_all()
            Display.success("All memory slots cleared.")
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    if cmd == "mca":
        memory.clear_all()
        Display.success("All memory slots cleared.")
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
        return True, angle_mode, ans

    # Not a recognised command → treat as expression
    return False, angle_mode, ans


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7 ─ MAIN APPLICATION LOOP
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    memory     = CalculatorMemory()
    history    = CalculatorHistory(max_entries=200)
    ans        = 0.0
    angle_mode = "deg"         # Default: degrees for trig functions

    while True:
        # ── Redraw header ──────────────────────────────────────────────────────
        Display.header(angle_mode, len(history), memory)

        # ── Input ──────────────────────────────────────────────────────────────
        try:
            raw = Display.prompt(ans)
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n  {C.BGREEN}👋  Goodbye!{C.RESET}\n")
            break

        if not raw:
            continue

        # ── Exit ───────────────────────────────────────────────────────────────
        if raw.lower() in ("exit", "quit", "q"):
            print(f"\n  {C.BGREEN}👋  Goodbye!  "
                  f"({len(history)} calculation(s) this session){C.RESET}\n")
            break

        # ── Try app command first ─────────────────────────────────────────────
        try:
            handled, angle_mode, ans = handle_command(
                raw, memory, history, ans, angle_mode
            )
        except (ValueError, IndexError):
            Display.error("Invalid command syntax.  Type 'help' for guidance.")
            input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
            continue

        if handled:
            continue

        # ── Evaluate as expression ────────────────────────────────────────────
        try:
            result = evaluate(raw, angle_mode=angle_mode, ans=ans, memory=memory)
        except ZeroDivisionError as exc:
            Display.error(f"Math error: {exc}")
            input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
            continue
        except (SyntaxError, NameError, TypeError, ValueError) as exc:
            Display.error(f"{type(exc).__name__}: {exc}")
            input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
            continue
        except Exception as exc:
            Display.error(f"Unexpected error: {exc}")
            input(f"  {C.DIM}Press Enter to continue…{C.RESET}")
            continue

        # ── Display and record ────────────────────────────────────────────────
        Display.result_panel(raw, result)
        history.add(raw, result)
        ans = result
        input(f"  {C.DIM}Press Enter to continue…{C.RESET}")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8 ─ ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()