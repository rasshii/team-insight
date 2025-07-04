# テスト戦略とTDD

**このガイドで学べること**：
- Team Insightのテスト戦略
- ユニットテスト、統合テスト、E2Eテストの書き方
- テスト駆動開発（TDD）の実践
- テストカバレッジとCI/CDの設定

## 🎯 テスト戦略の概要

### テストピラミッド

```
         /\
        /E2E\       ← 少数の重要なシナリオ
       /------\
      /統合テスト\   ← APIエンドポイント、DB操作
     /----------\
    /ユニットテスト\  ← ビジネスロジック、ユーティリティ
   /--------------\
```

### 各テストレベルの目的

1. **ユニットテスト**（70%）
   - 個々の関数やクラスの動作を検証
   - 高速実行、独立性が高い
   - モックを活用して外部依存を排除

2. **統合テスト**（20%）
   - 複数のコンポーネントの連携を検証
   - データベース、外部APIとの統合
   - 実際の環境に近い条件でテスト

3. **E2Eテスト**（10%）
   - ユーザー視点での主要フローを検証
   - ブラウザ自動化による実際の操作
   - 最も重要なビジネスフローに限定

## 🧪 バックエンドのテスト

### pytest設定

```python
# backend/pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --maxfail=1
    --tb=short
```

### conftest.pyの設定

```python
# backend/tests/conftest.py
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.api.deps import get_db
from app.models.user import User
from app.models.role import Role
from app.core.security import create_access_token

# テスト用データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """テスト用のデータベースセッション"""
    # インメモリSQLiteを使用
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    yield session
    
    session.close()
    # テーブル削除
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator:
    """テスト用のFastAPIクライアント"""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session: Session) -> User:
    """テスト用ユーザー"""
    user = User(
        email="test@example.com",
        name="Test User",
        backlog_id="12345",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(db_session: Session) -> User:
    """管理者ユーザー"""
    # ADMINロールを作成
    admin_role = Role(name="ADMIN", description="Administrator")
    db_session.add(admin_role)
    
    user = User(
        email="admin@example.com",
        name="Admin User",
        backlog_id="99999",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    # ロールを割り当て
    user.user_roles.append(UserRole(user_id=user.id, role_id=admin_role.id))
    db_session.commit()
    db_session.refresh(user)
    
    return user

@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """認証ヘッダー"""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """管理者認証ヘッダー"""
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

### ユニットテストの例

```python
# backend/tests/unit/test_project_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate

class TestProjectService:
    """ProjectServiceのユニットテスト"""
    
    def test_create_project_success(self, db_session):
        """プロジェクト作成の正常系テスト"""
        # Arrange
        service = ProjectService(db_session)
        project_data = ProjectCreate(
            name="Test Project",
            description="Test Description",
            project_key="TEST"
        )
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Act
        project = service.create_project(project_data, user_id)
        
        # Assert
        assert project.name == "Test Project"
        assert project.description == "Test Description"
        assert project.project_key == "TEST"
        
        # プロジェクトメンバーが追加されていることを確認
        assert len(project.project_members) == 1
        assert project.project_members[0].user_id == user_id
        assert project.project_members[0].role == "LEADER"
    
    @patch('app.services.project_service.BacklogClient')
    def test_sync_from_backlog(self, mock_backlog_client, db_session):
        """Backlogからの同期テスト"""
        # Arrange
        mock_client = Mock()
        mock_backlog_client.return_value = mock_client
        
        # Backlog APIのレスポンスをモック
        mock_client.get_project.return_value = {
            "id": 12345,
            "projectKey": "SYNC",
            "name": "Synced Project",
            "description": "From Backlog"
        }
        
        service = ProjectService(db_session)
        
        # Act
        project = service.sync_project_from_backlog(12345, "fake-token")
        
        # Assert
        assert project.backlog_project_id == 12345
        assert project.project_key == "SYNC"
        assert project.name == "Synced Project"
        mock_client.get_project.assert_called_once_with(12345)
    
    def test_get_user_projects_with_role_filter(self, db_session, test_user):
        """ロールによるプロジェクトフィルタリングテスト"""
        # Arrange
        service = ProjectService(db_session)
        
        # 複数のプロジェクトを作成
        project1 = service.create_project(
            ProjectCreate(name="Project 1", project_key="P1"),
            test_user.id
        )
        project2 = service.create_project(
            ProjectCreate(name="Project 2", project_key="P2"),
            test_user.id
        )
        
        # project2のロールをMEMBERに変更
        member = db_session.query(ProjectMember).filter(
            ProjectMember.project_id == project2.id,
            ProjectMember.user_id == test_user.id
        ).first()
        member.role = "MEMBER"
        db_session.commit()
        
        # Act
        leader_projects = service.get_user_projects(
            test_user.id, 
            role_filter="LEADER"
        )
        
        # Assert
        assert len(leader_projects) == 1
        assert leader_projects[0].id == project1.id
