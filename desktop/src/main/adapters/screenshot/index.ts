import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import sharp from 'sharp'

import { logger } from '../../logger'
import type { ScreenshotResult } from '../../protocol'
import { firstSuccessful, runCommand, runCommandBuffer } from '../shell'

export interface ScreenshotEncodeOptions {
  blurRadius: number
  scale: number
  quality: number
}

const CAPTURE_TIMEOUT_MS = 8000
const WEBP_EFFORT = 4

async function captureMacos(): Promise<Buffer | null> {
  const directory = await mkdtemp(join(tmpdir(), 'heartbeat-shot-'))
  const file = join(directory, 'screen.png')
  try {
    const result = await runCommand('screencapture', ['-x', '-t', 'png', file], CAPTURE_TIMEOUT_MS)
    if (!result.ok) {
      return null
    }
    return await readFile(file)
  } catch (error) {
    logger.debug(`screencapture failed: ${String(error)}`)
    return null
  } finally {
    await rm(directory, { recursive: true, force: true })
  }
}

const WINDOWS_SCRIPT = `
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$stream = New-Object System.IO.MemoryStream
$bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
[Console]::OpenStandardOutput().Write($stream.ToArray(), 0, $stream.Length)
$graphics.Dispose()
$bitmap.Dispose()
`

function captureWindows(): Promise<Buffer | null> {
  return runCommandBuffer(
    'powershell',
    ['-NoProfile', '-NonInteractive', '-Command', WINDOWS_SCRIPT],
    CAPTURE_TIMEOUT_MS
  )
}

function captureLinux(): Promise<Buffer | null> {
  return firstSuccessful([
    () => runCommandBuffer('grim', ['-t', 'png', '-'], CAPTURE_TIMEOUT_MS),
    () => runCommandBuffer('gnome-screenshot', ['-f', '/dev/stdout'], CAPTURE_TIMEOUT_MS),
    () => runCommandBuffer('scrot', ['-o', '-'], CAPTURE_TIMEOUT_MS),
    () => runCommandBuffer('import', ['-window', 'root', 'png:-'], CAPTURE_TIMEOUT_MS)
  ])
}

const CAPTURERS: Record<string, () => Promise<Buffer | null>> = {
  macos: captureMacos,
  windows: captureWindows,
  linux: captureLinux
}

export function captureScreen(platform: string): Promise<Buffer | null> {
  const capturer = CAPTURERS[platform]
  return capturer ? capturer() : Promise.resolve(null)
}

export async function encodeScreenshot(
  raw: Buffer,
  options: ScreenshotEncodeOptions
): Promise<ScreenshotResult> {
  const pipeline = sharp(raw)
  const metadata = await pipeline.metadata()
  const width = Math.max(1, Math.round((metadata.width ?? 1) * options.scale))
  const height = Math.max(1, Math.round((metadata.height ?? 1) * options.scale))
  let image = pipeline.resize(width, height, { kernel: 'lanczos3' })
  if (options.blurRadius > 0) {
    image = image.blur(options.blurRadius)
  }
  const webp = await image
    .webp({ quality: Math.round(options.quality), effort: WEBP_EFFORT })
    .toBuffer()
  logger.debug(`Screenshot encoded: ${width}x${height} ${webp.length} bytes`)
  return { webp, width, height }
}
