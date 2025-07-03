import React from 'react'
import { useQueryErrorResetBoundary } from '@tanstack/react-query'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface ErrorFallbackProps {
  error: Error
  resetErrorBoundary: () => void
}

/**
 * React Query用のエラーフォールバックコンポーネント
 */
const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => {
  return (
    <div className="container mx-auto p-6">
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>エラーが発生しました</AlertTitle>
        <AlertDescription>
          <p className="mb-4">{error.message || '予期しないエラーが発生しました。'}</p>
          <Button
            onClick={resetErrorBoundary}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            再試行
          </Button>
        </AlertDescription>
      </Alert>
    </div>
  )
}

/**
 * React Query用のグローバルエラーバウンダリー
 */
export class GlobalQueryErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('GlobalQueryErrorBoundary caught error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        <QueryErrorResetBoundaryWrapper>
          {(reset) => (
            <ErrorFallback
              error={this.state.error}
              resetErrorBoundary={() => {
                this.setState({ hasError: false, error: null })
                reset()
              }}
            />
          )}
        </QueryErrorResetBoundaryWrapper>
      )
    }

    return this.props.children
  }
}

/**
 * React QueryのエラーリセットバウンダリーのWrapper
 */
const QueryErrorResetBoundaryWrapper: React.FC<{
  children: (reset: () => void) => React.ReactNode
}> = ({ children }) => {
  const { reset } = useQueryErrorResetBoundary()
  return <>{children(reset)}</>
}