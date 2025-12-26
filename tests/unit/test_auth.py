import time

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from main.auth import verify_jwt_token
from main.config import Settings


@pytest.mark.unit
async def test_valid_jwt_token_decodes_successfully():
    """測試有效的 JWT token 能成功解碼"""
    token = jwt.encode(
        {"sub": "testuser", "role": "admin"}, b"testsecret", algorithm="HS256"
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    settings = Settings(jwt_keys={"default": b"testsecret"})

    payload = await verify_jwt_token(credentials, settings)

    assert payload["sub"] == "testuser"
    assert payload["role"] == "admin"


@pytest.mark.unit
async def test_invalid_signature_raises_403():
    """測試無效簽名的 token 拋出 403 錯誤"""
    token = jwt.encode({"sub": "testuser"}, b"wrongsecret", algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    settings = Settings(jwt_keys={"default": b"testsecret"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(credentials, settings)

    assert exc_info.value.status_code == 403
    assert "signature" in exc_info.value.detail.lower()


@pytest.mark.unit
async def test_expired_token_raises_403():
    """測試過期的 token 拋出 403 錯誤"""
    token = jwt.encode(
        {"sub": "testuser", "exp": int(time.time()) - 3600},
        b"testsecret",
        algorithm="HS256",
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    settings = Settings(jwt_keys={"default": b"testsecret"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(credentials, settings)

    assert exc_info.value.status_code == 403
    assert "expired" in exc_info.value.detail.lower()


@pytest.mark.unit
async def test_multi_key_support():
    """測試多密鑰支援 - 遍歷所有密鑰直到成功"""
    token = jwt.encode({"sub": "testuser"}, b"key2", algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    settings = Settings(
        jwt_keys={
            "key1": b"wrongkey1",
            "key2": b"key2",
            "key3": b"wrongkey3",
        }
    )

    payload = await verify_jwt_token(credentials, settings)

    assert payload["sub"] == "testuser"


@pytest.mark.unit
async def test_all_keys_fail_raises_403():
    """測試所有密鑰都失敗時拋出 403 錯誤"""
    token = jwt.encode({"sub": "testuser"}, b"correctkey", algorithm="HS256")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    settings = Settings(
        jwt_keys={
            "key1": b"wrongkey1",
            "key2": b"wrongkey2",
            "key3": b"wrongkey3",
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(credentials, settings)

    assert exc_info.value.status_code == 403


@pytest.mark.unit
@pytest.mark.parametrize(
    "algorithm",
    ["HS256", "HS384", "HS512"],
)
async def test_supports_multiple_algorithms(algorithm):
    """測試支援多種 JWT 演算法"""
    secret = b"testsecret"
    token = jwt.encode({"sub": "testuser"}, secret, algorithm=algorithm)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    settings = Settings(jwt_keys={"default": secret})

    payload = await verify_jwt_token(credentials, settings)

    assert payload["sub"] == "testuser"


@pytest.mark.unit
async def test_malformed_token_raises_403():
    """測試格式錯誤的 token 拋出 403 錯誤"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="not.a.valid.jwt.token"
    )
    settings = Settings(jwt_keys={"default": b"testsecret"})

    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(credentials, settings)

    assert exc_info.value.status_code == 403
    assert "invalid" in exc_info.value.detail.lower()
