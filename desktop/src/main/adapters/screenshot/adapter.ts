import { logger } from '../../logger'
import type { PrivacyGate } from '../privacy'
import type { ScreenshotResult } from '../../protocol'
import { currentPlatform } from '../platform'
import { captureScreen, encodeScreenshot, type ScreenshotEncodeOptions } from './index'

export type { ScreenshotEncodeOptions }

export class ScreenshotAdapter {
  constructor(private options: ScreenshotEncodeOptions) {}

  updateOptions(options: ScreenshotEncodeOptions): void {
    this.options = options
  }

  async collect(gate: PrivacyGate): Promise<ScreenshotResult | null> {
    if (!gate.allow('screenshot')) {
      return null
    }
    const raw = await captureScreen(currentPlatform())
    if (!raw || raw.length === 0) {
      logger.debug('Screenshot capture returned nothing')
      return null
    }
    return encodeScreenshot(raw, this.options)
  }
}
