import type { AppConfig, PrivacyConfig, Secrets } from './config/schema'
import { HeartbeatApi } from './api'
import { HeartbeatCollector, type CollectorHandlers, type PushRecord } from './collector'
import type { PrivacyFlags } from './protocol'

export function toPrivacyFlags(privacy: PrivacyConfig): PrivacyFlags {
  return {
    screenshot: privacy.collect_screenshot,
    media: privacy.collect_media,
    processes: privacy.collect_processes,
    system: privacy.collect_system_load
  }
}

export class CollectorHost {
  private api: HeartbeatApi
  private collector: HeartbeatCollector | null = null

  constructor(
    private clientVersion: string,
    private handlers: CollectorHandlers = {}
  ) {
    this.api = new HeartbeatApi({
      baseUrl: 'http://127.0.0.1:8000',
      apiKey: '',
      timeoutSeconds: 10,
      clientVersion,
      clientId: ''
    })
  }

  start(config: AppConfig, secrets: Secrets): void {
    this.api.update(this.apiSettings(config, secrets))
    this.collector = new HeartbeatCollector(this.api, this.runtimeConfig(config), this.handlers)
    this.collector.start()
  }

  apply(config: AppConfig, secrets: Secrets): void {
    this.api.update(this.apiSettings(config, secrets))
    if (!this.collector) {
      this.start(config, secrets)
      return
    }
    this.collector.applyConfig(this.runtimeConfig(config))
  }

  stop(): void {
    this.collector?.stop()
    this.collector = null
  }

  get history(): PushRecord[] {
    return this.collector?.pushHistory ?? []
  }

  get apiService(): HeartbeatApi {
    return this.api
  }

  get collectorInstance(): HeartbeatCollector | null {
    return this.collector
  }

  private apiSettings(config: AppConfig, secrets: Secrets) {
    return {
      baseUrl: config.server.base_url,
      apiKey: secrets.api_key,
      timeoutSeconds: config.server.timeout_seconds,
      clientVersion: this.clientVersion,
      clientId: config.client_id
    }
  }

  private runtimeConfig(config: AppConfig) {
    return {
      clientId: config.client_id,
      clientVersion: this.clientVersion,
      pushEnabled: config.push.enabled,
      intervalSeconds: config.push.interval_seconds,
      backoffSeconds: config.push.retry_backoff_seconds,
      privacy: toPrivacyFlags(config.privacy),
      collectors: {
        processWhitelist: config.process_whitelist,
        processCollectAll: config.process_collect_all,
        screenshot: {
          blurRadius: config.screenshot.blur_radius,
          scale: config.screenshot.scale,
          quality: config.screenshot.quality
        }
      }
    }
  }
}
