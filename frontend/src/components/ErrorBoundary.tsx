'use client'

import React, { Component, ReactNode } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertCircle } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="container mx-auto p-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>エラーが発生しました</AlertTitle>
            <AlertDescription>
              ページの表示中に問題が発生しました。
              {this.state.error?.message && (
                <p className="mt-2 text-sm">{this.state.error.message}</p>
              )}
            </AlertDescription>
          </Alert>
          <div className="mt-4 space-x-2">
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
            >
              ページを再読み込み
            </Button>
            <Button
              variant="outline"
              onClick={() => window.history.back()}
            >
              前のページに戻る
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}