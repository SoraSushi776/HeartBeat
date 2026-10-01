import { cpus, loadavg, totalmem } from 'node:os'
import si from 'systeminformation'

import { currentPlatform } from '../platform'
import type { PrivacyGate } from '../privacy'
import type { SystemInfo } from '../../protocol'

interface CpuSample {
  idle: number
  total: number
}

function sampleCpu(): CpuSample {
  return cpus().reduce<CpuSample>(
    (accumulator, cpu) => {
      const times = cpu.times
      const total = times.user + times.nice + times.sys + times.idle + times.irq
      return { idle: accumulator.idle + times.idle, total: accumulator.total + total }
    },
    { idle: 0, total: 0 }
  )
}

export function cpuPercent(previous: CpuSample | null, current: CpuSample): number {
  if (!previous) {
    return 0
  }
  const idleDelta = current.idle - previous.idle
  const totalDelta = current.total - previous.total
  if (totalDelta <= 0) {
    return 0
  }
  return Math.min(Math.max((1 - idleDelta / totalDelta) * 100, 0), 100)
}

export function loadAverage(platform: ReturnType<typeof currentPlatform>): number[] {
  if (platform === 'windows') {
    return []
  }
  return loadavg().map((value) => Math.round(value * 100) / 100)
}

export function memoryPercent(total: number, available: number): number {
  if (total <= 0) {
    return 0
  }
  return Math.min(Math.max(((total - available) / total) * 100, 0), 100)
}

export class SystemLoadAdapter {
  private previous: CpuSample | null = null

  async collect(gate: PrivacyGate): Promise<SystemInfo | null> {
    if (!gate.allow('system')) {
      return null
    }
    const current = sampleCpu()
    const percent = cpuPercent(this.previous, current)
    this.previous = current
    const memory = await si.mem()
    const total = memory.total > 0 ? memory.total : totalmem()
    const available = memory.available > 0 ? memory.available : memory.free
    return {
      cpu_percent: Math.round(percent * 10) / 10,
      memory_percent: Math.round(memoryPercent(total, available) * 10) / 10,
      load_avg: loadAverage(currentPlatform())
    }
  }
}
