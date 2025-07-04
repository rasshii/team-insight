# データベース設計と操作

**このガイドで学べること**：
- データベースとRDBMSの基本概念から理解
- PostgreSQLの基礎知識と基本的なSQL文
- SQLAlchemy 2.0（ORM）の基本から応用まで
- Alembicによるマイグレーション管理の仕組み
- インデックスとクエリ最適化の実践
- パフォーマンスチューニングの手法

## 🌟 はじめに：データベースとは？

### 📊 データベースを日常生活で例えると

データベースは「整理整頓された情報倉庫」のようなものです：

```
現実世界の例：
┌─────────────────────────────┐
│      図書館の管理システム      │
├─────────────────────────────┤
│ 本棚（テーブル）              │
│ ├─ 本の情報カード（レコード）  │
│ │  ├─ タイトル（カラム）      │
│ │  ├─ 著者（カラム）         │
│ │  └─ ISBN（主キー）         │
│ └─ 索引カード（インデックス）   │
└─────────────────────────────┘

データベース：
┌─────────────────────────────┐
│         PostgreSQL          │
├─────────────────────────────┤
│ テーブル                     │
│ ├─ レコード（行）            │
│ │  ├─ カラム（列）           │
│ │  └─ 主キー（ID）          │
│ └─ インデックス              │
└─────────────────────────────┘
```

### 🔑 RDBMSとは？

RDBMS（Relational Database Management System）= リレーショナルデータベース管理システム

**特徴**：
1. **テーブル形式**: Excelのような表形式でデータを管理
2. **リレーション**: テーブル間の関係を定義できる
3. **SQL**: 統一されたクエリ言語でデータ操作
4. **ACID特性**: データの整合性を保証

```
例：ユーザーとプロジェクトの関係

usersテーブル            projectsテーブル
┌────┬──────┐          ┌────┬──────────┐
│ id │ name │          │ id │ name     │
├────┼──────┤          ├────┼──────────┤
│ 1  │ 田中 │  ←関係→  │ 1  │ Web開発   │
│ 2  │ 佐藤 │          │ 2  │ アプリ開発 │
└────┴──────┘          └────┴──────────┘
```

### 🐘 PostgreSQLとは？

PostgreSQLは、オープンソースの高機能なRDBMSです。

**なぜPostgreSQLを選ぶのか？**
1. **無料**: オープンソースで商用利用も可能
2. **高機能**: JSON型、配列型など豊富なデータ型
3. **信頼性**: 30年以上の歴史と実績
4. **拡張性**: 大規模システムにも対応

## 🏗️ Team Insightのデータベース構造

### 全体のER図

Team Insightのデータベースは、以下のような構造になっています：

```mermaid
erDiagram
    users ||--o{ user_roles : has
    users ||--o{ oauth_tokens : has
    users ||--o{ project_members : belongs_to
    users ||--o{ team_members : belongs_to
    users ||--o{ tasks : assigned_to
    users ||--o{ tasks : reported_by
    users ||--o{ report_schedules : has
    users ||--o{ login_history : has
    users ||--o{ activity_logs : has
    users ||--o| user_preferences : has
    
    roles ||--o{ user_roles : assigned_to
    roles ||--o{ role_permissions : has
    permissions ||--o{ role_permissions : assigned_to
    
    projects ||--o{ project_members : has
    projects ||--o{ tasks : contains
    
    teams ||--o{ team_members : has
    
    users {
        int id PK
        string email UK
        string name
        int backlog_id UK
        boolean is_active
        string timezone
        string locale
        timestamp created_at
        timestamp updated_at
    }
    
    roles {
        int id PK
        string name UK
        string description
        boolean is_system
    }
    
    permissions {
        int id PK
        string name UK
        string resource
        string action
        string description
    }
    
    user_roles {
        int id PK
        int user_id FK
        int role_id FK
        int project_id FK "nullable"
    }
    
    projects {
        int id PK
        string name
        string description
        int backlog_project_id UK
        string status
        timestamp created_at
        timestamp updated_at
    }
    
    teams {
        int id PK
        string name
        string description
        timestamp created_at
        timestamp updated_at
    }
    
    tasks {
        int id PK
        int project_id FK
        int assignee_id FK
        int reporter_id FK
        string title
        string status
        int backlog_issue_id UK
        timestamp created_at
        timestamp updated_at
    }
```

### スキーマ設計の特徴

#### 1. **専用スキーマの使用**

Team Insightでは、`team_insight`という専用のスキーマを使用しています：

```sql
-- すべてのテーブルは team_insight スキーマに属する
CREATE SCHEMA IF NOT EXISTS team_insight;

-- テーブル作成例
CREATE TABLE team_insight.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    -- ...
);
```

**なぜ専用スキーマを使うのか？**
- **名前空間の分離**: 他のアプリケーションとの競合を避ける
- **アクセス制御**: スキーマ単位で権限管理が可能
- **整理整頓**: 関連するテーブルをグループ化

#### 2. **主要なテーブルの詳細**

##### users テーブル
ユーザー情報を管理する中心的なテーブル：

```sql
CREATE TABLE team_insight.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    
    -- Backlog連携用
    backlog_id INTEGER UNIQUE,
    user_id VARCHAR(255) UNIQUE,  -- BacklogのユーザーID
    name VARCHAR(255),
    
    -- ユーザー設定
    timezone VARCHAR(50) DEFAULT 'Asia/Tokyo',
    locale VARCHAR(10) DEFAULT 'ja',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    
    -- タイムスタンプ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**設計のポイント**：
- `email`は`UNIQUE`だが`NULL`許可（Backlog連携ユーザー用）
- `backlog_id`でBacklogとの連携を管理
- タイムゾーン対応のタイムスタンプ（`WITH TIME ZONE`）

##### roles と permissions テーブル（RBAC）

```sql
-- ロール定義
CREATE TABLE team_insight.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    is_system BOOLEAN DEFAULT false,  -- システム定義ロール
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 権限定義
CREATE TABLE team_insight.permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,  -- 例: 'users', 'projects'
    action VARCHAR(50) NOT NULL,     -- 例: 'read', 'write', 'delete'
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ユーザーとロールの関連（多対多）
CREATE TABLE team_insight.user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES team_insight.users(id),
    role_id INTEGER NOT NULL REFERENCES team_insight.roles(id),
    project_id INTEGER REFERENCES team_insight.projects(id),  -- プロジェクト固有ロール
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id, project_id)  -- 複合ユニーク制約
);
```

**RBAC設計の特徴**：
- **グローバルロール**: `project_id`が`NULL`の場合
- **プロジェクトロール**: 特定プロジェクト内でのロール
- **柔軟な権限管理**: リソースとアクションの組み合わせ

##### projects と project_members テーブル

```sql
-- プロジェクト
CREATE TABLE team_insight.projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    backlog_project_id INTEGER UNIQUE,
    backlog_project_key VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- プロジェクトメンバー（多対多）
