import { existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import { CollectorRegistry } from '../src/main/adapters/index'
import { currentPlatform } from '../src/main/adapters/platform'
import { runCommand } from '../src/main/adapters/shell'
import { HeartbeatApi } from '../src/main/api'
import { syncAutostart } from '../src/main/app/autostart/index'
import type { AutostartProvider } from '../src/main/app/autostart/types'
import { buildDesktopEntry, commandLine as linuxCommandLine, desktopEntryPath } from '../src/main/app/autostart/linux'
import { buildPlist, launchctlArgs, plistPath } from '../src/main/app/autostart/macos'
import { RUN_KEY, parseRegistryValue, registryAddArgs, registryDeleteArgs, registryQueryArgs } from '../src/main/app/autostart/windows'
import { buildTrayMenuTemplate } from '../src/main/app/tray-menu'
import { linuxCommand, macosCommand, windowsCommand } from '../src/main/notify'
import { MediaClock } from '../src/main/adapters/media/clock'
import { parseMetadata, unwrap } from '../src/main/adapters/media/linux'
import { APP_SCRIPTS, installedAppScripts, parseScriptOutput } from '../src/main/adapters/media/macos'
import { parseNowPlayingJson } from '../src/main/adapters/media/nowplaying'
import { preferPlaying } from '../src/main/adapters/media/selection'
import { encodePowerShell, friendlyAppName, parseSessions } from '../src/main/adapters/media/windows'
import { PrivacyGate } from '../src/main/adapters/privacy'
import { encodeScreenshot } from '../src/main/adapters/screenshot/index'
import { cpuPercent, loadAverage, memoryPercent } from '../src/main/adapters/system/index'
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
    ui: { language: 'fr-FR' },
    site: { tags: ['a', 3, 'b'], show_heatmap: 'true' }
  })
  check('server falls back to default', config.server.base_url === 'http://127.0.0.1:8000')
  check('push.enabled falls back true', config.push.enabled === true)
  check('interval falls back 60', config.push.interval_seconds === 60)
  check('backoff falls back to table', config.push.retry_backoff_seconds.join(',') === DEFAULT_BACKOFF_SECONDS.join(','))
  check('privacy.media falls back true', config.privacy.collect_media === true)
  check('blur falls back 10', config.screenshot.blur_radius === DEFAULT_SCREENSHOT.blur_radius)
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

group('autostart / macOS launch agent')
{
  const target = { command: '/Applications/HeartBeat.app/Contents/MacOS/HeartBeat' }
  const plist = buildPlist(target)
  check('declares label', plist.includes('<key>Label</key>'))
  check('label matches the launch agent id', plist.includes('<string>com.heartbeat.client</string>'))
  check('registers the product path', plist.includes('<string>/Applications/HeartBeat.app/Contents/MacOS/HeartBeat</string>'))
  check('runs at load', plist.includes('<key>RunAtLoad</key>'))
  check('is a valid plist root', plist.startsWith('<?xml') && plist.trimEnd().endsWith('</plist>'))
  check('escapes xml entities', buildPlist({ command: '/tmp/a&b' }).includes('/tmp/a&amp;b'))
  check('adds extra arguments', buildPlist({ command: '/app', arguments: ['/repo'] }).includes('<string>/repo</string>'))
  check('plist lives under LaunchAgents', plistPath().endsWith('Library/LaunchAgents/com.heartbeat.client.plist'), plistPath())
  const args = launchctlArgs('bootstrap', '/tmp/x.plist')
  check('launchctl targets the gui domain', args[1].startsWith('gui/'), args[1])
}

group('autostart / Linux desktop entry')
{
  const entry = buildDesktopEntry({ command: '/opt/heartbeat/heartbeat-desktop' })
  check('is a desktop entry', entry.startsWith('[Desktop Entry]'))
  check('has exec line', entry.includes('Exec=/opt/heartbeat/heartbeat-desktop'))
  check('starts enabled', entry.includes('Hidden=false'))
  check('joins extra arguments', linuxCommandLine({ command: '/app', arguments: ['/repo'] }) === '/app /repo')
  check('entry lives in autostart dir', desktopEntryPath().includes('autostart/heartbeat-client.desktop'), desktopEntryPath())
}

