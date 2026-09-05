// Tactile Archival Web Audio API Sound Effects

class SoundFX {
  private ctx: AudioContext | null = null
  public enabled: boolean = true

  private getContext(): AudioContext | null {
    if (!this.ctx && typeof window !== 'undefined') {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      if (AudioCtx) {
        this.ctx = new AudioCtx()
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {})
    }
    return this.ctx
  }

  // Tactile rubber stamp landing thud
  stampImpact(pitch = 120) {
    if (!this.enabled) return
    const ctx = this.getContext()
    if (!ctx) return

    try {
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'triangle'
      osc.frequency.setValueAtTime(pitch, now)
      osc.frequency.exponentialRampToValueAtTime(45, now + 0.12)

      gain.gain.setValueAtTime(0.08, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(now)
      osc.stop(now + 0.15)
    } catch {
      // Audio playback failed
    }
  }

  // Camera shutter click (Webcam capture)
  cameraShutter() {
    if (!this.enabled) return
    const ctx = this.getContext()
    if (!ctx) return

    try {
      const now = ctx.currentTime
      // Click 1
      const osc1 = ctx.createOscillator()
      const gain1 = ctx.createGain()
      osc1.type = 'sine'
      osc1.frequency.setValueAtTime(1200, now)
      osc1.frequency.exponentialRampToValueAtTime(400, now + 0.03)
      gain1.gain.setValueAtTime(0.06, now)
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.04)
      osc1.connect(gain1)
      gain1.connect(ctx.destination)
      osc1.start(now)
      osc1.stop(now + 0.05)

      // Click 2 (shutter release)
      const osc2 = ctx.createOscillator()
      const gain2 = ctx.createGain()
      osc2.type = 'triangle'
      osc2.frequency.setValueAtTime(800, now + 0.06)
      osc2.frequency.exponentialRampToValueAtTime(250, now + 0.1)
      gain2.gain.setValueAtTime(0.05, now + 0.06)
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.11)
      osc2.connect(gain2)
      gain2.connect(ctx.destination)
      osc2.start(now + 0.06)
      osc2.stop(now + 0.12)
    } catch {
      // Ignore
    }
  }

  // Paper slide / tab select
  paperSlide() {
    if (!this.enabled) return
    const ctx = this.getContext()
    if (!ctx) return

    try {
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sine'
      osc.frequency.setValueAtTime(320, now)
      osc.frequency.exponentialRampToValueAtTime(220, now + 0.06)

      gain.gain.setValueAtTime(0.02, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(now)
      osc.stop(now + 0.07)
    } catch {
      // Ignore
    }
  }

  // Field ink stamp land (during verification sequence)
  fieldInkLand() {
    if (!this.enabled) return
    const ctx = this.getContext()
    if (!ctx) return

    try {
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sine'
      osc.frequency.setValueAtTime(260, now)
      osc.frequency.exponentialRampToValueAtTime(140, now + 0.05)

      gain.gain.setValueAtTime(0.035, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(now)
      osc.stop(now + 0.07)
    } catch {
      // Ignore
    }
  }

  // Badge / checkpoint alert unlock chime
  badgeUnlock() {
    if (!this.enabled) return
    const ctx = this.getContext()
    if (!ctx) return

    try {
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sine'
      osc.frequency.setValueAtTime(520, now)
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.15)

      gain.gain.setValueAtTime(0.05, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(now)
      osc.stop(now + 0.22)
    } catch {
      // Ignore
    }
  }

  // Tamper / critical alert alarm tone
  tamperAlert() {
    if (!this.enabled) return
    const ctx = this.getContext()
    if (!ctx) return

    try {
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sawtooth'
      osc.frequency.setValueAtTime(440, now)
      osc.frequency.setValueAtTime(330, now + 0.08)

      gain.gain.setValueAtTime(0.06, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start(now)
      osc.stop(now + 0.18)
    } catch {
      // Ignore
    }
  }
}

export const soundFX = new SoundFX()
