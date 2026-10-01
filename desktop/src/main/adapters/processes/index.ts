import si from 'systeminformation'

import { logger } from '../../logger'
import type { ProcessInfo } from '../../protocol'
import type { PrivacyGate } from '../privacy'
import { ProcessFilter, aggregate, aggregateKey, type ProcessDescriptor } from './filter'

const ZOMBIE_STATE = 'zombie'

interface RawProcess {
  name?: string
  path?: string
  command?: string
  state?: string
}

function describe(item: RawProcess): ProcessDescriptor {
  const command = item.command ?? ''
  const cmdline0 = command ? (command.split(' ')[0] ?? '') : ''
  return {
    name: (item.name ?? '').trim(),
    exe: item.path ? item.path : null,
    cmdline0: cmdline0 || null
  }
}

export class SystemInformationProcessAdapter {
  constructor(private filter: ProcessFilter = new ProcessFilter([], undefined, true)) {}

  updateFilter(filter: ProcessFilter): void {
    this.filter = filter
  }

  async collect(gate: PrivacyGate): Promise<ProcessInfo[] | null> {
    if (!gate.allow('processes')) {
      return null
    }
    if (!this.filter.enabled) {
      return []
    }
    const response = await si.processes()
    const matched: string[] = []
    for (const item of response.list as RawProcess[]) {
      const descriptor = describe(item)
      if (!descriptor.name) {
        continue
      }
      if ((item.state ?? '').toLowerCase() === ZOMBIE_STATE) {
        continue
      }
      if (this.filter.matches(descriptor)) {
        matched.push(aggregateKey(descriptor))
      }
    }
    logger.debug(`Processes matched: ${matched.length} of ${response.list.length}`)
    return aggregate(matched)
  }
}
