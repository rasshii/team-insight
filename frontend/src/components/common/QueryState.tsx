import React from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface QueryStateProps {
  isLoading?: boolean
  error?: Error | null
  isEmpty?: boolean
  emptyMessage?: string
  emptyIcon?: React.ReactNode
  loadingComponent?: React.ReactNode
  errorComponent?: React.ReactNode
  onRetry?: () => void
  children: React.ReactNode
}

/**
 * React Queryのローディング、エラー、空状態を統一的に処理するコンポーネント
 */
export const QueryState: React.FC<QueryStateProps> = ({
  isLoading = false,
  error = null,
  isEmpty = false,
  emptyMessage = 'データがありません',
  emptyIcon,
  loadingComponent,
  errorComponent,
  onRetry,
  children,
}) => {
  // ローディング状態
  if (isLoading) {
    if (loadingComponent) {
      return <>{loadingComponent}</>
    }
    
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  // エラー状態
  if (error) {
    if (errorComponent) {
      return <>{errorComponent}</>
    }
    
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <div className="flex items-center justify-between">
            <span>{error.message || 'エラーが発生しました'}</span>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="ml-4"
              >
                <RefreshCw className="mr-2 h-3 w-3" />
                再試行
              </Button>
            )}
          </div>
        </AlertDescription>
      </Alert>
    )
  }

  // 空状態
  if (isEmpty) {
    return (
      <div className="text-center py-12">
        {emptyIcon && (
          <div className="flex justify-center mb-4">
            {emptyIcon}
          </div>
        )}
        <p className="text-muted-foreground">{emptyMessage}</p>
      </div>
    )
  }

  // 正常なコンテンツ
  return <>{children}</>
}

/**
 * テーブル用のローディングスケルトン
 */
export const TableLoadingSkeleton: React.FC<{ rows?: number; columns?: number }> = ({
  rows = 5,
  columns = 4,
}) => {
  return (
    <div className="space-y-2">
      {/* ヘッダー */}
      <div className="flex space-x-4 pb-2 border-b">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={`header-${i}`} className="h-4 w-24" />
        ))}
      </div>
      
      {/* 行 */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={`row-${rowIndex}`} className="flex space-x-4 py-2">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={`cell-${rowIndex}-${colIndex}`}
              className={`h-4 ${colIndex === 0 ? 'w-32' : 'w-24'}`}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

/**
 * カード用のローディングスケルトン
 */
export const CardLoadingSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="space-y-3 p-6 border rounded-lg">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-5/6" />
          <div className="flex justify-between pt-2">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
      ))}
    </div>
  )
}