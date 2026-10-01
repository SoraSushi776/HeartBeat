import { CAPABILITY_BY_FLAG, emptyFlags, type Capability, type PrivacyFlags } from '../protocol'

export type PrivacyListener = (flags: PrivacyFlags) => void

export class PrivacyGate {
  private current: PrivacyFlags
  private listeners: PrivacyListener[] = []

  constructor(flags: PrivacyFlags = emptyFlags()) {
    this.current = { ...flags }
  }

  get flags(): PrivacyFlags {
    return { ...this.current }
  }

  allow(capability: Capability): boolean {
    return this.current[CAPABILITY_BY_FLAG[capability]]
  }

  update(flags: PrivacyFlags): void {
    this.current = { ...flags }
    for (const listener of [...this.listeners]) {
      listener(this.flags)
    }
  }

  subscribe(listener: PrivacyListener): () => void {
    this.listeners.push(listener)
    return () => {
      this.listeners = this.listeners.filter((item) => item !== listener)
    }
  }
}
