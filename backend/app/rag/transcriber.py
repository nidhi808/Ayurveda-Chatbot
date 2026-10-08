import os
import tempfile
from typing import Optional, Dict, Any

# Try importing pywhispercpp — it requires native C++ build tools.
# On Windows this may fail if the C++ toolchain is missing. We handle that gracefully.
try:
    from pywhispercpp.model import Model as _WhisperModel
    _PYWHISPERCPP_AVAILABLE = True
except Exception as _whisper_import_err:
    _WhisperModel = None
    _PYWHISPERCPP_AVAILABLE = False
    print(
        f"[WhisperCpp] Warning: pywhispercpp could not be imported: {_whisper_import_err}\n"
        "  Voice transcription will be unavailable.\n"
        "  On Windows, install Visual C++ Build Tools and re-run: pip install pywhispercpp\n"
        "  See: https://github.com/absadiki/pywhispercpp#installation"
    )


class WhisperCppTranscriber:
    """Provides speech-to-text transcription using whisper.cpp.

    Gracefully degrades on Windows / environments where pywhispercpp
    cannot be compiled, returning a descriptive error instead of crashing.
    """

    def __init__(self, model_name: str = "tiny"):
        self.model_name = model_name
        self._model = None
        self._initialized = False

    @property
    def available(self) -> bool:
        """Returns True if pywhispercpp was successfully imported."""
        return _PYWHISPERCPP_AVAILABLE

    def get_model(self):
        """Lazy loader for whisper.cpp model."""
        if not self._initialized:
            if not _PYWHISPERCPP_AVAILABLE:
                self._model = None
                self._initialized = True
                return None
            try:
                print(f"[WhisperCpp] Initializing whisper.cpp with model '{self.model_name}'...")
                self._model = _WhisperModel(self.model_name, n_threads=4)
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
        Returns a dict with 'text', and optionally 'error' and 'language'.
        """
        if not _PYWHISPERCPP_AVAILABLE:
            return {
                "text": "",
                "error": (
                    "pywhispercpp is not available on this system. "
                    "On Windows, install Visual C++ Build Tools and re-run: pip install pywhispercpp"
                ),
                "language": language or "en"
            }

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
            full_text = " ".join(
                [seg.text.strip() for seg in segments if hasattr(seg, "text") and seg.text]
            )
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

    def transcribe_bytes(
        self, audio_bytes: bytes, filename: str = "audio.wav", language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves bytes to a temporary file and runs whisper.cpp transcription."""
        if not _PYWHISPERCPP_AVAILABLE:
            return {
                "text": "",
                "error": (
                    "pywhispercpp is not available on this system. "
                    "On Windows, install Visual C++ Build Tools and re-run: pip install pywhispercpp"
                ),
                "language": language or "en"
            }

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            return self.transcribe_file(tmp_path, language=language)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass


# Global transcriber instance
whisper_transcriber = WhisperCppTranscriber()
