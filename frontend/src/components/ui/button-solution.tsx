import { cn } from "@/lib/utils";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline:
          "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

/**
 * 解決策1: ポインターイベントの問題を修正
 * disabled:pointer-events-none クラスが問題を引き起こす可能性があるため、
 * disabledプロパティを正しく処理
 */
const ButtonSolution1 = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    
    // disabledの場合のみpointer-events-noneを適用するようにクラスを調整
    const finalClassName = cn(
      buttonVariants({ variant, size }),
      disabled && "pointer-events-none opacity-50",
      !disabled && className
    );
    
    return (
      <Comp
        className={finalClassName}
        ref={ref}
        disabled={disabled}
        aria-disabled={disabled}
        {...props}
      />
    );
  }
);
ButtonSolution1.displayName = "ButtonSolution1";

/**
 * 解決策2: Radix UI Tabs内での相互作用を考慮
 * TabsContentが非アクティブな時にdisplay:noneになることを考慮
 */
const ButtonSolution2 = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, onClick, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    const [isMounted, setIsMounted] = React.useState(false);
    
    React.useEffect(() => {
      setIsMounted(true);
    }, []);
    
    const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
      // 明示的にcurrentTargetを使用
      if (onClick && e.currentTarget instanceof HTMLButtonElement) {
        onClick(e);
      }
    }, [onClick]);
    
    if (!isMounted) {
      return null;
    }
    
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        onClick={handleClick}
        {...props}
      />
    );
  }
);
ButtonSolution2.displayName = "ButtonSolution2";

/**
 * 解決策3: 最もシンプルな修正
 * 問題の原因となる可能性のある要素を除去
 */
const ButtonSolution3 = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    
    // pointer-events関連のクラスを条件付きで適用
    const buttonClassName = React.useMemo(() => {
      const baseClasses = cn(buttonVariants({ variant, size, className }));
      // disabled:pointer-events-noneを削除し、disabledプロパティに依存
      return baseClasses.replace('disabled:pointer-events-none', '');
    }, [variant, size, className]);
    
    return (
      <Comp
        className={buttonClassName}
        ref={ref}
        type={props.type || "button"} // デフォルトでtype="button"を設定
        {...props}
      />
    );
  }
);
ButtonSolution3.displayName = "ButtonSolution3";

/**
 * 解決策4: BacklogSettings.tsxで使用されている回避策を改善
 * Buttonコンポーネントをラップして確実に動作させる
 */
export const WorkingButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, onClick, disabled, className, variant, size, ...props }, ref) => {
    // Buttonコンポーネントのスタイルを使用しつつ、ネイティブボタンの動作を保証
    return (
      <button
        ref={ref}
        type="button"
        disabled={disabled}
        className={cn(buttonVariants({ variant, size, className }))}
        onClick={(e) => {
          if (!disabled && onClick) {
            e.preventDefault();
            onClick(e);
          }
        }}
        {...props}
      >
        {children}
      </button>
    );
  }
);
WorkingButton.displayName = "WorkingButton";

export { ButtonSolution1, ButtonSolution2, ButtonSolution3, buttonVariants };