/**
 * 型安全なReduxフック
 *
 * TypeScriptで型安全にReduxを使用するための
 * カスタムフックを定義します。
 */

import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";
import type { AppDispatch, RootState } from "./index";

/**
 * 型安全なuseDispatchフック
 *
 * AppDispatch型を使用して、非同期アクションも含めて
 * 型安全にディスパッチできます。
 */
export const useAppDispatch = () => useDispatch<AppDispatch>();

/**
 * 型安全なuseSelectorフック
 *
 * RootState型を使用して、ストアの状態を
 * 型安全に取得できます。
 */
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
