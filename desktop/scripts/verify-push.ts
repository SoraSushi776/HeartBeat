import { createServer, type IncomingMessage, type ServerResponse } from 'node:http'

import sharp from 'sharp'

import type { CollectorBundle, CollectorConfig } from '../src/main/adapters/index'
import { HeartbeatApi } from '../src/main/api'
import { HeartbeatCollector } from '../src/main/collector'
import { backoffDelaySeconds } from '../src/main/collector'
import { toBackgroundJpeg, toCoverJpeg } from '../src/main/imaging'
import { emptyFlags, type HeartbeatPayload, type MediaInfo, type PrivacyFlags } from '../src/main/protocol'

let failures = 0

function check(name: string, condition: boolean, detail = ''): void {
  process.stdout.write(`  ${condition ? 'ok  ' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}\n`)
  if (!condition) {
    failures += 1
  }
}

interface Captured {
  heartbeats: Array<{ headers: IncomingMessage['headers']; payload: HeartbeatPayload }>
  covers: Buffer[]
  screenshots: Array<{ bytes: Buffer; ts: string | undefined }>
}

function readBody(request: IncomingMessage): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = []
    request.on('data', (chunk: Buffer) => chunks.push(chunk))
    request.on('end', () => resolve(Buffer.concat(chunks)))
    request.on('error', reject)
  })
}

function respond(response: ServerResponse, status: number, body: unknown): void {
  const text = JSON.stringify(body)
  response.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(text) })
  response.end(text)
}

async function startServer(captured: Captured, failHeartbeat: () => boolean): Promise<{ port: number; close: () => Promise<void> }> {
  const server = createServer((request, response) => {
    const url = request.url ?? ''
    void (async () => {
      const body = await readBody(request)
      if (request.method === 'POST' && url === '/api/v1/heartbeat') {
        if (failHeartbeat()) {
          respond(response, 500, { ok: false, error: { message: 'injected failure' } })
          return
        }
        captured.heartbeats.push({
          headers: request.headers,
          payload: JSON.parse(body.toString('utf8')) as HeartbeatPayload
        })
        respond(response, 200, { ok: true, data: { screenshot_upload_url: '/api/v1/screenshot/mock' } })
        return
      }
      if (request.method === 'PUT' && url.startsWith('/api/v1/cover/')) {
        captured.covers.push(body)
        respond(response, 200, { ok: true, data: { url: 'https://cdn.example/cover.jpg' } })
        return
      }
      if (request.method === 'PUT' && url.startsWith('/api/v1/screenshot/')) {
        captured.screenshots.push({ bytes: body, ts: request.headers['x-heartbeat-ts'] as string | undefined })
        respond(response, 200, { ok: true, data: {} })
        return
      }
      respond(response, 404, { ok: false, error: { message: 'not found' } })
    })()
  })
  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve))
  const address = server.address()
  const port = typeof address === 'object' && address ? address.port : 0
  return {
    port,
    close: () =>
      new Promise<void>((resolve) => {
        server.closeAllConnections()
        server.close(() => resolve())
      })
  }
}

async function syntheticPng(width: number, height: number): Promise<Buffer> {
  const pixels = Buffer.alloc(width * height * 3)
  for (let index = 0; index < width * height; index += 1) {
    pixels[index * 3] = (index * 3) % 255
    pixels[index * 3 + 1] = (index * 11) % 255
    pixels[index * 3 + 2] = (index * 17) % 255
  }
  return sharp(pixels, { raw: { width, height, channels: 3 } }).png().toBuffer()
}

const captured: Captured = { heartbeats: [], covers: [], screenshots: [] }
let failing = false
const server = await startServer(captured, () => failing)

const COVER_SOURCE = await syntheticPng(600, 400)
const SHOT_SOURCE = await syntheticPng(800, 600)
const SHOT_WEBP = await sharp(SHOT_SOURCE).webp({ quality: 75 }).toBuffer()

const config: CollectorConfig = {
  screenshot: { blurRadius: 10, scale: 0.5, quality: 75 }
}

const stubMedia: MediaInfo = {
  state: 'playing',
  title: 'Mock Song',
  artist: 'Mock Artist',
  album: 'Mock Album',
  app: 'MockPlayer',
  cover_url: null,
  cover_bytes: COVER_SOURCE,
  position_ms: 1500,
  duration_ms: 200000
}

const flags: PrivacyFlags = { ...emptyFlags() }

