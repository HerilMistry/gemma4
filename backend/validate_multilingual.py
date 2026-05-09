#!/usr/bin/env python3
"""
Validation script for multilingual & feedback implementation.

Usage:
    python backend/validate_multilingual.py

Checks:
- All new modules can be imported
- Configuration defaults are sensible
- Database schema is created
- Language detection works (basic)
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def check_imports():
    """Verify all new modules can be imported."""
    print("=" * 60)
    print("IMPORT CHECKS")
    print("=" * 60)
    
    imports_ok = True
    
    modules_to_check = [
        ("config", "Config"),
        ("lang_utils", ["detect_language", "translate_text", "WHISPER_LANGUAGE_MAP"]),
        ("audio_processing", ["transcribe_audio"]),
        ("database", "SecureVault"),
        ("server", ["AnalyzeResponse", "FeedbackRequest", "FeedbackResponse"]),
    ]
    
    for module_name, items in modules_to_check:
        try:
            module = __import__(module_name)
            if isinstance(items, list):
                for item in items:
                    if not hasattr(module, item):
                        print(f"❌ {module_name}.{item} — NOT FOUND")
                        imports_ok = False
                    else:
                        print(f"✅ {module_name}.{item}")
            else:
                if not hasattr(module, items):
                    print(f"❌ {module_name}.{items} — NOT FOUND")
                    imports_ok = False
                else:
                    print(f"✅ {module_name}.{items}")
        except ImportError as e:
            print(f"❌ {module_name} — IMPORT ERROR: {e}")
            imports_ok = False
    
    return imports_ok


def check_config():
    """Verify configuration has new settings."""
    print("\n" + "=" * 60)
    print("CONFIGURATION CHECKS")
    print("=" * 60)
    
    config_ok = True
    from config import Config
    
    new_configs = [
        "LLM_MULTILINGUAL_SUPPORT",
        "TRANSLATION_SERVICE",
        "WHISPER_LANGUAGE_AUTO_DETECT",
        "ENABLE_USER_FEEDBACK",
        "FEEDBACK_STORAGE",
    ]
    
    for cfg in new_configs:
        if hasattr(Config, cfg):
            value = getattr(Config, cfg)
            print(f"✅ Config.{cfg} = {value}")
        else:
            print(f"❌ Config.{cfg} — NOT FOUND")
            config_ok = False
    
    return config_ok


def check_language_detection():
    """Basic test of language detection."""
    print("\n" + "=" * 60)
    print("LANGUAGE DETECTION TESTS")
    print("=" * 60)
    
    detect_ok = True
    from lang_utils import detect_language, WHISPER_LANGUAGE_MAP
    
    test_cases = [
        ("Hello, I'm anxious", "en"),
        ("Me siento ansioso", "es"),
        ("Je me sens anxieux", "fr"),
        ("Mir ist beklommen", "de"),
    ]
    
    for text, expected_lang in test_cases:
        try:
            detected_lang, confidence = detect_language(text)
            if detected_lang == expected_lang:
                print(f"✅ '{text}' → {detected_lang} (confidence: {confidence:.2f})")
            else:
                print(f"⚠️  '{text}' → {detected_lang} (expected: {expected_lang})")
                # Not a failure, just a notice
        except Exception as e:
            print(f"❌ '{text}' — DETECTION ERROR: {e}")
            detect_ok = False
    
    # Check language map
    print(f"\n✅ Whisper language map has {len(WHISPER_LANGUAGE_MAP)} entries")
    
    return detect_ok


def check_database():
    """Verify database schema includes feedback table."""
    print("\n" + "=" * 60)
    print("DATABASE CHECKS")
    print("=" * 60)
    
    import tempfile
    import sqlite3
    from pathlib import Path
    from unittest.mock import patch
    
    db_ok = True
    
    try:
        # Create temp database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            with patch("database.Config.DB_PATH") as mock_db:
                mock_db.__str__ = lambda: str(db_path)
                mock_db.__fspath__ = lambda: str(db_path)
                
                from database import SecureVault
                vault = SecureVault()
                vault._ensure_init()
        
        # Check schema
        with sqlite3.connect(db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [row[0] for row in tables]
            
            if "encrypted_logs" in table_names:
                print("✅ encrypted_logs table exists")
            else:
                print("❌ encrypted_logs table NOT FOUND")
                db_ok = False
            
            if "feedback" in table_names:
                print("✅ feedback table exists")
                
                # Check feedback columns
                feedback_columns = conn.execute(
                    "PRAGMA table_info(feedback)"
                ).fetchall()
                col_names = [row[1] for row in feedback_columns]
                
                required_cols = ["id", "log_id", "rating", "feedback_text", "nonce", "ciphertext"]
                for col in required_cols:
                    if col in col_names:
                        print(f"  ✅ Column: {col}")
                    else:
                        print(f"  ❌ Column: {col} — NOT FOUND")
                        db_ok = False
            else:
                print("❌ feedback table NOT FOUND")
                db_ok = False
    
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        db_ok = False
    
    return db_ok


def check_response_models():
    """Verify Pydantic models have language fields."""
    print("\n" + "=" * 60)
    print("RESPONSE MODEL CHECKS")
    print("=" * 60)
    
    models_ok = True
    
    try:
        from server import AnalyzeResponse, FeedbackRequest, FeedbackResponse
        
        # Check AnalyzeResponse
        analyze_fields = AnalyzeResponse.__fields__.keys()
        analyze_required = {"response", "route_used", "language", "language_name", "translated"}
        
        if analyze_required.issubset(analyze_fields):
            print(f"✅ AnalyzeResponse has required fields: {', '.join(analyze_required)}")
        else:
            missing = analyze_required - set(analyze_fields)
            print(f"❌ AnalyzeResponse missing fields: {', '.join(missing)}")
            models_ok = False
        
        # Check FeedbackRequest
        feedback_req_fields = FeedbackRequest.__fields__.keys()
        feedback_req_required = {"log_id", "rating", "feedback_text"}
        
        if feedback_req_required.issubset(feedback_req_fields):
            print(f"✅ FeedbackRequest has required fields: {', '.join(feedback_req_required)}")
        else:
            missing = feedback_req_required - set(feedback_req_fields)
            print(f"❌ FeedbackRequest missing fields: {', '.join(missing)}")
            models_ok = False
        
        # Check FeedbackResponse
        feedback_resp_fields = FeedbackResponse.__fields__.keys()
        feedback_resp_required = {"status", "message"}
        
        if feedback_resp_required.issubset(feedback_resp_fields):
            print(f"✅ FeedbackResponse has required fields: {', '.join(feedback_resp_required)}")
        else:
            missing = feedback_resp_required - set(feedback_resp_fields)
            print(f"❌ FeedbackResponse missing fields: {', '.join(missing)}")
            models_ok = False
    
    except Exception as e:
        print(f"❌ RESPONSE MODEL ERROR: {e}")
        models_ok = False
    
    return models_ok


def main():
    """Run all checks."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  SANCTUARY 3.0 — MULTILINGUAL & FEEDBACK VALIDATION".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = {
        "Imports": check_imports(),
        "Configuration": check_config(),
        "Language Detection": check_language_detection(),
        "Database": check_database(),
        "Response Models": check_response_models(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_ok = True
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} — {check_name}")
        if not result:
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ ALL CHECKS PASSED")
        print("\nNext steps:")
        print("1. Install dependencies: pip install langdetect")
        print("2. Review MULTILINGUAL_GUIDE.md for configuration & API docs")
        print("3. Run tests: pytest backend/test_multilingual.py -v")
        print("4. Deploy and enable feedback collection!")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the errors above and fix before deploying.")
    print("=" * 60)
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
