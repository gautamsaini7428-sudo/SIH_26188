import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { ArrowLeft, Mail, Lock, Shield, BarChart3, Zap } from 'lucide-react'
import { toast } from 'sonner'
import { loginUser } from '../../services/api'
import type { UserAuth } from '../../types'
import { soundFX } from '../../utils/audio'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { BrandPanel } from './BrandPanel'
import { ThemeToggle } from '../Common/ThemeToggle'

const loginSchema = z.object({
  email: z.string().email({ message: 'Enter a valid email address.' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters.' }),
})

type LoginFormValues = z.infer<typeof loginSchema>

const ROLE_META = {
  OFFICER: {
    icon: Shield,
    label: 'Officer',
    description: 'Document intake & live verification',
    chipBg: 'var(--officer-chip-bg)',
    chipText: 'var(--officer-chip-text)',
  },
  SUPERVISOR: {
    icon: BarChart3,
    label: 'Supervisor',
    description: 'Review console & audit oversight',
    chipBg: 'var(--supervisor-chip-bg)',
    chipText: 'var(--supervisor-chip-text)',
  },
}

// One-click credential suggestions per role
const QUICK_CREDENTIALS: Record<'OFFICER' | 'SUPERVISOR', { label: string; email: string; password: string; sub: string }[]> = {
  OFFICER: [
    { label: 'Attari Officer', sub: 'Attari-Wagah Border', email: 'officer.attari@mha.gov.in', password: 'Password@123' },
    { label: 'Petrapole Officer', sub: 'Petrapole-Benapole', email: 'officer.petrapole@mha.gov.in', password: 'Password@123' },
  ],
  SUPERVISOR: [
    { label: 'Delhi Supervisor', sub: 'Border HQ', email: 'supervisor.delhi@mha.gov.in', password: 'Password@123' },
    { label: 'Admin', sub: 'Central Command', email: 'admin@mha.gov.in', password: 'Password@123' },
  ],
}

interface CredentialScreenProps {
  role: 'OFFICER' | 'SUPERVISOR'
  onBack: () => void
  onLoginSuccess: (user: UserAuth) => void
}

export const CredentialScreen: React.FC<CredentialScreenProps> = ({
  role,
  onBack,
  onLoginSuccess,
}) => {
  const [loading, setLoading] = useState(false)
  const [activeQuick, setActiveQuick] = useState<string | null>(null)
  const meta = ROLE_META[role]
  const Icon = meta.icon

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const attemptLogin = async (email: string, password: string) => {
    setLoading(true)
    soundFX.paperSlide()
    try {
      const user = await loginUser(email, password)
      soundFX.stampImpact(130)
      toast.success('Access granted', {
        description: `Signed in as ${user.role} · ${user.checkpointLocation}`,
      })
      onLoginSuccess(user)
    } catch (err: any) {
      soundFX.stampImpact(85)
      toast.error('Access denied', {
        description: err.message || 'Invalid credentials or server unavailable.',
      })
    } finally {
      setLoading(false)
    }
  }

  const onSubmit = (values: LoginFormValues) =>
    attemptLogin(values.email, values.password)

  const handleQuickFill = (cred: { label: string; email: string; password: string }) => {
    setValue('email', cred.email, { shouldValidate: true })
    setValue('password', cred.password, { shouldValidate: true })
    setActiveQuick(cred.email)
    // Auto-submit immediately
    attemptLogin(cred.email, cred.password)
  }

  const quickCreds = QUICK_CREDENTIALS[role]

  return (
    <div
      className="min-h-screen p-4 sm:p-6 md:p-8 lg:p-10 flex flex-col justify-center font-sans relative"
      style={{
        backgroundColor: 'var(--auth-page)',
        backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.08) 1.2px, transparent 1.2px)',
        backgroundSize: '28px 28px',
      }}
    >
      <div className="max-w-6xl w-full mx-auto space-y-5">
        {/* ── TOP NAV ── */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 text-xs font-medium transition-opacity hover:opacity-70 cursor-pointer text-[#50589C] dark:text-[#AAB6C8]"
            style={{ background: 'none', border: 'none', padding: 0 }}
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to role selection
          </button>

          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-[var(--foreground)]">
              Sign in
            </span>
            <ThemeToggle />
          </div>
        </div>

        {/* -- CARD -- */}
        <div
          className="w-full rounded-[28px] overflow-hidden border shadow-lg flex flex-col md:flex-row items-stretch"
          style={{ borderColor: 'var(--border)', backgroundColor: 'var(--auth-panel)', minHeight: '600px' }}
        >
          {/* Left Panel */}
          <BrandPanel />
          <div className="flex-1 p-6 sm:p-10 lg:p-12 flex flex-col justify-center" style={{ backgroundColor: 'var(--auth-panel)' }}>
            <div className="max-w-md w-full mx-auto space-y-5">
              {/* Role badge */}
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 mb-1.5">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: meta.chipBg, border: `1px solid ${meta.chipText}22` }}>
                    <Icon className="w-4 h-4" style={{ color: meta.chipText }} />
                  </div>
                  <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded" style={{ backgroundColor: meta.chipBg, color: meta.chipText }}>
                    {meta.label}
                  </span>
                  <span className="text-xs text-[var(--page-secondary)]">
                    {meta.description}
                  </span>
                </div>

                <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--card-foreground)]">
                  {role === 'OFFICER' ? 'Officer sign-in' : 'Supervisor sign-in'}
                </h2>
                <p className="text-xs sm:text-sm text-[var(--page-secondary)]">
                  Use your official MHA credentials to access the screening console.
                </p>
              </div>

              {/* ── QUICK LOGIN CHIPS ── */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5">
                  <Zap className="w-3 h-3 text-[var(--accent)]" />
                  <span className="text-[11px] font-semibold text-[var(--accent)] uppercase tracking-widest">
                    Quick sign-in
                  </span>
                </div>
                <div className="flex flex-col gap-2">
                  {quickCreds.map((cred) => (
                    <button
                      key={cred.email}
                      type="button"
                      disabled={loading}
                      onClick={() => handleQuickFill(cred)}
                      className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border border-[#E5DDD8] dark:border-[#1C345C] bg-[var(--auth-card)] transition-all cursor-pointer text-left group"
                      style={{
                        backgroundColor: activeQuick === cred.email ? meta.chipBg : undefined,
                        borderColor: activeQuick === cred.email ? meta.chipText + '44' : undefined,
                        opacity: loading && activeQuick !== cred.email ? 0.5 : 1,
                      }}
                    >
                      <div>
                        <p className="text-xs font-semibold text-[var(--card-foreground)] group-hover:text-[var(--page-heading)]">
                          {cred.label}
                        </p>
                        <p className="text-[10px] text-[var(--page-secondary)] font-mono mt-0.5">
                          {cred.email}
                        </p>
                      </div>
                      <span
                        className="text-[10px] font-medium px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: meta.chipBg, color: meta.chipText }}
                      >
                        {cred.sub}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Divider */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-[var(--border)]" />
                <span className="text-[11px] text-[var(--muted-foreground)] font-medium">or enter manually</span>
                <div className="flex-1 h-px bg-[var(--border)]" />
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
                <div className="space-y-1">
                  <label
                    className="text-xs sm:text-sm font-semibold text-[var(--card-foreground)]"
                    htmlFor="cred-email"
                  >
                    Official Email
                  </label>
                  <div className="relative">
                    <Mail
                      className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted-foreground)]"
                    />
                    <Input
                      id="cred-email"
                      type="email"
                      placeholder={role === 'OFFICER' ? 'officer.attari@mha.gov.in' : 'supervisor.delhi@mha.gov.in'}
                      autoComplete="email"
                      style={{
                        paddingLeft: '2.25rem',
                        backgroundColor: 'var(--auth-panel)',
                        border: '1px solid var(--border)',
                        color: 'var(--card-foreground)',
                      }}
                      {...register('email')}
                    />
                  </div>
                  {errors.email && (
                    <p className="text-xs text-[#DC2626]">
                      {errors.email.message}
                    </p>
                  )}
                </div>

                <div className="space-y-1">
                  <label
                    className="text-xs sm:text-sm font-semibold text-[var(--page-heading)]"
                    htmlFor="cred-password"
                  >
                    Password
                  </label>
                  <div className="relative">
                    <Lock
                      className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--page-secondary)]"
                    />
                    <Input
                      id="cred-password"
                      type="password"
                      placeholder="••••••••"
                      autoComplete="current-password"
                      style={{
                        paddingLeft: '2.25rem',
                        backgroundColor: 'var(--auth-panel)',
                        border: '1px solid var(--border)',
                        color: 'var(--card-foreground)',
                      }}
                      {...register('password')}
                    />
                  </div>
                  {errors.password && (
                    <p className="text-xs text-[#DC2626]">
                      {errors.password.message}
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full font-semibold h-10 sm:h-11 cursor-pointer bg-[#3C467B] dark:bg-[#334FE0] hover:bg-[#50589C] dark:hover:bg-[#3D8FD8] text-white transition-all rounded-xl"
                >
                  {loading ? 'Signing in…' : 'Sign in to Console'}
                </Button>
              </form>

              {/* Footer */}
              <p className="text-[11px] text-center text-[var(--page-secondary)] pt-1">
                Restricted access — authorized government personnel only
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
