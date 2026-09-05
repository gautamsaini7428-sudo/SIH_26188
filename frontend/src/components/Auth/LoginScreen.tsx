import React, { useState } from 'react'
import { RoleSelectScreen } from './RoleSelectScreen'
import { CredentialScreen } from './CredentialScreen'
import type { UserAuth } from '../../types'

type AuthStep = 'role-select' | 'credential'

interface LoginScreenProps {
  onLoginSuccess: (user: UserAuth) => void
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onLoginSuccess }) => {
  const [step, setStep] = useState<AuthStep>('role-select')
  const [selectedRole, setSelectedRole] = useState<'OFFICER' | 'SUPERVISOR' | null>(null)

  const handleSelectRole = (role: 'OFFICER' | 'SUPERVISOR') => {
    setSelectedRole(role)
    setStep('credential')
  }

  const handleBack = () => {
    setStep('role-select')
    setSelectedRole(null)
  }

  if (step === 'credential' && selectedRole) {
    return (
      <CredentialScreen
        role={selectedRole}
        onBack={handleBack}
        onLoginSuccess={onLoginSuccess}
      />
    )
  }

  return <RoleSelectScreen onSelectRole={handleSelectRole} />
}
