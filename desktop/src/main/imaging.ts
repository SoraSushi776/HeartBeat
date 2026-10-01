import sharp from 'sharp'

import { logger } from './logger'

export const COVER_SIZE = 200
export const COVER_JPEG_QUALITY = 80
export const BACKGROUND_MAX_EDGE = 1600
export const BACKGROUND_JPEG_QUALITY = 78
export const BACKGROUND_MAX_BYTES = 2_200_000
export const BACKGROUND_QUALITY_STEPS = [BACKGROUND_JPEG_QUALITY, 70, 60, 50]

async function decode(raw: Buffer | null): Promise<sharp.Sharp | null> {
  if (!raw || raw.length === 0) {
    return null
  }
  try {
    const image = sharp(raw)
    await image.metadata()
    return image
  } catch (error) {
    logger.warn(`Image decode failed: ${String(error)}`)
    return null
  }
}

export async function toCoverJpeg(raw: Buffer | null): Promise<Buffer | null> {
  const image = await decode(raw)
  if (!image) {
    return null
  }
  return image
    .resize(COVER_SIZE, COVER_SIZE, { fit: 'cover', position: 'centre' })
    .jpeg({ quality: COVER_JPEG_QUALITY })
    .toBuffer()
}

export async function toBackgroundJpeg(raw: Buffer | null): Promise<Buffer | null> {
  const image = await decode(raw)
  if (!image) {
    return null
  }
  const resized = image.resize(BACKGROUND_MAX_EDGE, BACKGROUND_MAX_EDGE, {
    fit: 'inside',
    withoutEnlargement: true
  })
  let smallest: Buffer | null = null
  for (const quality of BACKGROUND_QUALITY_STEPS) {
    const encoded = await resized
      .clone()
      .jpeg({ quality })
      .toBuffer()
    if (encoded.length <= BACKGROUND_MAX_BYTES) {
      return encoded
    }
    smallest = encoded
  }
  return smallest
}
