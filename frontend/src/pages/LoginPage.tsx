import React from 'react'
import { LoginScreen } from '../components/Auth/LoginScreen'
import type { UserAuth } from '../types'

interface LoginPageProps {
  onLoginSuccess: (user: UserAuth) => void
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  return <LoginScreen onLoginSuccess={onLoginSuccess} />
}
