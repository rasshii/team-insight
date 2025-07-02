# shadcn/ui Button コンポーネントの TabsContent 内でのクリックイベント問題分析

## 問題の概要

shadcn/uiのButtonコンポーネントがRadix UIのTabsContent内で使用された際に、クリックイベントが発火しない問題が発生しています。

## 調査結果

### 1. 現在の実装状況

**Buttonコンポーネント (`/frontend/src/components/ui/button.tsx`):**
- Radix UIの`Slot`コンポーネントを使用（`asChild`プロパティがtrueの場合）
- CVA（class-variance-authority）でスタイリング
- `disabled:pointer-events-none`クラスがデフォルトで含まれている

**Tabsコンポーネント (`/frontend/src/components/ui/tabs.tsx`):**
- Radix UIの`@radix-ui/react-tabs`を使用
- TabsContentは非アクティブ時に`display: none`となる

**使用されているバージョン:**
- @radix-ui/react-tabs: ^1.1.12
- @radix-ui/react-slot: ^1.2.3

### 2. 問題の原因分析

考えられる原因：

1. **pointer-eventsの競合**
   - `disabled:pointer-events-none`クラスが誤って適用される可能性
   - Tailwind CSSのJITコンパイルによる予期しない動作

2. **Radix UI Tabsの仕様**
   - TabsContentのマウント/アンマウントのタイミング
   - イベントバブリングの処理

3. **React 18のイベント委譲の変更**
   - React 18でイベント委譲の仕組みが変更された影響

### 3. 回避策（現在の実装）

`BacklogSettings.tsx`では、以下の回避策が使用されていました：

```jsx
// Buttonコンポーネントの代わりに通常のbutton要素を使用
<button
  type="button"
  className="w-full bg-primary text-primary-foreground shadow hover:bg-primary/90 inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring h-9 px-4 py-2"
  onClick={(e) => {
    e.preventDefault()
    handleOAuthDirectConnect()
  }}
>
  Backlogでログイン
</button>
```

## 推奨される解決策

### 解決策1: Buttonコンポーネントの修正（推奨）

`button.tsx`を以下のように修正：

```tsx
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    
    // disabledでない場合はpointer-eventsを制御しない
    const buttonClasses = React.useMemo(() => {
      const baseClasses = buttonVariants({ variant, size, className });
      if (!disabled) {
        // disabled:pointer-events-noneを削除
        return baseClasses.replace(/disabled:pointer-events-none/g, '');
      }
      return baseClasses;
    }, [variant, size, className, disabled]);
    
    return (
      <Comp
        className={buttonClasses}
        ref={ref}
        disabled={disabled}
        type={props.type || "button"} // デフォルトtype追加
        {...props}
      />
    );
  }
);
```

### 解決策2: 使用側での対処

TabsContent内でButtonを使用する際の推奨パターン：

```tsx
<TabsContent value="oauth" className="space-y-4">
  <Button
    type="button"
    className="w-full"
    onClick={(e) => {
      e.preventDefault();
      e.stopPropagation();
      // ハンドラーの実行
      handleAction();
    }}
  >
    ボタンテキスト
  </Button>
</TabsContent>
```

### 解決策3: カスタムButtonコンポーネント

TabsContent専用のButtonコンポーネントを作成：

```tsx
export const TabButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ onClick, ...props }, ref) => {
    const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
      e.stopPropagation();
      onClick?.(e);
    }, [onClick]);
    
    return <Button ref={ref} type="button" onClick={handleClick} {...props} />;
  }
);
```

## テスト手順

1. テストページへアクセス:
   - `/test-button-tabs` - 基本的な動作確認
   - `/test-button-diagnostic` - 詳細な診断

2. 以下を確認:
   - TabsContent外でのButton動作
   - TabsContent内でのButton動作
   - ネイティブbutton要素との比較
   - コンソールログの確認

## 今後の対応

1. **短期的対応**
   - 現在の回避策（ネイティブbutton）を維持
   - または、修正されたButtonコンポーネントに置き換え

2. **長期的対応**
   - Radix UIのアップデート確認
   - shadcn/uiの公式アップデートを待つ
   - 必要に応じてissueを報告

## 参考リンク

- [Radix UI Tabs Documentation](https://www.radix-ui.com/docs/primitives/components/tabs)
- [React 18 Event Delegation Changes](https://react.dev/blog/2022/03/08/react-18-upgrade-guide#other-breaking-changes)
- [shadcn/ui GitHub Issues](https://github.com/shadcn-ui/ui/issues)