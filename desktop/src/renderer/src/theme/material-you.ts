import {
  Hct,
  SchemeContent,
  SchemeExpressive,
  SchemeFidelity,
  SchemeFruitSalad,
  SchemeMonochrome,
  SchemeNeutral,
  SchemeRainbow,
  SchemeTonalSpot,
  SchemeVibrant,
  argbFromHex,
  hexFromArgb
} from '@material/material-color-utilities'

export const COLOR_ROLES = [
  'primary',
  'onPrimary',
  'primaryContainer',
  'onPrimaryContainer',
  'secondary',
  'onSecondary',
  'secondaryContainer',
  'onSecondaryContainer',
  'tertiary',
  'onTertiary',
  'tertiaryContainer',
  'onTertiaryContainer',
  'error',
  'onError',
  'errorContainer',
  'onErrorContainer',
  'background',
  'onBackground',
  'surface',
  'onSurface',
  'surfaceVariant',
  'onSurfaceVariant',
  'surfaceDim',
  'surfaceBright',
  'surfaceContainerLowest',
  'surfaceContainerLow',
  'surfaceContainer',
  'surfaceContainerHigh',
  'surfaceContainerHighest',
  'outline',
  'outlineVariant',
  'shadow',
  'scrim',
  'inverseSurface',
  'inverseOnSurface',
  'inversePrimary'
] as const

export type ColorRole = (typeof COLOR_ROLES)[number]

export type SchemeVariant =
  | 'tonalSpot'
  | 'content'
  | 'fidelity'
  | 'vibrant'
  | 'expressive'
  | 'neutral'
  | 'monochrome'
  | 'rainbow'
  | 'fruitSalad'

export const SCHEME_VARIANTS: Record<SchemeVariant, SchemeVariant> = {
  tonalSpot: 'tonalSpot',
  content: 'content',
  fidelity: 'fidelity',
  vibrant: 'vibrant',
  expressive: 'expressive',
  neutral: 'neutral',
  monochrome: 'monochrome',
  rainbow: 'rainbow',
  fruitSalad: 'fruitSalad'
}

type SchemeConstructor = new (source: Hct, dark: boolean, contrast: number) => unknown

const SCHEME_CLASSES: Record<SchemeVariant, SchemeConstructor> = {
  tonalSpot: SchemeTonalSpot,
  content: SchemeContent,
  fidelity: SchemeFidelity,
  vibrant: SchemeVibrant,
  expressive: SchemeExpressive,
  neutral: SchemeNeutral,
  monochrome: SchemeMonochrome,
  rainbow: SchemeRainbow,
  fruitSalad: SchemeFruitSalad
}

export const SEED_PRESETS: { label: string; value: string }[] = [
  { label: 'Material 紫', value: '#6750A4' },
  { label: '心跳红', value: '#E5484D' },
  { label: '深海蓝', value: '#0B6BCB' },
  { label: '森林绿', value: '#1F7A4D' },
  { label: '暖沙橙', value: '#C4622D' },
  { label: '樱花粉', value: '#D6336C' },
  { label: '石墨灰', value: '#5A5D63' }
]

export const DEFAULT_SEED = '#6750A4'

export interface ThemeOptions {
  seed: string
  dark: boolean
  variant: SchemeVariant
  contrast: number
}

function toKebab(role: string): string {
  return role.replace(/([a-z0-9])([A-Z])/g, '$1-$2').toLowerCase()
}

export function colorVar(name: string): string {
  return `var(--md-sys-color-${name})`
}

export function roleVar(role: ColorRole): string {
  return colorVar(toKebab(role))
}

export function stateLayer(color: string, opacity: number): string {
  return `linear-gradient(color-mix(in srgb, ${color} ${Math.round(opacity * 100)}%, transparent) 0 0)`
}

export type ColorScheme = Record<ColorRole, string>

export function buildScheme(options: ThemeOptions): ColorScheme {
  const SchemeClass = SCHEME_CLASSES[options.variant]
  const scheme = new SchemeClass(
    Hct.fromInt(argbFromHex(options.seed)),
    options.dark,
    options.contrast
  ) as Record<ColorRole, number>
  const resolved: Partial<ColorScheme> = {}
  for (const role of COLOR_ROLES) {
    resolved[role] = hexFromArgb(scheme[role])
  }
  return resolved as ColorScheme
}

export function buildColorTokens(scheme: ColorScheme): Record<string, string> {
  const tokens: Record<string, string> = {}
  for (const role of COLOR_ROLES) {
    tokens[`--md-sys-color-${toKebab(role)}`] = scheme[role]
  }
  return tokens
}

export const SHAPE_TOKENS: Record<string, string> = {
  '--md-sys-shape-corner-none': '0px',
  '--md-sys-shape-corner-extra-small': '4px',
  '--md-sys-shape-corner-small': '8px',
  '--md-sys-shape-corner-medium': '12px',
  '--md-sys-shape-corner-large': '16px',
  '--md-sys-shape-corner-extra-large': '28px',
  '--md-sys-shape-corner-full': '999px'
}

export const STATE_TOKENS: Record<string, string> = {
  '--md-sys-state-hover-opacity': '0.08',
  '--md-sys-state-focus-opacity': '0.1',
  '--md-sys-state-pressed-opacity': '0.1',
  '--md-sys-state-dragged-opacity': '0.16',
  '--md-sys-state-disabled-container-opacity': '0.12',
  '--md-sys-state-disabled-content-opacity': '0.38'
}

export const LAYOUT_TOKENS: Record<string, string> = {
  '--md-sys-navigation-rail-width': '88px',
  '--md-sys-top-bar-height': '64px',
  '--md-comp-filled-button-height': '40px',
  '--md-comp-icon-button-size': '40px',
  '--md-comp-list-item-height': '56px'
}

export function buildTokens(options: ThemeOptions): Record<string, string> {
  return {
    ...buildColorTokens(buildScheme(options)),
    ...SHAPE_TOKENS,
    ...STATE_TOKENS,
    ...LAYOUT_TOKENS
  }
}

export function applyTokens(target: HTMLElement, tokens: Record<string, string>): void {
  for (const [name, value] of Object.entries(tokens)) {
    target.style.setProperty(name, value)
  }
}
