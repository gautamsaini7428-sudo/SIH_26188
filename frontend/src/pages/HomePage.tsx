import React from 'react'
import { Link } from 'wouter'
import { ScanVerify } from '../components/ScanVerify/ScanVerify'
import {
  Shield,
  CheckCircle2,
  XCircle,
  FileText,
  Scan,
  Lock,
  ArrowRight,
  ChevronRight,
  Fingerprint,
  Binary,
  Search,
  Activity,
  ShieldCheck,
  IdCard,
  CreditCard,
  FileBadge,
  Stamp,
  Globe,
} from 'lucide-react'

export const HomePage: React.FC = () => {

  return (
    <div className="min-h-screen bg-[#0f1634] text-[#F8F5F3] selection:bg-[#DDE4FF] selection:text-[#3C467B] font-sans">
      {/* ========================================================================= */}
      {/* 1. PUBLIC NAVBAR                                                          */}
      {/* ========================================================================= */}
      <nav className="w-full bg-[#0f1634]/90 backdrop-blur-md border-b border-[#2d3d7a] sticky top-0 z-50 transition-all">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-18 flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-3 group select-none cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-[#3C467B] border border-[#DDE4FF]/40 flex items-center justify-center text-[#EAF0FF] group-hover:bg-[#6E8CFB] group-hover:text-[#ffffff] transition-all duration-200 shadow-md">
              <Shield className="w-5 h-5 transition-transform group-hover:scale-110" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-[#F8F5F3] group-hover:text-[#DDE4FF] transition-colors">
                  Case Examination Registry
                </span>
                <span className="text-[10px] font-mono font-bold text-[#ffffff] bg-[#6E8CFB] px-2 py-0.5 rounded shadow-xs">
                  SIH26188
                </span>
              </div>
              <p className="text-[11px] text-[#DDE4FF]/80 font-sans tracking-wide">
                AI Identity Screening System • MHA Border Control
              </p>
            </div>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center space-x-7 text-sm font-medium text-[#F8F5F3]/75">
            <a href="#how-it-works" className="hover:text-[#A7F3D0] transition-colors">
              How It Works
            </a>
            <a href="#capabilities" className="hover:text-[#A7F3D0] transition-colors">
              Capabilities
            </a>
            <a href="#documents" className="hover:text-[#A7F3D0] transition-colors">
              Supported Docs
            </a>
            <a href="#security" className="hover:text-[#A7F3D0] transition-colors">
              Security Architecture
            </a>
          </div>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="hidden sm:inline-flex items-center justify-center text-sm font-medium text-[#F8F5F3] hover:text-[#DDE4FF] px-4 py-2 rounded-lg border border-[#3C467B] hover:border-[#6E8CFB]/60 hover:bg-[#171f46] transition-all"
            >
              Sign In
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 text-sm font-semibold bg-[#6E8CFB] hover:bg-[#50589C] text-[#ffffff] px-4 py-2 rounded-lg shadow-sm hover:shadow-md transition-all active:scale-95"
            >
              <span>Access Console</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ========================================================================= */}
      {/* 2. HERO SECTION                                                           */}
      {/* ========================================================================= */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28 border-b border-[#2d3d7a]">
        {/* Subtle Background Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[350px] bg-[#3C467B]/60 blur-[130px] -z-10 rounded-full pointer-events-none" />
        <div className="absolute top-10 right-10 w-[300px] h-[300px] bg-[#6E8CFB]/10 blur-[100px] -z-10 rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Hero Content */}
            <div className="lg:col-span-6 space-y-6">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#171f46] border border-[#6E8CFB]/30 text-xs font-mono text-[#DDE4FF]">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>ICAO Doc 9303 • NIST-Standard Biometrics</span>
              </div>

              {/* Main Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-5xl font-extrabold tracking-tight text-[#F8F5F3] leading-[1.15]">
                Automated Identity Screening &amp; Forensic Document Inspection
              </h1>

              {/* Subtext */}
              <p className="text-base sm:text-lg text-[#F8F5F3]/80 leading-relaxed font-normal">
                Multi-layer AI verification engine engineered for border checkpoints, immigration desks, and
                high-trust registries. Detects pixel-level tampering, validates machine-readable zones, and matches
                live facial biometrics in milliseconds.
              </p>

              {/* CTAs */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-[#6E8CFB] text-[#ffffff] font-bold text-base hover:bg-[#50589C] shadow-lg shadow-[#6E8CFB]/20 transition-all active:scale-98"
                >
                  <Scan className="w-5 h-5" />
                  <span>Start Verification</span>
                  <ChevronRight className="w-4 h-4" />
                </Link>

                <Link
                  to="/login"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-[#171f46] hover:bg-[#212d5f] text-[#F8F5F3] font-medium text-base border border-[#3C467B] hover:border-[#6E8CFB]/60 transition-all"
                >
                  <Lock className="w-4 h-4 text-[#DDE4FF]" />
                  <span>Operator Login</span>
                </Link>
              </div>

              {/* Trust Indicators / Badges */}
              <div className="pt-6 border-t border-[#133D37]/80 grid grid-cols-3 gap-4">
                <div>
                  <div className="text-2xl font-bold font-mono text-[#DDE4FF]">5-Gate</div>
                  <div className="text-xs text-[#F8F5F3]/60 mt-0.5">Forensic Pipeline</div>
                </div>
                <div>
                  <div className="text-2xl font-bold font-mono text-[#DDE4FF]">Sub-Sec</div>
                  <div className="text-xs text-[#F8F5F3]/60 mt-0.5">Automated Verdict</div>
                </div>
                <div>
                  <div className="text-2xl font-bold font-mono text-[#DDE4FF]">0 Cloud</div>
                  <div className="text-xs text-[#F8F5F3]/60 mt-0.5">Data Retention Option</div>
                </div>
              </div>
            </div>

            {/* Right Hero Animation (ScanVerify) */}
            <div className="lg:col-span-6 flex justify-center items-center">
              <ScanVerify />
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. CAPABILITIES / TRUST CARDS (5 Core Pillars)                            */}
      {/* ========================================================================= */}
      <section id="capabilities" className="py-20 bg-[#0f1634] border-b border-[#2d3d7a]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#A7F3D0] bg-[#0B2925] border border-[#133D37] px-3 py-1 rounded-full">
              System Capabilities
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8F5F3] tracking-tight">
              Five Layers of Defense-Grade Forensic Analysis
            </h2>
            <p className="text-[#F8F5F3]/70 text-base">
              Engineered with specialized computer vision algorithms, mathematical checksum validators, and deep
              convolutional biometric networks.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="rounded-xl bg-[#0B2925] border border-[#133D37] p-6 hover:border-[#A7F3D0]/40 transition-all duration-200 group">
              <div className="w-12 h-12 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-5 group-hover:bg-[#A7F3D0] group-hover:text-[#0B2925] transition-colors">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#F8F5F3] mb-2">High-Precision OCR &amp; Extraction</h3>
              <p className="text-sm text-[#F8F5F3]/70 leading-relaxed mb-4">
                Multi-pass optical character recognition tailored for passports, ID cards, and driving permits. Parses
                Latin, Devanagari, and complex security micro-typography without field distortion.
              </p>
              <div className="text-xs font-mono text-[#A7F3D0] flex items-center gap-1.5">
                <span>Multi-Resolution Tesseract Engine</span>
              </div>
            </div>

            {/* Card 2 */}
            <div className="rounded-xl bg-[#0B2925] border border-[#133D37] p-6 hover:border-[#A7F3D0]/40 transition-all duration-200 group">
              <div className="w-12 h-12 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-5 group-hover:bg-[#A7F3D0] group-hover:text-[#0B2925] transition-colors">
                <Binary className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#F8F5F3] mb-2">MRZ &amp; Checksum Verification</h3>
              <p className="text-sm text-[#F8F5F3]/70 leading-relaxed mb-4">
                Strict adherence to ICAO Doc 9303 standards. Computes modulo-10 weights for document number, birth
                date, expiry, and composite checksums to identify synthetically generated numbers.
              </p>
              <div className="text-xs font-mono text-[#A7F3D0] flex items-center gap-1.5">
                <span>TD1, TD2, TD3 Modulo-10 Rules</span>
              </div>
            </div>

            {/* Card 3 */}
            <div className="rounded-xl bg-[#0B2925] border border-[#133D37] p-6 hover:border-[#A7F3D0]/40 transition-all duration-200 group">
              <div className="w-12 h-12 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-5 group-hover:bg-[#A7F3D0] group-hover:text-[#0B2925] transition-colors">
                <Search className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#F8F5F3] mb-2">Forensic Tampering &amp; Splicing</h3>
              <p className="text-sm text-[#F8F5F3]/70 leading-relaxed mb-4">
                Error Level Analysis (ELA) and Laplacian gradient filters expose photo-replacement borders, font
                kerning alterations, digital copy-paste patches, and color temperature discrepancies.
              </p>
              <div className="text-xs font-mono text-[#A7F3D0] flex items-center gap-1.5">
                <span>ELA &amp; Fourier Edge Transform</span>
              </div>
            </div>

            {/* Card 4 */}
            <div className="rounded-xl bg-[#0B2925] border border-[#133D37] p-6 hover:border-[#A7F3D0]/40 transition-all duration-200 group">
              <div className="w-12 h-12 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-5 group-hover:bg-[#A7F3D0] group-hover:text-[#0B2925] transition-colors">
                <Fingerprint className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#F8F5F3] mb-2">Biometric Facial Verification</h3>
              <p className="text-sm text-[#F8F5F3]/70 leading-relaxed mb-4">
                512-dimensional facial embedding generation cross-matched between the photo cropped from the physical ID
                and live camera selfie. Cosine similarity metric flags impersonation attempts.
              </p>
              <div className="text-xs font-mono text-[#A7F3D0] flex items-center gap-1.5">
                <span>NIST FRVT-Aligned Embeddings</span>
              </div>
            </div>

            {/* Card 5 */}
            <div className="rounded-xl bg-[#0B2925] border border-[#133D37] p-6 hover:border-[#A7F3D0]/40 transition-all duration-200 group md:col-span-2 lg:col-span-2">
              <div className="w-12 h-12 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-5 group-hover:bg-[#A7F3D0] group-hover:text-[#0B2925] transition-colors">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#F8F5F3] mb-2">Explainable Risk Scoring &amp; Audit Trail</h3>
              <p className="text-sm text-[#F8F5F3]/70 leading-relaxed mb-4">
                Every verdict is accompanied by transparent, mathematically bounded risk factor breakdowns rather than a
                black-box score. Supervisor escalation workflows log immutable checkpoint timestamps and officer decisions.
              </p>
              <div className="text-xs font-mono text-[#A7F3D0] flex items-center gap-1.5">
                <span>Supervisor Review Console • Case Logging</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. HOW IT WORKS (5-Step Timeline)                                         */}
      {/* ========================================================================= */}
      <section id="how-it-works" className="py-20 bg-[#0B2925]/40 border-b border-[#133D37]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#A7F3D0] bg-[#0B2925] border border-[#133D37] px-3 py-1 rounded-full">
              Inspection Workflow
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8F5F3] tracking-tight">
              From Document Capture to Final Verdict
            </h2>
            <p className="text-[#F8F5F3]/70 text-base">
              A synchronized 5-stage verification sequence designed for seamless checkpoint throughput.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
            {/* Step 1 */}
            <div className="p-5 rounded-xl bg-[#0B2925] border border-[#133D37] relative flex flex-col justify-between">
              <div>
                <div className="w-8 h-8 rounded-full bg-[#A7F3D0] text-[#0B2925] font-mono font-bold flex items-center justify-center text-sm mb-4">
                  01
                </div>
                <h4 className="font-bold text-base text-[#F8F5F3] mb-2">Secure Intake</h4>
                <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                  Operator uploads a high-resolution scan or captures direct physical document feed via camera scanner.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#133D37] text-[11px] font-mono text-[#A7F3D0]">
                Resolution &amp; Glare Check
              </div>
            </div>

            {/* Step 2 */}
            <div className="p-5 rounded-xl bg-[#0B2925] border border-[#133D37] relative flex flex-col justify-between">
              <div>
                <div className="w-8 h-8 rounded-full bg-[#133D37] text-[#A7F3D0] font-mono font-bold flex items-center justify-center text-sm mb-4">
                  02
                </div>
                <h4 className="font-bold text-base text-[#F8F5F3] mb-2">AI Extraction</h4>
                <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                  Neural OCR segments name, document number, birthdate, and extracts raw MRZ lines for character alignment.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#133D37] text-[11px] font-mono text-[#A7F3D0]">
                Bounding Box Parsing
              </div>
            </div>

            {/* Step 3 */}
            <div className="p-5 rounded-xl bg-[#0B2925] border border-[#133D37] relative flex flex-col justify-between">
              <div>
                <div className="w-8 h-8 rounded-full bg-[#133D37] text-[#A7F3D0] font-mono font-bold flex items-center justify-center text-sm mb-4">
                  03
                </div>
                <h4 className="font-bold text-base text-[#F8F5F3] mb-2">Forensic Audit</h4>
                <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                  Computer vision algorithms evaluate compression signatures, font consistency, and splice borders around portrait photos.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#133D37] text-[11px] font-mono text-[#A7F3D0]">
                Error Level Analysis
              </div>
            </div>

            {/* Step 4 */}
            <div className="p-5 rounded-xl bg-[#0B2925] border border-[#133D37] relative flex flex-col justify-between">
              <div>
                <div className="w-8 h-8 rounded-full bg-[#133D37] text-[#A7F3D0] font-mono font-bold flex items-center justify-center text-sm mb-4">
                  04
                </div>
                <h4 className="font-bold text-base text-[#F8F5F3] mb-2">Face Biometrics</h4>
                <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                  Live traveler selfie is captured, tested for presentation spoofing, and matched against extracted document photo.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#133D37] text-[11px] font-mono text-[#A7F3D0]">
                1:1 Vector Distance
              </div>
            </div>

            {/* Step 5 */}
            <div className="p-5 rounded-xl bg-[#0B2925] border border-[#133D37] relative flex flex-col justify-between">
              <div>
                <div className="w-8 h-8 rounded-full bg-[#A7F3D0] text-[#0B2925] font-mono font-bold flex items-center justify-center text-sm mb-4">
                  05
                </div>
                <h4 className="font-bold text-base text-[#F8F5F3] mb-2">Final Verdict</h4>
                <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                  Engine renders instant VERIFIED, SUSPICIOUS, or REJECTED stamp with full report routing to supervisor console.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#133D37] text-[11px] font-mono text-[#A7F3D0]">
                Audit Trail Recorded
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. SUPPORTED DOCUMENT TYPES (6 Cards)                                     */}
      {/* ========================================================================= */}
      <section id="documents" className="py-20 bg-[#061A17] border-b border-[#133D37]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#A7F3D0] bg-[#0B2925] border border-[#133D37] px-3 py-1 rounded-full">
              Document Coverage
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8F5F3] tracking-tight">
              Universal Credential Support
            </h2>
            <p className="text-[#F8F5F3]/70 text-base">
              Pre-trained and calibrated to identify authentic government-issued identity documents globally.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Doc 1 */}
            <div className="p-6 rounded-xl bg-[#0B2925] border border-[#133D37] hover:border-[#A7F3D0]/30 transition-all">
              <div className="w-10 h-10 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-4">
                <FileBadge className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-[#F8F5F3] mb-1">International Passports</h3>
              <p className="text-xs text-[#A7F3D0] font-mono mb-3">ICAO 9303 • TD3 Specification</p>
              <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                2-line machine readable zone parsing, national crest authenticity checks, portrait isolation, and expiry validation.
              </p>
            </div>

            {/* Doc 2 */}
            <div className="p-6 rounded-xl bg-[#0B2925] border border-[#133D37] hover:border-[#A7F3D0]/30 transition-all">
              <div className="w-10 h-10 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-4">
                <IdCard className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-[#F8F5F3] mb-1">National ID Cards</h3>
              <p className="text-xs text-[#A7F3D0] font-mono mb-3">TD1 &amp; TD2 Formats</p>
              <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                Dual-surface alignment, national identity number checksums, holograph texture detection, and ghost portrait matching.
              </p>
            </div>

            {/* Doc 3 */}
            <div className="p-6 rounded-xl bg-[#0B2925] border border-[#133D37] hover:border-[#A7F3D0]/30 transition-all">
              <div className="w-10 h-10 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-4">
                <CreditCard className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-[#F8F5F3] mb-1">Driving Licenses</h3>
              <p className="text-xs text-[#A7F3D0] font-mono mb-3">Regional &amp; State Formats</p>
              <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                Automated vehicle class classification parsing, barcode cross-correlation, and issuer security pattern inspection.
              </p>
            </div>

            {/* Doc 4 */}
            <div className="p-6 rounded-xl bg-[#0B2925] border border-[#133D37] hover:border-[#A7F3D0]/30 transition-all">
              <div className="w-10 h-10 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-4">
                <Globe className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-[#F8F5F3] mb-1">Visas &amp; Entry Permits</h3>
              <p className="text-xs text-[#A7F3D0] font-mono mb-3">Consular &amp; e-Visa Endorsements</p>
              <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                Counter-entry tracking, sticker seal tamper identification, entry clearance duration math, and MRV-A / MRV-B format parsing.
              </p>
            </div>

            {/* Doc 5 */}
            <div className="p-6 rounded-xl bg-[#0B2925] border border-[#133D37] hover:border-[#A7F3D0]/30 transition-all">
              <div className="w-10 h-10 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-4">
                <Stamp className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-[#F8F5F3] mb-1">Residence &amp; Work Permits</h3>
              <p className="text-xs text-[#A7F3D0] font-mono mb-3">Long-Stay &amp; Diplomatic Credentials</p>
              <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                Foreign citizen authorization validation, biometric chip emulation cross-checks, and validity window verification.
              </p>
            </div>

            {/* Doc 6 */}
            <div className="p-6 rounded-xl bg-[#0B2925] border border-[#133D37] hover:border-[#A7F3D0]/30 transition-all">
              <div className="w-10 h-10 rounded-lg bg-[#133D37] text-[#A7F3D0] flex items-center justify-center mb-4">
                <Shield className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-lg text-[#F8F5F3] mb-1">Government ID Credentials</h3>
              <p className="text-xs text-[#A7F3D0] font-mono mb-3">Defense &amp; Law Enforcement Badges</p>
              <p className="text-xs text-[#F8F5F3]/70 leading-relaxed">
                Custom credential structure mapping, tamper-evident background watermark examination, and agency verification registry checks.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. SECURITY ARCHITECTURE SECTION                                          */}
      {/* ========================================================================= */}
      <section id="security" className="py-20 bg-[#0B2925]/30 border-b border-[#133D37]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-6 space-y-5">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#A7F3D0] bg-[#0B2925] border border-[#133D37] px-3 py-1 rounded-full">
                Zero Trust Architecture
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8F5F3] tracking-tight">
                Designed for Border Security &amp; Regulated Defense Deployments
              </h2>
              <p className="text-[#F8F5F3]/70 text-base leading-relaxed">
                Our architecture enforces rigorous operational security principles. Biometric templates are calculated
                in volatile memory and immediately discarded unless explicitly configured for local encrypted audit logs.
              </p>

              <div className="space-y-3.5 pt-2">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-md bg-[#133D37] text-[#A7F3D0] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h5 className="font-bold text-sm text-[#F8F5F3]">Volatile In-Memory Verification</h5>
                    <p className="text-xs text-[#F8F5F3]/60">
                      Zero persistent disk caching of raw selfie streams or unredacted passport crops during screening.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-md bg-[#133D37] text-[#A7F3D0] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h5 className="font-bold text-sm text-[#F8F5F3]">Dual-Control Officer Supervision</h5>
                    <p className="text-xs text-[#F8F5F3]/60">
                      Border cases flagged with high risk automatically route to senior supervisor consoles for final adjudication.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-md bg-[#133D37] text-[#A7F3D0] flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h5 className="font-bold text-sm text-[#F8F5F3]">Immutable Audit Trail</h5>
                    <p className="text-xs text-[#F8F5F3]/60">
                      Cryptographically signed audit logs for chain of custody and legal admissibility in immigration inquiries.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Architecture Diagram Visualization */}
            <div className="lg:col-span-6">
              <div className="rounded-xl bg-[#0B2925] border border-[#133D37] p-6 space-y-3 font-mono text-xs shadow-xl">
                <div className="text-[#A7F3D0] text-sm font-bold flex items-center justify-between pb-3 border-b border-[#133D37]">
                  <span>SECURITY PIPELINE LAYERS</span>
                  <span className="text-[11px] text-[#F8F5F3]/50">ISO / IEC 30107</span>
                </div>

                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-[#A7F3D0]" />
                    <span className="text-[#F8F5F3] font-semibold">Layer 1: Input Integrity &amp; Quality</span>
                  </div>
                  <span className="text-emerald-400 text-[11px]">DPI &gt; 300</span>
                </div>

                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-[#A7F3D0]" />
                    <span className="text-[#F8F5F3] font-semibold">Layer 2: Syntactic &amp; MRZ Checksums</span>
                  </div>
                  <span className="text-emerald-400 text-[11px]">Modulo-10</span>
                </div>

                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-[#A7F3D0]" />
                    <span className="text-[#F8F5F3] font-semibold">Layer 3: Computer Vision Forensic ELA</span>
                  </div>
                  <span className="text-emerald-400 text-[11px]">Fourier Trans</span>
                </div>

                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-[#A7F3D0]" />
                    <span className="text-[#F8F5F3] font-semibold">Layer 4: Biometric Landmark Matching</span>
                  </div>
                  <span className="text-emerald-400 text-[11px]">Cosine Distance</span>
                </div>

                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-[#A7F3D0]" />
                    <span className="text-[#F8F5F3] font-semibold">Layer 5: Supervisor Ledger Routing</span>
                  </div>
                  <span className="text-[#A7F3D0] text-[11px]">Signed Event</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 7. VERIFIED VS REJECTED COMPARISON                                        */}
      {/* ========================================================================= */}
      <section className="py-20 bg-[#061A17] border-b border-[#133D37]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#A7F3D0] bg-[#0B2925] border border-[#133D37] px-3 py-1 rounded-full">
              Inspection Comparison
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8F5F3] tracking-tight">
              Instant Detection of Digital Alterations
            </h2>
            <p className="text-[#F8F5F3]/70 text-base">
              See the differential markers our forensic model highlights when scrutinizing genuine versus modified credentials.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Authentic Case Card */}
            <div className="rounded-2xl bg-[#0B2925] border border-emerald-900/50 p-6 shadow-lg space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#133D37]">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <span className="font-bold text-base text-[#F8F5F3]">Authentic Credential Marker</span>
                </div>
                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  STATUS: PASS
                </span>
              </div>

              <div className="space-y-3 text-xs text-[#F8F5F3]/80">
                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <span className="font-medium">MRZ Composite Parity</span>
                  <span className="text-emerald-400 font-mono font-bold">100% Valid</span>
                </div>
                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <span className="font-medium">Photo Boundary Compression</span>
                  <span className="text-emerald-400 font-mono font-bold">Uniform (No Splice)</span>
                </div>
                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <span className="font-medium">Font Baseline &amp; Kerning</span>
                  <span className="text-emerald-400 font-mono font-bold">Zero Anomaly</span>
                </div>
                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <span className="font-medium">Facial Embedding Similarity</span>
                  <span className="text-emerald-400 font-mono font-bold">98.4% Match</span>
                </div>
              </div>

              <p className="text-xs text-[#F8F5F3]/60 italic">
                Result: Fast-track automated clearance with 0 supervisor escalation flags.
              </p>
            </div>

            {/* Tampered Case Card */}
            <div className="rounded-2xl bg-[#0B2925] border border-rose-900/50 p-6 shadow-lg space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-[#133D37]">
                <div className="flex items-center gap-2">
                  <XCircle className="w-5 h-5 text-rose-400" />
                  <span className="font-bold text-base text-[#F8F5F3]">Tampered Credential Flags</span>
                </div>
                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  STATUS: REJECTED
                </span>
              </div>

              <div className="space-y-3 text-xs text-[#F8F5F3]/80">
                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <span className="font-medium">MRZ Composite Parity</span>
                  <span className="text-rose-400 font-mono font-bold">Failed (Line 2 Mismatch)</span>
                </div>
                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <span className="font-medium">Photo Boundary Compression</span>
                  <span className="text-rose-400 font-mono font-bold">ELA Splice Artifacts</span>
                </div>
                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <span className="font-medium">Font Baseline &amp; Kerning</span>
                  <span className="text-rose-400 font-mono font-bold">Altered DOB Glyph</span>
                </div>
                <div className="p-3 rounded-lg bg-[#061A17] border border-[#133D37] flex items-center justify-between">
                  <span className="font-medium">Facial Embedding Similarity</span>
                  <span className="text-rose-400 font-mono font-bold">41.2% Disparity</span>
                </div>
              </div>

              <p className="text-xs text-[#F8F5F3]/60 italic">
                Result: Case quarantined. Immediate critical alert dispatched to supervisor station.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 8. FINAL CALL TO ACTION                                                   */}
      {/* ========================================================================= */}
      <section className="py-20 bg-[#0B2925] border-b border-[#133D37] relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#A7F3D0]/5 blur-[120px] rounded-full pointer-events-none" />

        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6 relative z-10">
          <div className="w-14 h-14 rounded-2xl bg-[#133D37] border border-[#A7F3D0]/40 flex items-center justify-center text-[#A7F3D0] mx-auto shadow-md">
            <Shield className="w-7 h-7" />
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8F5F3] tracking-tight">
            Ready to Run Case Examination Screening?
          </h2>

          <p className="text-base sm:text-lg text-[#F8F5F3]/80 max-w-2xl mx-auto leading-relaxed">
            Access the officer checkpoint intake console, review active fraud alerts, or launch the automated document
            analysis pipeline.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-[#A7F3D0] text-[#0B2925] font-bold text-base hover:bg-[#86efac] shadow-lg shadow-[#A7F3D0]/10 transition-all active:scale-98"
            >
              <Scan className="w-5 h-5" />
              <span>Launch Intake Console</span>
              <ChevronRight className="w-4 h-4" />
            </Link>

            <Link
              to="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-[#061A17] hover:bg-[#133D37] text-[#F8F5F3] font-medium text-base border border-[#133D37] hover:border-[#A7F3D0]/40 transition-all"
            >
              <span>Officer Sign In</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 9. FOOTER                                                                 */}
      {/* ========================================================================= */}
      <footer className="py-12 bg-[#061A17] text-[#F8F5F3]/60 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-[#0B2925] border border-[#133D37] flex items-center justify-center text-[#A7F3D0]">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-[#F8F5F3] text-sm">Case Examination Registry</span>
              <span className="ml-2 font-mono text-[10px] bg-[#0B2925] border border-[#133D37] text-[#A7F3D0] px-1.5 py-0.5 rounded">
                SIH26188
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6">
            <a href="#how-it-works" className="hover:text-[#A7F3D0] transition-colors">
              How It Works
            </a>
            <a href="#capabilities" className="hover:text-[#A7F3D0] transition-colors">
              Capabilities
            </a>
            <a href="#documents" className="hover:text-[#A7F3D0] transition-colors">
              Document Formats
            </a>
            <a href="#security" className="hover:text-[#A7F3D0] transition-colors">
              Security Standards
            </a>
            <Link to="/login" className="text-[#A7F3D0] hover:underline">
              Operator Sign In
            </Link>
          </div>

          <div className="text-center sm:text-right font-sans">
            <p>© 2026 Ministry of Home Affairs • Border Control Screening Division</p>
            <p className="text-[10px] text-[#F8F5F3]/40 mt-0.5">Automated Identity Screening Prototype SIH26188</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
