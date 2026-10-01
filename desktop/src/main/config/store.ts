import { randomBytes } from 'node:crypto'
import { chmodSync, mkdirSync, renameSync, writeFileSync } from 'node:fs'
import { dirname } from 'node:path'

import { logger } from '../logger'
import { configDir, configPath, secretsPath } from './paths'
import { readJsonFile, toRecord } from './read'
import {
  appConfigSchema,
  defaultSecrets,
  secretsSchema,
  type AppConfig,
  type Secrets
} from './schema'

export type ConfigListener = (config: AppConfig) => void
export type SecretsListener = (secrets: Secrets) => void

function writeAtomic(path: string, payload: string, mode?: number): void {
  mkdirSync(dirname(path), { recursive: true })
  const temporary = `${path}.tmp`
  writeFileSync(temporary, payload, mode === undefined ? undefined : { mode })
  if (mode !== undefined) {
    chmodSync(temporary, mode)
  }
  renameSync(temporary, path)
}

export class AppConfigStore {
  private config: AppConfig = appConfigSchema.parse({})
  private configListeners: ConfigListener[] = []

  load(): AppConfig {
    const loaded = appConfigSchema.parse(readJsonFile(configPath()))
    if (!loaded.client_id) {
      loaded.client_id = randomBytes(6).toString('hex')
    }
    this.config = loaded
    this.save()
    logger.info(`Config loaded from ${configDir()}, client_id=${this.config.client_id}`)
    return this.config
  }

  get(): AppConfig {
    return this.config
  }

  replace(next: AppConfig): AppConfig {
    this.config = appConfigSchema.parse(next)
    this.save()
    for (const listener of [...this.configListeners]) {
      listener(this.config)
    }
    return this.config
  }

  save(): void {
    writeAtomic(configPath(), `${JSON.stringify(this.config, null, 2)}\n`)
  }

  subscribe(listener: ConfigListener): () => void {
    this.configListeners.push(listener)
    return () => {
      this.configListeners = this.configListeners.filter((item) => item !== listener)
    }
  }
}

export class SecretStore {
  private secrets: Secrets = defaultSecrets()
  private listeners: SecretsListener[] = []

  load(): Secrets {
    this.secrets = secretsSchema.parse(toRecord(readJsonFile(secretsPath())))
    logger.info(`Secrets loaded from ${secretsPath()}`)
    return this.secrets
  }

  get(): Secrets {
    return this.secrets
  }

  replace(next: Secrets): Secrets {
    this.secrets = secretsSchema.parse(next)
    writeAtomic(secretsPath(), `${JSON.stringify(this.secrets, null, 2)}\n`, 0o600)
    for (const listener of [...this.listeners]) {
      listener(this.secrets)
    }
    return this.secrets
  }

  subscribe(listener: SecretsListener): () => void {
    this.listeners.push(listener)
    return () => {
      this.listeners = this.listeners.filter((item) => item !== listener)
    }
  }
}

export const appConfigStore = new AppConfigStore()
export const secretStore = new SecretStore()
