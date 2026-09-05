import React from 'react'

interface OfficerBadgeIconProps {
  className?: string
  size?: number
}

/**
 * Full-bleed circular smiley badge icon in a Mint / Soft Sage palette
 * designed to complement dark forest green backgrounds.
 */
export const OfficerBadgeIcon: React.FC<OfficerBadgeIconProps> = ({
  className = 'w-9 h-9',
  size,
}) => {
  return (
    <svg
      viewBox="0 0 36 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={size ? { width: size, height: size } : undefined}
    >
      <defs>
        {/* Soft Mint-to-Sage spherical gradient */}
        <radialGradient
          id="mintSageDisc"
          cx="32%"
          cy="28%"
          r="75%"
          fx="25%"
          fy="22%"
        >
          <stop offset="0%" stopColor="#EAF4F4" />
          <stop offset="45%" stopColor="#CCE3DE" />
          <stop offset="85%" stopColor="#A4C3B2" />
          <stop offset="100%" stopColor="#6B9080" />
        </radialGradient>
      </defs>

      {/* Face Circle - No outer golden ring */}
      <circle
        cx="18"
        cy="18"
        r="18"
        fill="url(#mintSageDisc)"
      />

      {/* Subtle top ambient sheen */}
      <ellipse
        cx="18"
        cy="7.5"
        rx="10"
        ry="3"
        fill="#FFFFFF"
        opacity="0.6"
      />

      {/* Left Eye (Deep Pine) */}
      <ellipse
        cx="12.5"
        cy="14.5"
        rx="1.9"
        ry="2.4"
        fill="#162C24"
      />

      {/* Right Eye (Deep Pine) */}
      <ellipse
        cx="23.5"
        cy="14.5"
        rx="1.9"
        ry="2.4"
        fill="#162C24"
      />

      {/* Catchlight specs */}
      <circle cx="12" cy="13.5" r="0.7" fill="#FFFFFF" />
      <circle cx="23" cy="13.5" r="0.7" fill="#FFFFFF" />

      {/* Deep Pine Smile Arc */}
      <path
        d="M10.5 19C12 25.2 24 25.2 25.5 19"
        stroke="#162C24"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
    </svg>
  )
}