```

### パラメータ化テスト

```python
# backend/tests/unit/test_validators.py
import pytest
from app.core.validators import validate_email, validate_project_key

class TestValidators:
    """バリデーターのテスト"""
    
    @pytest.mark.parametrize("email,expected", [
        ("valid@example.com", True),
        ("user.name@company.co.jp", True),
        ("invalid", False),
        ("@example.com", False),
        ("user@", False),
        ("", False),
        (None, False),
    ])
    def test_email_validation(self, email, expected):
        """メールアドレスバリデーションのテスト"""
        assert validate_email(email) == expected
    
    @pytest.mark.parametrize("key,expected_valid,expected_error", [
        ("VALID", True, None),
        ("TEST123", True, None),
        ("A", True, None),
        ("TOOLONGPROJECTKEY", False, "Project key must be 1-10 characters"),
        ("", False, "Project key is required"),
        ("invalid-key", False, "Project key must be alphanumeric"),
        ("テスト", False, "Project key must be alphanumeric"),
    ])
    def test_project_key_validation(self, key, expected_valid, expected_error):
        """プロジェクトキーバリデーションのテスト"""
        is_valid, error = validate_project_key(key)
        assert is_valid == expected_valid
        assert error == expected_error

## 🔗 統合テスト

### APIエンドポイントのテスト

```python
# backend/tests/integration/test_project_api.py
import pytest
from fastapi import status
from app.models.project import Project

class TestProjectAPI:
    """プロジェクトAPIの統合テスト"""
    
    def test_create_project_endpoint(self, client, auth_headers):
        """プロジェクト作成エンドポイントのテスト"""
        # Arrange
        project_data = {
            "name": "Integration Test Project",
            "description": "Created via API",
            "project_key": "INTEG"
        }
        
        # Act
        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["project_key"] == project_data["project_key"]
        assert "id" in data
        assert "created_at" in data
    
    def test_get_projects_with_pagination(self, client, auth_headers, db_session):
        """プロジェクト一覧取得（ページネーション）のテスト"""
        # Arrange: 複数のプロジェクトを作成
        for i in range(15):
            project = Project(
                name=f"Project {i}",
                project_key=f"P{i}",
                description=f"Description {i}"
            )
            db_session.add(project)
        db_session.commit()
        
        # Act: 最初のページを取得
        response = client.get(
            "/api/v1/projects/?limit=10&offset=0",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15
        assert data["limit"] == 10
        assert data["offset"] == 0
        
        # Act: 2ページ目を取得
        response = client.get(
            "/api/v1/projects/?limit=10&offset=10",
            headers=auth_headers
        )
        
        # Assert
        data = response.json()
        assert len(data["items"]) == 5
    
    def test_project_access_control(self, client, auth_headers, admin_headers):
        """プロジェクトアクセス制御のテスト"""
        # Arrange: 管理者でプロジェクト作成
        project_data = {"name": "Admin Project", "project_key": "ADMIN"}
        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers=admin_headers
        )
        project_id = response.json()["id"]
        
        # Act: 一般ユーザーでアクセス試行
        response = client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers
        )
        
        # Assert: アクセス拒否
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.parametrize("invalid_data,expected_error", [
        ({"name": ""}, "Name is required"),
        ({"name": "Test"}, "project_key is required"),
        ({"name": "Test", "project_key": ""}, "Project key is required"),
        ({"name": "Test", "project_key": "WAYTOOLONGKEY"}, "Project key must be"),
    ])
    def test_create_project_validation(self, client, auth_headers, invalid_data, expected_error):
        """プロジェクト作成のバリデーションテスト"""
        response = client.post(
            "/api/v1/projects/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert expected_error in response.text
```

