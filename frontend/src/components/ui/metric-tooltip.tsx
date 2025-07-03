'use client'

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Info } from 'lucide-react'
import { metricsGlossary, type MetricKey } from '@/lib/metrics-glossary'

interface MetricTooltipProps {
  metric: MetricKey
  children?: React.ReactNode
  showIcon?: boolean
  className?: string
  clickable?: boolean
  onClick?: () => void
}

export function MetricTooltip({ 
  metric, 
  children, 
  showIcon = true, 
  className = "",
  clickable = false,
  onClick
}: MetricTooltipProps) {
  const glossaryItem = metricsGlossary[metric]
  
  if (!glossaryItem) {
    return <>{children}</>
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span 
            className={`inline-flex items-center gap-1 border-b border-dotted border-muted-foreground/50 transition-all ${clickable ? 'cursor-pointer hover:border-solid hover:border-primary hover:text-primary' : 'cursor-help'} ${className}`}
            onClick={clickable ? onClick : undefined}
          >
            {children || glossaryItem.term}
            {showIcon && <Info className={`h-3 w-3 ${clickable ? 'text-primary' : 'text-muted-foreground'}`} />}
          </span>
        </TooltipTrigger>
        <TooltipContent className="max-w-md p-4 space-y-2">
          <div>
            <p className="font-semibold text-sm">{glossaryItem.term}</p>
            <div className="text-sm text-muted-foreground mt-1 whitespace-pre-line">
              {glossaryItem.description}
            </div>
          </div>
          {glossaryItem.example && (
            <div className="pt-2 border-t">
              <p className="text-xs text-muted-foreground italic">
                {glossaryItem.example}
              </p>
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

// 便利なラッパーコンポーネント
export function MetricLabel({ 
  metric, 
  children,
  className = "",
  clickable = false,
  onClick
}: {
  metric: MetricKey
  children: React.ReactNode
  className?: string
  clickable?: boolean
  onClick?: () => void
}) {
  return (
    <MetricTooltip metric={metric} showIcon={false} className={className} clickable={clickable} onClick={onClick}>
      <span className="inline-flex items-center gap-1">
        {children}
        <Info className="h-3 w-3 text-muted-foreground" />
      </span>
    </MetricTooltip>
  )
}