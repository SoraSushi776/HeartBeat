import { format } from 'node:util'

const PREFIX = '[heartbeat]'

function write(stream: NodeJS.WriteStream, level: string, args: unknown[]): void {
  stream.write(`${PREFIX} ${level} ${format(...args)}\n`)
}

export const logger = {
  debug: (...args: unknown[]): void => write(process.stdout, 'DEBUG', args),
  info: (...args: unknown[]): void => write(process.stdout, 'INFO ', args),
  warn: (...args: unknown[]): void => write(process.stderr, 'WARN ', args),
  error: (...args: unknown[]): void => write(process.stderr, 'ERROR', args)
}
