-- Team Insight Database Initialization

-- データベースが存在しない場合のみ作成
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'team_insight') THEN
        CREATE DATABASE team_insight;
    END IF;
END
$$;

-- データベースに接続
\c team_insight;

-- ユーザーが存在しない場合のみ作成
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'team_insight_user') THEN
        CREATE USER team_insight_user WITH PASSWORD 'team_insight_password';
    END IF;
END
$$;

-- スキーマの作成
CREATE SCHEMA IF NOT EXISTS team_insight;

-- スキーマの権限を付与
GRANT ALL ON SCHEMA team_insight TO team_insight_user;

-- テーブルの作成はAlembicマイグレーションで行うため、ここでは権限の付与のみ行う
-- デフォルトの権限を設定
ALTER DEFAULT PRIVILEGES IN SCHEMA team_insight GRANT ALL PRIVILEGES ON TABLES TO team_insight_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA team_insight GRANT USAGE, SELECT ON SEQUENCES TO team_insight_user;
