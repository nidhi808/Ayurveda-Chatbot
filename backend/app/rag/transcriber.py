import os
import io
import wave
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

# We use pywhispercpp for whisper.cpp C++ bindings
class WhisperCppTranscriber:
    """Provides speech-to-text transcription using whisper.cpp."""

    def __init__(self, model_name: str = "tiny"):
        self.model_name = model_name
        self._model = None
        self._initialized = False

    def get_model(self):
        """Lazy loader for whisper.cpp model."""
        if not self._initialized:
            try:
                from pywhispercpp.model import Model
                print(f"[WhisperCpp] Initializing whisper.cpp with model '{self.model_name}'...")
                self._model = Model(self.model_name, n_threads=4)
                self._initialized = True
                print("[WhisperCpp] Model loaded successfully.")
            except Exception as e:
                print(f"[WhisperCpp] Warning: Could not initialize pywhispercpp Model: {e}")
                self._model = None
                self._initialized = True
        return self._model

    def transcribe_file(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes an audio file (16kHz WAV recommended) using whisper.cpp.
        """
        model = self.get_model()
        if not model:
            return {
                "text": "",
                "error": "whisper.cpp model not initialized",
                "language": language or "en"
            }

        try:
            params = {}
            if language and language != "auto":
                params["language"] = language

            segments = model.transcribe(audio_path, **params)
            full_text = " ".join([seg.text.strip() for seg in segments if hasattr(seg, 'text') and seg.text])
            return {
                "text": full_text.strip(),
                "language": language or "auto",
                "segments_count": len(segments)
            }
        except Exception as e:
            print(f"[WhisperCpp] Transcription error: {e}")
            return {
                "text": "",
                "error": str(e),
                "language": language or "auto"
            }

    def transcribe_bytes(self, audio_bytes: bytes, filename: str = "audio.wav", language: Optional[str] = None) -> Dict[str, Any]:
        """Saves bytes to temporary file and runs whisper.cpp transcription."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            result = self.transcribe_file(tmp_path, language=language)
            return result
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

# Global transcriber instance
whisper_transcriber = WhisperCppTranscriber()
