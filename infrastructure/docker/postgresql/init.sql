-- Team Insight Database Initialization

-- Create database if not exists
SELECT 'CREATE DATABASE team_insight'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'team_insight');

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE team_insight TO postgres;

-- データベースに接続
\c team_insight

-- スキーマの設定
CREATE SCHEMA IF NOT EXISTS public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
