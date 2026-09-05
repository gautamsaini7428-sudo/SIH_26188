import type { FC } from 'react'
import { Volume2, VolumeX, RotateCcw, Shield, FileText, UserCheck, Bell, BarChart3, LogOut, User as UserIcon } from 'lucide-react'
import { soundFX } from '../../utils/audio'
import type { AppView, UserAuth } from '../../types'

interface DossierHeaderProps {
  caseNumber?: string
  currentScreen: 'intake' | 'verifying' | 'results'
  currentView: AppView
  onNavigateView: (view: AppView) => void
  unreadAlertsCount?: number
  soundEnabled: boolean
  onToggleSound: () => void
  onReset: () => void
  currentUser?: UserAuth | null
  onLogout?: () => void
}

export const DossierHeader: FC<DossierHeaderProps> = ({
  caseNumber = 'CASE-26188',
  currentScreen,
  currentView,
  onNavigateView,
  unreadAlertsCount = 0,
  soundEnabled,
  onToggleSound,
  onReset,
  currentUser,
  onLogout,
}) => {
  const navItems = [
    { id: 'dossier' as AppView, label: 'Case Intake', icon: FileText },
    { id: 'facematch' as AppView, label: 'Face Biometrics', icon: UserCheck },
    { id: 'alerts' as AppView, label: 'Alerts', icon: Bell, badge: unreadAlertsCount },
    { id: 'reporting' as AppView, label: 'Audit & Reports', icon: BarChart3 },
  ]

  return (
    <header className="w-full border-b border-[#E3DCD6] bg-[#FFFFFF] sticky top-0 z-40">
      {/* Top Bar */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-15 flex items-center justify-between">
        {/* Official Header Badge */}
        <div
          onClick={() => {
            onNavigateView('dossier')
            onReset()
          }}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-8 h-8 rounded bg-[#F8F5F3] border border-[#E3DCD6] flex items-center justify-center text-[#0B2925] group-hover:border-[#0B2925] transition-colors">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-editorial text-base font-bold text-[#0B2925] tracking-tight">
                Case Examination Registry
              </span>
              <span className="text-[10px] font-mono text-[#6E6571] bg-[#F2ECE9] px-1.5 py-0.2 rounded border border-[#E3DCD6]">
                {caseNumber}
              </span>
            </div>
            <p className="text-[10.5px] text-[#6E6571] font-sans">
              Identity Document &amp; Biometric Intake System
            </p>
          </div>
        </div>

        {/* Secondary Nav Bar */}
        <nav className="hidden md:flex items-center space-x-1 bg-[#F8F5F3] p-1 rounded-lg border border-[#E3DCD6]">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentView === item.id

            return (
              <button
                key={item.id}
                onClick={() => {
                  soundFX.paperSlide()
                  onNavigateView(item.id)
                }}
                className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-sans transition-all select-none cursor-pointer ${
                  isActive
                    ? 'bg-[#FFFFFF] text-[#0B2925] font-semibold shadow-xs border border-[#E3DCD6]/80'
                    : 'text-[#6E6571] hover:text-[#0B2925] hover:bg-[#FFFFFF]/50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>

                {item.badge !== undefined && item.badge > 0 && (
                  <span className="ml-0.5 px-1.5 py-0.2 rounded-full text-[9.5px] font-mono font-bold bg-[#8B1E1E] text-[#FFFFFF]">
                    {item.badge}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* User Account Status Badge & Controls */}
        <div className="flex items-center gap-2.5">
          {currentUser && (
            <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded border border-[#E3DCD6] bg-[#FCFAF8] text-xs">
              <UserIcon className="w-3.5 h-3.5 text-[#0B2925]" />
              <div className="leading-tight">
                <div className="font-semibold text-[#0B2925] flex items-center gap-1">
                  <span className="font-mono text-[10px] bg-[#A7F3D0]/60 text-[#0B2925] px-1 rounded uppercase font-bold">
                    {currentUser.role}
                  </span>
                  <span className="truncate max-w-[140px]">{currentUser.email}</span>
                </div>
                <div className="text-[9.5px] text-[#6E6571] truncate max-w-[160px]">
                  {currentUser.checkpointLocation}
                </div>
              </div>
            </div>
          )}

          {/* Sound Toggle */}
          <button
            onClick={() => {
              onToggleSound()
              soundFX.paperSlide()
            }}
            title={soundEnabled ? 'Mute Audio' : 'Enable Audio'}
            className="p-1.5 rounded border border-[#E3DCD6] bg-[#FFFFFF] text-[#6E6571] hover:text-[#0B2925] hover:border-[#0B2925] transition-colors text-xs flex items-center gap-1 cursor-pointer"
          >
            {soundEnabled ? (
              <Volume2 className="w-4 h-4 text-[#0B2925]" />
            ) : (
              <VolumeX className="w-4 h-4 text-[#C8BEB7]" />
            )}
          </button>

          {/* Reset Action */}
          {currentView === 'dossier' && currentScreen !== 'intake' && (
            <button
              onClick={() => {
                soundFX.paperSlide()
                onReset()
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-[#0B2925] bg-[#0B2925] text-[#FFFFFF] text-xs font-sans font-medium hover:bg-[#16433C] transition-colors cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>New Exam</span>
            </button>
          )}

          {/* Logout Button */}
          {onLogout && (
            <button
              onClick={() => {
                soundFX.paperSlide()
                onLogout()
              }}
              title="Logout session"
              className="p-1.5 rounded border border-[#E3DCD6] bg-[#FFFFFF] hover:bg-[#755B73]/10 text-[#755B73] hover:border-[#755B73] transition-colors text-xs flex items-center gap-1 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline text-xs font-medium">Logout</span>
            </button>
          )}
        </div>
      </div>

      {/* Mobile Nav Bar */}
      <div className="flex md:hidden border-t border-[#E3DCD6] bg-[#F8F5F3] px-2 py-1 justify-around">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentView === item.id

          return (
            <button
              key={item.id}
              onClick={() => {
                soundFX.paperSlide()
                onNavigateView(item.id)
              }}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-sans transition-colors cursor-pointer ${
                isActive
                  ? 'bg-[#FFFFFF] text-[#0B2925] font-semibold border border-[#E3DCD6]'
                  : 'text-[#6E6571]'
              }`}
            >
              <Icon className="w-3 h-3" />
              <span>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="px-1 py-0.2 rounded-full text-[8.5px] font-mono font-bold bg-[#8B1E1E] text-[#FFFFFF]">
                  {item.badge}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </header>
  )
}
