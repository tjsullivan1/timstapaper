"""
Tests for SSRF (Server-Side Request Forgery) protection in URL validation.
"""

import pytest
from services.article_service import extract_article_content, validate_url_for_ssrf


class TestSSRFProtection:
    """Test suite for SSRF protection logic."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost/secret",
            "http://localhost:8080/admin",
            "http://127.0.0.1/internal",
            "http://127.0.0.1:3000/api",
            "http://0.0.0.0/",
            "http://0.0.0.0:8000/health",
            "http://[::1]/ipv6-localhost",
        ],
    )
    def test_blocks_localhost(self, url):
        """Should block localhost addresses."""
        result = extract_article_content(url)

        assert result.content == ""
        assert (
            "localhost" in result.excerpt.lower() or "blocked" in result.excerpt.lower()
        )
        assert result.image_url is None

    @pytest.mark.parametrize(
        "url",
        [
            "http://192.168.0.1/router",
            "http://192.168.1.1/admin",
            "http://192.168.100.50/config",
            "http://192.168.255.255/",
        ],
    )
    def test_blocks_192_168_range(self, url):
        """Should block 192.168.x.x private IP range."""
        result = extract_article_content(url)

        assert "private network" in result.excerpt.lower()

    @pytest.mark.parametrize(
        "url",
        [
            "http://10.0.0.1/internal",
            "http://10.1.2.3/api",
            "http://10.255.255.255/",
        ],
    )
    def test_blocks_10_range(self, url):
        """Should block 10.x.x.x private IP range."""
        result = extract_article_content(url)

        assert "private network" in result.excerpt.lower()

    @pytest.mark.parametrize(
        "prefix",
        [
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
        ],
    )
    def test_blocks_172_16_to_31_range(self, prefix):
        """Should block 172.16.x.x - 172.31.x.x private IP range."""
        url = f"http://{prefix}0.1/internal"
        result = extract_article_content(url)

        assert "private network" in result.excerpt.lower()

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com/file",
            "file:///etc/passwd",
            "gopher://example.com/",
            "data:text/html,<script>alert(1)</script>",
            "javascript:alert(1)",
        ],
    )
    def test_blocks_non_http_schemes(self, url):
        """Should block non-HTTP/HTTPS URL schemes."""
        result = extract_article_content(url)

        assert result.content == ""
        assert "invalid url scheme" in result.excerpt.lower()

    @pytest.mark.parametrize(
        "url",
        [
            "http://172.15.0.1/allowed",  # Just outside the blocked range
            "http://172.32.0.1/allowed",  # Just outside the blocked range
        ],
    )
    def test_allows_non_private_172_ranges(self, url):
        """Should allow 172.x ranges outside 172.16-31."""
        # These should NOT be blocked as SSRF, though they may fail
        # for other reasons (network unreachable, etc.)
        is_valid, _ = validate_url_for_ssrf(url)
        assert is_valid

    def test_allows_http_scheme(self):
        """Should allow http:// scheme (will fail at network level, not SSRF check)."""
        result = extract_article_content("http://this-domain-does-not-exist-12345.com/")

        # Should not be blocked as invalid scheme
        assert "invalid url scheme" not in result.excerpt.lower()

    def test_allows_https_scheme(self):
        """Should allow https:// scheme (will fail at network level, not SSRF check)."""
        result = extract_article_content(
            "https://this-domain-does-not-exist-12345.com/"
        )

        # Should not be blocked as invalid scheme
        assert "invalid url scheme" not in result.excerpt.lower()
