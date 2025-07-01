import { useState, useEffect } from 'react';

/**
 * 値のデバウンスを行うカスタムフック
 * @param value デバウンスする値
 * @param delay デバウンス時間（ミリ秒）
 * @returns デバウンスされた値
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}