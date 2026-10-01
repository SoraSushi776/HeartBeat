import { existsSync } from 'node:fs'

import { configPath, secretsPath } from '../src/main/config/paths'
import { readJsonFile } from '../src/main/config/read'
import {
  DEFAULT_BACKOFF_SECONDS,
  DEFAULT_PUSH,
  DEFAULT_SCREENSHOT,
  DEFAULT_SITE,
  appConfigSchema,
  secretsSchema
} from '../src/main/config/schema'

let failures = 0

function group(name: string): void {
  process.stdout.write(`\n${name}\n`)
}

function check(name: string, condition: boolean, detail = ''): void {
  const mark = condition ? 'ok  ' : 'FAIL'
  process.stdout.write(`  ${mark} ${name}${detail ? ` — ${detail}` : ''}\n`)
  if (!condition) {
    failures += 1
  }
}

function parse(input: unknown) {
  return appConfigSchema.parse(input)
}

group('config / defaults')
{
  const config = parse({})
  check('client_id empty before store fills it', config.client_id === '')
  check('setup_completed defaults false', config.setup_completed === false)
  check('interval defaults 60', config.push.interval_seconds === 60)
  check('backoff table defaults', config.push.retry_backoff_seconds.join(',') === DEFAULT_BACKOFF_SECONDS.join(','))
  check('process_collect_all defaults true', config.process_collect_all === true)
  check('ui.language defaults zh-CN', config.ui.language === 'zh-CN')
  check('site title defaults', config.site.title === DEFAULT_SITE.title)
  check('site tags defaults empty', config.site.tags.length === 0)
}

group('config / bad data falls back')
{
  const config = parse({
    server: 'not-an-object',
    push: { enabled: 'yes', interval_seconds: 'abc', retry_backoff_seconds: 'nope' },
    privacy: { collect_media: 'true' },
    screenshot: { blur_radius: null },
    process_whitelist: [1, 'Safari', null, 'Code'],
    ui: { language: 'fr-FR' },
    site: { tags: ['a', 3, 'b'], show_heatmap: 'true' }
  })
  check('server falls back to default', config.server.base_url === 'http://127.0.0.1:8000')
  check('push.enabled falls back true', config.push.enabled === true)
  check('interval falls back 60', config.push.interval_seconds === 60)
  check('backoff falls back to table', config.push.retry_backoff_seconds.join(',') === DEFAULT_BACKOFF_SECONDS.join(','))
  check('privacy.media falls back true', config.privacy.collect_media === true)
  check('blur falls back 10', config.screenshot.blur_radius === DEFAULT_SCREENSHOT.blur_radius)
  check('whitelist keeps strings only', config.process_whitelist.join(',') === 'Safari,Code')
  check('unknown language falls back', config.ui.language === 'zh-CN')
  check('site tags keep strings only', config.site.tags.join(',') === 'a,b')
  check('show_heatmap falls back true', config.site.show_heatmap === true)
}

group('config / ranges clamp')
{
  const config = parse({
    push: { interval_seconds: 100000 },
    screenshot: { blur_radius: -5, scale: 5, quality: 0 }
  })
  check('interval clamps to 3600', config.push.interval_seconds === 3600, String(config.push.interval_seconds))
  check('blur clamps to 0', config.screenshot.blur_radius === 0, String(config.screenshot.blur_radius))
  check('scale clamps to 1', config.screenshot.scale === 1, String(config.screenshot.scale))
  check('quality clamps to 1', config.screenshot.quality === 1, String(config.screenshot.quality))

  const low = parse({ push: { interval_seconds: 1 } })
  check('interval clamps up to 5', low.push.interval_seconds === 5, String(low.push.interval_seconds))
}

group('config / backoff table shape')
{
  const custom = parse({ push: { retry_backoff_seconds: [0, 2, 4] } })
  check('custom table survives', custom.push.retry_backoff_seconds.join(',') === '0,2,4')
  const mixed = parse({ push: { retry_backoff_seconds: [1, 'x', -3] } })
  check('mixed table keeps numbers and clamps', mixed.push.retry_backoff_seconds.join(',') === '1,0')
  check('max_queue_size default', parse({}).push.max_queue_size === DEFAULT_PUSH.max_queue_size)
}

group('secrets')
{
  const empty = secretsSchema.parse({})
  check('api_key defaults empty', empty.api_key === '')
  check('github_token defaults empty', empty.github_token === '')
  const partial = secretsSchema.parse({ api_key: 'k', github_login: 42 })
  check('api_key kept', partial.api_key === 'k')
  check('github_login falls back empty', partial.github_login === '')
}

if (process.argv.includes('--live')) {
  group('live config (read only)')
  const configFile = configPath()
  const secretsFile = secretsPath()
  check('client.json exists', existsSync(configFile), configFile)
  if (existsSync(configFile)) {
    const live = appConfigSchema.parse(readJsonFile(configFile))
    check('client_id present', live.client_id.length > 0, live.client_id)
    check('setup_completed', live.setup_completed)
    check('base_url', live.server.base_url.length > 0, live.server.base_url)
    check('interval in range', live.push.interval_seconds >= 5 && live.push.interval_seconds <= 3600, String(live.push.interval_seconds))
    process.stdout.write(`  info whitelist=${live.process_whitelist.length} collect_all=${live.process_collect_all} language=${live.ui.language}\n`)
  }
  check('client.secrets.json exists', existsSync(secretsFile), secretsFile)
  if (existsSync(secretsFile)) {
    const live = secretsSchema.parse(readJsonFile(secretsFile))
    check('api_key present', live.api_key.length > 0, `length=${live.api_key.length}`)
    check('github_token present', live.github_token.length > 0, `length=${live.github_token.length}`)
  }
}

process.stdout.write(`\n${failures === 0 ? 'smoke: all checks passed' : `smoke: ${failures} failing checks`}\n`)
process.exitCode = failures === 0 ? 0 : 1
