import React from 'react'
import { Link, useLocation } from 'wouter'
import { Shield, FileText, UserCheck, Bell, BarChart3, LogOut, User as UserIcon } from 'lucide-react'
import { soundFX } from '../../utils/audio'
import type { UserAuth } from '../../types'
import { ThemeToggle } from './ThemeToggle'
import { Button } from '../ui/button'

interface HeaderProps {
  currentUser: UserAuth | null
  onLogout: () => void
  unreadAlertsCount?: number
}

export const Header: React.FC<HeaderProps> = ({ currentUser, onLogout, unreadAlertsCount = 0 }) => {
  const [location] = useLocation()

  const navItems = [
    { href: '/intake', label: 'Case Intake', icon: FileText },
    { href: '/facematch', label: 'Face Biometrics', icon: UserCheck },
    { href: '/alerts', label: 'Alerts', icon: Bell, badge: unreadAlertsCount },
    { href: '/audit', label: 'Audit Console', icon: BarChart3 },
  ]

  return (
    <header className="w-full bg-[#0B2925] text-[#F8F5F3] border-b border-[#133D37] sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand Badge */}
        <Link
          to={currentUser?.role === 'SUPERVISOR' ? '/audit' : '/intake'}
          onClick={() => soundFX.paperSlide()}
          className="flex items-center gap-3 group select-none cursor-pointer"
        >
          <div className="w-9 h-9 rounded-xl bg-[#133D37] border border-[#A7F3D0]/30 flex items-center justify-center text-[#A7F3D0] group-hover:bg-[#A7F3D0] group-hover:text-[#0B2925] transition-all shadow-xs">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base text-[#F8F5F3] tracking-tight">
                Case Examination Registry
              </span>
              <span className="text-[10px] font-mono font-bold text-[#0B2925] bg-[#A7F3D0] px-1.5 py-0.5 rounded">
                SIH26188
              </span>
            </div>
            <p className="text-[10.5px] text-[#A7F3D0]/80 font-sans">
              AI Identity Screening System • MHA Border Control
            </p>
          </div>
        </Link>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1 bg-[#133D37]/70 p-1 rounded-xl border border-[#A7F3D0]/20">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location === item.href || (location === '/' && item.href === '/intake')

            return (
              <Link
                key={item.href}
                to={item.href}
                onClick={() => soundFX.paperSlide()}
                className={`relative flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all select-none cursor-pointer ${
                  isActive
                    ? 'bg-[#A7F3D0] text-[#0B2925] shadow-xs'
                    : 'text-[#F8F5F3]/80 hover:text-[#FFFFFF] hover:bg-[#133D37]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>

                {item.badge !== undefined && item.badge > 0 && (
                  <span className="ml-0.5 px-1.5 py-0.2 rounded-full text-[9.5px] font-mono font-bold bg-[#DC2626] text-[#FFFFFF]">
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* User Account Status & Controls */}
        <div className="flex items-center gap-2.5">
          {currentUser && (
            <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-xl border border-[#A7F3D0]/20 bg-[#133D37]/50 text-xs text-[#F8F5F3]">
              <UserIcon className="w-3.5 h-3.5 text-[#A7F3D0]" />
              <div className="leading-tight">
                <div className="font-semibold flex items-center gap-1.5">
                  <span className="font-mono text-[9.5px] bg-[#A7F3D0] text-[#0B2925] px-1.5 py-0.2 rounded uppercase font-bold">
                    {currentUser.role}
                  </span>
                  <span className="truncate max-w-[150px]">{currentUser.email}</span>
                </div>
                <div className="text-[10px] text-[#A7F3D0]/70 truncate max-w-[170px]">
                  {currentUser.checkpointLocation}
                </div>
              </div>
            </div>
          )}

          {/* Theme Switcher Button */}
          <ThemeToggle />

          {/* Logout Action */}
          {currentUser && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                soundFX.paperSlide()
                onLogout()
              }}
              title="Logout session"
              className="gap-1.5 text-xs text-[#F8F5F3]/80 hover:text-[#FFFFFF] hover:bg-[#133D37]"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          )}
        </div>
      </div>

      {/* Mobile Navigation Bar */}
      <div className="flex md:hidden border-t border-[#133D37] bg-[#0B2925] px-2 py-1.5 justify-around">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location === item.href

          return (
            <Link
              key={item.href}
              to={item.href}
              onClick={() => soundFX.paperSlide()}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                isActive ? 'bg-[#A7F3D0] text-[#0B2925]' : 'text-[#F8F5F3]/80'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="px-1 py-0.2 rounded-full text-[8.5px] font-mono font-bold bg-[#DC2626] text-[#FFFFFF]">
                  {item.badge}
                </span>
              )}
            </Link>
          )
        })}
      </div>
    </header>
  )
}
