"""
main.py
=======
Application entry point.

Responsibilities:
  • Main menu (Play / Leaderboard / How to Play / Quit)
  • Difficulty selection screen
  • Driving the game loop (collect guess → show feedback → repeat)
  • Post-game screen (reveal secret, show score, offer replay)
  • Graceful Ctrl+C / EOF handling

All game logic lives in game.py.
All persistence lives in score_manager.py.
All I/O utilities live in utils.py.
"""

import sys

from game import DIFFICULTIES, GameSession
from score_manager import ScoreManager, calculate_score
from utils import (
    Color, Timer,
    header, section, rule,
    get_int_input, get_choice, confirm,
    print_success, print_error, print_info, print_warning,
    format_duration, format_score,
)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

APP_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: HOW TO PLAY
# ─────────────────────────────────────────────────────────────────────────────

def show_how_to_play() -> None:
    """Display the rules and feature overview."""
    header()
    section("📖  HOW TO PLAY")

    lines = [
        ("Goal",        "Guess the secret number before you run out of attempts."),
        ("Feedback",    "After each guess you'll see: Too High ▼ or Too Low ▲."),
        ("Hot / Cold",  "A proximity label (🔥 Scorching → 🧊 Cold) tells you how close you are."),
        ("Hints",       "After a few failed attempts, automatic hints will appear."),
        ("Score",       "Win faster with fewer guesses for a higher score."),
        ("High Scores", "Your best scores are saved to scores.json automatically."),
    ]

    for label, desc in lines:
        print(f"  {Color.BYELLOW}{Color.BOLD}{label:<14}{Color.RESET}{desc}")

    section("🎯  DIFFICULTY LEVELS")

    for key, cfg in DIFFICULTIES.items():
        attempts = cfg.attempts_display
        hint_str = ", ".join(
            f"after attempt {n}" for n in cfg.hint_at
        )
        print(f"  {cfg.label:<30} Range: {cfg.range_min}–{cfg.range_max}  |  "
              f"Attempts: {attempts}")
        print(f"  {Color.DIM}  Hints: {hint_str}{Color.RESET}")
        print()

    input(f"  {Color.DIM}Press Enter to return to the main menu…{Color.RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: DIFFICULTY SELECTION
# ─────────────────────────────────────────────────────────────────────────────

def select_difficulty() -> str | None:
    """
    Show the difficulty menu and return the chosen key ("easy"/"medium"/"hard").
    Returns None if the user wants to go back to the main menu.
    """
    header()
    section("🎮  SELECT DIFFICULTY")

    menu_items = [
        ("1", "easy",   "Range 1–50   |  Unlimited attempts  |  Best for learning"),
        ("2", "medium", "Range 1–100  |  10 attempts          |  Standard challenge"),
        ("3", "hard",   "Range 1–200  |  7 attempts           |  For the brave"),
        ("b", None,     "Back to main menu"),
    ]

    for key, diff_key, desc in menu_items:
        if diff_key:
            cfg   = DIFFICULTIES[diff_key]
            label = cfg.label
        else:
            label = f"{Color.DIM}Back{Color.RESET}"
        print(f"  [{Color.BCYAN}{key}{Color.RESET}]  {label:<40}  {Color.DIM}{desc}{Color.RESET}")

    print()
    choice = get_choice(
        "Choose a difficulty",
        valid_choices=["1", "2", "3", "b"],
    )

    diff_map = {"1": "easy", "2": "medium", "3": "hard", "b": None}
    return diff_map[choice]


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN: IN-GAME LOOP
# ─────────────────────────────────────────────────────────────────────────────

def run_game(difficulty_key: str, score_manager: ScoreManager) -> None:
    """
    Run a full game session for the given difficulty, then show the post-game
    screen and offer a replay.
    """
    config  = DIFFICULTIES[difficulty_key]
    session = GameSession(
        config      = config,
        score_fn    = calculate_score,
        timer_class = Timer,
    )

    # ── Pre-game briefing ─────────────────────────────────────────────────────
    header()
    section(f"🎯  {config.label} — NEW GAME")

    print(f"  I'm thinking of a number between "
          f"{Color.BMAGENTA}{config.range_min}{Color.RESET} and "
          f"{Color.BMAGENTA}{config.range_max}{Color.RESET}.")

    attempts_msg = (
        f"  You have {Color.BGREEN}unlimited{Color.RESET} attempts."
        if config.max_attempts is None
        else f"  You have {Color.BYELLOW}{config.max_attempts}{Color.RESET} attempts."
    )
    print(attempts_msg)
    print(f"  {Color.DIM}Hints will appear automatically. Good luck!{Color.RESET}")
    rule("─", Color.DIM)

    # ── Guess loop ────────────────────────────────────────────────────────────
    while not session.is_finished:
        session.print_status_bar()

        guess = get_int_input(
            f"Enter your guess ({config.range_min}–{config.range_max}):",
            min_val = config.range_min,
            max_val = config.range_max,
        )

        outcome = session.make_guess(guess)

        if outcome["status"] == "correct":
            _show_win_screen(outcome["result"], score_manager)
            break

        if outcome["status"] == "out_of_attempts":
            _show_loss_screen(outcome["result"])
            break

        # ── Standard feedback (not finished yet) ─────────────────────────────
        session.print_feedback(outcome)

    # ── Offer replay ──────────────────────────────────────────────────────────
    print()
    if confirm("Play again?"):
        run_game(difficulty_key, score_manager)    # Recurse for a fresh session


# ─────────────────────────────────────────────────────────────────────────────
# POST-GAME SCREENS
# ─────────────────────────────────────────────────────────────────────────────

def _show_win_screen(result, score_manager: ScoreManager) -> None:
    """Print the victory screen and record the score."""
    header()

    # Big win banner
    print(f"\n  {Color.BGREEN}{Color.BOLD}")
    print("  ╔══════════════════════════════════╗")
    print("  ║   🎉  CORRECT!  YOU WIN!  🎉    ║")
    print("  ╚══════════════════════════════════╝")
    print(f"{Color.RESET}")

    print(f"  The secret number was "
          f"{Color.BMAGENTA}{Color.BOLD}{result.secret}{Color.RESET}.")
    print(f"  You got it in {Color.BYELLOW}{result.attempts_used}{Color.RESET} "
          f"attempt(s) in {Color.BYELLOW}{format_duration(result.elapsed)}{Color.RESET}.")

    # Show guess journey
    if len(result.guess_history) > 1:
        journey = " → ".join(
            f"{Color.DIM}{g}{Color.RESET}" if g != result.secret
            else f"{Color.BGREEN}{Color.BOLD}{g}{Color.RESET}"
            for g in result.guess_history
        )
        print(f"\n  Your guesses:  {journey}")

    # Record and display score
    new_diff, new_alltime = score_manager.record(
        difficulty      = result.difficulty,
        score           = result.score,
        attempts_used   = result.attempts_used,
        elapsed_seconds = result.elapsed,
        won             = True,
    )
    score_manager.display_post_game(
        difficulty      = result.difficulty,
        score           = result.score,
        attempts_used   = result.attempts_used,
        elapsed         = result.elapsed,
        new_diff_record = new_diff,
        new_alltime_record = new_alltime,
    )


def _show_loss_screen(result) -> None:
    """Print the defeat screen."""
    header()

    print(f"\n  {Color.BRED}{Color.BOLD}")
    print("  ╔══════════════════════════════════╗")
    print("  ║   💀  OUT OF ATTEMPTS!  💀       ║")
    print("  ╚══════════════════════════════════╝")
    print(f"{Color.RESET}")

    print(f"  The secret number was "
          f"{Color.BMAGENTA}{Color.BOLD}{result.secret}{Color.RESET}. "
          f"Better luck next time!")

    if result.guess_history:
        closest = min(result.guess_history, key=lambda g: abs(g - result.secret))
        diff    = abs(closest - result.secret)
        print(f"  Your closest guess was "
              f"{Color.BYELLOW}{closest}{Color.RESET} "
              f"(only {Color.BYELLOW}{diff}{Color.RESET} away!).")

    rule("─", Color.DIM)
    print(f"  {Color.DIM}Score: 0 pts (no points for a loss){Color.RESET}")
    rule("─", Color.DIM)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────────────────────

def main_menu(score_manager: ScoreManager) -> None:
    """
    Display the main menu and route to the appropriate screen.
    Loops until the user chooses to quit.
    """
    while True:
        header()
        print(f"  {Color.DIM}v{APP_VERSION}{Color.RESET}\n")

        menu = [
            ("1", "▶  Play Game"),
            ("2", "🏆  Leaderboard"),
            ("3", "📖  How to Play"),
            ("q", "✖  Quit"),
        ]

        for key, label in menu:
            color = Color.BGREEN if key == "1" else Color.BCYAN if key != "q" else Color.DIM
            print(f"  [{Color.BCYAN}{key}{Color.RESET}]  {color}{label}{Color.RESET}")

        print()
        choice = get_choice("Select an option", valid_choices=["1", "2", "3", "q"])

        if choice == "1":
            diff = select_difficulty()
            if diff:
                run_game(diff, score_manager)

        elif choice == "2":
            header()
            score_manager.display_leaderboard()
            input(f"  {Color.DIM}Press Enter to return to the main menu…{Color.RESET}")

        elif choice == "3":
            show_how_to_play()

        elif choice == "q":
            header()
            print(f"\n  {Color.BGREEN}{Color.BOLD}Thanks for playing! See you next time. 👋{Color.RESET}\n")
            break


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Bootstrap the application."""
    score_manager = ScoreManager(filepath="scores.json")

    try:
        main_menu(score_manager)
    except (KeyboardInterrupt, EOFError):
        # Handle Ctrl+C gracefully instead of printing a traceback
        print(f"\n\n  {Color.BGREEN}Interrupted. Goodbye! 👋{Color.RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()