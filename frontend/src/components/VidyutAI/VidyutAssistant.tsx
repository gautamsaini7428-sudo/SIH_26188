import React, { useState, useRef, useEffect, useCallback } from 'react'
import { X, Send, ChevronDown } from 'lucide-react'
import { OfficerBadgeIcon } from './OfficerBadgeIcon'
import { SCREEN_GUIDANCE } from './vidyutKnowledge'
import {
  askVidyutAssistant,
  type VidyutCaseContext,
  type VidyutChatMessage,
} from '../../services/api'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export type VidyutScreen = 'INTAKE' | 'RESULTS' | 'FACEMATCH' | 'ALERTS' | 'AUDIT' | 'GENERAL'
export type VidyutRole = 'OFFICER' | 'SUPERVISOR'

interface VidyutAssistantProps {
  screen: VidyutScreen
  role?: VidyutRole
  caseContext?: VidyutCaseContext
  hasNewInsight?: boolean
}

// ─── Markdown-lite renderer ──────────────────────────────────────────────────

function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split('\n')
  return lines.map((line, i) => {
    const parts: React.ReactNode[] = []
    const boldRegex = /\*\*(.*?)\*\*/g
    let lastIdx = 0
    let match
    let keyIdx = 0

    while ((match = boldRegex.exec(line)) !== null) {
      if (match.index > lastIdx) {
        parts.push(<span key={keyIdx++}>{line.slice(lastIdx, match.index)}</span>)
      }
      parts.push(<strong key={keyIdx++} className="font-bold">{match[1]}</strong>)
      lastIdx = match.index + match[0].length
    }
    if (lastIdx < line.length) {
      parts.push(<span key={keyIdx++}>{line.slice(lastIdx)}</span>)
    }

    const lineContent = parts.length > 0 ? parts : [line]
    return (
      <span key={i} className="block leading-relaxed">
        {lineContent}
        {i < lines.length - 1 && line === '' && <span className="block h-1.5" />}
      </span>
    )
  })
}

// ─── Floating Action Pill Badge ─────────────────────────────────────────────

interface FABProps {
  onClick: () => void
  pulse: boolean
  isOpen: boolean
  titleText: string
}