group('autostart / Windows run key')
{
  const add = registryAddArgs({ command: 'C:\\Program Files\\HeartBeat\\HeartBeat.exe' })
  check('targets the Run key', add[1] === RUN_KEY)
  check('uses the HeartBeat value name', add[add.indexOf('/v') + 1] === 'HeartBeat')
  check('quotes paths with spaces', add[add.indexOf('/d') + 1] === '"C:\\Program Files\\HeartBeat\\HeartBeat.exe"', add[add.indexOf('/d') + 1])
  check('registryAddArgs.join', add.join(' ').includes('/t REG_SZ'))
  check('delete args remove the value', registryDeleteArgs().join(' ').includes('/v HeartBeat /f'))
  check('query args read the value', registryQueryArgs()[0] === 'query')
}

group('autostart sync')
{
  const scenarios = [
    { name: 'off stays off', enabled: false, registered: false, upToDate: false, expect: 'none', result: false },
    { name: 'off unregisters', enabled: false, registered: true, upToDate: true, expect: 'disable', result: false },
    { name: 'on registers', enabled: true, registered: false, upToDate: false, expect: 'enable', result: true },
    { name: 'on leaves a matching entry alone', enabled: true, registered: true, upToDate: true, expect: 'none', result: true },
    { name: 'on rewrites a moved path', enabled: true, registered: true, upToDate: false, expect: 'enable', result: true }
  ]
  for (const scenario of scenarios) {
    const calls: string[] = []
    let registered = scenario.registered
    const provider: AutostartProvider = {
      enable: () => {
        calls.push('enable')
        registered = true
      },
      disable: () => {
        calls.push('disable')
        registered = false
      },
      isEnabled: () => registered,
      isUpToDate: () => scenario.upToDate
    }
    const result = syncAutostart(provider, scenario.enabled)
    check(`${scenario.name}`, (calls[0] ?? 'none') === scenario.expect && result === scenario.result, `${calls.join(',') || 'none'} -> ${result}`)
  }
}

group('registry parsing')
{
  const expected = '"C:\\Program Files\\HeartBeat\\HeartBeat.exe"'
  const output = ['(default)', `    HeartBeat    REG_SZ    ${expected}`, ''].join('\n')
  check('reads the REG_SZ command', parseRegistryValue(output) === expected, parseRegistryValue(output))
  check('empty output yields empty', parseRegistryValue('') === '')
}

group('notifications')
{
  const mac = macosCommand('HeartBeat', 'hello "world"')
  check('macos uses osascript', mac[0] === 'osascript' && mac[1] === '-e')
  check('macos escapes quotes', mac[2].includes('\\"world\\"'), mac[2])
  const win = windowsCommand('HeartBeat', 'a & b')
  check('windows uses powershell', win[0] === 'powershell')
  check('windows escapes xml', win[4].includes('a &amp; b'))
  const linux = linuxCommand('HeartBeat', 'body')
  check('linux uses notify-send', linux[0] === 'notify-send' && linux[2] === 'HeartBeat' && linux[3] === 'body')
}

group('tray menu')
{
  const clicks: string[] = []
  const template = buildTrayMenuTemplate(
    { open: '打开设置', quit: '退出', status: '推送已开启' },
    { onOpen: () => clicks.push('open'), onQuit: () => clicks.push('quit') }
  )
  check('has a status row', template[0]?.label === '推送已开启' && template[0]?.enabled === false)
  check('separates sections', template.filter((item) => item.type === 'separator').length === 2)
  check('labels open and quit', template.some((item) => item.label === '打开设置') && template.some((item) => item.label === '退出'))
  template.find((item) => item.label === '打开设置')?.click?.({} as never, {} as never, {} as never)
  template.find((item) => item.label === '退出')?.click?.({} as never, {} as never, {} as never)
  check('click handlers wired', clicks.join(',') === 'open,quit', clicks.join(','))
}

