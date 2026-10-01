import { execFile } from 'node:child_process'

import { logger } from '../logger'

export interface CommandResult {
  ok: boolean
  stdout: string
  stderr: string
}

const MAX_BUFFER = 8 * 1024 * 1024

export function runCommand(command: string, args: string[], timeoutMs: number): Promise<CommandResult> {
  return new Promise((resolve) => {
    execFile(
      command,
      args,
      { timeout: timeoutMs, maxBuffer: MAX_BUFFER, encoding: 'utf8' },
      (error, stdout, stderr) => {
        if (error) {
          logger.debug(`${command} failed: ${String(error)}`)
          resolve({ ok: false, stdout: stdout ?? '', stderr: stderr ?? '' })
          return
        }
        resolve({ ok: true, stdout: stdout ?? '', stderr: stderr ?? '' })
      }
    )
  })
}

export function runCommandBuffer(
  command: string,
  args: string[],
  timeoutMs: number
): Promise<Buffer | null> {
  return new Promise((resolve) => {
    execFile(
      command,
      args,
      { timeout: timeoutMs, maxBuffer: MAX_BUFFER, encoding: 'buffer' },
      (error, stdout) => {
        if (error) {
          logger.debug(`${command} failed: ${String(error)}`)
          resolve(null)
          return
        }
        resolve(Buffer.isBuffer(stdout) ? stdout : Buffer.from(stdout ?? ''))
      }
    )
  })
}

export async function firstSuccessful(
  attempts: Array<() => Promise<Buffer | null>>
): Promise<Buffer | null> {
  for (const attempt of attempts) {
    const result = await attempt()
    if (result && result.length > 0) {
      return result
    }
  }
  return null
}
