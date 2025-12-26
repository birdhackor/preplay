import time
from typing import Any, Optional

from loguru import logger


class SimpleCache:
    """基於記憶體的 TTL 快取，帶 LRU 淘汰策略

    使用 dict 儲存 (value, timestamp) tuple，實作延遲清理策略。
    當達到最大條目數時，使用 LRU（Least Recently Used）淘汰最舊的項目。
    """

    def __init__(self, ttl: int = 86400, max_entries: int = 50):
        """初始化快取

        Args:
            ttl: Time-to-live in seconds（預設 24 小時）
            max_entries: 最大快取條目數（預設 1000）
        """
        self.ttl = ttl
        self.max_entries = max_entries
        self._cache: dict[str, tuple[str, float]] = {}
        self._access_order: list[str] = []
        logger.info(
            f"Initialized SimpleCache with TTL={ttl}s, max_entries={max_entries}"
        )

    def get(self, key: str) -> Optional[str]:
        """獲取快取值，自動檢查並刪除過期項目

        Args:
            key: 快取鍵（通常是 URL）

        Returns:
            快取的 HTML 或 None（未找到或已過期）
        """
        if key not in self._cache:
            logger.debug(f"Cache miss: {key}")
            return None

        value, timestamp = self._cache[key]
        age = time.monotonic() - timestamp

        if age > self.ttl:
            # 過期，刪除並返回 None
            logger.debug(f"Cache expired: {key} (age: {age:.1f}s)")
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None

        # 未過期，更新 access_order（移到末尾表示最近使用）
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"Cache hit: {key} (age: {age:.1f}s)")
        return value

    def set(self, key: str, value: str) -> None:
        """設定快取項目

        如果達到最大條目數，先執行 LRU 淘汰。

        Args:
            key: 快取鍵
            value: 要快取的值（HTML）
        """
        # 如果已存在，先從 access_order 中移除
        if key in self._access_order:
            self._access_order.remove(key)

        # 如果達到上限，執行 LRU 淘汰
        if len(self._cache) >= self.max_entries and key not in self._cache:
            self._evict_lru()

        # 儲存快取
        self._cache[key] = (value, time.monotonic())
        self._access_order.append(key)

        logger.debug(f"Cache set: {key} (size: {len(value)} bytes)")

    def _evict_lru(self) -> None:
        """LRU 淘汰：移除最久未使用的項目"""
        if not self._access_order:
            return

        # 移除最舊的項目（access_order 的第一個）
        lru_key = self._access_order.pop(0)
        if lru_key in self._cache:
            del self._cache[lru_key]
            logger.info(f"Evicted LRU cache entry: {lru_key}")

    def clear_expired(self) -> int:
        """主動清理過期項目（維護方法）

        Returns:
            清理的項目數量
        """
        now = time.monotonic()
        expired_keys = [k for k, (_, ts) in self._cache.items() if now - ts > self.ttl]

        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)

        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def stats(self) -> dict[str, Any]:
        """返回快取統計資訊（用於監控）

        Returns:
            包含總條目數、TTL、最大條目數的字典
        """
        return {
            "total_entries": len(self._cache),
            "ttl": self.ttl,
            "max_entries": self.max_entries,
        }