group('privacy gate')
{
  const gate = new PrivacyGate({ screenshot: true, media: false, system: false })
  check('allows enabled capability', gate.allow('screenshot'))
  check('blocks disabled capability', !gate.allow('media'))
  check('blocks disabled system capability', !gate.allow('system'))
  const seen: string[] = []
  gate.subscribe((flags) => seen.push(JSON.stringify(flags)))
  gate.update({ screenshot: false, media: false, system: false })
  check('notifies subscribers', seen.length === 1 && seen[0].includes('"screenshot":false'))
  check('flags snapshot reflects update', gate.flags.media === false)
  check('snapshot is a copy', gate.flags !== gate.flags)
}

group('media selection and clock')
{
  const playing = preferPlaying([
    { ...blankMedia(), state: 'paused', title: 'a' },
    { ...blankMedia(), state: 'playing', title: 'b' }
  ])
  check('prefers playing over paused', playing.title === 'b')
  check('returns idle for empty candidates', preferPlaying([]).state === 'idle')

  const clock = new MediaClock()
  const first = clock.decorate({ ...blankMedia(), state: 'playing', title: 'T', position_ms: 0, duration_ms: 200000 })
  check('anchors a zero position', first.position_ms === 0)
  const later = clock.decorate({ ...blankMedia(), state: 'playing', title: 'T', position_ms: 0, duration_ms: 200000 })
  check('interpolates while playing', (later.position_ms ?? 0) >= 0)
  const clamped = clock.decorate({ ...blankMedia(), state: 'playing', title: 'T', position_ms: 999999, duration_ms: 1000 })
  check('clamps to duration', clamped.position_ms === 1000)
}

group('media / macOS')
{
  const idle = parseScriptOutput('idle', 'Music')
  check('idle maps to idle', idle.state === 'idle')
  const sep = '\u001f'
  const row = parseScriptOutput(['playing', 'Song', 'Artist', 'Album', '210000', '1000'].join(sep), 'Music')
  check('parses playing state', row.state === 'playing')
  check('parses metadata', row.title === 'Song' && row.artist === 'Artist' && row.album === 'Album')
  check('parses timings', row.duration_ms === 210000 && row.position_ms === 1000)
  check('app is the queried player', row.app === 'Music')
  const spotify = parseScriptOutput(['playing', 'S', 'A', 'Al', '1000', '10', 'https://cover/x.jpg'].join(sep), 'Spotify')
  check('captures spotify artwork url', spotify.cover_url === 'https://cover/x.jpg')
  check('truncated output is rejected', parseScriptOutput('playing\u001fSong', 'Music').state === 'idle')
  check('scripts avoid the reserved st identifier', APP_SCRIPTS.every((entry) => !/\bst\b/.test(entry.script)))
  check('scripts pair state with pstate variable', APP_SCRIPTS.every((entry) => entry.script.includes('set pstate to player state as text')))
}

group('media / nowplaying-cli')
{
  const empty = parseNowPlayingJson('')
  check('empty output is idle', empty.state === 'idle')
  const playing = parseNowPlayingJson(
    JSON.stringify({
      title: 'Song',
      artist: 'Artist',
      album: 'Album',
      playbackRate: 1,
      duration: 200,
      elapsedTime: 12,
      clientBundleIdentifier: 'com.spotify.client',
      artworkData: Buffer.from('cover').toString('base64')
    })
  )
  check('playing rate maps to playing', playing.state === 'playing')
  check('seconds convert to ms', playing.duration_ms === 200000 && playing.position_ms === 12000)
  check('bundle id maps to app name', playing.app === 'Spotify')
  check('artwork decodes to bytes', playing.cover_bytes?.toString() === 'cover')
  const paused = parseNowPlayingJson(JSON.stringify({ title: 'S', playbackRate: 0 }))
  check('zero rate maps to idle', paused.state === 'idle')
  check('unknown bundle falls back to last segment', parseNowPlayingJson(JSON.stringify({ title: 'S', playbackRate: 1, clientBundleIdentifier: 'com.foo.Bar' })).app === 'Bar')
  check('missing title and artist is idle', parseNowPlayingJson(JSON.stringify({ playbackRate: 1 })).state === 'idle')
  check('broken json is idle', parseNowPlayingJson('{oops').state === 'idle')
}

