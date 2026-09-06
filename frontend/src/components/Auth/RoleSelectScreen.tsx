import React from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Shield,
  BarChart3,
  Building2,
} from 'lucide-react'
import { BrandPanel } from './BrandPanel'
import { ThemeToggle } from '../Common/ThemeToggle'

interface RoleSelectScreenProps {
  onSelectRole: (role: 'OFFICER' | 'SUPERVISOR') => void
}

const ROLE_CARDS = [
  {
    role: 'OFFICER' as const,
    title: 'Officer',
    description: 'Document intake, live verification, and case screening at the checkpoint.',
    icon: Shield,
  },
  {
    role: 'SUPERVISOR' as const,
    title: 'Supervisor',
    description: 'Review console, audit trail, and cross-checkpoint oversight.',
    icon: BarChart3,
  },
]

export const RoleSelectScreen: React.FC<RoleSelectScreenProps> = ({ onSelectRole }) => {
  const [hovered, setHovered] = React.useState<'OFFICER' | 'SUPERVISOR' | null>(null)

  return (
    <div
      className="min-h-screen p-4 sm:p-6 md:p-8 lg:p-10 flex flex-col justify-center font-sans relative"
      style={{
        backgroundColor: 'var(--auth-page)',
        backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.08) 1.2px, transparent 1.2px)',
        backgroundSize: '28px 28px',
      }}
    >
      <div className="max-w-6xl w-full mx-auto space-y-4">
        {/* ── TOP NAV (Sits outside and above the rounded card) ── */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => window.history.back()}
            className="flex items-center gap-1.5 text-xs font-medium transition-opacity hover:opacity-70 cursor-pointer text-[#50589C] dark:text-[#AAB6C8]"
            style={{ background: 'none', border: 'none', padding: 0 }}
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to case registry
          </button>

          <div className="flex items-center gap-3">
            <div
              className="flex items-center rounded-full p-1 gap-1 shadow-2xs"
              style={{ backgroundColor: 'rgba(255,255,255,0.08)', border: '1px solid var(--border)' }}
            >
              <span
                className="text-[11px] font-semibold px-3 py-1 rounded-full cursor-pointer"
                style={{ backgroundColor: 'var(--primary)', color: 'var(--primary-foreground)' }}
              >
                Role Portals
              </span>
              <span
                className="text-[11px] font-medium px-3 py-1 cursor-pointer hover:text-[#3C467B] dark:hover:text-white transition-colors"
                style={{ color: 'var(--muted-foreground)' }}
              >
                Sign In
              </span>
            </div>
            <ThemeToggle />
          </div>
        </div>

        {/* ── FLOATING ROUNDED CARD CONTAINER (28px radius, true two-tone split) ── */}
        <div
          className="w-full rounded-[28px] overflow-hidden border shadow-xl flex flex-col md:flex-row items-stretch"
          style={{ borderColor: 'var(--border)', backgroundColor: 'var(--auth-panel)', minHeight: '600px' }}
        >
          {/* LEFT HALF: Solid dark forest green (#0B2925) */}
          <BrandPanel />

          {/* RIGHT HALF: Solid white / off-white (#FFFFFF) with crisp hard divider */}
          <div className="flex-1 p-6 sm:p-9 lg:p-12 flex flex-col justify-center" style={{ backgroundColor: 'var(--auth-panel)' }}>
            <div className="w-full max-w-xl mx-auto flex flex-col justify-between h-full space-y-6">
              {/* Eyebrow + heading + subcopy in dark charcoal */}
              <div className="space-y-2">
                <p className="text-[11px] font-mono font-semibold uppercase tracking-widest text-[#50589C] dark:text-[#AAB6C8]">
                  Select your workspace
                </p>
                <h1 className="text-2xl sm:text-3xl lg:text-[32px] font-bold tracking-tight text-[var(--card-foreground)] leading-tight">
                  Welcome to the screening console
                </h1>
                <p className="text-xs sm:text-sm leading-relaxed text-[var(--muted-foreground)]">
                  Click a role card to launch its dedicated workspace. If unauthenticated, you will be guided to sign in with that role pre-configured.
                </p>
              </div>

              {/* Role cards grid (white cards with thin borders sitting on light panel) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {ROLE_CARDS.map(({ role, title, description, icon: Icon }) => {
                  const isHovered = hovered === role
                  return (
                    <button
                      key={role}
                      type="button"
                      onClick={() => onSelectRole(role)}
                      onMouseEnter={() => setHovered(role)}
                      onMouseLeave={() => setHovered(null)}
                      className="w-full text-left p-5 sm:p-6 rounded-2xl transition-all duration-200 cursor-pointer relative flex flex-col justify-between group"
                      style={{
                        backgroundColor: 'var(--card)',
                        border: isHovered ? '1.5px solid var(--primary)' : '1px solid var(--border)',
                        boxShadow: isHovered
                          ? '0 8px 24px -4px rgba(99, 108, 203, 0.22), 0 2px 6px -1px rgba(0, 0, 0, 0.04)'
                          : '0 1px 3px 0 rgba(0, 0, 0, 0.03)',
                        transform: isHovered ? 'translateY(-2px)' : 'none',
                      }}
                    >
                      {/* Top icon and arrow row */}
                      <div className="flex items-center justify-between w-full mb-4">
                        <div
                          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-transform duration-200 group-hover:scale-105"
                          style={{
                            backgroundColor: 'var(--primary)',
                            color: 'var(--primary-foreground)',
                          }}
                        >
                          <Icon className="w-5 h-5 text-[var(--primary-foreground)]" />
                        </div>
                        <ArrowRight
                          className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1"
                          style={{ color: isHovered ? 'var(--primary)' : 'var(--muted-foreground)' }}
                        />
                      </div>

                      {/* Title & Description */}
                      <div className="space-y-1.5">
                        <h3 className="text-base sm:text-lg font-bold text-[var(--card-foreground)] tracking-tight">
                          {title}
                        </h3>
                        <p className="text-xs sm:text-[13px] leading-relaxed text-[var(--muted-foreground)]">
                          {description}
                        </p>
                      </div>
                    </button>
                  )
                })}
              </div>

              {/* Bottom Institutional SSO bar */}
              <div
                className="p-4 sm:p-4.5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                style={{
                  backgroundColor: 'rgba(255,255,255,0.04)',
                  border: '1px solid var(--border)',
                }}
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-[var(--foreground)]" />
                    <span className="text-xs sm:text-sm font-bold text-[var(--foreground)]">
                      Institutional Single Sign-On
                    </span>
                  </div>
                  <p className="text-[11px] text-[var(--muted-foreground)]">
                    Authenticate via MHA / Govt SSO secure access gateway
                  </p>
                </div>
                <button
                  type="button"
                  className="inline-flex items-center justify-center text-xs font-semibold px-4 py-2 rounded-xl transition-all duration-150 cursor-pointer shadow-xs hover:opacity-90 shrink-0"
                  style={{
                    backgroundColor: 'var(--accent)',
                    color: 'var(--accent-foreground)',
                  }}
                >
                  Institutional SSO
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
