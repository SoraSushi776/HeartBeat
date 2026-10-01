import { logger } from './logger'
import { showNotification } from './notify'
import { translator } from './i18n'
import type { HeartbeatApi } from './api'
import type { Language } from './config/schema'

const POLL_MS = 8000

interface AdminMessage {
  id: number
  author?: string
  content?: string
}

function toMessages(value: unknown): AdminMessage[] {
  const items = Array.isArray(value)
    ? value
    : value && typeof value === 'object' && Array.isArray((value as { items?: unknown }).items)
      ? ((value as { items: unknown[] }).items as unknown[])
      : []
  return items.filter(
    (item): item is AdminMessage =>
      typeof item === 'object' && item !== null && typeof (item as AdminMessage).id === 'number'
  )
}

export class MessageNotifier {
  private timer: NodeJS.Timeout | null = null
  private seen = new Set<number>()
  private primed = false

  constructor(
    private api: () => HeartbeatApi,
    private language: () => Language
  ) {}

  start(): void {
    this.stop()
    this.timer = setInterval(() => {
      void this.poll()
    }, POLL_MS)
    logger.info('Message notifier started')
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
  }

  private async poll(): Promise<void> {
    try {
      const messages = toMessages(await this.api().listMessages(20, 0))
      if (!this.primed) {
        for (const message of messages) {
          this.seen.add(message.id)
        }
        this.primed = true
        logger.info(`Message notifier baseline: ${this.seen.size} ids`)
        return
      }
      const fresh = messages.filter((message) => !this.seen.has(message.id))
      for (const message of fresh) {
        this.seen.add(message.id)
      }
      if (fresh.length === 0) {
        return
      }
      const t = translator(this.language())
      const preview = fresh[0].content ? fresh[0].content.slice(0, 80) : t('notify.message.body')
      showNotification(t('notify.message.title'), fresh.length > 1 ? `${preview} (+${fresh.length - 1})` : preview)
      logger.info(`Notified ${fresh.length} new message(s)`)
    } catch (error) {
      logger.debug(`Message poll failed: ${String(error)}`)
    }
  }
}