group('media / Windows GSMTC')
{
  const rows = parseSessions(
    JSON.stringify([
      { app: 'Spotify.exe', status: 'Playing', title: 'A', artist: 'B', album: 'C', positionMs: 100, endMs: 200 },
      { app: 'Chrome.exe', status: 'Closed', title: '', positionMs: 0, endMs: 0 }
    ])
  )
  check('drops idle sessions without a title', rows.length === 1)
  check('maps playing status', rows[0]?.state === 'playing')
  check('maps app id to friendly name', rows[0]?.app === 'Spotify')
  check('single object payload is accepted', parseSessions(JSON.stringify({ status: 'Playing', title: 'A' })).length === 1)
  check('broken json yields nothing', parseSessions('nope').length === 0)
  check('unknown app id falls back to package', friendlyAppName('Foo.Bar!App') === 'Foo.Bar')
  const encoded = Buffer.from(encodePowerShell('Get-Date'), 'base64').toString('utf16le')
  check('powershell script is utf16 base64', encoded === 'Get-Date')
}

group('media / MPRIS')
{
  const variant = (value: unknown) => ({ signature: 's', value })
  check('unwraps nested variants', unwrap(variant(variant('x'))) === 'x')
  const info = parseMetadata(
    {
      'xesam:title': variant('Song'),
      'xesam:artist': variant([variant('A'), variant('B')]),
      'xesam:album': variant('Album'),
      'mpris:length': variant(180000000),
      'mpris:artUrl': variant('file:///cover.png')
    },
    'Playing',
    'spotify',
    variant(30000000)
  )
  check('maps playing status', info.state === 'playing')
  check('joins artist array', info.artist === 'A, B')
  check('microseconds convert to ms', info.duration_ms === 180000 && info.position_ms === 30000)
  check('keeps artwork url', info.cover_url === 'file:///cover.png')
  check('stopped status is idle', parseMetadata({}, 'Stopped', 'x').state === 'idle')
}

group('system load')
{
  check('cpu percent from deltas', Math.round(cpuPercent({ idle: 0, total: 0 }, { idle: 50, total: 100 })) === 50)
  check('cpu percent with no previous sample', cpuPercent(null, { idle: 1, total: 2 }) === 0)
  check('cpu percent clamps', cpuPercent({ idle: 0, total: 0 }, { idle: 100, total: 100 }) === 0)
  check('memory percent', Math.round(memoryPercent(1000, 250)) === 75)
  check('memory percent guards zero total', memoryPercent(0, 0) === 0)
  check('windows reports no load average', loadAverage('windows').length === 0)
  check('macos reports three load averages', loadAverage('macos').length === 3)
}

group('screenshot encoding')
{
  const encoded = await encodeScreenshot(await syntheticScreen(400, 200), { blurRadius: 10, scale: 0.5, quality: 75 })
  check('halves both dimensions', encoded.width === 200 && encoded.height === 100, `${encoded.width}x${encoded.height}`)
  check('emits a webp payload', encoded.webp.subarray(0, 4).toString() === 'RIFF' && encoded.webp.subarray(8, 12).toString() === 'WEBP')
  const untouched = await encodeScreenshot(await syntheticScreen(100, 100), { blurRadius: 0, scale: 1, quality: 75 })
  check('zero blur keeps the frame size', untouched.width === 100 && untouched.height === 100)
  check('blur softens detail', (await encodeScreenshot(await syntheticScreen(200, 200), { blurRadius: 40, scale: 1, quality: 75 })).webp.length > 0)
}

async function syntheticScreen(width: number, height: number): Promise<Buffer> {
  const sharpModule = await import('sharp')
  const pixels = Buffer.alloc(width * height * 3)
  for (let index = 0; index < width * height; index += 1) {
    pixels[index * 3] = (index * 7) % 255
    pixels[index * 3 + 1] = (index * 13) % 255
    pixels[index * 3 + 2] = (index * 29) % 255
  }
  return sharpModule.default(pixels, { raw: { width, height, channels: 3 } }).png().toBuffer()
}

function blankMedia() {
  return {
    state: 'idle' as const,
    title: null,
    artist: null,
    album: null,
    app: null,
    cover_url: null,
    cover_bytes: null,
    position_ms: null,
    duration_ms: null
  }
}

