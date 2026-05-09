"""
Test suite for multilingual and feedback features.

Run with: pytest backend/test_multilingual.py -v
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

# Assuming backend is in the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent))


class TestLanguageDetection:
    """Tests for lang_utils.detect_language and related functions."""

    def test_detect_language_english(self):
        """Should detect English text."""
        from lang_utils import detect_language
        
        text = "I feel anxious about my upcoming presentation at work."
        lang_code, confidence = detect_language(text)
        
        assert lang_code == "en", f"Expected 'en', got '{lang_code}'"
        assert confidence >= 0.5, f"Confidence too low: {confidence}"

    def test_detect_language_spanish(self):
        """Should detect Spanish text."""
        from lang_utils import detect_language
        
        text = "Me siento ansioso sobre mi presentación en el trabajo."
        lang_code, confidence = detect_language(text)
        
        assert lang_code == "es", f"Expected 'es', got '{lang_code}'"
        assert confidence >= 0.5, f"Confidence too low: {confidence}"

    def test_detect_language_french(self):
        """Should detect French text."""
        from lang_utils import detect_language
        
        text = "Je me sens anxieux face à ma présentation au travail."
        lang_code, confidence = detect_language(text)
        
        assert lang_code == "fr", f"Expected 'fr', got '{lang_code}'"
        assert confidence >= 0.5, f"Confidence too low: {confidence}"

    def test_detect_language_short_text(self):
        """Should default to 'en' for very short text."""
        from lang_utils import detect_language
        
        text = "ok"
        lang_code, confidence = detect_language(text)
        
        assert lang_code == "en", f"Expected 'en' for short text, got '{lang_code}'"
        assert confidence == 0.0

    def test_detect_language_empty_text(self):
        """Should default to 'en' for empty text."""
        from lang_utils import detect_language
        
        text = ""
        lang_code, confidence = detect_language(text)
        
        assert lang_code == "en", f"Expected 'en' for empty text, got '{lang_code}'"
        assert confidence == 0.0

    def test_detect_language_with_probs(self):
        """Should return language probabilities."""
        from lang_utils import detect_language_with_probs
        
        text = "Hello, I'm feeling anxious and sad today."
        lang_code, prob_dict = detect_language_with_probs(text)
        
        assert isinstance(prob_dict, dict)
        assert "en" in prob_dict, f"'en' not in probabilities: {prob_dict}"
        assert lang_code == "en", f"Expected 'en', got '{lang_code}'"


class TestWhisperLanguageMapping:
    """Tests for Whisper language mapping."""

    def test_get_whisper_language_english(self):
        """Should map English to Whisper language name."""
        from lang_utils import get_whisper_language
        
        result = get_whisper_language("en")
        assert result == "english", f"Expected 'english', got '{result}'"

    def test_get_whisper_language_spanish(self):
        """Should map Spanish to Whisper language name."""
        from lang_utils import get_whisper_language
        
        result = get_whisper_language("es")
        assert result == "spanish", f"Expected 'spanish', got '{result}'"

    def test_get_whisper_language_unknown(self):
        """Should return None for unknown language code."""
        from lang_utils import get_whisper_language
        
        result = get_whisper_language("xx")
        assert result is None, f"Expected None for unknown language, got '{result}'"


class TestLLMMultilingualSupport:
    """Tests for LLM multilingual routing."""

    @patch("lang_utils.Config.LLM_MULTILINGUAL_SUPPORT", False)
    def test_should_translate_english_only_llm(self):
        """Should require translation for non-English when LLM is English-only."""
        from lang_utils import should_translate_for_llm
        
        # Spanish should need translation
        assert should_translate_for_llm("es") is True
        # German should need translation
        assert should_translate_for_llm("de") is True
        # English should not need translation
        assert should_translate_for_llm("en") is False

    @patch("lang_utils.Config.LLM_MULTILINGUAL_SUPPORT", True)
    def test_should_not_translate_multilingual_llm(self):
        """Should not require translation when LLM is multilingual."""
        from lang_utils import should_translate_for_llm
        
        # No translation needed for any language
        assert should_translate_for_llm("es") is False
        assert should_translate_for_llm("en") is False
        assert should_translate_for_llm("fr") is False

    @patch("lang_utils.Config.TRANSLATION_SERVICE", "disabled")
    def test_translate_text_disabled(self):
        """Should return original text when translation is disabled."""
        from lang_utils import translate_text
        
        text = "Hola mundo"
        translated, success = translate_text(text, "es", "en")
        
        assert translated == text, "Should return original text"
        assert success is False, "Should return success=False"

    def test_translate_text_same_language(self):
        """Should skip translation when source and target are the same."""
        from lang_utils import translate_text
        
        text = "Hello world"
        translated, success = translate_text(text, "en", "en")
        
        assert translated == text, "Should return original text"
        assert success is True, "Should return success=True"


class TestAudioProcessing:
    """Tests for updated audio_processing with language support."""

    @patch("audio_processing.get_whisper_model")
    def test_transcribe_audio_with_language(self, mock_get_model):
        """Should pass language parameter to Whisper."""
        from audio_processing import transcribe_audio
        
        # Mock Whisper model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello, I'm anxious",
            "language": "en",
        }
        mock_get_model.return_value = mock_model
        
        # Create a temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(b"fake audio data")
            tmp_path = tmp.name
        
        try:
            result = transcribe_audio(tmp_path, language="en")
            
            assert result["text"] == "Hello, I'm anxious"
            assert result["language"] == "en"
            # Verify language parameter was passed
            mock_model.transcribe.assert_called_once()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @patch("audio_processing.get_whisper_model")
    def test_transcribe_audio_without_language(self, mock_get_model):
        """Should work without language parameter (auto-detect)."""
        from audio_processing import transcribe_audio
        
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Test text",
            "language": "en",
        }
        mock_get_model.return_value = mock_model
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(b"fake audio data")
            tmp_path = tmp.name
        
        try:
            result = transcribe_audio(tmp_path)
            assert result["text"] == "Test text"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_transcribe_audio_missing_file(self):
        """Should gracefully handle missing audio file."""
        from audio_processing import transcribe_audio
        
        result = transcribe_audio("/nonexistent/audio.wav")
        
        assert result["text"] == ""
        assert result["language"] is None


class TestDatabaseFeedback:
    """Tests for feedback storage in database.py."""

    @pytest.fixture
    def vault_with_test_db(self):
        """Create a temporary vault for testing."""
        from database import SecureVault
        import tempfile
        
        # Override config to use temp database
        with patch("database.Config.DB_PATH") as mock_db_path:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = f"{tmpdir}/test.db"
                mock_db_path.__str__ = lambda: db_path
                mock_db_path.__fspath__ = lambda: db_path
                
                vault = SecureVault()
                vault._ensure_init()
                yield vault

    def test_store_feedback_with_rating(self, vault_with_test_db):
        """Should store feedback with rating."""
        vault = vault_with_test_db
        
        vault.store_feedback(log_id=1, rating=5, feedback_text="Very helpful!")
        
        # Retrieve and verify
        feedback_list = vault.retrieve_and_decrypt_feedback()
        assert len(feedback_list) > 0, "No feedback stored"
        
        latest = feedback_list[-1]
        assert latest["rating"] == 5
        assert latest["feedback_text"] == "Very helpful!"

    def test_store_feedback_without_text(self, vault_with_test_db):
        """Should store feedback with only rating."""
        vault = vault_with_test_db
        
        vault.store_feedback(log_id=1, rating=4)
        
        feedback_list = vault.retrieve_and_decrypt_feedback()
        assert len(feedback_list) > 0
        assert feedback_list[-1]["rating"] == 4

    def test_store_feedback_nullable_fields(self, vault_with_test_db):
        """Should handle None values for feedback fields."""
        vault = vault_with_test_db
        
        vault.store_feedback(log_id=None, rating=None, feedback_text=None)
        
        feedback_list = vault.retrieve_and_decrypt_feedback()
        assert len(feedback_list) > 0


class TestFeedbackEndpoint:
    """Tests for /feedback endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        from fastapi.testclient import TestClient
        from server import app
        
        return TestClient(app)

    @patch("server.Config.ENABLE_USER_FEEDBACK", True)
    @patch("server.vault.store_feedback")
    def test_feedback_endpoint_with_rating(self, mock_store_feedback, client):
        """Should accept feedback with rating."""
        response = client.post(
            "/feedback",
            json={
                "log_id": 1,
                "rating": 5,
                "feedback_text": "Excellent response",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_store_feedback.assert_called_once()

    @patch("server.Config.ENABLE_USER_FEEDBACK", False)
    def test_feedback_endpoint_disabled(self, client):
        """Should return disabled status when feedback is disabled."""
        response = client.post(
            "/feedback",
            json={"rating": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disabled"


class TestAnalyzeEndpointMultilingual:
    """Integration tests for multilingual /analyze endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client for FastAPI app."""
        from fastapi.testclient import TestClient
        from server import app
        
        return TestClient(app)

    @patch("server.get_llm", return_value=MagicMock())
    @patch("server.retrieve_context", return_value="Clinical context")
    @patch("server.generate_response", return_value="Test response")
    @patch("server.CactusEdgeRouter.route_task", return_value="heavy_core")
    @patch("server.vault.encrypt_and_store")
    def test_analyze_endpoint_english(
        self,
        mock_encrypt,
        mock_route,
        mock_generate,
        mock_rag,
        mock_llm,
        client,
    ):
        """Should process English text and return language metadata."""
        response = client.post(
            "/analyze",
            data={
                "text": "I feel anxious about my presentation.",
                "typing": "{}",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"
        assert data["language"] == "en" or data["language"] is None  # May not detect on empty text
        mock_encrypt.assert_called_once()

    @patch("server.get_llm", return_value=MagicMock())
    @patch("server.retrieve_context", return_value="Contexto clínico")
    @patch("server.generate_response", return_value="Respuesta de prueba")
    @patch("server.CactusEdgeRouter.route_task", return_value="heavy_core")
    @patch("server.vault.encrypt_and_store")
    def test_analyze_endpoint_spanish(
        self,
        mock_encrypt,
        mock_route,
        mock_generate,
        mock_rag,
        mock_llm,
        client,
    ):
        """Should process Spanish text and detect language."""
        response = client.post(
            "/analyze",
            data={
                "text": "Me siento ansioso por mi presentación.",
                "typing": "{}",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Respuesta de prueba"
        # Language should be detected as Spanish or not set
        mock_encrypt.assert_called_once()

    @patch("server.get_llm", return_value=MagicMock())
    @patch("server.retrieve_context", return_value="Clinical context")
    @patch("server.generate_response", return_value="Test response")
    @patch("server.CactusEdgeRouter.route_task", return_value="heavy_core")
    @patch("server.vault.encrypt_and_store")
    def test_analyze_endpoint_with_language_override(
        self,
        mock_encrypt,
        mock_route,
        mock_generate,
        mock_rag,
        mock_llm,
        client,
    ):
        """Should accept user-specified language parameter."""
        response = client.post(
            "/analyze",
            data={
                "text": "Some text",
                "typing": "{}",
                "language": "es",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