CREATE TABLE team_insight.project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES team_insight.projects(id),
    user_id INTEGER NOT NULL REFERENCES team_insight.users(id),
    role VARCHAR(50) DEFAULT 'MEMBER',  -- 'LEADER', 'MEMBER'
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id)
);
```

##### activity_logs テーブル（監査ログ）

```sql
CREATE TABLE team_insight.activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES team_insight.users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),  -- 'PROJECT', 'USER', 'TEAM'など
    target_id VARCHAR(255),
    details JSONB,  -- 詳細情報をJSON形式で保存
    ip_address INET,  -- IPアドレス型
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- パフォーマンス用インデックス
CREATE INDEX idx_activity_logs_user_id ON team_insight.activity_logs(user_id);
CREATE INDEX idx_activity_logs_created_at ON team_insight.activity_logs(created_at DESC);
CREATE INDEX idx_activity_logs_action ON team_insight.activity_logs(action);
```

**監査ログの設計ポイント**：
- `JSONB`型で柔軟な詳細情報保存
- `INET`型でIPアドレスを正確に保存
- 適切なインデックスでクエリ性能を確保

### インデックス戦略

Team Insightでは、以下の戦略でインデックスを設計しています：

```sql
-- 1. 外部キーには自動的にインデックスが作成される

-- 2. 頻繁に検索される列にインデックス
CREATE INDEX idx_users_email ON team_insight.users(email);
CREATE INDEX idx_users_backlog_id ON team_insight.users(backlog_id);

-- 3. 複合インデックス（複数列での検索用）
CREATE INDEX idx_tasks_project_assignee ON team_insight.tasks(project_id, assignee_id);

-- 4. 部分インデックス（条件付きインデックス）
CREATE INDEX idx_active_users ON team_insight.users(email) WHERE is_active = true;

-- 5. GINインデックス（JSONB検索用）
CREATE INDEX idx_activity_logs_details ON team_insight.activity_logs USING gin(details);
```

**インデックス設計の原則**：
1. **選択性の高い列**: ユニークに近い値を持つ列
2. **WHERE句で頻繁に使用**: 検索条件によく使われる列
3. **JOIN条件**: テーブル結合で使用される列
4. **ORDER BY**: ソートでよく使われる列

## 📝 SQL基礎知識

### 基本的なSQL文

#### 1. SELECT文（データ取得）

```sql
-- 基本構文
SELECT カラム名 FROM テーブル名 WHERE 条件;

-- 全件取得
SELECT * FROM team_insight.users;

-- 条件付き取得
SELECT name, email 
FROM team_insight.users 
WHERE is_active = true;

-- 並び替え
SELECT * FROM team_insight.tasks 
ORDER BY created_at DESC  -- 降順
LIMIT 10;                -- 10件のみ

-- 集計
SELECT 
    status,
    COUNT(*) as task_count 
FROM team_insight.tasks 
GROUP BY status;
```

#### 2. INSERT文（データ追加）

```sql
-- 1件追加
INSERT INTO team_insight.users (name, email, is_active) 
VALUES ('山田太郎', 'yamada@example.com', true);

-- 複数件追加
INSERT INTO team_insight.users (name, email) VALUES 
('田中花子', 'tanaka@example.com'),
('佐藤次郎', 'sato@example.com');

-- 別テーブルからコピー
INSERT INTO team_insight.user_backup 
SELECT * FROM team_insight.users WHERE is_active = true;
```

#### 3. UPDATE文（データ更新）

```sql
-- 特定のレコードを更新
UPDATE team_insight.users 
SET 
    name = '山田太郎（更新）',
    updated_at = CURRENT_TIMESTAMP
WHERE id = '123e4567-e89b-12d3-a456-426614174000';

-- 複数レコードを一括更新
UPDATE team_insight.tasks 
SET status = 'completed' 
WHERE due_date < CURRENT_DATE AND status = 'in_progress';
```

#### 4. DELETE文（データ削除）

```sql
-- 特定のレコードを削除
DELETE FROM team_insight.users 
WHERE id = '123e4567-e89b-12d3-a456-426614174000';

-- 条件に合うレコードを削除
DELETE FROM team_insight.oauth_states 
WHERE expires_at < CURRENT_TIMESTAMP;

-- 全件削除（危険！）
-- DELETE FROM team_insight.users;  -- WHERE句なしは全削除
```

### JOINの基本

```sql
-- INNER JOIN: 両方のテーブルに存在するデータのみ
SELECT 
    u.name as user_name,
    p.name as project_name
FROM team_insight.users u
INNER JOIN team_insight.project_members pm ON u.id = pm.user_id
INNER JOIN team_insight.projects p ON pm.project_id = p.id;

-- LEFT JOIN: 左側のテーブルの全データ＋右側の一致データ
SELECT 
    u.name,
    COUNT(t.id) as task_count
FROM team_insight.users u
LEFT JOIN team_insight.tasks t ON u.id = t.assignee_id
GROUP BY u.id, u.name;
```

## 🏗️ SQLAlchemy 2.0 の詳細

### 📚 ORM（Object Relational Mapping）の概念

SQLAlchemyは、PythonのORM（オブジェクト関係マッピング）ライブラリです。

**ORMを使う理由**：
```python
# 従来の方法（生のSQL）
cursor.execute(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    ("田中太郎", "tanaka@example.com")
)

# ORMを使った方法（SQLAlchemy）
user = User(name="田中太郎", email="tanaka@example.com")
db.add(user)
db.commit()
```

**メリット**：
1. **SQLを書かなくていい**: Pythonのコードだけで済む
2. **型安全**: IDEの補完が効く
3. **データベース独立**: PostgreSQL→MySQLへの移行が容易
4. **セキュリティ**: SQLインジェクション攻撃を防げる

### 🔄 SQLAlchemyの仕組み

```
Pythonオブジェクト ←→ SQLAlchemy ←→ SQL ←→ データベース

例：
user = User(name="田中")  →  INSERT INTO users (name) VALUES ('田中')
user.name = "佐藤"       →  UPDATE users SET name = '佐藤' WHERE id = ?
db.query(User).all()     →  SELECT * FROM users
```

### Team InsightでのSQLAlchemy実装パターン

#### 1. **モデル定義の基本構造**

```python
# backend/app/db/base_class.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from app.core.datetime_utils import utcnow

Base = declarative_base()

class BaseModel(Base):
    """すべてのモデルの基底クラス"""
    __abstract__ = True  # このクラス自体はテーブルを作らない
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
```

#### 2. **実際のモデル実装例**

```python
# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.base_class import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = {"schema": "team_insight"}  # スキーマ指定
    
    # カラム定義
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Backlog連携用フィールド
    backlog_id = Column(Integer, unique=True, index=True, nullable=True)
    
    # リレーション定義
    user_roles = relationship(
        "UserRole", 
        back_populates="user",
        cascade="all, delete-orphan"  # ユーザー削除時に関連も削除
    )
    
    # 多対多リレーション
    projects = relationship(
        "Project",
        secondary="team_insight.project_members",  # 中間テーブル
        back_populates="members"
    )
```

#### 3. **リレーションシップの詳細**

```python
# 1対多リレーション
class Project(BaseModel):
    __tablename__ = "projects"
    
    # 外部キー参照側（多）
    tasks = relationship("Task", back_populates="project")

class Task(BaseModel):
    __tablename__ = "tasks"
    
    # 外部キー定義（1）
    project_id = Column(Integer, ForeignKey("team_insight.projects.id"))
    project = relationship("Project", back_populates="tasks")

