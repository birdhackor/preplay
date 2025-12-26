from urllib.parse import parse_qs, urlencode

from pydantic import HttpUrl


def normalize_url(url: HttpUrl) -> str:
    """規範化 URL 用於快取鍵

    移除 fragment (#anchor) 並排序 query 參數，確保相同內容的 URL 有相同的快取鍵

    Args:
        url: Pydantic HttpUrl 物件

    Returns:
        規範化後的 URL 字串

    Example:
        >>> from pydantic import HttpUrl
        >>> url = HttpUrl("https://example.com/page?b=2&a=1#section")
        >>> normalize_url(url)
        'https://example.com/page?a=1&b=2'

    References:
        - https://docs.pydantic.dev/latest/api/networks/
        - https://docs.pydantic.dev/2.11/api/networks/
    """
    # 建構基本 URL（scheme + host + port + path）
    parts = [f"{url.scheme}://"]

    # 加入 host
    if url.host:
        parts.append(url.host)

    # 加入 port（如果不是預設 port）
    if url.port and url.port not in (80, 443):
        parts.append(f":{url.port}")

    # 加入 path
    if url.path:
        parts.append(url.path)

    # 處理 query 參數：解析並排序
    if url.query:
        query_params = parse_qs(url.query, keep_blank_values=True)
        sorted_query = urlencode(sorted(query_params.items()), doseq=True)
        parts.append(f"?{sorted_query}")

    # 不包含 fragment（這是關鍵優化點）

    return "".join(parts)
