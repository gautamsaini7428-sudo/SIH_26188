import React from 'react'

interface ScanVerifyProps {
  className?: string
}

export const ScanVerify: React.FC<ScanVerifyProps> = ({ className = '' }) => {
  return (
    <div
      className={`relative w-full max-w-[440px] mx-auto rounded-2xl overflow-hidden shadow-2xl border border-[#133D37] bg-[#0A1220] ${className}`}
    >
      <iframe
        src="/scan-verify-v2.html"
        title="Document Verification Scanning Animation"
        className="w-full h-[470px] border-0 block bg-[#0A1220]"
        loading="eager"
      />
    </div>
  )
}