# 多対多リレーション（中間テーブル経由）
class ProjectMember(BaseModel):
    __tablename__ = "project_members"
    
    project_id = Column(Integer, ForeignKey("team_insight.projects.id"))
    user_id = Column(Integer, ForeignKey("team_insight.users.id"))
    role = Column(String, default="MEMBER")
    
    # 両側へのリレーション
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
```

#### 4. **クエリの実装パターン**

```python
# backend/app/services/user_service.py
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    # 基本的なクエリ
    def get_user_by_email(self, email: str) -> User:
        return self.db.query(User).filter(
            User.email == email
        ).first()
    
    # N+1問題を避けるクエリ（joinedload使用）
    def get_users_with_roles(self) -> List[User]:
        return self.db.query(User).options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        ).all()
    
    # 条件付きクエリ
    def get_active_project_members(self, project_id: int) -> List[User]:
        return self.db.query(User).join(
            ProjectMember
        ).filter(
            and_(
                ProjectMember.project_id == project_id,
                User.is_active == True
            )
        ).all()
    
    # 集計クエリ
    def get_user_statistics(self) -> dict:
        return self.db.query(
            func.count(User.id).label('total_users'),
            func.count(User.id).filter(User.is_active == True).label('active_users')
        ).first()
    
    # ページネーション
    def get_users_paginated(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()
```

#### 5. **トランザクション管理**

```python
# backend/app/services/project_service.py
from contextlib import contextmanager

class ProjectService:
    @contextmanager
    def transaction(self):
        """トランザクション管理のコンテキストマネージャー"""
        try:
            yield self.db
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
    
    def create_project_with_members(self, project_data: dict, member_ids: List[int]):
        """トランザクション内で複数の操作を実行"""
        with self.transaction():
            # プロジェクト作成
            project = Project(**project_data)
            self.db.add(project)
            self.db.flush()  # IDを生成（コミット前）
            
            # メンバー追加
            for user_id in member_ids:
                member = ProjectMember(
                    project_id=project.id,
                    user_id=user_id
                )
                self.db.add(member)
            
            # ここで自動的にコミット（またはエラー時はロールバック）
```

### SQLAlchemy 2.0 の新機能

#### 1. **型アノテーションのサポート**

```python
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class User(BaseModel):
    __tablename__ = "users"
    
    # SQLAlchemy 2.0スタイル（型アノテーション付き）
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
```

#### 2. **新しいクエリスタイル**

```python
from sqlalchemy import select

# 従来のスタイル
users = db.query(User).filter(User.is_active == True).all()

# SQLAlchemy 2.0スタイル
stmt = select(User).where(User.is_active == True)
users = db.execute(stmt).scalars().all()
```

## 🗄️ データベース設計の概要

Team Insightのデータベースは以下の原則に基づいて設計されています：

### 設計原則

1. **スキーマ分離**: すべてのテーブルは`team_insight`スキーマに配置
   ```sql
   -- スキーマとは：データベース内の名前空間
   -- 例：team_insight.users（team_insightスキーマのusersテーブル）
   CREATE SCHEMA IF NOT EXISTS team_insight;
   ```

2. **UUID主キー**: すべてのテーブルでUUIDを使用
   ```sql
   -- UUID = Universally Unique Identifier
   -- 例：550e8400-e29b-41d4-a716-446655440000
   -- メリット：グローバルに一意、分散システムに適している
   id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
   ```

3. **監査フィールド**: created_at、updated_atを標準装備
   ```sql
   -- いつ作成・更新されたかを自動記録
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   ```

4. **インデックス戦略**: 検索頻度の高いカラムにインデックス設定
   ```sql
   -- インデックス = 本の索引のようなもの
   -- 検索を高速化するが、容量は増える
   CREATE INDEX idx_users_email ON users(email);
   ```

### データベース接続情報

```python
# backend/app/core/config.py より
DATABASE_URL = "postgresql://teaminsight:teaminsight@postgres:5432/teaminsight"
#              postgresql://ユーザー名:パスワード@ホスト:ポート/データベース名

# SQLAlchemy設定
SQLALCHEMY_DATABASE_URI = DATABASE_URL
```

## 📊 テーブル設計

### 🔑 データベース設計の基本概念

#### 1. 主キー（Primary Key）とは？

```sql
-- 主キー = そのテーブルでレコードを一意に識別するカラム
-- 例：学生証番号、社員番号、ISBN

CREATE TABLE students (
    student_id VARCHAR(10) PRIMARY KEY,  -- これが主キー
    name VARCHAR(100),
    email VARCHAR(255)
);

-- Team Insightでは全テーブルでUUIDを使用
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
```

#### 2. 外部キー（Foreign Key）とは？

```sql
-- 外部キー = 他のテーブルの主キーを参照するカラム
-- テーブル間の関係を定義する

CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),  -- usersテーブルのidを参照
    total_amount DECIMAL(10,2)
);
```

#### 3. 正規化とは？

**正規化 = データの重複を排除し、整合性を保つための設計手法**

```
❌ 悪い例（非正規化）：
注文テーブル
┌────┬──────────┬───────────┬──────────────┐
│ id │ 商品名    │ 顧客名     │ 顧客住所      │
├────┼──────────┼───────────┼──────────────┤
│ 1  │ ノート    │ 田中太郎   │ 東京都...     │
│ 2  │ ペン      │ 田中太郎   │ 東京都...     │ ← 同じ情報が重複
└────┴──────────┴───────────┴──────────────┘

✅ 良い例（正規化）：
注文テーブル                    顧客テーブル
┌────┬──────────┬──────┐     ┌────┬───────────┬──────────────┐
│ id │ 商品名    │ 顧客ID│     │ id │ 顧客名     │ 顧客住所      │
├────┼──────────┼──────┤     ├────┼───────────┼──────────────┤
│ 1  │ ノート    │ 101  │ ←→  │101 │ 田中太郎   │ 東京都...     │
│ 2  │ ペン      │ 101  │     └────┴───────────┴──────────────┘
└────┴──────────┴──────┘
```

### ER図（Entity Relationship Diagram）

**ER図 = テーブル間の関係を視覚的に表現した図**

```
記号の意味：
────  : 1対1の関係
───<  : 1対多の関係（1人のユーザーが複数のタスクを持つ）
>──<  : 多対多の関係（中間テーブルが必要）

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   users     │────<│ project_     │>────│  projects   │
│  （ユーザー） │     │ members      │     │（プロジェクト）│
└─────────────┘     │ （中間テーブル）│     └─────────────┘
       │            └──────────────┘              │
       │                                         │
       ▼                                         ▼
┌─────────────┐                          ┌─────────────┐
│ user_roles  │                          │    tasks    │
│ （ユーザー   │                          │  （タスク）   │
│  ロール）    │                          │             │
└─────────────┘                          └─────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   roles     │────<│ role_        │
│  （ロール）   │     │ permissions  │
└─────────────┘     │ （ロール権限） │
                    └──────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │ permissions │
                    │   （権限）    │
                    └─────────────┘
```

### 主要テーブルの詳細

#### 1. usersテーブル

```sql
CREATE TABLE team_insight.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backlog_id VARCHAR(50) UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    timezone VARCHAR(50) DEFAULT 'Asia/Tokyo',
    locale VARCHAR(10) DEFAULT 'ja',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- インデックス
CREATE INDEX idx_users_email ON team_insight.users(email);
CREATE INDEX idx_users_backlog_id ON team_insight.users(backlog_id);
```

#### 📝 SQLAlchemyモデルの解説

```python
# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid

