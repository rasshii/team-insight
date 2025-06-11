// ==============================================================================
// Mine-CMS Jest セットアップファイル
// ==============================================================================
// このファイルは、各テストファイルの実行前に一度だけ実行されます。
// テスト環境のグローバルな設定、モックの定義、カスタムマッチャーの追加などを行います。
//
// 主な設定内容:
// - @testing-library/jest-dom のマッチャー追加
// - ブラウザAPIのモック
// - 環境変数の設定
// - グローバルヘルパー関数の定義
// ==============================================================================

// @testing-library/jest-dom のカスタムマッチャーを追加
// これにより、toBeInTheDocument()、toHaveClass() などの便利なマッチャーが使えるようになります
import "@testing-library/jest-dom";

// ==============================================================================
// 環境変数の設定
// ==============================================================================
// テスト環境で使用する環境変数を設定
// 実際の環境変数ファイルを読み込む代わりに、テスト用の値を直接設定します
process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
process.env.NEXT_PUBLIC_APP_NAME = "Mine-CMS Test";
process.env.NEXT_PUBLIC_APP_URL = "http://localhost:3000";

// 機能フラグ（テスト環境ではすべて有効）
process.env.NEXT_PUBLIC_ENABLE_MERMAID = "true";
process.env.NEXT_PUBLIC_ENABLE_PLANTUML = "true";
process.env.NEXT_PUBLIC_ENABLE_GRAPHVIZ = "true";
process.env.NEXT_PUBLIC_ENABLE_BLOCKDIAG = "true";

// ==============================================================================
// グローバルモックの設定
// ==============================================================================

// window.matchMedia のモック
// レスポンシブデザインのテストで使用されます
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // 非推奨だが互換性のため
    removeListener: jest.fn(), // 非推奨だが互換性のため
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// IntersectionObserver のモック
// 遅延読み込みや無限スクロールのテストで使用されます
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback, options) {
    this.callback = callback;
    this.options = options;
  }

  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();

  // テスト用のヘルパーメソッド
  // 交差状態を手動でトリガーできるようにします
  mockIntersect(entries) {
    this.callback(entries, this);
  }
};

// ResizeObserver のモック
// レスポンシブコンポーネントのテストで使用されます
global.ResizeObserver = class ResizeObserver {
  constructor(callback) {
    this.callback = callback;
  }

  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
};

// fetch のモック（基本的なモック、必要に応じて各テストでオーバーライド）
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(""),
    blob: () => Promise.resolve(new Blob()),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    headers: new Headers(),
    status: 200,
    statusText: "OK",
  })
);

// console メソッドのモック（テスト実行時の不要な出力を抑制）
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeAll(() => {
  // エラーとワーニングをモック（ただし、エラー情報は保持）
  console.error = jest.fn((...args) => {
    // React の既知の警告は無視
    const message = args[0]?.toString() || "";
    if (
      message.includes("Warning: ReactDOM.render is no longer supported") ||
      message.includes("Warning: An invalid form control")
    ) {
      return;
    }
    originalConsoleError(...args);
  });

  console.warn = jest.fn((...args) => {
    // 開発時の警告で、テストには影響しないものは無視
    const message = args[0]?.toString() || "";
    if (message.includes("componentWillReceiveProps has been renamed")) {
      return;
    }
    originalConsoleWarn(...args);
  });
});

afterAll(() => {
  // 元のconsoleメソッドを復元
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});

// ==============================================================================
// Next.js Image コンポーネントのモック
// ==============================================================================
// Next.js の Image コンポーネントは Node.js 環境では動作しないためモック
jest.mock("next/image", () => ({
  __esModule: true,
  default: function Image({ src, alt, ...props }) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={src} alt={alt} {...props} />;
  },
}));

// ==============================================================================
// Next.js Router のモック
// ==============================================================================
const mockRouter = {
  basePath: "",
  pathname: "/",
  route: "/",
  asPath: "/",
  query: {},
  push: jest.fn(() => Promise.resolve(true)),
  replace: jest.fn(() => Promise.resolve(true)),
  reload: jest.fn(),
  back: jest.fn(),
  prefetch: jest.fn(() => Promise.resolve()),
  beforePopState: jest.fn(),
  events: {
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
  },
  isFallback: false,
  isLocaleDomain: false,
  isReady: true,
  isPreview: false,
};

jest.mock("next/router", () => ({
  useRouter: () => mockRouter,
}));

// ==============================================================================
// カスタムテストユーティリティ
// ==============================================================================
// テストで頻繁に使用するヘルパー関数をグローバルに定義

// 非同期処理を待つヘルパー関数
global.sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// act() 内で状態更新を待つヘルパー関数
global.waitForNextUpdate = async () => {
  await act(async () => {
    await sleep(0);
  });
};

// ==============================================================================
// テストごとのクリーンアップ
// ==============================================================================
afterEach(() => {
  // すべてのモックをクリア
  jest.clearAllMocks();

  // fetch モックをリセット
  global.fetch.mockClear();

  // ローカルストレージをクリア
  if (typeof window !== "undefined") {
    window.localStorage.clear();
    window.sessionStorage.clear();
  }
});

// ==============================================================================
// カスタムマッチャーの追加
// ==============================================================================
// プロジェクト固有のカスタムマッチャーを追加できます
expect.extend({
  // 例: 日付文字列が有効かチェックするマッチャー
  toBeValidDate(received) {
    const pass = !isNaN(Date.parse(received));
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be a valid date`
          : `expected ${received} to be a valid date`,
    };
  },

  // 例: URLが有効かチェックするマッチャー
  toBeValidUrl(received) {
    let pass = false;
    try {
      new URL(received);
      pass = true;
    } catch (e) {
      pass = false;
    }
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be a valid URL`
          : `expected ${received} to be a valid URL`,
    };
  },
});

// ==============================================================================
// MSW (Mock Service Worker) の設定（APIモック用）
// ==============================================================================
// もしMSWを使用する場合は、ここで設定します
// import { server } from './mocks/server'
//
// beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
// afterEach(() => server.resetHandlers())
// afterAll(() => server.close())
