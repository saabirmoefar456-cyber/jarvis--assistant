"""Speech-to-text and text-to-speech, kept as two small functions so the
rest of the assistant doesn't care how they're implemented.

- listen(): records from the default microphone after you press Enter,
  until you stop talking, and returns the transcribed text (via Google's
  free Web Speech API through the `speech_recognition` library — needs
  internet).
- speak(text): speaks `text` out loud using the OS's built-in TTS voice
  (via pyttsx3 — works offline, uses SAPI5 on Windows).
"""

from __future__ import annotations

import speech_recognition as sr


def listen(timeout: float = 8.0, phrase_time_limit: float = 20.0) -> str:
    """Record one utterance from the microphone and return the transcribed
    text, or raise an exception (sr.UnknownValueError / sr.WaitTimeoutError /
    sr.RequestError) if nothing usable was captured.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    return recognizer.recognize_google(audio)


class _Speaker:
    """Lazily-created pyttsx3 engine (importing/initializing it is slow, and
    unnecessary for pure text mode)."""

    _engine = None

    @classmethod
    def get(cls):
        if cls._engine is None:
            import pyttsx3

            cls._engine = pyttsx3.init()
        return cls._engine


def speak(text: str) -> None:
    if not text:
        return
    engine = _Speaker.get()
    engine.say(text)
    engine.runAndWait()