const FloatingBadgeButton: React.FC<FABProps> = ({ onClick, pulse, isOpen, titleText }) => (
  <button
    type="button"
    id="vidyut-fab"
    onClick={onClick}
    aria-label="Open Vidyut AI Assistant"
    className="group relative flex items-center gap-3 px-3.5 py-2 rounded-full cursor-pointer transition-all duration-300 select-none shadow-2xl hover:scale-105 active:scale-95"
    style={{
      backgroundColor: 'rgba(15, 30, 24, 0.94)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(164, 195, 178, 0.35)',
      boxShadow: isOpen
        ? '0 0 20px rgba(107, 144, 128, 0.45), 0 8px 32px rgba(0, 0, 0, 0.5)'
        : '0 8px 30px rgba(0, 0, 0, 0.4), 0 0 16px rgba(107, 144, 128, 0.25)',
    }}
  >
    {/* Left: Full Circular Mint-Sage Smiley Avatar */}
    <div className="relative shrink-0 flex items-center justify-center">
      {isOpen ? (
        <div className="w-9 h-9 rounded-full bg-[#162C24] border border-[#6B9080] flex items-center justify-center">
          <ChevronDown className="w-5 h-5 text-[#A4C3B2] rotate-180 transition-transform duration-200" />
        </div>
      ) : (
        <OfficerBadgeIcon className="w-9 h-9 transition-transform duration-300 group-hover:scale-105" />
      )}

      {/* Red Alert / Live Notification Dot */}
      {pulse && !isOpen && (
        <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-rose-500 border-2 border-[#0F1E18] animate-ping" />
      )}
    </div>

    {/* Right: Stacked Label */}
    <div className="flex flex-col items-start pr-1 text-left leading-none select-none">
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-[13px] font-bold text-[#F6FFF8] tracking-tight font-sans">
          Vidyut AI
        </span>
        {/* Live Green Online Beacon */}
        <span className="relative flex h-2 w-2 items-center justify-center">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-400 shadow-[0_0_6px_#34d399]" />
        </span>
      </div>

      <span className="text-[10px] text-[#A4C3B2] font-medium tracking-wide">
        {titleText}
      </span>
    </div>
  </button>
)

// ─── Chat Panel ──────────────────────────────────────────────────────────────

export const VidyutAssistant: React.FC<VidyutAssistantProps> = ({
  screen = 'GENERAL',
  role,
  caseContext,
  hasNewInsight = false,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [pulse, setPulse] = useState(hasNewInsight)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const historyRef = useRef<VidyutChatMessage[]>([])

  // Dynamic persona based on role or audit screen
  const isSupervisor = role === 'SUPERVISOR' || screen === 'AUDIT'
  const assistantTitle = isSupervisor ? 'Command Advisor' : 'Screening Copilot'

  const guidance = SCREEN_GUIDANCE[screen] ?? SCREEN_GUIDANCE.GENERAL

  useEffect(() => {
    setPulse(hasNewInsight)
  }, [hasNewInsight])

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150)
    }
  }, [isOpen])

  const handleOpen = useCallback(() => {
    setPulse(false)
    if (messages.length === 0) {
      const greetings: Record<string, string> = {
        INTAKE: `**Welcome, Officer.** I'm Vidyut AI, your Border Screening Assistant.\n\nI can guide you through document intake requirements, explain why a specimen might be rejected at this stage, or help with webcam capture tips. What do you need?`,
        RESULTS: caseContext
          ? `**Case Active — ${caseContext.case_number ?? 'Unknown'}.**\n\nVerdict: **${caseContext.verdict}** | Risk Score: **${caseContext.risk_score ?? 'N/A'}/100**.\n\nI can explain what this score means, decode the tampering heatmap, or walk you through the operational protocol for this verdict.`
          : `**Results Review Mode.** I can explain risk scores, MRZ checksum failures, tampering heatmap details, and next-step protocols. Ask me anything.`,
        FACEMATCH: `**Biometric Verification Mode.** I can explain face match thresholds, troubleshoot webcam capture quality, or help interpret a biometric disparity result.`,
        AUDIT: `**Command Oversight Mode.** Supervisor session active. I can assist with audit log investigations, cross-checkpoint alerts, false-positive resolution, and formal escalation packaging.`,
        GENERAL: `**Namaste.** I'm Vidyut AI — your in-system Border Screening Copilot.\n\nAsk me about checkpoint protocols, document tampering indicators, biometric verification, or compliance procedures.`,
      }

      const greeting = greetings[screen] ?? greetings.GENERAL
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: greeting,
          timestamp: new Date(),
        },
      ])
      historyRef.current = [{ role: 'assistant', content: greeting }]
    }
    setIsOpen(true)
  }, [messages.length, screen, caseContext])

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return

      const userMsg: Message = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: text.trim(),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMsg])
      setInputText('')
      setIsLoading(true)

      historyRef.current = [
        ...historyRef.current,
        { role: 'user', content: text.trim() },
      ]

      const response = await askVidyutAssistant(
        text.trim(),
        screen,
        caseContext,
        historyRef.current.slice(-8),
      )

      const assistMsg: Message = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
      }

      historyRef.current = [...historyRef.current, { role: 'assistant', content: response.answer }]
      setMessages((prev) => [...prev, assistMsg])
      setIsLoading(false)
    },
    [isLoading, screen, caseContext],
  )

  const handleQuickPrompt = useCallback(
    (promptId: string) => {
      const chip = guidance.quickPrompts.find((p) => p.id === promptId)
      if (!chip) return

      const userMsg: Message = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: chip.query,
        timestamp: new Date(),
      }

      if (chip.localAnswer) {
        const assistMsg: Message = {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: chip.localAnswer,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, userMsg, assistMsg])
        historyRef.current = [
          ...historyRef.current,
          { role: 'user', content: chip.query },
          { role: 'assistant', content: chip.localAnswer },
        ]
      } else {
        setMessages((prev) => [...prev, userMsg])
        sendMessage(chip.query)
      }
    },
    [guidance.quickPrompts, sendMessage],
  )

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(inputText)
    }
  }

  const caseBadgeText =
    caseContext?.case_number
      ? `${caseContext.case_number} · ${caseContext.verdict ?? ''} (${caseContext.risk_score ?? '?'}/100)`
      : null

  return (
    <div
      id="vidyut-ai-container"
      style={{
        position: 'fixed',
        bottom: '1.5rem',
        right: '1.5rem',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: '0.75rem',
        fontFamily: 'inherit',
      }}
    >
      {/* ── CHAT PANEL (slide-up) ── */}
      {isOpen && (
        <div
          id="vidyut-chat-panel"
          style={{
            width: '380px',
            maxWidth: 'calc(100vw - 3rem)',
            height: '560px',
            maxHeight: 'calc(100vh - 10rem)',
            backgroundColor: '#FFFFFF',
            borderRadius: '20px',
            border: '1px solid #CCE3DE',
            boxShadow: '0 20px 60px rgba(27, 51, 43, 0.25), 0 4px 16px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            animation: 'vidyutSlideUp 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)',
          }}
        >
          {/* Header */}
          <div
            style={{
              backgroundColor: '#162C24',
              padding: '14px 16px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              flexShrink: 0,
            }}
          >
            {/* Header Avatar */}
            <OfficerBadgeIcon className="w-8 h-8 shrink-0" />

            {/* Title + dynamic role subtitle */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ color: '#F6FFF8', fontWeight: 700, fontSize: 14, lineHeight: 1.2, margin: 0 }}>
                Vidyut AI
              </p>
              <p style={{ color: '#A4C3B2', fontSize: 11, margin: 0, fontWeight: 500 }}>
                {assistantTitle}
              </p>
            </div>

            {/* Context Pill */}
            <div
              style={{
                padding: '2px 8px',
                borderRadius: 999,
                backgroundColor: 'rgba(164, 195, 178, 0.15)',
                border: '1px solid rgba(164, 195, 178, 0.3)',
                flexShrink: 0,
              }}
            >
              <span style={{ color: '#CCE3DE', fontSize: 10, fontWeight: 600, fontFamily: 'monospace' }}>
                {guidance.badge.split(' ').slice(1).join(' ')}
              </span>
            </div>

            {/* Close Button */}
            <button
              id="vidyut-close-btn"
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label="Close Vidyut AI"
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: 4,
                color: '#A4C3B2',
                display: 'flex',
                alignItems: 'center',
                borderRadius: 8,
                transition: 'color 0.15s',
              }}
              onMouseOver={(e) => { (e.currentTarget as HTMLButtonElement).style.color = '#F6FFF8' }}
              onMouseOut={(e) => { (e.currentTarget as HTMLButtonElement).style.color = '#A4C3B2' }}
            >
              <X style={{ width: 16, height: 16 }} />
            </button>
          </div>

          {/* Active Case Context Banner */}
          {caseBadgeText && (
            <div
              style={{
                padding: '6px 14px',
                backgroundColor: '#FEF3C7',
                borderBottom: '1px solid #FDE68A',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                flexShrink: 0,
              }}
            >
              <span style={{ fontSize: 10, fontWeight: 700, color: '#92400E', fontFamily: 'monospace' }}>
                ⚠ ACTIVE CASE
              </span>
              <span style={{ fontSize: 10, color: '#92400E', fontWeight: 500 }}>{caseBadgeText}</span>
            </div>
          )}

          {/* Message History */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '14px 14px 8px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            {messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  alignItems: 'flex-end',
                  gap: 8,
                }}
              >
                {msg.role === 'assistant' && (
                  <OfficerBadgeIcon className="w-7 h-7 shrink-0 mb-1" />
                )}

                <div
                  style={{
                    maxWidth: '82%',
                    padding: '10px 13px',
                    borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '4px 16px 16px 16px',
                    backgroundColor: msg.role === 'user' ? '#162C24' : '#EAF4F4',
                    border: msg.role === 'user' ? 'none' : '1px solid #CCE3DE',
                    color: msg.role === 'user' ? '#F6FFF8' : '#1B332B',
                    fontSize: 12.5,
                    lineHeight: 1.55,
                  }}
                >
                  {renderMarkdown(msg.content)}
                </div>
              </div>
            ))}

            {/* Dot Loader */}
            {isLoading && (
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
                <OfficerBadgeIcon className="w-7 h-7 shrink-0 mb-1" />
                <div
                  style={{
                    padding: '10px 14px',
                    borderRadius: '4px 16px 16px 16px',
                    backgroundColor: '#EAF4F4',
                    border: '1px solid #CCE3DE',
                    display: 'flex',
                    gap: 4,
                    alignItems: 'center',
                  }}
                >
                  {[0, 0.15, 0.3].map((delay, i) => (
                    <span
                      key={i}
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: '50%',
                        backgroundColor: '#6B9080',
                        opacity: 0.6,
                        animation: 'vidyutDotPulse 1s ease-in-out infinite',
                        animationDelay: `${delay}s`,
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          <div
            style={{
              padding: '8px 14px 6px',
              borderTop: '1px solid #CCE3DE',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '6px',
              flexShrink: 0,
            }}
          >
            {guidance.quickPrompts.slice(0, 4).map((chip) => (
              <button
                key={chip.id}
                type="button"
                id={`vidyut-chip-${chip.id}`}
                onClick={() => handleQuickPrompt(chip.id)}
                disabled={isLoading}
                style={{
                  padding: '4px 10px',
                  borderRadius: 999,
                  border: '1px solid #A4C3B2',
                  backgroundColor: '#EAF4F4',
                  color: '#1B332B',
                  fontSize: 11,
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  whiteSpace: 'nowrap',
                  opacity: isLoading ? 0.5 : 1,
                }}
                onMouseOver={(e) => {
                  ;(e.currentTarget as HTMLButtonElement).style.backgroundColor = '#CCE3DE'
                }}
                onMouseOut={(e) => {
                  ;(e.currentTarget as HTMLButtonElement).style.backgroundColor = '#EAF4F4'
                }}
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <div
            style={{
              padding: '8px 10px 10px',
              borderTop: '1px solid #CCE3DE',
              display: 'flex',
              gap: 8,
              alignItems: 'center',
              flexShrink: 0,
              backgroundColor: '#F6FFF8',
            }}
          >
            <input
              ref={inputRef}
              id="vidyut-input"
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Ask Vidyut about this case or workflow…"
              style={{
                flex: 1,
                padding: '9px 12px',
                borderRadius: 12,
                border: '1.5px solid #CCE3DE',
                backgroundColor: '#FFFFFF',
                color: '#1B332B',
                fontSize: 12.5,
                outline: 'none',
                fontFamily: 'inherit',
                transition: 'border-color 0.15s',
              }}
              onFocus={(e) => { e.target.style.borderColor = '#6B9080' }}
              onBlur={(e) => { e.target.style.borderColor = '#CCE3DE' }}
            />
            <button
              id="vidyut-send-btn"
              type="button"
              onClick={() => sendMessage(inputText)}
              disabled={isLoading || !inputText.trim()}
              aria-label="Send message to Vidyut AI"
              style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                backgroundColor: inputText.trim() && !isLoading ? '#162C24' : '#CCE3DE',
                border: 'none',
                cursor: inputText.trim() && !isLoading ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'background-color 0.15s',
              }}
            >
              <Send
                style={{
                  width: 15,
                  height: 15,
                  color: inputText.trim() && !isLoading ? '#A4C3B2' : '#5C776E',
                }}
              />
            </button>
          </div>
        </div>
      )}

      {/* ── FLOATING ACTION BADGE ── */}
      <FloatingBadgeButton
        onClick={isOpen ? () => setIsOpen(false) : handleOpen}
        pulse={pulse}
        isOpen={isOpen}
        titleText={assistantTitle}
      />

      <style>{`
        @keyframes vidyutSlideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0)   scale(1); }
        }
        @keyframes vidyutDotPulse {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40%            { transform: scale(1);   opacity: 1; }
        }
      `}</style>
    </div>
  )
}