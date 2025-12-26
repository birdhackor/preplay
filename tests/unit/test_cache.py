import time

import pytest

from main.cache import SimpleCache


@pytest.mark.unit
def test_basic_get_set_operations():
    """測試基本的 get/set 操作"""
    cache = SimpleCache(ttl=60, max_entries=10)

    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    cache.set("key2", "value2")
    assert cache.get("key2") == "value2"
    assert cache.get("key1") == "value1"


@pytest.mark.unit
def test_get_nonexistent_key_returns_none():
    """測試獲取不存在的鍵返回 None"""
    cache = SimpleCache(ttl=60, max_entries=10)

    assert cache.get("nonexistent") is None


@pytest.mark.unit
def test_ttl_expiration():
    """測試 TTL 過期自動刪除"""
    cache = SimpleCache(ttl=1, max_entries=10)

    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    time.sleep(1.1)

    assert cache.get("key1") is None


@pytest.mark.unit
def test_lru_eviction_on_max_entries():
    """測試達到 max_entries 時 LRU 驅逐策略"""
    cache = SimpleCache(ttl=60, max_entries=3)

    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    assert len(cache._cache) == 3

    cache.set("key4", "value4")

    assert len(cache._cache) == 3
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


@pytest.mark.unit
def test_repeated_access_updates_access_order():
    """測試重複存取更新 access_order"""
    cache = SimpleCache(ttl=60, max_entries=3)

    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    cache.get("key1")

    cache.set("key4", "value4")

    assert cache.get("key1") == "value1"
    assert cache.get("key2") is None
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


@pytest.mark.unit
def test_clear_expired():
    """測試 clear_expired() 主動清理"""
    cache = SimpleCache(ttl=1, max_entries=10)

    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    assert len(cache._cache) == 3

    time.sleep(1.1)

    cleared = cache.clear_expired()

    assert cleared == 3
    assert len(cache._cache) == 0


@pytest.mark.unit
def test_clear_expired_no_expired_items():
    """測試 clear_expired() 在沒有過期項目時的行為"""
    cache = SimpleCache(ttl=60, max_entries=10)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    cleared = cache.clear_expired()

    assert cleared == 0
    assert len(cache._cache) == 2


@pytest.mark.unit
def test_stats():
    """測試 stats() 返回正確統計"""
    cache = SimpleCache(ttl=60, max_entries=10)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    stats = cache.stats()

    assert stats["total_entries"] == 2
    assert stats["ttl"] == 60
    assert stats["max_entries"] == 10


@pytest.mark.unit
def test_empty_cache_stats():
    """測試空快取的統計"""
    cache = SimpleCache(ttl=60, max_entries=10)

    stats = cache.stats()

    assert stats["total_entries"] == 0
    assert stats["ttl"] == 60
    assert stats["max_entries"] == 10


@pytest.mark.unit
def test_updating_existing_key():
    """測試更新已存在的鍵"""
    cache = SimpleCache(ttl=60, max_entries=10)

    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    cache.set("key1", "value2")
    assert cache.get("key1") == "value2"
    assert len(cache._cache) == 1
