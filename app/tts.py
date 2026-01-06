import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from openai import OpenAI


class TextToSpeech:
    def __init__(self, client: OpenAI):
        self.client = client
        self.voice = "cedar"
        self.model = "gpt-4o-mini-tts"
        self.temp_dir = Path(tempfile.gettempdir())

    def speak(self, text: str) -> None:
        if not text or not text.strip():
            return

        temp_file: Optional[Path] = None
        try:
            temp_file = self.temp_dir / "guido_speech_.mp3"
            with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
            ) as response:
                response.stream_to_file(str(temp_file))

            if not temp_file.exists() or temp_file.stat().st_size == 0:
                print("\nError: Audio file was not generated properly.")
                return

            subprocess.run(["afplay", str(temp_file)], check=True)

        except Exception as e:
            print(f"\nError generating or playing speech: {e}")

        finally:
            if temp_file and temp_file.exists():
                temp_file.unlink(missing_ok=True)