class User(Base):
    """
    ユーザーテーブルのモデル定義
    SQLAlchemyがこのクラスをSQLテーブルにマッピングする
    """
    
    # === テーブル設定 ===
    __tablename__ = "users"  # 実際のテーブル名
    __table_args__ = {"schema": "team_insight"}  # スキーマ指定
    
    # === カラム定義（各フィールドの説明）===
    
    # 主キー：UUID型で自動生成
    id = Column(
        UUID(as_uuid=True),      # UUID型（Pythonのuuid.UUIDとして扱える）
        primary_key=True,        # これが主キー
        default=uuid.uuid4       # デフォルト値：新規作成時に自動でUUID生成
    )
    
    # Backlog連携用のID（ユニーク制約＋インデックス）
    backlog_id = Column(
        String(50),             # 文字列型（最大50文字）
        unique=True,            # 重複を許さない
        index=True              # 検索高速化のためインデックス作成
    )
    
    # メールアドレス（必須項目）
    email = Column(
        String(255),            # 文字列型（最大255文字）
        unique=True,            # 重複を許さない
        index=True,             # 検索高速化
        nullable=False          # NULL不可（必須項目）
    )
    
    # 名前（必須項目）
    name = Column(
        String(100),            # 文字列型（最大100文字）
        nullable=False          # NULL不可
    )
    
    # アクティブフラグ（論理削除用）
    is_active = Column(
        Boolean,                # 真偽値型（True/False）
        default=True            # デフォルト値：True
    )
    
    # タイムゾーン設定
    timezone = Column(
        String(50),             
        default="Asia/Tokyo"    # デフォルト値：日本時間
    )
    
    # ロケール（言語設定）
    locale = Column(
        String(10),             
        default="ja"            # デフォルト値：日本語
    )
    
    # 作成日時（自動設定）
    created_at = Column(
        DateTime,               # 日時型
        server_default=func.now()  # DB側で現在時刻を自動設定
    )
    
    # 更新日時（自動更新）
    updated_at = Column(
        DateTime,
        server_default=func.now(),     # 作成時：現在時刻
        onupdate=func.now()            # 更新時：自動的に現在時刻
    )
    
    # 最終ログイン日時（NULL許可）
    last_login = Column(
        DateTime,               
        nullable=True           # NULL許可（未ログインの場合）
    )
    
    # === リレーションシップ（他のテーブルとの関係）===
    
    # 1対多：1人のユーザーが複数のロールを持つ
    user_roles = relationship(
        "UserRole",                    # 関連するモデル名
        back_populates="user",         # 逆参照の属性名
        cascade="all, delete-orphan"   # ユーザー削除時に関連も削除
    )
    
    # 1対多：1人のユーザーが複数のプロジェクトに参加
    project_members = relationship(
        "ProjectMember",
        back_populates="user"
    )
    
    # 1対多：1人のユーザーが複数のタスクを担当
    tasks = relationship(
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assignee_id"  # 外部キーを明示
    )
    
    # === 便利なメソッド ===
    def __repr__(self):
        """デバッグ時の表示用"""
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"
```

#### 🔗 リレーションシップの使い方

```python
# ユーザーから関連データを取得
user = db.query(User).first()

# ユーザーのロール一覧
for user_role in user.user_roles:
    print(f"ロール: {user_role.role.name}")

# ユーザーが参加しているプロジェクト
for member in user.project_members:
    print(f"プロジェクト: {member.project.name}")

# ユーザーが担当しているタスク
for task in user.tasks:
    print(f"タスク: {task.summary}")
```

#### 2. projectsテーブル

```sql
CREATE TABLE team_insight.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backlog_project_id INTEGER UNIQUE,
    project_key VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_projects_project_key ON team_insight.projects(project_key);
CREATE INDEX idx_projects_is_active ON team_insight.projects(is_active);
```

#### 3. tasksテーブル

```sql
CREATE TABLE team_insight.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES team_insight.projects(id),
    backlog_issue_id INTEGER UNIQUE,
    issue_key VARCHAR(50) UNIQUE NOT NULL,
    summary VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    priority VARCHAR(20),
    assignee_id UUID REFERENCES team_insight.users(id),
    created_by_id UUID REFERENCES team_insight.users(id),
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    start_date TIMESTAMP,
    due_date TIMESTAMP,
    completed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_tasks_project_id ON team_insight.tasks(project_id);
CREATE INDEX idx_tasks_assignee_id ON team_insight.tasks(assignee_id);
CREATE INDEX idx_tasks_status ON team_insight.tasks(status);
CREATE INDEX idx_tasks_due_date ON team_insight.tasks(due_date);
```

## 🔧 SQLAlchemy 2.0の使い方

### 📚 SQLAlchemyの基本概念

#### セッションとは？

```python
# セッション = データベースとの会話
# 複数の操作をまとめて管理する仕組み

from sqlalchemy.orm import Session

# セッションの基本的な流れ
db = Session()  # セッション開始
try:
    # データベース操作
    user = User(name="田中")
    db.add(user)  # 追加（まだDBには反映されない）
    db.commit()   # 確定（ここでDBに反映）
except:
    db.rollback()  # エラー時は巻き戻し
finally:
    db.close()    # セッション終了
```

### 基本的なクエリパターン

#### 1. SELECT文の実行（データ取得）

```python
# backend/app/services/user_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select  # SQLAlchemy 2.0の新しい書き方
from typing import List, Optional
from app.models.user import User

