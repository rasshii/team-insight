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

-- テーブルの作成
CREATE TABLE IF NOT EXISTS team_insight.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_insight.teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_insight.team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES team_insight.teams(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES team_insight.users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id)
);

CREATE TABLE IF NOT EXISTS team_insight.projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    team_id INTEGER REFERENCES team_insight.teams(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_insight.tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    project_id INTEGER REFERENCES team_insight.projects(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES team_insight.users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL,
    priority VARCHAR(50) NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- テーブルの権限を付与
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA team_insight TO team_insight_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA team_insight TO team_insight_user;

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_users_username ON team_insight.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON team_insight.users(email);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_insight.team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_insight.team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_team_id ON team_insight.projects(team_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON team_insight.tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON team_insight.tasks(assigned_to);
