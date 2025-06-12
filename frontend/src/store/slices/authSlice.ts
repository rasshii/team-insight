/**
 * 認証スライス
 *
 * Redux Toolkitを使用して認証状態を管理します。
 * 非同期処理にはcreateAsyncThunkを使用します。
 */

import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { authService, UserInfo } from "../../services/auth.service";

/**
 * 認証状態の型定義
 */
interface AuthState {
  /** 現在のユーザー情報 */
  user: UserInfo | null;
  /** ローディング状態 */
  loading: boolean;
  /** エラー情報 */
  error: string | null;
  /** 認証済みかどうか */
  isAuthenticated: boolean;
  /** 初期化完了フラグ */
  isInitialized: boolean;
}

/**
 * 初期状態
 */
const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
  isAuthenticated: false,
  isInitialized: false,
};

/**
 * 認証URLを取得する非同期アクション
 */
export const getAuthorizationUrl = createAsyncThunk(
  "auth/getAuthorizationUrl",
  async () => {
    const response = await authService.getAuthorizationUrl();
    return response;
  }
);

/**
 * 認証コールバックを処理する非同期アクション
 */
export const handleAuthCallback = createAsyncThunk(
  "auth/handleCallback",
  async ({ code, state }: { code: string; state: string }) => {
    const response = await authService.handleCallback(code, state);
    return response;
  }
);

/**
 * 現在のユーザー情報を取得する非同期アクション
 */
export const fetchCurrentUser = createAsyncThunk(
  "auth/fetchCurrentUser",
  async () => {
    const user = await authService.getCurrentUser();
    return user;
  }
);

/**
 * トークンをリフレッシュする非同期アクション
 */
export const refreshAuthToken = createAsyncThunk(
  "auth/refreshToken",
  async () => {
    const response = await authService.refreshToken();
    return response;
  }
);

/**
 * 認証を初期化する非同期アクション
 */
export const initializeAuth = createAsyncThunk("auth/initialize", async () => {
  // 認証サービスを初期化
  authService.initialize();

  // 保存されたユーザー情報を取得
  const savedUser = authService.getUser();

  if (authService.isAuthenticated() && savedUser) {
    // トークンが存在する場合は、最新のユーザー情報を取得
    try {
      const currentUser = await authService.getCurrentUser();
      return currentUser;
    } catch (error) {
      // ユーザー情報の取得に失敗した場合は、保存された情報を使用
      return savedUser;
    }
  }

  return null;
});

/**
 * 認証スライス
 */
const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    /**
     * ログアウト
     */
    logout: (state) => {
      authService.logout();
      state.user = null;
      state.isAuthenticated = false;
      state.error = null;
    },
    /**
     * エラーをクリア
     */
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // 認証URL取得
    builder
      .addCase(getAuthorizationUrl.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getAuthorizationUrl.fulfilled, (state, action) => {
        state.loading = false;
        // 認証URLへのリダイレクトは呼び出し側で行う
      })
      .addCase(getAuthorizationUrl.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || "認証URLの取得に失敗しました";
      });

    // 認証コールバック処理
    builder
      .addCase(handleAuthCallback.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(handleAuthCallback.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.isAuthenticated = true;
      })
      .addCase(handleAuthCallback.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || "認証に失敗しました";
      });

    // ユーザー情報取得
    builder
      .addCase(fetchCurrentUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(fetchCurrentUser.rejected, (state, action) => {
        state.loading = false;
        state.error =
          action.error.message || "ユーザー情報の取得に失敗しました";
      });

    // トークンリフレッシュ
    builder
      .addCase(refreshAuthToken.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(refreshAuthToken.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
      })
      .addCase(refreshAuthToken.rejected, (state, action) => {
        state.loading = false;
        state.error =
          action.error.message || "トークンのリフレッシュに失敗しました";
        // リフレッシュに失敗した場合はログアウト
        authService.logout();
        state.user = null;
        state.isAuthenticated = false;
      });

    // 認証初期化
    builder
      .addCase(initializeAuth.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(initializeAuth.fulfilled, (state, action) => {
        state.loading = false;
        state.isInitialized = true;
        if (action.payload) {
          state.user = action.payload;
          state.isAuthenticated = true;
        }
      })
      .addCase(initializeAuth.rejected, (state, action) => {
        state.loading = false;
        state.isInitialized = true;
        state.error = action.error.message || "認証の初期化に失敗しました";
      });
  },
});

// アクションのエクスポート
export const { logout, clearError } = authSlice.actions;

// リデューサーのエクスポート
export default authSlice.reducer;