class UserService:
    def __init__(self, db: Session):
        """
        サービスクラスの初期化
        dbセッションを受け取って保持
        """
        self.db = db
    
    # === 基本的なSELECT ===
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        メールアドレスでユーザーを検索
        
        流れ：
        1. SQL文を構築（まだ実行されない）
        2. execute()で実行
        3. 結果を取得
        """
        # STEP 1: SQL文を構築（SELECT * FROM users WHERE email = ?）
        stmt = select(User).where(User.email == email)
        
        # STEP 2: 実行して結果を取得
        result = self.db.execute(stmt)
        
        # STEP 3: 結果を処理
        # scalar_one_or_none(): 1件取得（なければNone）
        return result.scalar_one_or_none()
        
        # 他の結果取得メソッド：
        # .scalar_one()    → 1件取得（なければエラー）
        # .scalars().all() → 全件取得（リスト）
        # .scalars().first() → 最初の1件（なければNone）
    
    # === 複数条件での検索 ===
    def get_active_users(self, limit: int = 100) -> List[User]:
        """
        アクティブなユーザー一覧を取得
        
        SQLに変換すると：
        SELECT * FROM team_insight.users 
        WHERE is_active = true 
        ORDER BY created_at DESC 
        LIMIT 100
        """
        stmt = (
            select(User)
            .where(User.is_active == True)      # WHERE句
            .order_by(User.created_at.desc())   # ORDER BY句（降順）
            .limit(limit)                       # LIMIT句
        )
        
        # 実行して全件取得
        return self.db.execute(stmt).scalars().all()
    
    # === 複雑な条件 ===
    def search_users(
        self, 
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """動的な検索条件の構築"""
        
        # 基本のクエリ
        stmt = select(User)
        
        # 条件を動的に追加
        if keyword:
            # OR条件：名前またはメールに含まれる
            stmt = stmt.where(
                (User.name.contains(keyword)) | 
                (User.email.contains(keyword))
            )
        
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        
        # 並び順
        stmt = stmt.order_by(User.name)
        
        return self.db.execute(stmt).scalars().all()
```

#### 🔍 クエリメソッドの解説

| メソッド | 説明 | 使用例 |
|---------|------|--------|
| `where()` | 条件指定（WHERE句） | `.where(User.age > 20)` |
| `order_by()` | 並び替え（ORDER BY句） | `.order_by(User.name.asc())` |
| `limit()` | 件数制限（LIMIT句） | `.limit(10)` |
| `offset()` | 開始位置（OFFSET句） | `.offset(20)` |
| `distinct()` | 重複削除（DISTINCT） | `.distinct()` |

#### 条件式の書き方

```python
# 等価
User.name == "田中"

# 不等価
User.name != "田中"

# 大小比較
User.age > 20
User.age >= 20
User.age < 30
User.age <= 30

# LIKE検索
User.name.like("%田中%")      # %でワイルドカード
User.name.contains("田中")    # 部分一致（自動で%を付ける）
User.name.startswith("田")   # 前方一致
User.name.endswith("郎")     # 後方一致

# IN句
User.status.in_(["active", "pending"])

# NULL判定
User.deleted_at.is_(None)    # IS NULL
User.deleted_at.isnot(None)  # IS NOT NULL

# AND条件
stmt.where(User.is_active == True, User.age > 20)

# OR条件
from sqlalchemy import or_
stmt.where(or_(User.name == "田中", User.name == "佐藤"))
```

#### 2. JOINを使った複雑なクエリ

##### 🔗 JOINの基本概念

```
JOINとは：複数のテーブルを結合してデータを取得する

例：ユーザーとその担当タスクを一緒に取得
┌─────────────┐        ┌─────────────┐
│   users     │   JOIN │    tasks    │
├─────────────┤   ON   ├─────────────┤
│ id: 1       │ ←───── │ assignee_id:1│
│ name: 田中   │        │ summary: ...│
└─────────────┘        └─────────────┘
```

```python
from sqlalchemy.orm import selectinload, joinedload
from app.models.project import Project, ProjectMember
from app.models.user import User

def get_user_projects_with_members(self, user_id: UUID) -> List[Project]:
    """
    ユーザーが参加しているプロジェクトをメンバー情報付きで取得
    
    SQLイメージ：
    SELECT projects.*, project_members.*, users.*
    FROM projects
    JOIN project_members ON projects.id = project_members.project_id
    JOIN users ON project_members.user_id = users.id
    WHERE project_members.user_id = ?
    """
    
    # === N+1問題とは？ ===
    # 悪い例：プロジェクトごとにメンバー取得クエリが発生
    # projects = db.query(Project).all()  # 1回
    # for project in projects:
    #     members = project.project_members  # N回（プロジェクト数分）
    
    # === 解決策：joinedloadで一度に取得 ===
    stmt = (
        select(Project)
        .join(ProjectMember)  # ProjectMemberテーブルとJOIN
        .where(ProjectMember.user_id == user_id)  # 条件
        .options(
            # 関連データを事前に読み込み（Eager Loading）
            joinedload(Project.project_members)  # プロジェクトのメンバー
            .joinedload(ProjectMember.user)      # 各メンバーのユーザー情報
        )
        .order_by(Project.created_at.desc())
    )
    
    # unique()：JOINによる重複を除去
    return self.db.execute(stmt).unique().scalars().all()

# === ロード戦略の違い ===
def demonstrate_loading_strategies(self, project_id: UUID):
    """異なるロード戦略の説明"""
    
    # 1. joinedload：1つのクエリでJOINして取得（1対1、多対1向け）
    stmt1 = (
        select(Project)
        .where(Project.id == project_id)
        .options(joinedload(Project.created_by))  # 作成者（1対1）
    )
    
    # 2. selectinload：別クエリで取得（1対多向け、メモリ効率的）
    stmt2 = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.tasks))  # タスク一覧（1対多）
    )
    
    # 3. lazyload（デフォルト）：アクセス時に取得
    project = self.db.get(Project, project_id)
    # tasks = project.tasks  # この時点でクエリ実行
```

#### 3. データの作成・更新・削除

##### 📝 INSERT（作成）

```python
def create_user(self, user_data: dict) -> User:
    """
    新規ユーザーを作成
    
    処理の流れ：
    1. モデルインスタンスを作成
    2. セッションに追加
    3. コミットしてDBに反映
    """
    
    # === 方法1：個別に属性を設定 ===
    user = User()
    user.name = user_data["name"]
    user.email = user_data["email"]
    user.is_active = True
    
    # === 方法2：コンストラクタで一括設定 ===
    user = User(
        name=user_data["name"],
        email=user_data["email"],
        is_active=True
    )
    
    # === 方法3：辞書から展開 ===
    user = User(**user_data)
    
    # DBに追加（まだ保存されない）
    self.db.add(user)
    
    # コミット（ここで実際にINSERT文が実行される）
    self.db.commit()
    
    # リフレッシュ（DBで生成されたIDなどを取得）
    self.db.refresh(user)
    
    return user

def create_multiple_users(self, users_data: List[dict]) -> List[User]:
    """複数ユーザーを一括作成"""
    
    users = []
    for data in users_data:
        user = User(**data)
        self.db.add(user)
        users.append(user)
    
    # 一度にコミット（トランザクション）
    self.db.commit()
    
    return users
```

##### ✏️ UPDATE（更新）

```python
def update_user(self, user_id: UUID, update_data: dict) -> Optional[User]:
    """
    ユーザー情報を更新
    
    注意点：
    - 必ず既存のオブジェクトを取得してから更新
    - 部分更新も可能
    """
    
    # STEP 1: 既存のユーザーを取得
    user = self.db.get(User, user_id)
    if not user:
        return None
    
    # STEP 2: 属性を更新
    # 方法1：個別に更新
    user.name = update_data.get("name", user.name)
    user.email = update_data.get("email", user.email)
    
    # 方法2：ループで更新
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    # STEP 3: コミット
    self.db.commit()
    self.db.refresh(user)
    
    return user

def bulk_update_status(self, user_ids: List[UUID], is_active: bool):
    """複数ユーザーのステータスを一括更新"""
    
    # 一括UPDATE（効率的）
    stmt = (
        update(User)
        .where(User.id.in_(user_ids))
        .values(is_active=is_active, updated_at=func.now())
    )
    
    self.db.execute(stmt)
    self.db.commit()
```

##### 🗑️ DELETE（削除）

```python
def delete_user(self, user_id: UUID) -> bool:
    """
    ユーザーを削除
    
    注意：外部キー制約がある場合は関連データも考慮
    """
    
    # 方法1：オブジェクトを取得してから削除
    user = self.db.get(User, user_id)
    if not user:
        return False
    
    self.db.delete(user)
    self.db.commit()
    return True

def soft_delete_user(self, user_id: UUID) -> bool:
    """
    論理削除（実際には削除せず、フラグを更新）
    
    メリット：
    - データが残るので復元可能
    - 履歴として参照可能
    """
    
    user = self.db.get(User, user_id)
    if not user:
        return False
    
    user.is_active = False
    user.deleted_at = func.now()
    
    self.db.commit()
    return True

def bulk_delete_old_data(self, days: int = 90):
    """古いデータを一括削除"""
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    stmt = (
        delete(OAuthState)
        .where(OAuthState.created_at < cutoff_date)
    )
    
    result = self.db.execute(stmt)
    self.db.commit()
    
    return result.rowcount  # 削除された行数
```

#### 3. 集計クエリ

```python
from sqlalchemy import func, and_
from app.models.task import Task

def get_project_statistics(self, project_id: UUID) -> dict:
    """プロジェクトの統計情報を取得"""
    
    # タスク数の集計
    total_tasks = self.db.query(func.count(Task.id)).filter(
        Task.project_id == project_id
    ).scalar()
    
    # ステータス別タスク数
    status_counts = (
        self.db.query(
            Task.status,
            func.count(Task.id).label('count')
        )
        .filter(Task.project_id == project_id)
        .group_by(Task.status)
        .all()
    )
    
    # 担当者別タスク数（完了タスクのみ）
    assignee_stats = (
        self.db.query(
            User.name,
            func.count(Task.id).label('completed_count'),
            func.sum(Task.actual_hours).label('total_hours')
        )
        .join(Task, Task.assignee_id == User.id)
        .filter(
            and_(
                Task.project_id == project_id,
                Task.status == 'completed'
            )
        )
        .group_by(User.id, User.name)
        .all()
    )
    
    return {
        'total_tasks': total_tasks,
        'status_breakdown': dict(status_counts),
        'assignee_stats': [
            {
                'name': name,
                'completed_count': count,
                'total_hours': float(hours or 0)
            }
            for name, count, hours in assignee_stats
        ]
    }
```

### トランザクション管理

#### 💰 トランザクションとは？

**トランザクション = 複数の操作をまとめて「全部成功」か「全部失敗」にする仕組み**

```
銀行振込の例：
1. Aさんの口座から1万円引く
2. Bさんの口座に1万円足す

もし2の途中でエラーが起きたら？
→ トランザクションがないと、Aさんのお金だけ消える！
→ トランザクションがあれば、全部なかったことになる（ロールバック）
```

#### 🔄 ACID特性

トランザクションが保証する4つの性質：

| 特性 | 意味 | 例 |
|------|------|-----|
| **A**tomicity（原子性） | 全部成功か全部失敗 | 振込の途中で止まらない |
| **C**onsistency（一貫性） | データの整合性を保つ | 残高がマイナスにならない |
| **I**solation（独立性） | 他の処理と干渉しない | 同時振込でも正しく処理 |
| **D**urability（永続性） | 確定したら消えない | 停電してもデータは残る |

#### 📝 トランザクションの実装

```python
# backend/app/services/project_service.py
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager

def create_project_with_members(
    self, 
    project_data: ProjectCreate,
    member_ids: List[UUID]
) -> Project:
    """
    プロジェクトを作成し、メンバーを追加（トランザクション使用）
    
    処理内容：
    1. プロジェクトを作成
    2. メンバーを追加
    → どちらか失敗したら全部取り消し
    """
    
    try:
        # === 明示的なトランザクション開始 ===
        with self.db.begin():  # トランザクション開始
            
            # STEP 1: プロジェクト作成
            project = Project(**project_data.dict())
            self.db.add(project)
            
            # flush(): IDを生成するが、まだコミットしない
            self.db.flush()  
            
            # STEP 2: メンバー追加
            for user_id in member_ids:
                # ユーザーが存在するかチェック
                user = self.db.get(User, user_id)
                if not user:
                    raise ValueError(f"ユーザー {user_id} が見つかりません")
                
                member = ProjectMember(
                    project_id=project.id,
                    user_id=user_id,
                    role="MEMBER"
                )
                self.db.add(member)
            
            # withブロックを出る時に自動的にコミット
        
        # トランザクション成功後の処理
        self.db.refresh(project)  # 最新データを取得
        return project
        
    except IntegrityError as e:
        # データベースの制約違反（重複など）
        # ロールバックは自動実行される
        logger.error(f"データ整合性エラー: {str(e)}")
        raise ValueError("プロジェクトの作成に失敗しました")
    
    except Exception as e:
        # その他のエラー
        logger.error(f"予期しないエラー: {str(e)}")
        raise

# === 手動でのトランザクション管理 ===
def manual_transaction_example(self):
    """手動でトランザクションを管理する例"""
    
    # トランザクション開始
    trans = self.db.begin()
    
    try:
        # 何か処理
        user = User(name="テスト")
        self.db.add(user)
        
        # 成功したらコミット
        trans.commit()
        
    except Exception:
        # 失敗したらロールバック
        trans.rollback()
        raise
    
# === ネストしたトランザクション ===
def nested_transaction_example(self):
    """セーブポイントを使った部分的なロールバック"""
    
    with self.db.begin():
        # メイントランザクション
        user1 = User(name="ユーザー1")
        self.db.add(user1)
        
        # セーブポイント（部分的なトランザクション）
        with self.db.begin_nested():
            user2 = User(name="ユーザー2")
            self.db.add(user2)
            
            # ここでエラーが起きても、user1は残る
            if some_condition:
                raise ValueError("user2だけロールバック")
        
        # メイントランザクションは継続
        user3 = User(name="ユーザー3")
        self.db.add(user3)
```

#### ⚠️ トランザクションの注意点

```python
# ❌ 悪い例：長いトランザクション
with db.begin():
    users = db.query(User).with_for_update().all()  # 全ユーザーをロック
    
    # 時間のかかる処理（APIコールなど）
    for user in users:
        external_api_call(user)  # 他のユーザーが待たされる！
    
    # やっと更新
    for user in users:
        user.processed = True

# ✅ 良い例：必要最小限のトランザクション
# まず必要なデータを取得
user_ids = [u.id for u in db.query(User).filter(User.processed == False).all()]

# API処理（トランザクション外）
results = {}
for user_id in user_ids:
    results[user_id] = external_api_call(user_id)

# 更新だけトランザクション内で
with db.begin():
    for user_id, result in results.items():
        user = db.get(User, user_id)
        if user:
            user.processed = True
            user.result = result
```

## 🔄 Alembicによるマイグレーション

### 📚 マイグレーションとは？

**マイグレーション = データベースの構造（スキーマ）を変更する作業**

```
現実世界で例えると：
家のリフォーム = マイグレーション

1. 現在の状態を記録（設計図）
2. 変更内容を計画（リフォーム計画書）
3. 実際に工事（マイグレーション実行）
4. 元に戻せる手順も用意（ロールバック）
```

### なぜマイグレーションが必要？

```
手動でテーブル変更する場合の問題：
- 開発環境と本番環境で構造が違ってくる
- 誰がいつ何を変更したか分からない
- チームメンバー間で同期が取れない
- 間違えたときに戻せない

マイグレーションツール（Alembic）を使うと：
✅ 変更履歴が残る（Gitで管理可能）
✅ チーム全員が同じ構造を共有
✅ 本番環境への適用も安全
✅ 間違えても前のバージョンに戻せる
```

### Alembicの基本概念

Alembicは、データベーススキーマのバージョン管理ツールです。

### ディレクトリ構造

```
backend/
├── alembic.ini              # Alembic設定ファイル
├── migrations/
│   ├── README
│   ├── env.py              # マイグレーション環境設定
│   ├── script.py.mako      # マイグレーションテンプレート
│   └── versions/           # マイグレーションファイル
│       ├── 001_initial_schema.py
│       ├── 002_add_teams_table.py
│       └── ...
```

### 新しいマイグレーションの作成

#### 🎯 マイグレーションの流れ

```
1. モデルを変更（Python）
   ↓
2. マイグレーションファイルを生成
   ↓
3. 生成されたファイルを確認・修正
   ↓
4. マイグレーションを実行
   ↓
5. データベースに反映
```

#### 1. 自動生成（推奨）

##### STEP 1: モデルに変更を加える

```python
# backend/app/models/user.py
class User(Base):
    # 既存のフィールド...
    
    # 新しいフィールドを追加
    phone_number = Column(String(20), nullable=True)  # 電話番号を追加
```

##### STEP 2: マイグレーションファイルを自動生成

```bash
# Alembicがモデルの変更を検出して、マイグレーションファイルを作成
docker-compose exec backend alembic revision --autogenerate -m "add phone_number to users"

# 出力例：
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.autogenerate.compare] Detected added column 'team_insight.users.phone_number'
# Generating /app/migrations/versions/abc123_add_phone_number_to_users.py ... done
```

##### STEP 3: 生成されたファイルを確認

```python
# migrations/versions/abc123_add_phone_number_to_users.py
"""add phone_number to users

