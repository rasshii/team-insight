import * as React from "react";

export interface ToastProps {
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
}

interface ToastContextValue {
  toast: (props: ToastProps) => void;
}

const ToastContext = React.createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    // Provide a simple console-based fallback
    return {
      toast: (props: ToastProps) => {
        if (props.variant === "destructive") {
          console.error(`[Toast] ${props.title}: ${props.description}`);
        } else {
          console.log(`[Toast] ${props.title}: ${props.description}`);
        }
      },
    };
  }
  return context;
}

export const toast = (props: ToastProps) => {
  const { toast } = useToast();
  toast(props);
};
