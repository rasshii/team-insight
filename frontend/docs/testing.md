# フロントエンドテストガイド

## 概要

このドキュメントでは、Team Insightフロントエンドのテスト環境とテスト作成方法について説明します。

## テスト環境

### 使用ツール

- **Jest**: JavaScriptテストフレームワーク
- **React Testing Library**: Reactコンポーネントのテストライブラリ
- **@testing-library/jest-dom**: DOM要素のカスタムマッチャー

### setupTests.ts

`src/setupTests.ts`はJestの初期設定ファイルで、全てのテスト実行前に自動的に読み込まれます。

#### 主な設定内容

1. **jest-domの有効化**
   ```typescript
   import "@testing-library/jest-dom";
   ```
   これにより以下のようなマッチャーが使用可能になります：
   - `toBeInTheDocument()`: 要素がDOMに存在するか
   - `toHaveClass()`: 要素が特定のクラスを持つか
   - `toBeVisible()`: 要素が表示されているか
   - `toBeDisabled()`: 要素が無効化されているか

2. **Next.jsのモック設定**
   ```typescript
   // useRouter, useSearchParams, usePathnameのモック
   jest.mock("next/navigation", () => ({
     useRouter() {
       return {
         push: jest.fn(),
         replace: jest.fn(),
         prefetch: jest.fn(),
         back: jest.fn(),
       };
     },
     useSearchParams() {
       return new URLSearchParams();
     },
     usePathname() {
       return "";
     },
   }));
   ```

   テスト環境では実際のNext.jsルーティングが動作しないため、これらの機能をモック化しています。

## テストの作成

### ディレクトリ構造

```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   └── Button.test.tsx        # コンポーネントと同じディレクトリ
│   └── ...
├── services/
│   ├── __tests__/                 # サービステストは専用ディレクトリ
│   │   └── auth.service.test.ts
│   └── auth.service.ts
└── setupTests.ts
```

### 基本的なテストの書き方

#### コンポーネントテスト

```typescript
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "./Button";

describe("Button", () => {
  it("renders with text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("calls onClick handler", () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText("Click me"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

#### ルーティングを含むテスト

```typescript
import { render, screen } from "@testing-library/react";
import { useRouter } from "next/navigation";
import { NavigationComponent } from "./NavigationComponent";

// useRouterはsetupTests.tsでモック済み
const mockPush = jest.fn();
(useRouter as jest.Mock).mockReturnValue({
  push: mockPush,
});

describe("NavigationComponent", () => {
  it("navigates to dashboard on button click", () => {
    render(<NavigationComponent />);
    
    fireEvent.click(screen.getByText("Go to Dashboard"));
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });
});
```

### サービスのテスト

#### APIモックの例

```typescript
import axios from "axios";
import { authService } from "../auth.service";

jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe("AuthService", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("fetches user info successfully", async () => {
    const mockUserData = {
      id: 1,
      name: "Test User",
      email: "test@example.com",
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockUserData });

    const result = await authService.getCurrentUser();
    
    expect(mockedAxios.get).toHaveBeenCalledWith("/api/v1/auth/me");
    expect(result).toEqual(mockUserData);
  });

  it("handles API errors", async () => {
    mockedAxios.get.mockRejectedValueOnce(new Error("Network Error"));

    await expect(authService.getCurrentUser()).rejects.toThrow("Network Error");
  });
});
```

### 環境変数のモック

```typescript
// 環境変数のモック
jest.mock("@/config/env", () => ({
  env: {
    get: jest.fn((key: string) => {
      const mockEnv: Record<string, string> = {
        NEXT_PUBLIC_API_URL: "http://localhost:8000",
        NEXT_PUBLIC_APP_URL: "http://localhost:3000",
      };
      return mockEnv[key];
    }),
  },
}));
```

## テストの実行

### 基本コマンド

```bash
# 全てのテストを実行
yarn test

# ウォッチモードで実行（ファイル変更を監視）
yarn test:watch

# 特定のファイルをテスト
yarn test src/services/__tests__/auth.service.test.ts

# カバレッジレポート付きで実行
yarn test:coverage
```

### Dockerコンテナ内での実行

```bash
# コンテナ内でテスト実行
docker-compose exec frontend yarn test

# Makefileを使用
make test-frontend
```

## ベストプラクティス

### 1. テストの命名規則

- テストファイル: `ComponentName.test.tsx` または `serviceName.test.ts`
- テストケース: 動作を説明する文章形式
  ```typescript
  it("should display error message when API fails", () => {});
  ```

### 2. AAA パターン

```typescript
it("updates user profile", async () => {
  // Arrange（準備）
  const mockUser = { id: 1, name: "Test User" };
  mockedAxios.put.mockResolvedValueOnce({ data: mockUser });

  // Act（実行）
  const result = await userService.updateProfile(mockUser);

  // Assert（検証）
  expect(result).toEqual(mockUser);
  expect(mockedAxios.put).toHaveBeenCalledWith("/api/v1/users/1", mockUser);
});
```

### 3. テストの独立性

- 各テストは独立して実行可能にする
- `beforeEach`/`afterEach`でセットアップとクリーンアップ
- グローバルな状態を避ける

### 4. モックの管理

```typescript
// __mocks__/services/auth.service.ts
export const authService = {
  login: jest.fn(),
  logout: jest.fn(),
  getCurrentUser: jest.fn(),
};
```

## トラブルシューティング

### よくある問題

1. **"Cannot find module" エラー**
   - パスエイリアスが正しく設定されているか確認
   - `jest.config.js`の`moduleNameMapper`を確認

2. **非同期テストのタイムアウト**
   ```typescript
   it("long running test", async () => {
     // テストロジック
   }, 10000); // タイムアウトを10秒に設定
   ```

3. **act() 警告**
   ```typescript
   import { act } from "@testing-library/react";
   
   await act(async () => {
     fireEvent.click(button);
   });
   ```

## 参考資料

- [Jest公式ドキュメント](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Next.js](https://nextjs.org/docs/testing)