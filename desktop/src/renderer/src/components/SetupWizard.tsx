import type { ReactNode } from 'react'
import { useEffect, useMemo, useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import Step from '@mui/material/Step'
import StepLabel from '@mui/material/StepLabel'
import Stepper from '@mui/material/Stepper'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'

import { useTranslate } from '../i18n'
import { colorVar } from '../theme/material-you'
import { bridge, errorMessage } from '../utils/bridge'
import type { ConfigBundle, SetupCheck } from '@shared/ipc'
import type { TranslationKey } from '../i18n'

interface SetupWizardProps {
  open: boolean
  bundle: ConfigBundle
  onFinished: (bundle: ConfigBundle) => void
}

type StepKind = 'tools' | 'permissions' | 'server'

const STEPS: Array<{ kind: StepKind; labelKey: TranslationKey; hintKey: TranslationKey }> = [
  { kind: 'tools', labelKey: 'setup.step.tools', hintKey: 'setup.tools_hint' },
  { kind: 'permissions', labelKey: 'setup.step.permissions', hintKey: 'setup.permissions_hint' },
  { kind: 'server', labelKey: 'setup.step.server', hintKey: 'setup.server_hint' }
]

const TOOL_IDS = ['homebrew', 'nowplaying', 'capture-tool']
const PERMISSION_IDS = ['screen-recording', 'automation']

export function SetupWizard({ open, bundle, onFinished }: SetupWizardProps): ReactNode {
  const t = useTranslate()
  const [step, setStep] = useState(0)
  const [checks, setChecks] = useState<SetupCheck[]>([])
  const [server, setServer] = useState(bundle.config.server.base_url)
  const [apiKey, setApiKey] = useState(bundle.secrets.api_key)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    setServer(bundle.config.server.base_url)
    setApiKey(bundle.secrets.api_key)
    void refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, bundle])

  const refresh = async (): Promise<void> => {
    try {
      const report = await bridge.setup.report()
      setChecks(report.checks)
      setError(null)
    } catch (caught) {
      setError(errorMessage(caught))
    }
  }

  const runAction = async (actionId: string): Promise<void> => {
    setBusy(true)
    try {
      const report = await bridge.setup.run(actionId)
      setChecks(report.checks)
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const current = STEPS[step]
  const visible = useMemo(() => {
    if (current.kind === 'tools') {
      return checks.filter((check) => TOOL_IDS.includes(check.id))
    }
    if (current.kind === 'permissions') {
      return checks.filter((check) => PERMISSION_IDS.includes(check.id))
    }
    return []
  }, [checks, current.kind])

  const finish = async (): Promise<void> => {
    setBusy(true)
    try {
      const next: ConfigBundle = {
        ...bundle,
        config: {
          ...bundle.config,
          setup_completed: true,
          server: { ...bundle.config.server, base_url: server.trim() }
        },
        secrets: { ...bundle.secrets, api_key: apiKey }
      }
      const result = await bridge.config.save(next)
      onFinished(result.bundle)
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const pending = checks.filter((check) => !check.ok).length

  return (
    <Dialog open={open} maxWidth="sm" fullWidth onClose={() => undefined}>
      <DialogTitle>{t('setup.title')}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Stepper activeStep={step} alternativeLabel>
          {STEPS.map((entry) => (
            <Step key={entry.kind}>
              <StepLabel>{t(entry.labelKey)}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
          {t(current.hintKey)}
        </Typography>

        {current.kind === 'server' ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <TextField
              label={t('settings.base_url')}
              value={server}
              onChange={(event) => setServer(event.target.value)}
              fullWidth
            />
            <TextField
              label={t('settings.api_key')}
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              fullWidth
            />
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {visible.length === 0 ? (
              <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
                {t('common.empty')}
              </Typography>
            ) : null}
            {visible.map((check) => (
              <Box
                key={check.id}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  borderRadius: 3,
                  border: `1px solid ${colorVar('outline-variant')}`,
                  p: 1.5
                }}
              >
                {check.ok ? (
                  <CheckCircleIcon sx={{ color: colorVar('primary') }} fontSize="small" />
                ) : (
                  <ErrorOutlineIcon sx={{ color: colorVar('error') }} fontSize="small" />
                )}
                <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                  <Typography variant="body2">{t(check.labelKey as TranslationKey)}</Typography>
                  <Typography
                    variant="caption"
                    sx={{ color: colorVar('on-surface-variant'), wordBreak: 'break-all' }}
                  >
                    {check.detail}
                  </Typography>
                </Box>
                {check.actionId ? (
                  <Button
                    variant="tonal"
                    size="small"
                    disabled={busy}
                    onClick={() => void runAction(check.actionId as string)}
                  >
                    {check.actionId === 'install-nowplaying' ? t('setup.install') : t('setup.open_settings')}
                  </Button>
                ) : null}
              </Box>
            ))}
            <Button variant="text" onClick={() => void refresh()} disabled={busy} sx={{ alignSelf: 'flex-start' }}>
              {t('setup.recheck')}
            </Button>
            <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
              {pending === 0 ? t('setup.all_good') : t('setup.missing', { count: pending })}
            </Typography>
          </Box>
        )}

        {error ? (
          <Typography variant="body2" sx={{ color: colorVar('error') }}>
            {error}
          </Typography>
        ) : null}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button variant="text" disabled={step === 0} onClick={() => setStep((value) => value - 1)}>
          {t('setup.back')}
        </Button>
        <Box sx={{ flexGrow: 1 }} />
        <Button variant="text" onClick={() => void finish()} disabled={busy}>
          {t('setup.skip')}
        </Button>
        {step < STEPS.length - 1 ? (
          <Button variant="contained" onClick={() => setStep((value) => value + 1)}>
            {t('setup.next')}
          </Button>
        ) : (
          <Button variant="contained" onClick={() => void finish()} disabled={busy}>
            {t('setup.finish')}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  )
}
