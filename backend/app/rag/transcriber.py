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
        Transcribes an audio file (16kHz WAV recommended).
        Uses Google Gemini multimodal audio recognition first for superior multilingual accuracy
        (English, Hindi, Marathi, Sanskrit), and falls back to local whisper.cpp.
        """
        from backend.app.config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=GEMINI_API_KEY)
                with open(audio_path, "rb") as f:
                    data = f.read()

                lang_name = (
                    "Hindi" if language == "hi"
                    else "Marathi" if language == "mr"
                    else "Sanskrit" if language == "sa"
                    else "English" if language == "en"
                    else "multilingual (English, Hindi, or Marathi)"
                )
                prompt = (
                    f"Listen carefully to this audio recording. The speaker is talking in {lang_name} regarding Ayurveda or health. "
                    "Transcribe the user's spoken words verbatim into text. "
                    "If the audio contains only silence, noise, breathing, or no discernible words, reply with strictly empty text. "
                    "Return ONLY the transcribed words. Do not include quotes, timestamps, or conversational commentary."
                )

                for model_candidate in ["gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]:
                    try:
                        res = client.models.generate_content(
                            model=model_candidate,
                            contents=[
                                types.Part.from_bytes(data=data, mime_type="audio/wav"),
                                prompt
                            ]
                        )
                        transcription = (res.text or "").strip()
                        if transcription.lower() in ["[blank_audio]", "[silence]", "empty", "(silence)", "none"]:
                            transcription = ""
                        return {
                            "text": transcription,
                            "language": language or "auto",
                            "engine": f"gemini ({model_candidate})"
                        }
                    except Exception as model_err:
                        print(f"[Transcriber] Gemini {model_candidate} error: {model_err}")
                        continue
            except Exception as e:
                print(f"[Transcriber] Gemini audio transcription error: {e}")

        # Fallback to local whisper.cpp if available
        if _PYWHISPERCPP_AVAILABLE:
            model = self.get_model()
            if model:
                try:
                    params = {}
                    if language and language not in ("auto", "sa"):
                        params["language"] = language

                    segments = model.transcribe(audio_path, **params)
                    raw_text = " ".join(
                        [seg.text.strip() for seg in segments if hasattr(seg, "text") and seg.text]
                    ).strip()
                    if raw_text.lower() in ["[blank_audio]", "[silence]", "(silence)"]:
                        raw_text = ""
                    return {
                        "text": raw_text,
                        "language": language or "auto",
                        "engine": "whisper.cpp",
                        "segments_count": len(segments)
                    }
                except Exception as e:
                    print(f"[WhisperCpp] Transcription error: {e}")

        return {
            "text": "",
            "error": "No speech detected or transcription service temporarily unavailable. Please type your query.",
            "language": language or "en"
        }

    def transcribe_bytes(
        self, audio_bytes: bytes, filename: str = "audio.wav", language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves bytes to a temporary file and runs transcription."""
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
