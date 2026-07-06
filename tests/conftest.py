import os
import sys
from unittest.mock import MagicMock

import pytest


os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("RESEND_API_KEY", "re_test")
os.environ.setdefault("RESEND_FROM_EMAIL", "test@example.com")
os.environ.setdefault("ALERT_EMAIL", "admin@example.com")
os.environ.setdefault("LASTFM_API_KEY", "test-lastfm-key")


_mock_stealth = MagicMock()
_mock_stealth.stealth_sync = MagicMock()
_mock_stealth.Stealth = MagicMock

_sync_playwright = MagicMock()
_sync_playwright.sync_playwright = MagicMock()

sys.modules.setdefault("playwright_stealth", _mock_stealth)
sys.modules.setdefault("playwright", MagicMock())
sys.modules.setdefault("playwright.sync_api", _sync_playwright)
