import sys
from agent.core import Agent


def main():
    # Avoid Windows cp1252 crashes on LLM punctuation (e.g. non-breaking hyphen)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    agent = Agent()
    print("Job Search Agent. Type 'quit' to exit.")
    while True:
        user_text = input("\nYou: ").strip()
        if not user_text:
            continue
        if user_text.lower() in {"quit", "exit", "q"}:
            print("Bye.")
            break
        print("\nAgent:")
        agent.run(user_text)


if __name__ == "__main__":
    main()
