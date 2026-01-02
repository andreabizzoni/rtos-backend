def main():
    print("\nProgram starting")
    while True:
        try:
            user_query = input("\nYou: ").strip()

            if not user_query:
                continue

            if user_query.lower() in ["exit", "quit", "q"]:
                break

            # Process query
            agent_answer = "blank_answer_here"

            print(f"\nGuido: {agent_answer}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n\nError while running Guido - {e}")

    print("\nProgram terminated\n")


if __name__ == "__main__":
    main()
