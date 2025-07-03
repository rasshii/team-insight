/**
 * 認証スライス
 *
 * Redux Toolkitを使用して認証状態を管理します。
 * React Queryと併用し、グローバルな認証状態のみを管理します。
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { UserInfoResponse } from "../../services/auth.service";

/**
 * 認証状態の型定義
 */
interface AuthState {
  /** 現在のユーザー情報 */
  user: UserInfoResponse | null;
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
  isAuthenticated: false,
  isInitialized: false,
};

/**
 * 認証スライス
 * 
 * React Queryと併用するため、データフェッチングは行わず、
 * 認証状態の管理のみを担当します。
 */
const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    /**
     * ユーザー情報を設定
     */
    setUser: (state, action: PayloadAction<UserInfoResponse>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
      state.isInitialized = true;
    },
    
    /**
     * 認証を初期化（ユーザー情報なし）
     */
    initializeAuth: (state) => {
      state.isInitialized = true;
    },
    
    /**
     * ログアウト
     */
    logout: (state) => {
      state.user = null;
      state.isAuthenticated = false;
    },
  },
});

// アクションのエクスポート
export const { setUser, initializeAuth, logout } = authSlice.actions;

// セレクターのエクスポート
export const selectCurrentUser = (state: { auth: AuthState }) => state.auth.user;
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;
export const selectIsInitialized = (state: { auth: AuthState }) => state.auth.isInitialized;

// リデューサーのエクスポート
export default authSlice.reducer;