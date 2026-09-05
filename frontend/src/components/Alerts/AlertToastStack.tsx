import type { FC } from 'react'
import { AnimatePresence } from 'framer-motion'
import { AlertToast } from './AlertToast'
import type { CaseAlert } from '../../types'

interface AlertToastStackProps {
  alerts: CaseAlert[]
  onDismiss: (id: string | number) => void
  onInspect?: (alert: CaseAlert) => void
}

export const AlertToastStack: FC<AlertToastStackProps> = ({
  alerts,
  onDismiss,
  onInspect,
}) => {
  return (
    <div className="fixed top-20 right-4 z-50 flex flex-col gap-3 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {alerts.slice(0, 4).map((alert) => (
          <div key={alert.id} className="pointer-events-auto">
            <AlertToast
              alert={alert}
              onDismiss={onDismiss}
              onInspect={onInspect}
            />
          </div>
        ))}
      </AnimatePresence>
    </div>
  )
}