### データベース操作のテスト

```python
# backend/tests/integration/test_sync_service.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from app.services.sync_service import SyncService
from app.models import User, Project, Task

class TestSyncService:
    """同期サービスの統合テスト"""
    
    @pytest.mark.asyncio
    async def test_sync_project_tasks_full_flow(self, db_session):
        """タスク同期の完全フローテスト"""
        # Arrange
        project = Project(
            name="Sync Test Project",
            project_key="SYNC",
            backlog_project_id=12345
        )
        db_session.add(project)
        db_session.commit()
        
        # BacklogClientのモック
        mock_client = AsyncMock()
        mock_client.get_issues.return_value = [
            {
                "id": 1001,
                "issueKey": "SYNC-1",
                "summary": "Test Task 1",
                "description": "Description 1",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "created": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z"
            },
            {
                "id": 1002,
                "issueKey": "SYNC-2",
                "summary": "Test Task 2",
                "description": "Description 2",
                "status": {"name": "In Progress"},
                "priority": {"name": "Medium"},
                "created": "2024-01-02T00:00:00Z",
                "updated": "2024-01-02T00:00:00Z"
            }
        ]
        
        sync_service = SyncService(db_session, mock_client)
        
        # Act
        result = await sync_service.sync_project_tasks(project.id)
        
        # Assert
        assert result["synced_tasks"] == 2
        
        # データベースに保存されたことを確認
        tasks = db_session.query(Task).filter(
            Task.project_id == project.id
        ).all()
        assert len(tasks) == 2
        
        # タスクの詳細を確認
        task1 = next(t for t in tasks if t.issue_key == "SYNC-1")
        assert task1.summary == "Test Task 1"
        assert task1.status == "Open"
        assert task1.priority == "High"
        
        # 同期履歴が記録されたことを確認
        sync_history = db_session.query(SyncHistory).filter(
            SyncHistory.project_id == project.id
        ).first()
        assert sync_history is not None
        assert sync_history.items_synced == 2
        assert sync_history.status == "completed"
    
    @pytest.mark.asyncio
    async def test_sync_with_existing_tasks(self, db_session):
        """既存タスクがある場合の同期テスト"""
        # Arrange: プロジェクトと既存タスクを作成
        project = Project(
            name="Update Test Project",
            project_key="UPDATE",
            backlog_project_id=54321
        )
        db_session.add(project)
        db_session.flush()
        
        existing_task = Task(
            project_id=project.id,
            backlog_issue_id=2001,
            issue_key="UPDATE-1",
            summary="Old Summary",
            status="Open",
            updated_at=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(existing_task)
        db_session.commit()
        
        # BacklogClientのモック（更新されたデータ）
        mock_client = AsyncMock()
        mock_client.get_issues.return_value = [{
            "id": 2001,
            "issueKey": "UPDATE-1",
            "summary": "Updated Summary",
            "status": {"name": "Completed"},
            "updated": datetime.utcnow().isoformat() + "Z"
        }]
        
        sync_service = SyncService(db_session, mock_client)
        
        # Act
        await sync_service.sync_project_tasks(project.id)
        
        # Assert: タスクが更新されたことを確認
        db_session.refresh(existing_task)
        assert existing_task.summary == "Updated Summary"
        assert existing_task.status == "Completed"
        assert existing_task.completed_date is not None
```