Revision ID: abc123      # このマイグレーションのID（自動生成）
Revises: def456         # 前のマイグレーションのID
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# === リビジョン情報（変更不要）===
revision = 'abc123'      # このマイグレーションの識別子
down_revision = 'def456' # 直前のマイグレーション
branch_labels = None
depends_on = None

def upgrade() -> None:
    """
    アップグレード処理（新しいバージョンへ）
    この関数が実行されると、データベースが更新される
    """
    # カラムを追加
    op.add_column(
        'users',                                    # テーブル名
        sa.Column(                                  # 新しいカラム
            'phone_number',                         # カラム名
            sa.String(20),                          # データ型
            nullable=True                           # NULL許可
        ),
        schema='team_insight'                       # スキーマ名
    )

def downgrade() -> None:
    """
    ダウングレード処理（前のバージョンへ戻す）
    upgrade()の逆の処理を書く
    """
    # カラムを削除
    op.drop_column(
        'users',              # テーブル名
        'phone_number',       # カラム名
        schema='team_insight' # スキーマ名
    )
```

#### 🔍 Alembicの操作関数

```python
# よく使うAlembic操作関数

# テーブル操作
op.create_table('table_name', ...)      # テーブル作成
op.drop_table('table_name')             # テーブル削除
op.rename_table('old_name', 'new_name') # テーブル名変更

