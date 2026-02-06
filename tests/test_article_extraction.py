"""
Tests for article content extraction functionality.
"""

from unittest.mock import patch

from services.article_service import extract_article_content


class TestArticleExtraction:
    """Test suite for extract_article_content function."""

    def test_extracts_title_from_article(self, mock_article):
        """Should extract title from article."""
        mock = mock_article(title="My Test Title")

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.title == "My Test Title"

    def test_extracts_content_from_article(self, mock_article):
        """Should extract content from article."""
        content = "This is the full article content."
        mock = mock_article(text=content)

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.content == content

    def test_extracts_image_from_article(self, mock_article):
        """Should extract top image from article."""
        mock = mock_article(top_image="https://example.com/hero.jpg")

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.image_url == "https://example.com/hero.jpg"

    def test_creates_excerpt_from_content(self, mock_article):
        """Should create excerpt from first 200 characters."""
        long_content = "A" * 300
        mock = mock_article(text=long_content)

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert len(result.excerpt) == 203  # 200 chars + "..."
        assert result.excerpt.endswith("...")

    def test_excerpt_no_ellipsis_for_short_content(self, mock_article):
        """Should not add ellipsis for content under 200 chars."""
        short_content = "Short content"
        mock = mock_article(text=short_content)

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.excerpt == short_content
        assert not result.excerpt.endswith("...")

    def test_uses_hostname_when_title_missing(self, mock_article):
        """Should use hostname as title when article has no title."""
        mock = mock_article(title="")

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.title == "example.com"

    def test_handles_missing_image(self, mock_article):
        """Should handle articles without images."""
        mock = mock_article(top_image="")

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.image_url is None

    def test_handles_download_error(self, mock_article):
        """Should handle errors during article download."""
        mock = mock_article()
        mock.download.side_effect = Exception("Network error")

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.title == "example.com"
        assert result.content == ""
        assert result.excerpt == "Failed to extract content"

    def test_handles_parse_error(self, mock_article):
        """Should handle errors during article parsing."""
        mock = mock_article()
        mock.parse.side_effect = Exception("Parse error")

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.excerpt == "Failed to extract content"

    def test_calls_download_and_parse(self, mock_article):
        """Should call download and parse on the article."""
        mock = mock_article()

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            extract_article_content("https://example.com/article")

        mock.download.assert_called_once()
        mock.parse.assert_called_once()

    def test_handles_none_values(self, mock_article):
        """Should handle None values from newspaper."""
        mock = mock_article()
        mock.title = None
        mock.text = None
        mock.top_image = None

        with patch("services.article_service.NewspaperArticle", return_value=mock):
            result = extract_article_content("https://example.com/article")

        assert result.title == "example.com"
        assert result.content == ""
        assert result.image_url is None