### Redisキャッシュのテスト

```python
# backend/tests/integration/test_cache_service.py
import pytest
import asyncio
from datetime import timedelta
from app.services.cache_service import CacheService
from app.core.redis_client import redis_client

@pytest.mark.asyncio
class TestCacheService:
    """キャッシュサービスの統合テスト"""
    
    async def test_cache_set_and_get(self):
        """キャッシュの設定と取得のテスト"""
        # Arrange
        test_data = {
            "id": "123",
            "name": "Test Project",
            "members": ["user1", "user2"]
        }
        
        # Act: キャッシュに設定
        success = await CacheService.set(
            "project",
            "test_project_123",
            test_data,
            expiry=timedelta(seconds=5)
        )
        
        # Assert: 設定成功
        assert success is True
        
        # Act: キャッシュから取得
        cached_data = await CacheService.get("project", "test_project_123")
        
        # Assert: データが一致
        assert cached_data == test_data
        
        # Cleanup
        await CacheService.delete("project", "test_project_123")
    
    async def test_cache_expiry(self):
        """キャッシュの有効期限テスト"""
        # Act: 短い有効期限で設定
        await CacheService.set(
            "project",
            "expiry_test",
            {"data": "test"},
            expiry=timedelta(seconds=1)
        )
        
        # Assert: すぐに取得できる
        assert await CacheService.get("project", "expiry_test") is not None
        
        # Wait for expiry
        await asyncio.sleep(1.5)
        
        # Assert: 期限切れで取得できない
        assert await CacheService.get("project", "expiry_test") is None
    
    async def test_cache_invalidation_pattern(self):
        """パターンによるキャッシュ無効化テスト"""
        # Arrange: 複数のキャッシュを設定
        await CacheService.set("project", "user_projects:user1", ["p1", "p2"])
        await CacheService.set("project", "user_projects:user2", ["p3", "p4"])
        await CacheService.set("project", "detail:p1", {"name": "Project 1"})
        
        # Act: パターンで無効化
        deleted = await CacheService.invalidate_pattern("project:user_projects:*")
        
        # Assert
        assert deleted == 2
        assert await CacheService.get("project", "user_projects:user1") is None
        assert await CacheService.get("project", "user_projects:user2") is None
        assert await CacheService.get("project", "detail:p1") is not None
        
        # Cleanup
        await CacheService.delete("project", "detail:p1")
```

## 🎨 フロントエンドのテスト

### Jest設定

```typescript
// frontend/jest.config.js
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
  ],
}

module.exports = createJestConfig(customJestConfig)
```

### テストセットアップ

```javascript
// frontend/jest.setup.js
import '@testing-library/jest-dom'

// Next.js Routerのモック
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      refresh: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      prefetch: jest.fn(),
      pathname: '/',
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return '/'
  },
}))

// APIクライアントのモック
jest.mock('@/lib/api-client', () => ({
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))
```

### コンポーネントのテスト

```tsx
// frontend/src/components/projects/__tests__/ProjectCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { ProjectCard } from '../ProjectCard'
import { useRouter } from 'next/navigation'

jest.mock('next/navigation')

describe('ProjectCard', () => {
  const mockProject = {
    id: '123',
    name: 'Test Project',
    description: 'A test project description',
    project_key: 'TEST',
    member_count: 5,
    task_count: 10,
    is_active: true,
  }

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: jest.fn(),
    })
  })

  it('displays project information correctly', () => {
    render(<ProjectCard project={mockProject} />)
    
    expect(screen.getByText('Test Project')).toBeInTheDocument()
    expect(screen.getByText('A test project description')).toBeInTheDocument()
    expect(screen.getByText('TEST')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('navigates to project detail on click', () => {
    const router = useRouter()
    render(<ProjectCard project={mockProject} />)
    
    const card = screen.getByRole('article')
    fireEvent.click(card)
    
    expect(router.push).toHaveBeenCalledWith('/projects/123')
  })

  it('shows inactive badge for inactive projects', () => {
    const inactiveProject = { ...mockProject, is_active: false }
    render(<ProjectCard project={inactiveProject} />)
    
    expect(screen.getByText('非アクティブ')).toBeInTheDocument()
  })

  it('handles missing description gracefully', () => {
    const projectWithoutDesc = { ...mockProject, description: null }
    render(<ProjectCard project={projectWithoutDesc} />)
    
    expect(screen.getByText('説明なし')).toBeInTheDocument()
  })
})
```

