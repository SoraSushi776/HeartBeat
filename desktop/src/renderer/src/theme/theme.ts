import { alpha, createTheme, type Theme } from '@mui/material/styles'

import { STATE_TOKENS, colorVar, type ColorScheme } from './material-you'

export const FONT_STACK = [
  'Roboto',
  'PingFang SC',
  'HarmonyOS Sans SC',
  'Noto Sans SC',
  'Microsoft YaHei',
  'system-ui',
  '-apple-system',
  'Segoe UI',
  'sans-serif'
].join(', ')

const MONO_STACK = [
  'ui-monospace',
  'SFMono-Regular',
  'JetBrains Mono',
  'Menlo',
  'Consolas',
  'monospace'
].join(', ')

const HOVER = Number(STATE_TOKENS['--md-sys-state-hover-opacity'])
const FOCUS = Number(STATE_TOKENS['--md-sys-state-focus-opacity'])
const PRESSED = Number(STATE_TOKENS['--md-sys-state-pressed-opacity'])

function stateLayer(color: string, opacity: number): string {
  return `linear-gradient(${alpha(color, opacity)} 0 0)`
}

export function createMaterialYouTheme(mode: 'light' | 'dark', scheme: ColorScheme): Theme {
  const outline = scheme.outline
  const outlineVariant = scheme.outlineVariant

  return createTheme({
    cssVariables: false,
    palette: {
      mode,
      primary: { main: scheme.primary, contrastText: scheme.onPrimary },
      secondary: { main: scheme.secondary, contrastText: scheme.onSecondary },
      error: { main: scheme.error, contrastText: scheme.onError },
      warning: { main: scheme.tertiary, contrastText: scheme.onTertiary },
      info: { main: scheme.primary, contrastText: scheme.onPrimary },
      success: { main: scheme.tertiary, contrastText: scheme.onTertiary },
      background: { default: scheme.surface, paper: scheme.surfaceContainerLow },
      text: { primary: scheme.onSurface, secondary: scheme.onSurfaceVariant, disabled: alpha(scheme.onSurface, 0.38) },
      divider: outlineVariant,
      action: {
        active: scheme.onSurfaceVariant,
        hover: alpha(scheme.onSurface, HOVER),
        selected: alpha(scheme.primary, FOCUS),
        disabled: alpha(scheme.onSurface, 0.38),
        disabledBackground: alpha(scheme.onSurface, 0.12)
      }
    },
    shape: { borderRadius: 16 },
    typography: {
      fontFamily: FONT_STACK,
      h1: { fontSize: 32, lineHeight: '40px', fontWeight: 400 },
      h2: { fontSize: 28, lineHeight: '36px', fontWeight: 400 },
      h3: { fontSize: 24, lineHeight: '32px', fontWeight: 400 },
      h4: { fontSize: 22, lineHeight: '28px', fontWeight: 400 },
      h5: { fontSize: 16, lineHeight: '24px', fontWeight: 500 },
      h6: { fontSize: 14, lineHeight: '20px', fontWeight: 500, letterSpacing: '0.1px' },
      subtitle1: { fontSize: 14, lineHeight: '20px', fontWeight: 500, letterSpacing: '0.1px' },
      subtitle2: { fontSize: 12, lineHeight: '16px', fontWeight: 500, letterSpacing: '0.5px' },
      body1: { fontSize: 16, lineHeight: '24px', fontWeight: 400, letterSpacing: '0.5px' },
      body2: { fontSize: 14, lineHeight: '20px', fontWeight: 400, letterSpacing: '0.25px' },
      button: { fontSize: 14, lineHeight: '20px', fontWeight: 500, letterSpacing: '0.1px', textTransform: 'none' },
      caption: { fontSize: 12, lineHeight: '16px', fontWeight: 400, letterSpacing: '0.4px' },
      overline: { fontSize: 11, lineHeight: '16px', fontWeight: 500, letterSpacing: '0.5px', textTransform: 'none' }
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          'html, body, #root': { height: '100%', margin: 0, padding: 0 },
          body: {
            backgroundColor: scheme.surface,
            color: scheme.onSurface,
            overscrollBehavior: 'none'
          },
          '.app-drag-region': { WebkitAppRegion: 'drag' } as never,
          '.app-no-drag': { WebkitAppRegion: 'no-drag' } as never,
          '::-webkit-scrollbar': { width: 12, height: 12 },
          '::-webkit-scrollbar-thumb': {
            backgroundColor: outlineVariant,
            borderRadius: 999,
            border: '3px solid transparent',
            backgroundClip: 'content-box'
          },
          '::-webkit-scrollbar-thumb:hover': { backgroundColor: outline },
          '::-webkit-scrollbar-track': { backgroundColor: 'transparent' },
          '::selection': { backgroundColor: scheme.primaryContainer, color: scheme.onPrimaryContainer }
        }
      },
      MuiPaper: {
        defaultProps: { elevation: 0 },
        styleOverrides: { root: { backgroundImage: 'none' } }
      },
      MuiAppBar: {
        defaultProps: { elevation: 0, color: 'transparent' },
        styleOverrides: {
          root: {
            backgroundColor: scheme.surface,
            color: scheme.onSurface,
            boxShadow: 'none',
            backgroundImage: 'none'
          }
        }
      },
      MuiButton: {
        defaultProps: { disableElevation: true, disableRipple: false, variant: 'tonal' },
        styleOverrides: {
          root: {
            minHeight: 'var(--md-comp-filled-button-height)',
            borderRadius: 999,
            paddingInline: 24,
            fontWeight: 500,
            textTransform: 'none',
            transition: 'background-image 120ms ease, background-color 120ms ease'
          },
          containedPrimary: {
            backgroundColor: scheme.primary,
            color: scheme.onPrimary,
            '&:hover': { backgroundColor: scheme.primary, backgroundImage: stateLayer(scheme.onPrimary, HOVER) },
            '&:active': { backgroundImage: stateLayer(scheme.onPrimary, PRESSED) }
          },
          containedSecondary: {
            backgroundColor: scheme.secondaryContainer,
            color: scheme.onSecondaryContainer,
            '&:hover': {
              backgroundColor: scheme.secondaryContainer,
              backgroundImage: stateLayer(scheme.onSecondaryContainer, HOVER)
            }
          },
          containedError: {
            backgroundColor: scheme.error,
            color: scheme.onError,
            '&:hover': { backgroundColor: scheme.error, backgroundImage: stateLayer(scheme.onError, HOVER) }
          },
          outlined: {
            borderColor: outline,
            color: scheme.primary,
            '&:hover': { borderColor: outline, backgroundImage: stateLayer(scheme.primary, HOVER) },
            '&:active': { backgroundImage: stateLayer(scheme.primary, PRESSED) }
          },
          text: {
            color: scheme.primary,
            paddingInline: 16,
            '&:hover': { backgroundImage: stateLayer(scheme.primary, HOVER) },
            '&:active': { backgroundImage: stateLayer(scheme.primary, PRESSED) }
          },
          disabled: { opacity: Number(STATE_TOKENS['--md-sys-state-disabled-content-opacity']) }
        },
        variants: [
          {
            props: { variant: 'tonal' },
            style: {
              backgroundColor: scheme.secondaryContainer,
              color: scheme.onSecondaryContainer,
              '&:hover': {
                backgroundColor: scheme.secondaryContainer,
                backgroundImage: stateLayer(scheme.onSecondaryContainer, HOVER)
              },
              '&:active': { backgroundImage: stateLayer(scheme.onSecondaryContainer, PRESSED) }
            }
          },
          {
            props: { variant: 'elevated' },
            style: {
              backgroundColor: scheme.surfaceContainerLow,
              color: scheme.primary,
              boxShadow: mode === 'dark' ? 'none' : '0 1px 2px rgba(0,0,0,0.3), 0 1px 3px 1px rgba(0,0,0,0.15)',
              '&:hover': { backgroundColor: scheme.surfaceContainerLow, backgroundImage: stateLayer(scheme.primary, HOVER) }
            }
          }
        ]
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            width: 'var(--md-comp-icon-button-size)',
            height: 'var(--md-comp-icon-button-size)',
            borderRadius: 999,
            color: scheme.onSurfaceVariant,
            '&:hover': { backgroundImage: stateLayer(scheme.onSurfaceVariant, HOVER) },
            '&:active': { backgroundImage: stateLayer(scheme.onSurfaceVariant, PRESSED) }
          },
          sizeSmall: { width: 32, height: 32 }
        }
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            minHeight: 'var(--md-comp-list-item-height)',
            borderRadius: 999,
            color: scheme.onSurfaceVariant,
            '&:hover': { backgroundImage: stateLayer(scheme.onSurfaceVariant, HOVER) },
            '&:active': { backgroundImage: stateLayer(scheme.onSurfaceVariant, PRESSED) },
            '&.Mui-selected': {
              backgroundColor: scheme.secondaryContainer,
              color: scheme.onSecondaryContainer,
              '&:hover': { backgroundColor: scheme.secondaryContainer, backgroundImage: stateLayer(scheme.onSecondaryContainer, HOVER) }
            }
          }
        }
      },
      MuiListItemIcon: {
        styleOverrides: { root: { color: 'inherit', minWidth: 40 } }
      },
      MuiListItemText: {
        styleOverrides: { primary: { fontSize: 14, fontWeight: 500 } }
      },
      MuiCard: {
        defaultProps: { elevation: 0 },
        styleOverrides: {
          root: {
            backgroundColor: scheme.surfaceContainerLow,
            backgroundImage: 'none',
            borderRadius: 16,
            border: `1px solid ${outlineVariant}`,
            boxShadow: 'none'
          }
        }
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            backgroundColor: scheme.surfaceContainerHigh,
            borderRadius: 28,
            backgroundImage: 'none',
            padding: 8
          }
        }
      },
      MuiPopover: {
        styleOverrides: {
          paper: {
            backgroundColor: scheme.surfaceContainer,
            borderRadius: 4,
            backgroundImage: 'none',
            boxShadow: mode === 'dark' ? '0 2px 8px rgba(0,0,0,0.6)' : '0 2px 8px rgba(0,0,0,0.18)'
          }
        }
      },
      MuiMenu: {
        styleOverrides: {
          list: { padding: 8 },
          paper: { backgroundColor: scheme.surfaceContainer, borderRadius: 4, backgroundImage: 'none' }
        }
      },
      MuiMenuItem: {
        styleOverrides: {
          root: {
            borderRadius: 999,
            minHeight: 40,
            fontSize: 14,
            '&:hover': { backgroundImage: stateLayer(scheme.onSurface, HOVER) },
            '&.Mui-selected': { backgroundColor: scheme.secondaryContainer, color: scheme.onSecondaryContainer }
          }
        }
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: scheme.inverseSurface,
            color: scheme.inverseOnSurface,
            borderRadius: 4,
            fontSize: 12,
            padding: '6px 8px'
          }
        }
      },
      MuiTextField: { defaultProps: { variant: 'outlined', size: 'small' } },
      MuiFilledInput: {
        styleOverrides: {
          root: {
            backgroundColor: scheme.surfaceContainerHighest,
            borderRadius: '4px 4px 0 0',
            '&:hover': { backgroundColor: scheme.surfaceContainerHigh },
            '&.Mui-focused': { backgroundColor: scheme.surfaceContainerHighest },
            '&::before': { borderBottomColor: outline },
            '&::after': { borderBottomColor: scheme.primary },
            '&.Mui-disabled': { backgroundColor: alpha(scheme.onSurface, 0.12) }
          }
        }
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            '& .MuiOutlinedInput-notchedOutline': { borderColor: outline },
            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: scheme.onSurface },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: scheme.primary, borderWidth: 2 }
          }
        }
      },
      MuiInputLabel: {
        styleOverrides: { root: { fontSize: 14 }, shrink: { fontSize: 12 } }
      },
      MuiFormHelperText: { styleOverrides: { root: { marginLeft: 0, fontSize: 12 } } },
      MuiFormControlLabel: { styleOverrides: { label: { fontSize: 14 } } },
      MuiSwitch: {
        styleOverrides: {
          root: { width: 52, height: 32, padding: 0 },
          switchBase: {
            padding: 6,
            color: outline,
            '&.Mui-checked': {
              transform: 'translateX(20px)',
              color: scheme.onPrimary,
              '& + .MuiSwitch-track': {
                backgroundColor: scheme.primary,
                opacity: 1,
                border: 'none'
              }
            }
          },
          thumb: { width: 20, height: 20, boxShadow: 'none' },
          track: {
            borderRadius: 999,
            backgroundColor: scheme.surfaceContainerHighest,
            border: `2px solid ${outline}`,
            opacity: 1
          }
        }
      },
      MuiSlider: {
        defaultProps: { valueLabelDisplay: 'auto' },
        styleOverrides: {
          root: { height: 4, padding: '13px 0' },
          rail: {
            // MUI 默认横向定位自带 top:50% + translateY(-50%) 居中，
            // 这里不要再加 marginTop（会和 translateY 叠加导致轨道上移）。
            height: 16,
            borderRadius: 999,
            backgroundColor: scheme.surfaceContainerHighest,
            opacity: 1,
            '&::before, &::after': {
              content: '""',
              position: 'absolute',
              top: '50%',
              width: 4,
              height: 4,
              borderRadius: '50%',
              transform: 'translateY(-50%)',
              backgroundColor: alpha(scheme.onSurface, 0.38)
            },
            '&::before': { left: 6 },
            '&::after': { right: 6 },
            '&.Mui-disabled': { backgroundColor: alpha(scheme.onSurface, 0.12) }
          },
          track: {
            height: 16,
            borderRadius: 999,
            border: 'none',
            backgroundColor: scheme.primary,
            '&.Mui-disabled': { backgroundColor: alpha(scheme.onSurface, 0.38) }
          },
          thumb: {
            width: 4,
            height: 44,
            borderRadius: 999,
            backgroundColor: scheme.primary,
            // 官方 M3 更新版：手柄两侧与轨道断开（各留 6dp 缝），轨道不从手柄底下穿过。
            // ::after 用 z-index:-1 垫在手柄 bar 之下、轨道之上，中间 4px 透明露出手柄本体。
            // 背景色取滑条实际所在容器（SectionCard = surface-container-low）。
            '&::after': {
              content: '""',
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 16,
              height: 16,
              zIndex: -1,
              background: `linear-gradient(90deg, ${colorVar('surface-container-low')} 0 6px, transparent 6px 10px, ${colorVar('surface-container-low')} 10px 16px)`
            },
            '&::before': {
              content: '""',
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 48,
              height: 48,
              borderRadius: '50%',
              backgroundColor: scheme.primary,
              opacity: 0,
              transition: 'opacity 150ms ease'
            },
            '&:hover::before': { opacity: HOVER },
            '&.Mui-focusVisible::before': { opacity: FOCUS },
            '&.Mui-active::before': { opacity: PRESSED },
            '&.Mui-disabled': { backgroundColor: alpha(scheme.onSurface, 0.38), boxShadow: 'none' }
          },
          valueLabel: {
            backgroundColor: scheme.primary,
            color: scheme.onPrimary,
            borderRadius: 999,
            fontSize: 14,
            lineHeight: '20px',
            padding: '3px 8px'
          }
        }
      },
      MuiChip: {
        defaultProps: { size: 'small' },
        styleOverrides: {
          root: {
            borderRadius: 8,
            fontWeight: 500,
            fontSize: 13,
            backgroundColor: 'transparent',
            border: `1px solid ${outline}`,
            color: scheme.onSurfaceVariant
          }
        }
      },
      MuiDivider: { styleOverrides: { root: { borderColor: outlineVariant } } },
      MuiTabs: {
        styleOverrides: {
          indicator: { backgroundColor: scheme.primary, height: 3, borderRadius: '3px 3px 0 0' },
          root: { minHeight: 48 }
        }
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontSize: 14,
            fontWeight: 500,
            minHeight: 48,
            color: scheme.onSurfaceVariant,
            '&.Mui-selected': { color: scheme.primary }
          }
        }
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: { height: 4, borderRadius: 999, backgroundColor: scheme.surfaceContainerHighest },
          bar: { borderRadius: 999, backgroundColor: scheme.primary }
        }
      },
      MuiAlert: {
        styleOverrides: {
          root: { borderRadius: 12, fontSize: 14, border: `1px solid ${outlineVariant}` }
        }
      },
      MuiTableCell: {
        styleOverrides: {
          root: { borderBottomColor: outlineVariant, fontSize: 14 },
          head: { color: scheme.onSurfaceVariant, fontWeight: 500 }
        }
      },
      MuiAccordion: {
        styleOverrides: {
          root: {
            backgroundColor: scheme.surfaceContainerLow,
            backgroundImage: 'none',
            borderRadius: 12,
            border: `1px solid ${outlineVariant}`,
            '&::before': { display: 'none' },
            '&.Mui-expanded': { margin: 0 }
          }
        }
      },
      MuiToggleButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 999,
            border: `1px solid ${outline}`,
            color: scheme.onSurfaceVariant,
            '&.Mui-selected': {
              backgroundColor: scheme.secondaryContainer,
              color: scheme.onSecondaryContainer,
              '&:hover': { backgroundColor: scheme.secondaryContainer }
            }
          }
        }
      },
      MuiSnackbar: { styleOverrides: { root: { borderRadius: 4 } } },
      MuiSnackbarContent: {
        styleOverrides: {
          root: { backgroundColor: scheme.inverseSurface, color: scheme.inverseOnSurface, borderRadius: 4 }
        }
      },
      MuiCircularProgress: { defaultProps: { size: 20, thickness: 4 } },
      MuiTypography: { defaultProps: { variantMapping: { h6: 'h3' } } }
    }
  })
}

export type MaterialYouTheme = ReturnType<typeof createMaterialYouTheme>
export const TYPOGRAPHY_MONO = MONO_STACK
