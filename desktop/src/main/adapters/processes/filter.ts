import { basename } from 'node:path'

import type { ProcessInfo } from '../../protocol'

export const DEFAULT_EXCLUDE_PATTERNS: string[] = [
  '.* Helper.*',
  '.*Helper$',
  '.* Renderer.*',
  '.*Worker.*',
  '.*Service.*',
  '.*Daemon$',
  '.*Server$',
  '.*Handler$',
  '.*Compiler$',
  '.*Agent.*',
  '.*XPC.*',
  '.*Plugin.*',
  '.*Extension.*',
  '.*Launcher$',
  '.*Monitor$',
  '.*Ingestor$',
  '.*Intents$',
  'crashpad_handler',
  '.*com\\.apple\\..*',
  'kernel_task',
  'launchd',
  'loginwindow',
  'WindowServer',
  'distnoted',
  'cfprefsd',
  'opendirectoryd',
  'secd',
  'sharingd',
  'trustd',
  'nsurlsessiond',
  'nsurlstoraged',
  'hidd',
  'bluetoothd',
  'coreaudiod',
  'powerd',
  'syslogd',
  'UserEventAgent',
  'fseventsd',
  'mds_stores',
  'mdworker.*',
  'spotlight.*',
  'TimeMachine.*',
  'backupd.*'
]

const USER_APP_EXE_HINTS: string[] = [
  '/Applications/',
  '.app/Contents/MacOS/',
  '\\AppData\\Local\\',
  'C:\\Program Files',
  '/opt/homebrew/',
  '/usr/local/'
]

const SYSTEM_PATH_HINTS: string[] = [
  '/System/',
  '/usr/libexec/',
  '/usr/sbin/',
  '/usr/bin/',
  '/Library/Apple/',
  '/private/',
  '/sbin/',
  '\\Windows\\System32\\',
  '\\Windows\\SysWOW64\\',
  '\\Windows\\WinSxS\\',
  'C:\\Windows\\',
  '\\Program Files\\Windows Defender\\',
  '\\Program Files\\Microsoft\\',
  '\\Program Files (x86)\\Microsoft\\'
]

export interface ProcessDescriptor {
  name: string
  exe?: string | null
  cmdline0?: string | null
}

export function candidateNames(descriptor: ProcessDescriptor): string[] {
  const values = [descriptor.name]
  if (descriptor.exe) {
    values.push(basename(descriptor.exe))
  }
  if (descriptor.cmdline0) {
    values.push(basename(descriptor.cmdline0))
  }
  return [...new Set(values)]
}

export function aggregateKey(descriptor: ProcessDescriptor): string {
  return descriptor.exe ? basename(descriptor.exe) : descriptor.name
}

export function aggregate(names: string[]): ProcessInfo[] {
  const counter = new Map<string, number>()
  for (const name of names) {
    counter.set(name, (counter.get(name) ?? 0) + 1)
  }
  return [...counter.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((left, right) => (left.name < right.name ? -1 : left.name > right.name ? 1 : 0))
}

function looksLikeUserApp(descriptor: ProcessDescriptor): boolean {
  const paths = [descriptor.exe, descriptor.cmdline0].filter((item): item is string => Boolean(item))
  if (paths.some((path) => SYSTEM_PATH_HINTS.some((hint) => path.startsWith(hint) || path.includes(hint)))) {
    return false
  }
  const blob = [descriptor.name, descriptor.exe, descriptor.cmdline0].filter(Boolean).join(' ')
  if (USER_APP_EXE_HINTS.some((hint) => blob.includes(hint))) {
    return true
  }
  if (paths.length > 0) {
    return false
  }
  const clean = descriptor.name.trim()
  return clean.length > 0 && clean.length <= 64 && /^[A-Z]/.test(clean) && clean !== clean.toLowerCase()
}

export class ProcessFilter {
  private allow: RegExp[]
  private exclude: RegExp[]
  private collectAll: boolean

  constructor(patterns: string[] = [], exclude?: string[], collectAll = false) {
    this.allow = compileAll(patterns)
    this.exclude = compileAll(exclude ?? DEFAULT_EXCLUDE_PATTERNS)
    this.collectAll = collectAll
  }

  get enabled(): boolean {
    return this.allow.length > 0 || this.collectAll
  }

  matches(descriptor: ProcessDescriptor): boolean {
    const candidates = candidateNames(descriptor)
    if (candidates.some((item) => this.exclude.some((pattern) => fullMatch(pattern, item)))) {
      return false
    }
    if (this.allow.length > 0) {
      return candidates.some((item) => this.allow.some((pattern) => fullMatch(pattern, item)))
    }
    return this.collectAll && looksLikeUserApp(descriptor)
  }
}

function compileAll(patterns: string[]): RegExp[] {
  const compiled: RegExp[] = []
  for (const pattern of patterns) {
    try {
      compiled.push(new RegExp(`^(?:${pattern})$`))
    } catch {
      continue
    }
  }
  return compiled
}

function fullMatch(pattern: RegExp, value: string): boolean {
  pattern.lastIndex = 0
  return pattern.test(value)
}