### フックのテスト

```tsx
// frontend/src/hooks/queries/__tests__/useProjects.test.tsx
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useProjects } from '../useProjects'
import apiClient from '@/lib/api-client'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('useProjects', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('fetches projects successfully', async () => {
    const mockProjects = {
      items: [
        { id: '1', name: 'Project 1' },
        { id: '2', name: 'Project 2' },
      ],
      total: 2,
    }

    (apiClient.get as jest.Mock).mockResolvedValueOnce({
      data: mockProjects,
    })

    const { result } = renderHook(() => useProjects(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual(mockProjects)
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/projects/')
  })

  it('handles error correctly', async () => {
    const mockError = new Error('Failed to fetch')
    
    (apiClient.get as jest.Mock).mockRejectedValueOnce(mockError)

    const { result } = renderHook(() => useProjects(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toBe(mockError)
  })

  it('applies filters correctly', async () => {
    const filters = { status: 'active', search: 'test' }
    
    (apiClient.get as jest.Mock).mockResolvedValueOnce({
      data: { items: [], total: 0 },
    })

    renderHook(() => useProjects(filters), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/projects/',
        expect.objectContaining({
          params: filters,
        })
      )
    })
  })
})
```

## 🌐 E2Eテスト

### Playwright設定

```typescript
// frontend/playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### E2Eテストの例

```typescript
// frontend/e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test('user can login and logout', async ({ page }) => {
    // ログインページへ移動
    await page.goto('/auth/login')
    
    // Backlogログインボタンをクリック
    await page.click('button:has-text("Backlogでログイン")')
    
    // Backlog OAuth画面（モック）での認証
    // 実際のE2Eテストではテスト用のBacklogアカウントを使用
    await page.waitForURL('**/oauth/authorize**')
    await page.fill('#username', process.env.TEST_BACKLOG_USER!)
    await page.fill('#password', process.env.TEST_BACKLOG_PASS!)
    await page.click('button[type="submit"]')
    
    // ダッシュボードへリダイレクトされることを確認
    await page.waitForURL('/dashboard')
    expect(page.url()).toContain('/dashboard')
    
    // ユーザー名が表示されることを確認
    await expect(page.locator('[data-testid="user-menu"]')).toContainText('Test User')
    
    // ログアウト
    await page.click('[data-testid="user-menu"]')
    await page.click('button:has-text("ログアウト")')
    
    // ログインページへリダイレクト
    await page.waitForURL('/auth/login')
    expect(page.url()).toContain('/auth/login')
  })

  test('unauthenticated user is redirected to login', async ({ page }) => {
    // 保護されたページへ直接アクセス
    await page.goto('/dashboard')
    
    // ログインページへリダイレクトされることを確認
    await page.waitForURL('/auth/login')
    expect(page.url()).toContain('/auth/login')
  })
})
```

### プロジェクト管理のE2Eテスト

```typescript
// frontend/e2e/projects.spec.ts
import { test, expect } from '@playwright/test'
import { login } from './helpers/auth'