# カラム操作
op.add_column('table', column)          # カラム追加
op.drop_column('table', 'column_name')  # カラム削除
op.alter_column('table', 'column',      # カラム変更
    new_column_name='new_name',
    type_=sa.String(100),
    nullable=False
)

# インデックス操作
op.create_index('idx_name', 'table', ['column'])  # インデックス作成
op.drop_index('idx_name', 'table')                # インデックス削除

# 外部キー操作
op.create_foreign_key(
    'fk_name', 'source_table', 'target_table',
    ['source_column'], ['target_column']
)
op.drop_constraint('fk_name', 'table')
```

#### 2. 手動作成（複雑な変更時）

```bash
# 空のマイグレーションファイルを作成
docker-compose exec backend alembic revision -m "complex data migration"
```

複雑なデータ移行の例：

```python
def upgrade() -> None:
    # 1. 新しいカラムを追加
    op.add_column(
        'tasks',
        sa.Column('priority_level', sa.Integer(), nullable=True),
        schema='team_insight'
    )
    
    # 2. 既存データを移行
    connection = op.get_bind()
    result = connection.execute(
        sa.text("""
        UPDATE team_insight.tasks 
        SET priority_level = CASE 
            WHEN priority = 'HIGH' THEN 3
            WHEN priority = 'MEDIUM' THEN 2
            WHEN priority = 'LOW' THEN 1
            ELSE 2
        END
        """)
    )
    
    # 3. NOT NULL制約を追加
    op.alter_column(
        'tasks', 'priority_level',
        nullable=False,
        schema='team_insight'
    )
```

### マイグレーションの実行

```bash
# 最新版まで更新
make migrate

# または直接実行
docker-compose exec backend alembic upgrade head

# 特定のリビジョンまで更新
docker-compose exec backend alembic upgrade abc123

# 1つ前に戻す
make migrate-down

# 履歴確認
make migrate-history
```

### マイグレーションのベストプラクティス

1. **必ず開発環境でテスト**
   ```bash
   # テスト用DBで確認
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

2. **データの安全性を確保**
   ```python
   def upgrade():
       # バックアップテーブルを作成
       op.execute("""
           CREATE TABLE team_insight.users_backup AS 
           SELECT * FROM team_insight.users
       """)
       
       # 危険な操作を実行
       # ...
   ```

3. **段階的なマイグレーション**
   ```python
   def upgrade():
       # Step 1: カラムを追加（NULL許可）
       op.add_column('users', sa.Column('new_field', sa.String()))
       
       # Step 2: デフォルト値を設定
       op.execute("UPDATE team_insight.users SET new_field = 'default'")
       
       # Step 3: NOT NULL制約を追加
       op.alter_column('users', 'new_field', nullable=False)
   ```

## 🚀 パフォーマンス最適化

### 📊 インデックスとは？

**インデックス = データベースの「索引」**

```
本で例えると：
┌─────────────────────────────┐
│         辞書                 │
├─────────────────────────────┤
│ 目次（インデックスなし）       │
│ → 全ページを見る必要がある     │
│                             │
│ 索引（インデックスあり）       │
│ → 「田中」は523ページ         │
│ → すぐに見つかる！            │
└─────────────────────────────┘
```

#### インデックスの仕組み

```
テーブル：users（100万件）
┌────┬──────┬─────────────────┐
│ id │ name │ email           │
├────┼──────┼─────────────────┤
│ 1  │ 田中 │ tanaka@...      │
│ 2  │ 佐藤 │ sato@...        │
│ ...│ ...  │ ...             │
└────┴──────┴─────────────────┘

インデックスなし：
SELECT * FROM users WHERE email = 'tanaka@example.com'
→ 100万件全部チェック（遅い！）

インデックスあり（emailカラム）：
CREATE INDEX idx_users_email ON users(email);
→ 索引を使って一発で見つかる（速い！）
```

#### インデックスのメリット・デメリット

| メリット | デメリット |
|----------|-----------|
| 検索が高速化 | 容量が増える |
| ソートが速い | 更新が遅くなる |
| 一意性を保証できる | メンテナンスが必要 |

### インデックス戦略

#### 1. 適切なインデックスの設計

```python
# backend/app/models/task.py
class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        # === 単一カラムインデックス ===
        # よく検索されるカラムに設定
        Index('idx_task_status', 'status'),
        Index('idx_task_assignee', 'assignee_id'),
        
        # === 複合インデックス ===
        # 複数カラムを組み合わせて検索する場合
        # 例：WHERE project_id = ? AND status = ?
        Index('idx_task_project_status', 'project_id', 'status'),
        
        # === 部分インデックス（PostgreSQL特有）===
        # 特定の条件のレコードだけインデックス化
        # 完了していないタスクの期限だけインデックス
        Index(
            'idx_task_active_due_date',
            'due_date',
            postgresql_where=text("status != 'completed'")
        ),
        
        {"schema": "team_insight"}
    )
    
    # カラム定義でもインデックス指定可能
    email = Column(String(255), index=True)  # 単純なインデックス
    code = Column(String(50), unique=True)   # ユニークインデックス
```

#### インデックスを作るべきカラム

```python
# ✅ インデックスを作るべき
- 主キー、外部キー（自動的に作成される）
- WHERE句でよく使うカラム
- ORDER BY句でよく使うカラム  
- JOIN条件で使うカラム
- ユニーク制約があるカラム

# ❌ インデックスを避けるべき
- 更新頻度が高いカラム
- カーディナリティが低い（値の種類が少ない）カラム
  例：is_active（true/falseの2種類のみ）
- テキスト型の長いカラム
- ほとんど検索しないカラム
```

#### 2. インデックスの分析

```sql
-- 未使用のインデックスを検出
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE schemaname = 'team_insight'
    AND idx_scan = 0
ORDER BY tablename, indexname;

-- インデックスのサイズ確認
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'team_insight'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### クエリ最適化

#### 1. N+1問題の解決

```python
# ❌ 悪い例：N+1問題が発生
projects = db.query(Project).all()
for project in projects:
    # 各プロジェクトごとにクエリが発生
    member_count = len(project.project_members)

# ✅ 良い例：joinedloadで一度に取得
from sqlalchemy.orm import joinedload

