# Quiz_Game.py

def run_quiz():
    score = 0

    # Questions and answers
    questions = [
        {
            "question": "What does CPU stand for? ",
            "answer": "central processing unit"
        },
        {
            "question": "What does RAM stand for? ",
            "answer": "random access memory"
        },
        {
            "question": "What does GPU stand for? ",
            "answer": "graphics processing unit"
        },
        {
            "question": "What does HTML stand for? ",
            "answer": "hypertext markup language"
        }
    ]

    print("Welcome to the Quiz Game!\n")

    for q in questions:
        user_answer = input(q["question"]).strip().lower()

        if user_answer == q["answer"]:
            print("Correct!\n")
            score += 1
        else:
            print(f"Wrong! Correct answer is: {q['answer']}\n")

    print(f"Your final score: {score}/{len(questions)}")


# Main program
if __name__ == "__main__":
    run_quiz()
