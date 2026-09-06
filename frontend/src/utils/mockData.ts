import type { StepperStage, DocumentFieldMarker } from '../types'

// ── UI stage configuration (used by stepper and forensic overlay) ──

export const STEPPER_STAGES: StepperStage[] = [
  {
    id: 'extracting',
    label: 'Extracting text',
    description: 'Parsing legal name, dates, and document identifier codes',
  },
  {
    id: 'validation',
    label: 'Validating format',
    description: 'Verifying ICAO MRZ checksum, expiry date, and watchlist blacklist',
  },
  {
    id: 'tampering',
    label: 'Checking tampering',
    description: 'Analyzing compression ELA gradients and copy-move keypoint patches',
  },
  {
    id: 'matching_face',
    label: 'Matching face',
    description: 'Comparing document photo with live 512-d ArcFace biometric embedding',
  },
  {
    id: 'finalizing',
    label: 'Verdict',
    description: 'Computing risk score and applying forensic examiner verdict seal',
  },
]

export const DOCUMENT_FIELD_MARKERS: DocumentFieldMarker[] = [
  {
    id: 'marker-photo',
    field: 'photo',
    label: 'EXHIBIT_PHOTO',
    value: 'Photo Detected',
    confidence: 97.4,
    box: { top: '23%', left: '5%', width: '22%', height: '46%' },
  },
  {
    id: 'marker-name',
    field: 'name',
    label: 'LEGAL_NAME',
    value: 'NAME_BLOCK',
    confidence: 99.4,
    box: { top: '24%', left: '30%', width: '45%', height: '12%' },
  },
  {
    id: 'marker-id',
    field: 'id_number',
    label: 'IDENTIFIER',
    value: 'ID_DIGITS',
    confidence: 99.1,
    box: { top: '38%', left: '30%', width: '42%', height: '11%' },
  },
  {
    id: 'marker-dob',
    field: 'dob',
    label: 'BIRTH_DATE',
    value: 'DOB_STAMP',
    confidence: 98.7,
    box: { top: '50%', left: '30%', width: '25%', height: '11%' },
  },
  {
    id: 'marker-address',
    field: 'address',
    label: 'RESIDENCE',
    value: 'ADDR_BLOCK',
    confidence: 97.2,
    box: { top: '62%', left: '30%', width: '58%', height: '11%' },
  },
  {
    id: 'marker-mrz',
    field: 'mrz',
    label: 'MRZ_CHECKSUM',
    value: 'ICAO_LINE_2',
    confidence: 99.8,
    box: { top: '76%', left: '5%', width: '90%', height: '16%' },
  },
]
