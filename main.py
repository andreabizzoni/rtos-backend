from app.agent import Agent
from app.tts import TextToSpeech
from app.voice_input import VoiceInput


def main() -> None:
    print("\nProgram starting")
    agent = Agent()
    tts = TextToSpeech(agent.client)
    voice_input: VoiceInput | None = None
    voice_mode = False

    def on_transcription(text: str) -> None:
        nonlocal agent, tts
        print(f"\nYou said: {text}")
        try:
            agent_answer = agent.answer(query=text, chat=False)
            print(f"\nGuido: {agent_answer}")
            # Speak the response
            tts.speak(agent_answer)
        except Exception as e:
            print(f"\nError processing query: {e}")

    while True:
        try:
            if not voice_mode:
                user_query = input("\nYou: ").strip()

                if not user_query:
                    continue

                if user_query.lower() in ["exit", "quit", "q"]:
                    break

                if user_query.lower() in ["voice", "v"]:
                    try:
                        voice_input = VoiceInput(agent.client)
                        voice_input.on_transcription_complete = on_transcription
                        voice_input.start_listening()
                        voice_mode = True
                        print("\nVoice mode activated! Press SPACE to start recording, press again to stop.")
                        print("\nType 'text' or 't' to return to text mode.\n")
                    except Exception as e:
                        print(f"\nError starting voice mode: {e}")
                    continue

                agent_answer = agent.answer(query=user_query, chat=True)
                print(f"\nGuido: {agent_answer}")

            else:
                user_input = input().strip().lower()
                if user_input in ["text", "t"]:
                    if voice_input:
                        voice_input.stop_listening()
                        voice_input.cleanup()
                        voice_input = None
                    voice_mode = False
                    print("\nSwitched to text mode.")
                elif user_input in ["exit", "quit", "q"]:
                    break

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n\nError while running Guido - {e}")

    if voice_input:
        voice_input.cleanup()

    print("\nProgram terminated\n")


if __name__ == "__main__":
    main()
