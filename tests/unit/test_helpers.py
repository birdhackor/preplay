import pytest
from pydantic import HttpUrl

from main.helpers import normalize_url


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_url,expected",
    [
        (
            "https://example.com/page#section",
            "https://example.com/page",
        ),
        (
            "http://example.com/page#anchor",
            "http://example.com/page",
        ),
        (
            "https://example.com/#top",
            "https://example.com/",
        ),
    ],
)
def test_removes_fragment(input_url, expected):
    """測試移除 URL fragment (#anchor)"""
    url = HttpUrl(input_url)
    result = normalize_url(url)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_url,expected",
    [
        (
            "https://example.com/page?b=2&a=1",
            "https://example.com/page?a=1&b=2",
        ),
        (
            "https://example.com/page?z=3&y=2&x=1",
            "https://example.com/page?x=1&y=2&z=3",
        ),
        (
            "https://example.com/?filter=active&sort=name",
            "https://example.com/?filter=active&sort=name",
        ),
    ],
)
def test_sorts_query_parameters(input_url, expected):
    """測試排序 query 參數"""
    url = HttpUrl(input_url)
    result = normalize_url(url)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_url,expected",
    [
        (
            "http://example.com:80/page",
            "http://example.com/page",
        ),
        (
            "https://example.com:443/page",
            "https://example.com/page",
        ),
    ],
)
def test_removes_default_port(input_url, expected):
    """測試移除預設 port (80 for http, 443 for https)"""
    url = HttpUrl(input_url)
    result = normalize_url(url)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_url,expected",
    [
        (
            "http://example.com:8080/page",
            "http://example.com:8080/page",
        ),
        (
            "https://example.com:8443/page",
            "https://example.com:8443/page",
        ),
    ],
)
def test_preserves_non_default_port(input_url, expected):
    """測試保留非預設 port"""
    url = HttpUrl(input_url)
    result = normalize_url(url)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "input_url,expected",
    [
        (
            "https://example.com/page",
            "https://example.com/page",
        ),
        (
            "https://example.com/",
            "https://example.com/",
        ),
    ],
)
def test_handles_empty_query(input_url, expected):
    """測試處理空 query"""
    url = HttpUrl(input_url)
    result = normalize_url(url)
    assert result == expected


@pytest.mark.unit
def test_handles_special_characters_in_query():
    """測試處理 query 中的特殊字元編碼"""
    input_url = "https://example.com/search?q=hello+world&filter=type%3Ablog"
    url = HttpUrl(input_url)
    result = normalize_url(url)

    assert "filter=" in result
    assert "q=" in result


@pytest.mark.unit
def test_complex_url_normalization():
    """測試複雜 URL 的完整正規化流程"""
    input_url = "https://example.com:443/page?b=2&a=1#section"
    url = HttpUrl(input_url)
    result = normalize_url(url)

    expected = "https://example.com/page?a=1&b=2"
    assert result == expected


@pytest.mark.unit
def test_identical_urls_with_different_order_produce_same_key():
    """測試參數順序不同的相同 URL 產生相同的快取鍵"""
    url1 = HttpUrl("https://example.com/page?a=1&b=2&c=3")
    url2 = HttpUrl("https://example.com/page?c=3&a=1&b=2")
    url3 = HttpUrl("https://example.com/page?b=2&c=3&a=1")

    key1 = normalize_url(url1)
    key2 = normalize_url(url2)
    key3 = normalize_url(url3)

    assert key1 == key2 == key3