test.describe('Project Management', () => {
  test.beforeEach(async ({ page }) => {
    // 各テストの前にログイン
    await login(page)
  })

  test('create new project', async ({ page }) => {
    // プロジェクト一覧へ移動
    await page.goto('/projects')
    
    // 新規作成ボタンをクリック
    await page.click('button:has-text("新規プロジェクト")')
    
    // フォームに入力
    await page.fill('input[name="name"]', 'E2E Test Project')
    await page.fill('input[name="project_key"]', 'E2E')
    await page.fill('textarea[name="description"]', 'This is an E2E test project')
    
    // 作成ボタンをクリック
    await page.click('button:has-text("作成")')
    
    // 成功メッセージを確認
    await expect(page.locator('.toast')).toContainText('プロジェクトを作成しました')
    
    // 一覧に新しいプロジェクトが表示されることを確認
    await expect(page.locator('[data-testid="project-card"]')).toContainText('E2E Test Project')
  })

  test('sync projects from Backlog', async ({ page }) => {
    await page.goto('/projects')
    
    // 同期ボタンをクリック
    await page.click('button:has-text("Backlogと同期")')
    
    // 確認ダイアログで同期開始
    await page.click('button:has-text("同期開始")')
    
    // 進行状況インジケーターが表示される
    await expect(page.locator('[data-testid="sync-progress"]')).toBeVisible()
    
    // 完了メッセージを待つ（最大30秒）
    await expect(page.locator('.toast')).toContainText('同期完了', { timeout: 30000 })
  })
})
```

## 🎯 テスト駆動開発（TDD）の実践

### TDDのサイクル

```
1. Red: 失敗するテストを書く
2. Green: テストを通す最小限のコードを書く
3. Refactor: コードを改善する
```

### TDDの実例：タスク分析サービス

```python
# 1. Red: 最初にテストを書く
# backend/tests/unit/test_task_analytics.py
import pytest
from datetime import datetime, timedelta
from app.services.task_analytics import TaskAnalyticsService

class TestTaskAnalytics:
    def test_calculate_cycle_time(self):
        """サイクルタイム計算のテスト"""
        # Arrange
        created_at = datetime(2024, 1, 1, 10, 0, 0)
        completed_at = datetime(2024, 1, 3, 15, 30, 0)
        
        # Act
        cycle_time = TaskAnalyticsService.calculate_cycle_time(
            created_at, completed_at
        )
        
        # Assert
        assert cycle_time == 2.23  # 2日と5.5時間 = 2.23日
```

```python
# 2. Green: テストを通す最小限の実装
# backend/app/services/task_analytics.py
class TaskAnalyticsService:
    @staticmethod
    def calculate_cycle_time(
        created_at: datetime, 
        completed_at: datetime
    ) -> float:
        """タスクのサイクルタイムを計算（日単位）"""
        delta = completed_at - created_at
        return round(delta.total_seconds() / 86400, 2)  # 秒を日に変換
```

```python
# 3. Refactor: より多くのケースに対応
# さらにテストを追加
def test_calculate_cycle_time_with_none_values(self):
    """完了していないタスクのサイクルタイム"""
    result = TaskAnalyticsService.calculate_cycle_time(
        datetime.now(), None
    )
    assert result is None

def test_calculate_average_cycle_time(self):
    """複数タスクの平均サイクルタイム"""
    tasks = [
        {"created_at": datetime(2024, 1, 1), "completed_at": datetime(2024, 1, 2)},
        {"created_at": datetime(2024, 1, 1), "completed_at": datetime(2024, 1, 4)},
        {"created_at": datetime(2024, 1, 1), "completed_at": None},  # 未完了
    ]
    
    avg_cycle_time = TaskAnalyticsService.calculate_average_cycle_time(tasks)
    assert avg_cycle_time == 2.0  # (1 + 3) / 2

