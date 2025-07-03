# backend/tests/test_config.py
"""設定のテスト"""
import pytest
import logging
from app.core.config import Settings, validate_settings


def test_settings_validation():
    """設定の検証テスト"""
    # 最小限の設定でインスタンス化
    test_settings = Settings(
        DATABASE_URL="postgresql://test:test@localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        REDISCLI_AUTH="test_redis_password",
        BACKLOG_CLIENT_ID="test-client-id",
        BACKLOG_CLIENT_SECRET="test-client-secret",
        BACKLOG_SPACE_KEY="test-space",
        SECRET_KEY="test-secret-key-for-testing-only",
        DEBUG=True,
    )

    assert test_settings.APP_NAME == "Team Insight"
    assert test_settings.DEBUG == True
    assert test_settings.API_V1_STR == "/api/v1"
    assert test_settings.ACCESS_TOKEN_EXPIRE_MINUTES == 10080  # 7 days in minutes
    assert test_settings.CACHE_DEFAULT_EXPIRE == 300


def test_default_values():
    """デフォルト値のテスト"""
    # 環境変数の影響を受けるため、実際の環境での値を確認
    # または、環境変数をクリアしてからテスト
    import os

    # 一時的に環境変数を保存
    env_backup = {}
    keys_to_clear = [
        "DATABASE_URL",
        "REDIS_URL",
        "REDISCLI_AUTH",
        "SECRET_KEY",
        "BACKLOG_CLIENT_ID",
        "BACKLOG_CLIENT_SECRET",
        "BACKLOG_SPACE_KEY",
    ]

    for key in keys_to_clear:
        if key in os.environ:
            env_backup[key] = os.environ[key]
            del os.environ[key]

    try:
        settings = Settings(_env_file=None)

        assert settings.SECRET_KEY == "your-secret-key-here"
        assert (
            settings.DATABASE_URL
            == "postgresql://postgres:postgres@localhost:5432/team_insight"
        )
        assert settings.REDIS_URL == "redis://redis:6379"
        assert settings.REDISCLI_AUTH == "redis_password"
        assert settings.CACHE_DEFAULT_EXPIRE == 300
        assert settings.CACHE_MAX_CONNECTIONS == 20
        assert settings.CACHE_HEALTH_CHECK_INTERVAL == 30
    finally:
        # 環境変数を復元
        for key, value in env_backup.items():
            os.environ[key] = value


def test_validate_settings_with_defaults(caplog, monkeypatch):
    """デフォルト設定での検証テスト"""
    # テスト用の設定を作成
    test_settings = Settings(
        SECRET_KEY="your-secret-key-here",
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/team_insight",
        REDISCLI_AUTH="redis_password",
        BACKLOG_CLIENT_ID="",
        BACKLOG_CLIENT_SECRET="",
        BACKLOG_SPACE_KEY="",
        DEBUG=True,
    )

    # 元の設定を保存
    from app.core import config

    original_settings = config.settings

    try:
        # テスト用設定に置き換え
        config.settings = test_settings

        # ログレベルをWARNINGに設定してキャプチャ
        caplog.set_level(logging.WARNING)
        result = validate_settings()

        # 結果を確認
        assert result is False  # 問題があるのでFalse

        # 警告メッセージを確認
        warning_messages = [
            record.message for record in caplog.records if record.levelname == "WARNING"
        ]
        assert any("デフォルトのSECRET_KEY" in msg for msg in warning_messages)
        assert any("デフォルトのRedisパスワード" in msg for msg in warning_messages)

        # エラーメッセージを確認
        error_messages = [
            record.message for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_messages) > 0
        # エラーメッセージは複数の問題を含む1つのメッセージにまとめられている
        error_msg = error_messages[0]
        assert "Backlog OAuth認証が設定されていません" in error_msg
        assert "Backlogスペースキーが設定されていません" in error_msg

    finally:
        # 元の設定に戻す
        config.settings = original_settings


def test_validate_settings_production_mode(caplog, monkeypatch):
    """本番モードでの検証テスト"""
    # テスト用の設定を作成
    test_settings = Settings(
        SECRET_KEY="your-secret-key-here",
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/team_insight",
        REDISCLI_AUTH="redis_password",
        BACKLOG_CLIENT_ID="prod-client-id",
        BACKLOG_CLIENT_SECRET="prod-client-secret",
        BACKLOG_SPACE_KEY="prod-space",
        DEBUG=False,  # 本番モード
    )

    # 元の設定を保存
    from app.core import config

    original_settings = config.settings

    try:
        # テスト用設定に置き換え
        config.settings = test_settings

        # ログレベルをERRORに設定してキャプチャ
        caplog.set_level(logging.ERROR)
        result = validate_settings()

        # 結果を確認
        assert result is False  # 本番環境でデフォルト値を使っているのでFalse

        # エラーメッセージを確認
        error_messages = [
            record.message for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_messages) > 0
        assert "本番環境でデフォルトのSECRET_KEY" in error_messages[0]
        assert "本番環境でlocalhostのデータベースURL" in error_messages[0]
        assert "本番環境でデフォルトのRedisパスワード" in error_messages[0]

    finally:
        # 元の設定に戻す
        config.settings = original_settings


def test_validate_settings_valid_production(caplog, monkeypatch):
    """有効な本番設定での検証テスト"""
    # テスト用の設定を作成
    test_settings = Settings(
        SECRET_KEY="production-secret-key-abc123xyz-production-secret-key-abc123xyz",
        DATABASE_URL="postgresql://produser:prodpass@db.example.com:5432/team_insight",
        REDISCLI_AUTH="production-redis-password",
        BACKLOG_CLIENT_ID="prod-client-id",
        BACKLOG_CLIENT_SECRET="prod-client-secret",
        BACKLOG_SPACE_KEY="prod-space",
        DEBUG=False,
    )

    # 元の設定を保存
    from app.core import config

    original_settings = config.settings

    try:
        # テスト用設定に置き換え
        config.settings = test_settings

        # ログレベルをINFOに設定してキャプチャ
        caplog.set_level(logging.INFO)
        result = validate_settings()

        # 結果を確認
        assert result is True  # 問題なし

        # 成功メッセージを確認
        info_messages = [
            record.message for record in caplog.records if record.levelname == "INFO"
        ]
        assert any("設定の検証が正常に完了しました" in msg for msg in info_messages)

    finally:
        # 元の設定に戻す
        config.settings = original_settings


def test_password_policy_settings():
    """パスワードポリシー設定のテスト"""
    settings = Settings()

    assert settings.PASSWORD_MIN_LENGTH == 8
    assert settings.PASSWORD_REQUIRE_UPPERCASE == True
    assert settings.PASSWORD_REQUIRE_LOWERCASE == True
    assert settings.PASSWORD_REQUIRE_NUMBERS == True
    assert settings.PASSWORD_REQUIRE_SPECIAL == True


def test_env_override():
    """環境変数によるオーバーライドのテスト"""
    import os

    # 環境変数を設定
    os.environ["SECRET_KEY"] = "env-secret-key"
    os.environ["DEBUG"] = "false"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

    try:
        settings = Settings()

        assert settings.SECRET_KEY == "env-secret-key"
        assert settings.DEBUG == False
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    finally:
        # 環境変数をクリーンアップ
        os.environ.pop("SECRET_KEY", None)
        os.environ.pop("DEBUG", None)
        os.environ.pop("ACCESS_TOKEN_EXPIRE_MINUTES", None)