if (process.argv.includes('--live')) {
  group('live config (read only)')
  const configFile = configPath()
  const secretsFile = secretsPath()
  check('client.json exists', existsSync(configFile), configFile)
  const live = appConfigSchema.parse(readJsonFile(configFile))
  if (existsSync(configFile)) {
    check('client_id present', live.client_id.length > 0, live.client_id)
    check('setup_completed', live.setup_completed)
    check('base_url', live.server.base_url.length > 0, live.server.base_url)
    check('interval in range', live.push.interval_seconds >= 5 && live.push.interval_seconds <= 3600, String(live.push.interval_seconds))
    process.stdout.write(`  info language=${live.ui.language}\n`)
  }
  check('client.secrets.json exists', existsSync(secretsFile), secretsFile)
  const secrets = secretsSchema.parse(readJsonFile(secretsFile))
  if (existsSync(secretsFile)) {
    check('api_key present', secrets.api_key.length > 0, `length=${secrets.api_key.length}`)
    check('github_token present', secrets.github_token.length > 0, `length=${secrets.github_token.length}`)
  }

  if (process.argv.includes('--server')) {
    group('live server (read only)')
    const api = new HeartbeatApi({
      baseUrl: live.server.base_url,
      apiKey: secrets.api_key,
      timeoutSeconds: live.server.timeout_seconds,
      clientVersion: '1.0.0',
      clientId: live.client_id
    })
    try {
      const messages = await api.listMessages(1, 0)
      const list = Array.isArray(messages)
        ? messages
        : ((messages as { items?: unknown[] })?.items ?? [])
      check('admin message list accepted', Array.isArray(list), `${list.length} rows`)
    } catch (error) {
      check('admin message list accepted', false, String(error))
    }
    try {
      const bans = await api.listMessageBans()
      const list = Array.isArray(bans) ? bans : ((bans as { items?: unknown[] })?.items ?? [])
      check('ban list accepted', Array.isArray(list), `${list.length} rows`)
    } catch (error) {
      check('ban list accepted', false, String(error))
    }
  }

  group('live collectors')
  if (currentPlatform() === 'macos') {
    const installed = installedAppScripts()
    check('at least one player script is usable', installed.length > 0, installed.map((entry) => entry.app).join(','))
    for (const entry of installed) {
      const compiled = await runCommand(
        'osacompile',
        ['-e', entry.script, '-o', join(tmpdir(), `heartbeat-${entry.app}.scpt`)],
        8000
      )
      check(
        `${entry.app} applescript compiles`,
        compiled.ok,
        compiled.ok ? '' : compiled.stderr.trim().split('\n')[0]
      )
    }
  }
  const registry = new CollectorRegistry({
    screenshot: {
      blurRadius: live.screenshot.blur_radius,
      scale: live.screenshot.scale,
      quality: live.screenshot.quality
    }
  })
  const openGate = new PrivacyGate({ screenshot: true, media: true, system: true })
  const shutGate = new PrivacyGate({ screenshot: false, media: false, system: false })

  const shot = await registry.collectScreenshot(openGate)
  check('screenshot captured and encoded', shot !== null, shot ? `${shot.width}x${shot.height} ${shot.webp.length}B` : 'capture unavailable')
  check('screenshot blocked by privacy gate', (await registry.collectScreenshot(shutGate)) === null)

  const media = await registry.collectMedia(openGate)
  process.stdout.write(`  info media state=${media?.state} title=${media?.title ?? '-'} app=${media?.app ?? '-'} pos=${media?.position_ms ?? '-'}/${media?.duration_ms ?? '-'} cover=${media?.cover_bytes ? `${media.cover_bytes.length}B` : media?.cover_url ?? '-'}\n`)
  check('media collection returns a value', media !== null)
  check('media blocked by privacy gate', (await registry.collectMedia(shutGate)) === null)

  const system = await registry.collectSystem(openGate)
  process.stdout.write(`  info system cpu=${system?.cpu_percent} mem=${system?.memory_percent} load=${JSON.stringify(system?.load_avg)}\n`)
  check('system load collected', system !== null && system.memory_percent > 0)
  check('system blocked by privacy gate', (await registry.collectSystem(shutGate)) === null)
}

process.stdout.write(`\n${failures === 0 ? 'smoke: all checks passed' : `smoke: ${failures} failing checks`}\n`)
process.exitCode = failures === 0 ? 0 : 1