projects = (
    db.query(Project)
    .options(joinedload(Project.project_members))
    .all()
)
```

#### 2. 適切なロード戦略の選択

```python
# selectinload: 別クエリで関連データを取得（1対多で有効）
projects = (
    db.query(Project)
    .options(selectinload(Project.tasks))
    .all()
)

# subqueryload: サブクエリで取得（レガシー、selectinloadを推奨）
# joinedload: JOINで取得（1対1、多対1で有効）
user = (
    db.query(User)
    .options(joinedload(User.current_project))
    .first()
)

# lazy='dynamic': 大量データの場合
class Project(Base):
    tasks = relationship("Task", lazy="dynamic")

# 使用時に絞り込み可能
active_tasks = project.tasks.filter(Task.status == 'active').all()
```

#### 3. バルク操作

```python
# ❌ 悪い例：1件ずつINSERT
for data in task_data_list:
    task = Task(**data)
    db.add(task)
    db.commit()

# ✅ 良い例：bulk_insert_mappings
task_mappings = [
    {
        "id": uuid.uuid4(),
        "project_id": project_id,
        "summary": f"Task {i}",
        "status": "open"
    }
    for i in range(1000)
]
db.bulk_insert_mappings(Task, task_mappings)
db.commit()

# ✅ さらに高速：COPY（PostgreSQL専用）
from io import StringIO
import csv

buffer = StringIO()
writer = csv.writer(buffer)
for task in tasks:
    writer.writerow([task.id, task.project_id, task.summary])

buffer.seek(0)
connection = db.connection().connection
cursor = connection.cursor()
cursor.copy_from(
    buffer,
    'team_insight.tasks',
    columns=['id', 'project_id', 'summary'],
    sep=','
)
connection.commit()
```

### 接続プールの設定

```python
# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings

# プール設定の最適化
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # 常時接続数
    max_overflow=10,       # 最大追加接続数
    pool_timeout=30,       # 接続待機タイムアウト
    pool_recycle=3600,     # 接続リサイクル時間（1時間）
    pool_pre_ping=True,    # 接続確認を有効化
    echo=settings.DEBUG,   # SQLログ（開発時のみ）
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

## 🔍 データベースデバッグのコツ

### 1. SQLログの活用

```python
# 開発環境でのSQLログ設定
import logging

# SQLAlchemyのロガーを設定
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)

# 特定のクエリだけログ出力
from sqlalchemy import event

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    if "SELECT" in statement:
        logger.info(f"Query: {statement}")
        logger.info(f"Params: {params}")
```

### 2. クエリプランの確認

```python
# backend/app/utils/db_debug.py
def explain_query(db: Session, query):
    """クエリの実行計画を表示"""
    sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
    
    result = db.execute(f"EXPLAIN ANALYZE {sql}")
    for row in result:
        print(row[0])

# 使用例
query = db.query(Task).join(Project).filter(Task.status == 'active')
explain_query(db, query)
```

### 3. 実行時間の計測

```python
import time
from contextlib import contextmanager

@contextmanager
def timeit_db(description: str):
    """データベース操作の実行時間を計測"""
    start = time.time()
    yield
    elapsed = time.time() - start
    logger.info(f"{description}: {elapsed:.3f}秒")

# 使用例
with timeit_db("プロジェクト一覧取得"):
    projects = db.query(Project).all()
```

### 4. デッドロックの検出

```sql
-- 現在のロック状況を確認
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    query_start,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- ブロックしているクエリを検出
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity 
    ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity 
    ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.GRANTED;
```

## 📊 データベース監視

### 接続数の監視

```python
def get_db_connection_stats(db: Session):
    """データベース接続の統計情報を取得"""
    
    # 現在の接続数
    current_connections = db.execute("""
        SELECT count(*) 
        FROM pg_stat_activity 
        WHERE datname = current_database()
    """).scalar()
    
    # 最大接続数
    max_connections = db.execute(
        "SHOW max_connections"
    ).scalar()
    
    # アプリケーション別接続数
    app_connections = db.execute("""
        SELECT application_name, count(*) as count
        FROM pg_stat_activity
        WHERE datname = current_database()
        GROUP BY application_name
        ORDER BY count DESC
    """).fetchall()
    
    return {
        "current": current_connections,
        "max": max_connections,
        "usage_percent": (current_connections / int(max_connections)) * 100,
        "by_application": dict(app_connections)
    }
```

### テーブルサイズの監視

```sql
-- テーブルサイズ一覧
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'team_insight'
ORDER BY size_bytes DESC;

-- インデックスサイズを含む詳細
SELECT 
    tablename,
    pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_tables
WHERE schemaname = 'team_insight'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🚨 よくある問題と解決策

### 1. "relation does not exist"エラー

```python
# 問題：スキーマが指定されていない
# ❌ エラーになる
db.execute("SELECT * FROM users")

# ✅ 解決策1：スキーマを明示
db.execute("SELECT * FROM team_insight.users")

# ✅ 解決策2：search_pathを設定
db.execute("SET search_path TO team_insight, public")
```

### 2. タイムゾーンの問題

```python
# 問題：タイムゾーンが考慮されていない
from datetime import datetime

# ❌ ナイーブなdatetime
task.created_at = datetime.now()

# ✅ タイムゾーン付きdatetime
from datetime import timezone
task.created_at = datetime.now(timezone.utc)

# または
from app.core.utils import get_current_time
task.created_at = get_current_time()
```

### 3. トランザクションのデッドロック

```python
# 問題：長時間のトランザクション
# ❌ 悪い例
with db.begin():
    users = db.query(User).with_for_update().all()
    # 時間のかかる処理...
    time.sleep(10)
    # 更新処理

# ✅ 良い例：必要最小限のロック
with db.begin():
    # 必要なレコードだけロック
    user = db.query(User).with_for_update(skip_locked=True).filter(
        User.id == user_id
    ).first()
    
    if user:
        user.status = 'processed'
```

### 4. メモリ不足（大量データ処理）

```python
# ❌ 悪い例：全件メモリに読み込み
all_tasks = db.query(Task).all()
for task in all_tasks:
    process_task(task)

# ✅ 良い例：yield_perでストリーミング処理
query = db.query(Task)
for task in query.yield_per(1000):
    process_task(task)
    
# ✅ さらに良い例：window関数でバッチ処理
from sqlalchemy import func

batch_size = 1000
max_id = db.query(func.max(Task.id)).scalar()

for offset in range(0, max_id, batch_size):
    tasks = db.query(Task).filter(
        Task.id >= offset,
        Task.id < offset + batch_size
    ).all()
    
    for task in tasks:
        process_task(task)
    
    db.commit()  # バッチごとにコミット
```

## 💡 開発のベストプラクティス

1. **マイグレーションは必ずレビュー**
   - 自動生成されたマイグレーションも必ず確認
   - ダウングレードが可能か確認

2. **本番環境でのマイグレーション**
   ```bash
   # バックアップを取る
   pg_dump -d teaminsight > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # マイグレーション実行
   alembic upgrade head
   ```

3. **定期的なメンテナンス**
   ```sql
   -- VACUUM（自動実行されるが、手動実行も可能）
   VACUUM ANALYZE team_insight.tasks;
   
   -- インデックスの再構築
   REINDEX TABLE team_insight.tasks;
   ```

4. **監視の自動化**
   - 接続数の監視
   - スロークエリの検出
   - ディスク使用量の確認

---

次は[API連携の実装方法](07-api-integration.md)で、Backlog APIとの連携方法を学びましょう！
```