# リファクタリング後の実装
class TaskAnalyticsService:
    @staticmethod
    def calculate_cycle_time(
        created_at: Optional[datetime], 
        completed_at: Optional[datetime]
    ) -> Optional[float]:
        """タスクのサイクルタイムを計算（日単位）"""
        if not created_at or not completed_at:
            return None
        
        delta = completed_at - created_at
        return round(delta.total_seconds() / 86400, 2)
    
    @classmethod
    def calculate_average_cycle_time(cls, tasks: List[Dict]) -> Optional[float]:
        """複数タスクの平均サイクルタイムを計算"""
        cycle_times = []
        
        for task in tasks:
            cycle_time = cls.calculate_cycle_time(
                task.get("created_at"),
                task.get("completed_at")
            )
            if cycle_time is not None:
                cycle_times.append(cycle_time)
        
        if not cycle_times:
            return None
        
        return round(sum(cycle_times) / len(cycle_times), 2)
```

### フロントエンドでのTDD

```typescript
// 1. Red: コンポーネントのテストを先に書く
// frontend/src/components/analytics/__tests__/CycleTimeChart.test.tsx
describe('CycleTimeChart', () => {
  it('displays average cycle time correctly', () => {
    const data = {
      averageCycleTime: 3.5,
      tasks: [
        { name: 'Task 1', cycleTime: 2.0 },
        { name: 'Task 2', cycleTime: 5.0 },
      ]
    }
    
    render(<CycleTimeChart data={data} />)
    
    expect(screen.getByText('平均サイクルタイム')).toBeInTheDocument()
    expect(screen.getByText('3.5日')).toBeInTheDocument()
  })
})

// 2. Green: 最小限の実装
// frontend/src/components/analytics/CycleTimeChart.tsx
export function CycleTimeChart({ data }: Props) {
  return (
    <div>
      <h3>平均サイクルタイム</h3>
      <p>{data.averageCycleTime}日</p>
    </div>
  )
}
```

## 📊 テストカバレッジ

### カバレッジ目標

- 全体: 80%以上
- 重要なビジネスロジック: 90%以上
- APIエンドポイント: 100%
- UIコンポーネント: 70%以上

### カバレッジレポートの生成

```bash
# バックエンド
cd backend
pytest --cov=app --cov-report=html --cov-report=term

# フロントエンド
cd frontend
npm run test:coverage
```

### カバレッジの確認

```bash
# HTMLレポートを開く
open backend/htmlcov/index.html
open frontend/coverage/lcov-report/index.html
```

## 🔧 CI/CDパイプライン

### GitHub Actions設定

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
        REDIS_URL: redis://localhost:6379
        SECRET_KEY: test-secret-key
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend

  frontend-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'yarn'
        cache-dependency-path: frontend/yarn.lock
    
    - name: Install dependencies
      run: |
        cd frontend
        yarn install --frozen-lockfile
    
    - name: Run tests
      run: |
        cd frontend
        yarn test:ci
    
    - name: Run E2E tests
      run: |
        cd frontend
        npx playwright install --with-deps
        yarn test:e2e
    
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: playwright-report
        path: frontend/playwright-report/
```

## 💡 テストのベストプラクティス

### 1. テストの構造

```python
# AAA パターン
def test_example():
    # Arrange: テストデータの準備
    user = create_test_user()
    
    # Act: テスト対象の実行
    result = perform_action(user)
    
    # Assert: 結果の検証
    assert result.status == "success"
```

### 2. テストの独立性

- 各テストは他のテストに依存しない
- テストの実行順序に依存しない
- テスト後はクリーンアップ

### 3. モックの適切な使用

```python
# 外部依存はモック化
@patch('app.services.backlog_client.BacklogClient')
def test_sync_without_external_api(mock_client):
    mock_client.get_projects.return_value = [...]
    # 実際のAPIを呼ばずにテスト
```

### 4. テストの命名規則

```python
def test_<対象>_<条件>_<期待結果>():
    """
    例：
    test_user_with_valid_email_creates_successfully
    test_project_without_name_raises_validation_error
    """
```

### 5. 継続的な改善

- 失敗したテストはすぐに修正
- フレイキーなテストを排除
- 定期的にテストコードをリファクタリング

---

次は[デプロイと運用](09-deployment.md)で、本番環境への展開方法を学びましょう！
```