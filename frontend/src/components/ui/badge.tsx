import * as React from 'react'
import { cn } from '../../lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'rejected'
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  const variantStyles = {
    default: 'border-transparent bg-[#0B2925] text-[#F8F5F3]',
    secondary: 'border-transparent bg-[#EBE5E2] text-[#27212B]',
    // Genuine -> Mint #A7F3D0 background, forest green #0B2925 text
    success: 'border-transparent bg-[#A7F3D0] text-[#0B2925] font-semibold',
    // Suspicious -> Light mauve wash (~#EBE0E9), mauve #755B73 text
    warning: 'border-transparent bg-[#EBE0E9] text-[#755B73] font-semibold',
    // Fraudulent / Fake -> Light red wash (~#FBDADA), dark red #8A2323 text
    destructive: 'border-transparent bg-[#FBDADA] text-[#8A2323] font-semibold',
    rejected: 'border-transparent bg-[#FBDADA] text-[#8A2323] font-semibold',
    outline: 'text-[#27212B] border-[#E5DDD8]',
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
