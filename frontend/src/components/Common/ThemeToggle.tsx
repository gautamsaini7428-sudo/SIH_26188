import React from 'react'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'
import { soundFX } from '../../utils/audio'

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme()

  const handleToggle = () => {
    soundFX.paperSlide()
    toggleTheme()
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
      aria-label="Toggle Theme"
      className="p-2 rounded-xl border border-border bg-card text-foreground hover:bg-secondary transition-all cursor-pointer flex items-center justify-center shadow-xs"
    >
      {theme === 'light' ? (
        <Moon className="w-4 h-4 text-primary" />
      ) : (
        <Sun className="w-4 h-4 text-accent" />
      )}
    </button>
  )
}
