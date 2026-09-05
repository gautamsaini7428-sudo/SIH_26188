import React from 'react'
import {
  Shield,
  CheckCircle2,
  ScanLine,
  ShieldCheck,
  ClipboardList,
} from 'lucide-react'

const FEATURE_BADGES = [
  { icon: ScanLine, label: 'MRZ-verified' },
  { icon: ShieldCheck, label: 'Tamper detection' },
  { icon: ClipboardList, label: 'Audit trail' },
]

const TICKER_ITEMS = ['Hashed credentials', 'Role-scoped security', '2026 cycle active']

export const BrandPanel: React.FC = () => (
  <div
    className="w-full md:w-[44%] lg:w-[42%] flex flex-col justify-between px-7 sm:px-9 lg:px-11 py-9 lg:py-11 relative self-stretch shrink-0"
    style={{ backgroundColor: '#0B2925' }}
  >
    {/* Dot-grid texture */}
    <div
      className="absolute inset-0 pointer-events-none"
      style={{
        backgroundImage:
          'radial-gradient(circle, rgba(167,243,208,0.08) 1px, transparent 1px)',
        backgroundSize: '24px 24px',
      }}
    />

    <div className="relative z-10 flex flex-col justify-between h-full space-y-8">
      {/* ── ZONE 1: Top org lockup ── */}
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{
            backgroundColor: 'rgba(167, 243, 208, 0.12)',
            border: '1.5px solid rgba(167, 243, 208, 0.25)',
          }}
        >
          <Shield className="w-5 h-5 text-[#A7F3D0]" />
        </div>
        <div>
          <p
            className="text-xs font-mono font-semibold tracking-wide leading-tight text-[#A7F3D0]"
          >
            MHA · Border Control
          </p>
          <p className="text-[11px] leading-tight text-[#F8F5F3]/60">
            Identity Screening System
          </p>
        </div>
      </div>

      {/* ── ZONE 2: Headline block ── */}
      <div className="space-y-5 py-2">
        {/* Institutional pill badge */}
        <div>
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-[#A7F3D0]"
            style={{
              backgroundColor: 'rgba(167, 243, 208, 0.1)',
              border: '1px solid rgba(167, 243, 208, 0.22)',
            }}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Institutional access portal
          </span>
        </div>

        {/* Headline */}
        <div className="space-y-3">
          <h2
            className="font-bold leading-[1.2] tracking-tight text-[#F8F5F3] text-2xl sm:text-3xl lg:text-[32px]"
            style={{
              fontFamily: 'DM Sans, sans-serif',
            }}
          >
            Unified screening intelligence for border control.
          </h2>

          <p
            className="text-xs sm:text-sm leading-relaxed text-[#F8F5F3]/75"
            style={{
              fontFamily: 'DM Sans, sans-serif',
            }}
          >
            Verified document authenticity, biometric correlation, and
            risk-scored decisions for every checkpoint — in seconds.
          </p>
        </div>

        {/* Feature badge row */}
        <div className="flex flex-wrap gap-2 pt-1">
          {FEATURE_BADGES.map(({ icon: Icon, label }) => (
            <span
              key={label}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-[#A7F3D0]"
              style={{
                backgroundColor: 'rgba(167, 243, 208, 0.08)',
                border: '1px solid rgba(167, 243, 208, 0.18)',
              }}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* ── ZONE 3: Bottom ticker ── */}
      <div
        className="flex flex-wrap gap-x-5 gap-y-1.5 pt-4 border-t border-[#A7F3D0]/15"
      >
        {TICKER_ITEMS.map((item) => (
          <span
            key={item}
            className="flex items-center gap-1.5 text-[11px] font-medium text-[#A7F3D0]/60"
          >
            <CheckCircle2
              className="w-3 h-3 shrink-0 text-[#A7F3D0]/60"
            />
            {item}
          </span>
        ))}
      </div>
    </div>
  </div>
)
