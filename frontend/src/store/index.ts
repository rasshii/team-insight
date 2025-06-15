/**
 * Reduxストアの設定
 *
 * Redux Toolkitを使用してアプリケーション全体の
 * 状態管理を行うストアを設定します。
 */

import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";

/**
 * Reduxストアの作成
 */
export const store = configureStore({
  reducer: {
    auth: authReducer,
  },
  // 開発環境でのみRedux DevToolsを有効化
  devTools: process.env.NODE_ENV !== "production",
});

// RootState型の定義（useSelector用）
export type RootState = ReturnType<typeof store.getState>;

// AppDispatch型の定義（useDispatch用）
export type AppDispatch = typeof store.dispatch;
