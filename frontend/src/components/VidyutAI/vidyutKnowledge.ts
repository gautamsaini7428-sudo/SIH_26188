/**
 * Vidyut AI Knowledge Base & Context Configuration
 * Provides instant local answers for quick-question chips and context definitions.
 */

export interface QuickPrompt {
  id: string
  label: string
  query: string
  localAnswer?: string
}

export interface ScreenGuidance {
  badge: string
  headline: string
  quickPrompts: QuickPrompt[]
}

export const SCREEN_GUIDANCE: Record<string, ScreenGuidance> = {
  INTAKE: {
    badge: '📍 Case Intake',
    headline: 'Document Intake & Quality Control',
    quickPrompts: [
      {
        id: 'accepted-formats',
        label: 'Accepted file formats',
        query: 'What file formats and resolutions are accepted?',
        localAnswer:
          '**Accepted Document Formats:**\n\n' +
          '• **File Formats**: High-resolution `JPG`, `PNG`, `WEBP`, or single-page `PDF`.\n' +
          '• **Max Size**: 10 MB per file.\n' +
          '• **Recommended Resolution**: 300+ DPI (minimum 1200×800 px) for accurate sub-pixel tamper analysis.\n' +
          '• **Lighting**: Diffuse overhead lighting without flash hot-spots or glare on holographic laminates.',
      },
      {
        id: 'intake-rejection',
        label: 'Why documents get rejected',
        query: 'Why might a document get rejected at intake?',
        localAnswer:
          '**Common Rejection Causes:**\n\n' +
          '1. **Flash Glare**: Direct reflections washing out MRZ lines or microprinting.\n' +
          '2. **Corner Clipping**: Specimen boundary cut off outside camera frame.\n' +
          '3. **Severe Perspective Distortion**: Slanted angles > 15° disrupting aspect ratio calibration.\n' +
          '4. **Blur or Downsampling**: Low resolution preventing optical character recognition (OCR).',
      },
      {
        id: 'specimen-lighting',
        label: 'Best lighting practices',
        query: 'How should I position the physical document for best results?',
        localAnswer:
          '**Intake Capture Best Practices:**\n\n' +
          '• Lay document completely flat on a dark, non-reflective matte background.\n' +
          '• Ensure all four document corners are clearly visible inside the alignment frame.\n' +
          '• Avoid direct fluorescent reflection over the portrait photo and machine-readable zone.',
      },
      {
        id: 'preset-demo',
        label: 'How preset demo cases work',
        query: 'How do the preset demo cases work?',
        localAnswer:
          '**Preset Demo Scenarios:**\n\n' +
          'You can tap any of the quick preset scenarios (e.g. *Genuine Passport*, *Tampered Photo DL*, *MRZ Checksum Forgery*) to instantly load test specimens and observe the multi-layer forensic screening pipeline.',
      },
    ],
  },
  RESULTS: {
    badge: '📍 Results Review',
    headline: 'Specimen Risk & Tamper Analysis',
    quickPrompts: [
      {
        id: 'risk-score-meaning',
        label: 'Explain Risk Score',
        query: 'What does the risk score mean and how is it calculated?',
        localAnswer:
          '**Risk Score Framework (0–100 Scale):**\n\n' +
          '• **0 – 30 (GENUINE)**: Low risk. Specimen passes all cryptographic checksums, noise residual tests, and optical baselines.\n' +
          '• **31 – 65 (SUSPICIOUS)**: Moderate risk. Non-fatal anomalies detected (e.g. font baseline flutter, mild compression disparity). Secondary manual inspection required.\n' +
          '• **66 – 100 (FAKE)**: Critical risk. Fatal integrity violation (e.g. spliced photo border, failed MRZ checksum parity, deepfake portrait mismatch).\n\n' +
          'Formula combines **Tampering Severity (40%)**, **Face Biometric Disparity (30%)**, and **Validation Rule Errors (capped at 30%)**.',
      },
      {
        id: 'mrz-checksum-failed',
        label: 'What MRZ error means',
        query: 'What does MRZ checksum failed mean in plain language?',
        localAnswer:
          '**MRZ Checksum Parity Explained:**\n\n' +
          'ICAO 9303 documents include mathematical check digits derived from the document number, date of birth, and expiry using a repeating `7-3-1` weighting algorithm.\n\n' +
          '⚠️ **Failure Meaning**: The printed check digit does not match the computed value from the character string. This happens when text is altered using photo editing tools without recalculating the security checksum.',
      },
      {
        id: 'tampering-heatmap',
        label: 'Why heatmap flagged areas',
        query: 'Why did the tampering heatmap flag specific regions?',
        localAnswer:
          '**Tampering Heatmap Interpretation:**\n\n' +
          '• **Red / Orange Regions**: High Error Level Analysis (ELA) divergence indicating pasted elements saved at a different compression level than the substrate.\n' +
          '• **Sharp Intensity Discontinuities**: Artificial boundaries where a portrait photo was spliced over the background micro-pattern.\n' +
          '• **Uniform Green / Dark**: Authentic undisturbed substrate with uniform noise distribution.',
      },
      {
        id: 'verdict-next-steps',
        label: 'Next steps protocol',
        query: 'What are the required operational next steps for this verdict?',
        localAnswer:
          '**Officer Operational Protocol:**\n\n' +
          '1. **If FAKE**: Withhold document, place bearer in secondary queue, and escalate to Supervisor via the Alerts tab.\n' +
          '2. **If SUSPICIOUS**: Conduct tactile examination under UV light and verify bearer details against central registry.\n' +
          '3. **If GENUINE**: Confirm traveler identity and proceed with standard checkpoint clearance.',
      },
    ],
  },
  FACEMATCH: {
    badge: '📍 Face Biometrics',
    headline: 'Biometric Correlation & Liveness',
    quickPrompts: [
      {
        id: 'match-thresholds',
        label: 'Face match thresholds',
        query: 'What are the biometric face match thresholds?',
        localAnswer:
          '**Biometric Facial Match Thresholds:**\n\n' +
          '• **>= 75%**: Confirmed biometric match (`MATCH`).\n' +
          '• **50% – 74%**: Inconclusive similarity. Check for heavy eyeglasses, facial hair changes, or extreme aging.\n' +
          '• **< 50%**: Biometric mismatch. High probability of impostor / lookalike fraud.',
      },
      {
        id: 'webcam-troubleshoot',
        label: 'Webcam capture troubleshooting',
        query: 'How do I ensure a good live webcam capture?',
        localAnswer:
          '**Webcam Live Capture Tips:**\n\n' +
          '• Position traveler facing directly into the camera at eye level.\n' +
          '• Ensure uniform frontal illumination (avoid strong backlight from windows behind traveler).\n' +
          '• Traveler should keep a neutral facial expression with eyes open and forehead visible.',
      },
    ],
  },
  AUDIT: {
    badge: '📍 Audit Console',
    headline: 'Supervisor Review & Case Oversight',
    quickPrompts: [
      {
        id: 'escalate-case',
        label: 'How to escalate case',
        query: 'How does an officer escalate a case to supervisor review?',
        localAnswer:
          '**Case Escalation Workflow:**\n\n' +
          '1. When a specimen receives a `FAKE` or `SUSPICIOUS` verdict, the case is automatically added to the high-priority **Alerts** queue.\n' +
          '2. The Supervisor at Border HQ receives real-time alert notifications.\n' +
          '3. The Supervisor can open the **Audit Console** to review the full forensic report, inspect heatmaps, and log an official concurrence or disposition.',
      },
      {
        id: 'export-audit',
        label: 'Exporting audit reports',
        query: 'How can audit logs and case evidence be exported?',
        localAnswer:
          '**Audit Trail Export:**\n\n' +
          'In the Supervisor Console, tap **Export CSV** or **Export Full Dossier** to generate timestamped, cryptographically hashed case records for legal and law enforcement proceedings.',
      },
    ],
  },
  GENERAL: {
    badge: '📍 Vidyut AI Console',
    headline: 'MHA Screening Knowledge Base',
    quickPrompts: [
      {
        id: 'faq-overview',
        label: 'System overview',
        query: 'What forensic checks does the screening system perform?',
        localAnswer:
          '**Forensic Screening Capabilities:**\n\n' +
          '1. **Optical Character & MRZ Validation**: ICAO 9303 checksums, font baseline parity, glyph consistency.\n' +
          '2. **Digital Image Forensic Tampering**: Error Level Analysis (ELA), edge gradient continuity, copy-move detection.\n' +
          '3. **Biometric Face Match**: Deep facial embedding comparison between ID document portrait and live checkpoint camera.\n' +
          '4. **Composite Risk Engine**: Multi-factor scoring with automated hard gates for border security.',
      },
      {
        id: 'faq-escalation',
        label: 'Supervisor escalation',
        query: 'How do I escalate an issue to a supervisor?',
        localAnswer:
          'Flagged specimens automatically appear in the supervisor alerts stream. Officers can also navigate to the **Alerts** tab to inspect critical flags and record additional field notes.',
      },
      {
        id: 'faq-webcam',
        label: 'Webcam not working?',
        query: 'What should I do if the live camera is not opening?',
        localAnswer:
          '**Camera Troubleshooting:**\n\n' +
          '• Check browser permissions in the address bar (allow camera access for `localhost:5173`).\n' +
          '• Ensure no other application (e.g. Zoom, Teams) is currently locking the webcam device.\n' +
          '• Refresh the browser or reconnect the USB camera.',
      },
    ],
  },
}