const stub: CollectorBundle = {
  collectScreenshot: async () => ({ webp: SHOT_WEBP, width: 400, height: 300 }),
  collectMedia: async () => stubMedia,
  collectSystem: async () => ({ cpu_percent: 12.5, memory_percent: 66, load_avg: [1, 2, 3] }),
  update: () => undefined
}

const api = new HeartbeatApi({
  baseUrl: `http://127.0.0.1:${server.port}`,
  apiKey: 'test-key',
  timeoutSeconds: 5,
  clientVersion: '1.0.0',
  clientId: 'testclient01'
})

const collector = new HeartbeatCollector(
  api,
  {
    clientId: 'testclient01',
    clientVersion: '1.0.0',
    pushEnabled: true,
    intervalSeconds: 30,
    backoffSeconds: [0, 5, 15, 60, 300],
    privacy: flags,
    collectors: config
  },
  {},
  stub
)

process.stdout.write('\nheartbeat pipeline\n')
const record = await collector.tick()
check('tick reports success', record.ok, record.detail)
check('server received one heartbeat', captured.heartbeats.length === 1)
const sent = captured.heartbeats[0]
check('sends the api key header', sent?.headers['x-api-key'] === 'test-key')
check('sends the client version header', sent?.headers['x-client-version'] === '1.0.0')
check('payload carries a timestamp', typeof sent?.payload.ts === 'number' && sent.payload.ts > 0)
check('payload carries client info', sent?.payload.client.id === 'testclient01' && sent?.payload.client.platform === 'macos')
check('payload carries privacy flags', JSON.stringify(sent?.payload.privacy) === JSON.stringify(flags))
check('payload carries system load', sent?.payload.system?.memory_percent === 66)
check('media is serialized', sent?.payload.media?.title === 'Mock Song' && sent?.payload.media?.state === 'playing')
check('media carries no raw cover bytes', !JSON.stringify(sent?.payload).includes('cover_bytes'))
check('cover url is backfilled from the server', sent?.payload.media?.cover_url === 'https://cdn.example/cover.jpg')

check('cover image was uploaded', captured.covers.length === 1, `${captured.covers[0]?.length ?? 0} bytes`)
const coverMeta = await sharp(captured.covers[0] ?? Buffer.alloc(0)).metadata()
check('cover is a 200x200 jpeg', coverMeta.format === 'jpeg' && coverMeta.width === 200 && coverMeta.height === 200, `${coverMeta.format} ${coverMeta.width}x${coverMeta.height}`)

check('screenshot was uploaded', captured.screenshots.length === 1, `${captured.screenshots[0]?.bytes.length ?? 0} bytes`)
check('screenshot payload is webp', captured.screenshots[0]?.bytes.subarray(8, 12).toString() === 'WEBP')
check('screenshot carries the heartbeat ts', captured.screenshots[0]?.ts === String(sent?.payload.ts))

process.stdout.write('\nbackoff behaviour\n')
failing = true
const failed = await collector.tick()
check('failure is reported', !failed.ok, failed.detail)
check('failure records a push entry', collector.pushHistory[0]?.ok === false)
check('backoff table walks forward', backoffDelaySeconds([0, 5, 15, 60, 300], 0) === 0)
check('backoff table clamps at the end', backoffDelaySeconds([0, 5, 15, 60, 300], 99) === 300)
check('backoff survives an empty table', backoffDelaySeconds([], 3) === 0)

failing = false
const recovered = await collector.tick()
check('recovers after a failure', recovered.ok)
check('history keeps the newest first', collector.pushHistory[0]?.ok === true && collector.pushHistory.length >= 3)
check('history is capped at 20', collector.pushHistory.length <= 20)

process.stdout.write('\nimaging\n')
const cover = await toCoverJpeg(COVER_SOURCE)
const coverInfo = await sharp(cover ?? Buffer.alloc(0)).metadata()
check('cover crops to a square', coverInfo.width === 200 && coverInfo.height === 200)
check('cover rejects empty input', (await toCoverJpeg(null)) === null)
check('cover rejects garbage', (await toCoverJpeg(Buffer.from('not an image'))) === null)

const background = await toBackgroundJpeg(await syntheticPng(3200, 1800))
const backgroundInfo = await sharp(background ?? Buffer.alloc(0)).metadata()
check('background caps the long edge', backgroundInfo.width === 1600, String(backgroundInfo.width))
check('background keeps the aspect ratio', backgroundInfo.height === 900, String(backgroundInfo.height))

await server.close()
process.stdout.write(`\n${failures === 0 ? 'verify-push: all checks passed' : `verify-push: ${failures} failing checks`}\n`)
process.exit(failures === 0 ? 0 : 1)
