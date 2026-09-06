import * as React from 'react'
import { cn } from '../../lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'rejected'
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  const variantStyles = {
    default: 'border-transparent bg-[#3C467B] text-[#F8F5F3]',
    secondary: 'border-transparent bg-[#EAF0FF] text-[#3C467B]',
    // Genuine -> semantic green remains green for safe analysis
    success: 'border-transparent bg-[#A7F3D0] text-[#0B2925] font-semibold',
    // Medium risk -> yellow warning state
    warning: 'border-transparent bg-[#FEF3C7] text-[#92400E] font-semibold',
    // Fraudulent / Fake -> red remains red
    destructive: 'border-transparent bg-[#FBDADA] text-[#8A2323] font-semibold',
    rejected: 'border-transparent bg-[#FBDADA] text-[#8A2323] font-semibold',
    outline: 'text-[#3C467B] border-[#DDE4FF]',
  }

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-md border px-2.5 py-0.5 text-[11px] font-medium transition-colors select-none',
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
