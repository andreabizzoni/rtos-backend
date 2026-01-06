import tempfile
import threading
import wave
from pathlib import Path
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
from pynput import keyboard
from openai import OpenAI


class VoiceInput:
    def __init__(self, client: OpenAI):
        self.client = client
        self.sample_rate = 16000
        self.channels = 1
        self.is_recording = False
        self.audio_frames = []
        self.stream: Optional[sd.InputStream] = None
        self.listener: Optional[keyboard.Listener] = None
        self.temp_dir = Path(tempfile.gettempdir())
        self.on_transcription_complete: Optional[Callable[[str], None]] = None
        self.recording_lock = threading.Lock()

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if status:
            print(f"Audio status: {status}")
        if self.is_recording:
            self.audio_frames.append(indata.copy())

    def _on_space_press(self, key) -> bool:
        try:
            if key == keyboard.Key.space:
                with self.recording_lock:
                    if not self.is_recording:
                        # Start recording
                        self.is_recording = True
                        self.audio_frames = []
                        print("\nRecording... (press SPACE again to stop)", end="", flush=True)

                        # Start audio stream
                        try:
                            self.stream = sd.InputStream(
                                samplerate=self.sample_rate,
                                channels=self.channels,
                                dtype="float32",
                                callback=self._audio_callback,
                                blocksize=1024,
                            )
                            if self.stream:
                                self.stream.start()
                        except sd.PortAudioError as e:
                            print(f"\nAudio device error: {e}")
                            self.is_recording = False
                            self.stream = None
                    else:
                        # Stop recording
                        self.is_recording = False
                        print("\nProcessing...", end="", flush=True)

                        # Stop and close stream
                        if self.stream:
                            self.stream.stop()
                            self.stream.close()
                            self.stream = None

                        # Process audio if we have frames
                        if self.audio_frames:
                            threading.Thread(target=self._process_and_transcribe, daemon=True).start()
                        else:
                            print("\nNo audio recorded. Try again.")
        except Exception as e:
            print(f"\nError handling recording: {e}")
            self.is_recording = False
        return True

    def _process_and_transcribe(self) -> None:
        temp_file: Optional[Path] = None
        try:
            if not self.audio_frames:
                print("No audio frames to process.")
                return

            # Concatenate all audio frames
            audio_data = np.concatenate(self.audio_frames, axis=0)

            # Check if audio is too short (less than 1 second)
            if len(audio_data) < self.sample_rate * 1:
                print("Audio too short. Please record for at least 1 seconds.")
                return

            # Convert float32 to int16 PCM format
            audio_int16 = (audio_data * 32767).astype(np.int16)

            # Save to temporary WAV file
            temp_file = self.temp_dir / f"guido_voice_{threading.get_ident()}.wav"
            try:
                with wave.open(str(temp_file), "wb") as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(2)  # 2 bytes for int16
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_int16.tobytes())
            except Exception as e:
                print(f"\nError saving audio file: {e}")
                return

            # Transcribe using Whisper API
            try:
                with open(temp_file, "rb") as audio_file:
                    transcription = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text",
                    )
            except Exception as e:
                print(f"\nError calling Whisper API: {e}")
                return

            # Clean up temp file
            if temp_file and temp_file.exists():
                temp_file.unlink(missing_ok=True)

            # Call callback if set
            if self.on_transcription_complete:
                self.on_transcription_complete(transcription)
            else:
                print(f"\nTranscribed: {transcription}")

        except Exception as e:
            print(f"\nUnexpected error during transcription: {e}")
            if temp_file and temp_file.exists():
                temp_file.unlink(missing_ok=True)

    def start_listening(self) -> None:
        try:
            if self.listener and self.listener.running:
                return

            def on_press(key):
                try:
                    self._on_space_press(key)
                except Exception as e:
                    print(f"\nError handling key press: {e}")

            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
        except Exception as e:
            print(f"\nError starting keyboard listener: {e}")

    def stop_listening(self) -> None:
        if self.listener:
            self.listener.stop()

        with self.recording_lock:
            if self.is_recording and self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            self.is_recording = False

    def cleanup(self) -> None:
        """Clean up resources and temporary files."""
        self.stop_listening()
        # Clean up any remaining temp files
        for temp_file in self.temp_dir.glob("guido_voice_*.wav"):
            try:
                temp_file.unlink()
            except Exception:
                pass
