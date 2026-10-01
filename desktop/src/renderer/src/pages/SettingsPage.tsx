import type { ReactNode } from 'react'
import { useEffect, useMemo, useState } from 'react'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import MenuItem from '@mui/material/MenuItem'
import Snackbar from '@mui/material/Snackbar'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'

import { FieldRow } from '../components/FieldRow'
import { PageScaffold } from '../components/PageScaffold'
import { useHeaderActions } from '../shell/header'
import { SectionCard } from '../components/SectionCard'
import { SliderField, SwitchField } from '../components/SliderField'
import { StateBlock } from '../components/StateBlock'
import { TokenField } from '../components/TokenField'
import { LANGUAGES, useLanguage, useTranslate } from '../i18n'
import { bridge, errorMessage } from '../utils/bridge'
import { useAsync } from '../utils/hooks'
import { colorVar } from '../theme/material-you'
import type { AppConfig, Language, Secrets } from '@shared/config'
import type { ConfigBundle } from '@shared/ipc'

type Patch = (draft: ConfigBundle) => ConfigBundle

export function SettingsPage(): ReactNode {
  const t = useTranslate()
  const setLanguage = useLanguage((state) => state.setLanguage)
  const loaded = useAsync(() => bridge.config.load(), [])
  const [draft, setDraft] = useState<ConfigBundle | null>(null)
  const [saved, setSaved] = useState<ConfigBundle | null>(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<{ text: string; severity: 'success' | 'warning' | 'error' } | null>(null)

  useEffect(() => {
    if (!loaded.data) {
      return
    }
    setDraft(loaded.data)
    setSaved(loaded.data)
  }, [loaded.data])

  const dirty = useMemo(
    () => (draft && saved ? JSON.stringify(draft) !== JSON.stringify(saved) : false),
    [draft, saved]
  )

  const patch = (mutate: Patch): void => {
    setDraft((current) => (current ? mutate(structuredClone(current)) : current))
  }

  const patchConfig = (mutate: (config: AppConfig) => void): void =>
    patch((current) => {
      mutate(current.config)
      return current
    })

  const patchSecrets = (mutate: (secrets: Secrets) => void): void =>
    patch((current) => {
      mutate(current.secrets)
      return current
    })

  const save = async (): Promise<void> => {
    if (!draft) {
      return
    }
    setBusy(true)
    try {
      const result = await bridge.config.save(draft)
      setDraft(result.bundle)
      setSaved(result.bundle)
      setNotice({
        text: result.pushWarnings.length > 0 ? t('settings.saved_with_warnings') : t('settings.saved'),
        severity: result.pushWarnings.length > 0 ? 'warning' : 'success'
      })
    } catch (error) {
      setNotice({ text: errorMessage(error), severity: 'error' })
    } finally {
      setBusy(false)
    }
  }

  const headerActions = useMemo(
    () => (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        {dirty ? (
          <Typography variant="caption" sx={{ color: colorVar('tertiary') }}>
            {t('settings.dirty')}
          </Typography>
        ) : null}
        <Button variant="text" onClick={() => void uploadBackground()} disabled={busy}>
          {t('settings.upload_background')}
        </Button>
        <Button variant="contained" onClick={() => void save()} disabled={busy || !dirty}>
          {t('common.save')}
        </Button>
      </Box>
    ),
    [busy, dirty, t]
  )
  useHeaderActions(headerActions)

  const uploadBackground = async (): Promise<void> => {
    setBusy(true)
    try {
      const result = await bridge.site.uploadBackground()
      setNotice({
        text: result.cancelled ? t('settings.background_cancelled') : t('settings.background_done'),
        severity: result.cancelled ? 'warning' : 'success'
      })
    } catch (error) {
      setNotice({ text: errorMessage(error), severity: 'error' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <PageScaffold>
      <StateBlock loading={loaded.loading} error={loaded.error} onRetry={loaded.reload}>
        {draft ? (
          <>
            <SectionCard collapsible title={t('settings.section.server')}>
              <FieldRow
                label={t('settings.base_url')}
                control={
                  <TextField
                    value={draft.config.server.base_url}
                    onChange={(event) =>
                      patchConfig((config) => {
                        config.server.base_url = event.target.value
                      })
                    }
                    fullWidth
                  />
                }
              />
              <FieldRow
                label={t('settings.api_key')}
                control={
                  <TextField
                    type="password"
                    value={draft.secrets.api_key}
                    onChange={(event) =>
                      patchSecrets((secrets) => {
                        secrets.api_key = event.target.value
                      })
                    }
                    fullWidth
                  />
                }
              />
              <FieldRow
                label={t('settings.github_token')}
                control={
                  <TextField
                    type="password"
                    value={draft.secrets.github_token}
                    onChange={(event) =>
                      patchSecrets((secrets) => {
                        secrets.github_token = event.target.value
                      })
                    }
                    fullWidth
                  />
                }
              />
              <FieldRow
                label={t('settings.github_login')}
                control={
                  <TextField
                    value={draft.secrets.github_login}
                    onChange={(event) =>
                      patchSecrets((secrets) => {
                        secrets.github_login = event.target.value
                      })
                    }
                    fullWidth
                  />
                }
              />
              <FieldRow
                label={t('settings.timeout')}
                control={
                  <SliderField
                    value={draft.config.server.timeout_seconds}
                    min={1}
                    max={120}
                    step={1}
                    suffix="s"
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.server.timeout_seconds = value
                      })
                    }
                  />
                }
              />
            </SectionCard>

            <SectionCard collapsible title={t('settings.section.push')} hint={t('settings.push_hint')}>
              <FieldRow
                label={t('settings.push_enabled')}
                control={
                  <SwitchField
                    checked={draft.config.push.enabled}
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.push.enabled = value
                      })
                    }
                  />
                }
              />
              <FieldRow
                label={t('settings.interval')}
                hint={t('settings.interval_hint')}
                control={
                  <SliderField
                    value={draft.config.push.interval_seconds}
                    min={5}
                    max={3600}
                    step={5}
                    suffix="s"
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.push.interval_seconds = value
                      })
                    }
                  />
                }
              />
            </SectionCard>

            <SectionCard collapsible title={t('settings.section.privacy')} hint={t('settings.privacy_hint')}>
              {(
                [
                  ['collect_screenshot', 'settings.collect_screenshot'],
                  ['collect_media', 'settings.collect_media'],
                  ['collect_system_load', 'settings.collect_system_load']
                ] as const
              ).map(([key, labelKey]) => (
                <FieldRow
                  key={key}
                  label={t(labelKey)}
                  control={
                    <SwitchField
                      checked={draft.config.privacy[key]}
                      onChange={(value) =>
                        patchConfig((config) => {
                          config.privacy[key] = value
                        })
                      }
                    />
                  }
                />
              ))}
            </SectionCard>

            <SectionCard collapsible title={t('settings.section.screenshot')} hint={t('settings.screenshot_hint')}>
              <FieldRow
                label={t('settings.blur')}
                control={
                  <SliderField
                    value={draft.config.screenshot.blur_radius}
                    min={0}
                    max={100}
                    step={0.5}
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.screenshot.blur_radius = value
                      })
                    }
                  />
                }
              />
              <FieldRow
                label={t('settings.scale')}
                control={
                  <SliderField
                    value={draft.config.screenshot.scale}
                    min={0.05}
                    max={1}
                    step={0.05}
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.screenshot.scale = value
                      })
                    }
                  />
                }
              />
              <FieldRow
                label={t('settings.quality')}
                control={
                  <SliderField
                    value={draft.config.screenshot.quality}
                    min={1}
                    max={100}
                    step={1}
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.screenshot.quality = value
                      })
                    }
                  />
                }
              />
            </SectionCard>

            <SectionCard collapsible title={t('settings.section.site')}>
              {(
                [
                  ['title', 'settings.site_title'],
                  ['tagline', 'settings.site_tagline'],
                  ['tags_title', 'settings.site_tags_title'],
                  ['icp_text', 'settings.site_icp_text'],
                  ['icp_keyword', 'settings.site_icp_keyword'],
                  ['github_owner', 'settings.site_github_owner'],
                  ['github_repo', 'settings.site_github_repo']
                ] as const
              ).map(([key, labelKey]) => (
                <FieldRow
                  key={key}
                  label={t(labelKey)}
                  control={
                    <TextField
                      value={draft.config.site[key]}
                      onChange={(event) =>
                        patchConfig((config) => {
                          config.site[key] = event.target.value
                        })
                      }
                      fullWidth
                    />
                  }
                />
              ))}
              <FieldRow
                label={t('settings.site_tags')}
                control={
                  <TokenField
                    values={draft.config.site.tags}
                    placeholder={t('settings.site_tags')}
                    onChange={(values) =>
                      patchConfig((config) => {
                        config.site.tags = values
                      })
                    }
                  />
                }
              />
              <FieldRow
                label={t('settings.site_show_heatmap')}
                control={
                  <SwitchField
                    checked={draft.config.site.show_heatmap}
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.site.show_heatmap = value
                      })
                    }
                  />
                }
              />
              <FieldRow
                label={t('settings.site_show_icp')}
                control={
                  <SwitchField
                    checked={draft.config.site.show_icp}
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.site.show_icp = value
                      })
                    }
                  />
                }
              />
            </SectionCard>

            <SectionCard collapsible title={t('settings.section.general')}>
              <FieldRow
                label={t('settings.autostart')}
                hint={bridge.app.platform === 'darwin' ? t('settings.autostart_dev') : undefined}
                control={
                  <SwitchField
                    checked={draft.config.autostart.enabled}
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.autostart.enabled = value
                      })
                    }
                  />
                }
              />
              <FieldRow
                label={t('settings.start_minimized')}
                control={
                  <SwitchField
                    checked={draft.config.ui.start_minimized}
                    onChange={(value) =>
                      patchConfig((config) => {
                        config.ui.start_minimized = value
                      })
                    }
                  />
                }
              />
              <FieldRow
                label={t('language.title')}
                control={
                  <TextField
                    select
                    value={draft.config.ui.language}
                    onChange={(event) => {
                      const next = event.target.value as Language
                      setLanguage(next)
                      patchConfig((config) => {
                        config.ui.language = next
                      })
                    }}
                    sx={{ minWidth: 200 }}
                  >
                    {LANGUAGES.map((item) => (
                      <MenuItem key={item.value} value={item.value}>
                        {t(item.labelKey)}
                      </MenuItem>
                    ))}
                  </TextField>
                }
              />
            </SectionCard>

            <SectionCard collapsible title={t('settings.section.about')}>
              <FieldRow
                label={t('settings.version')}
                control={
                  <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
                    {draft.clientVersion}
                  </Typography>
                }
              />
              <FieldRow
                label={t('settings.config_path')}
                control={
                  <Typography
                    variant="body2"
                    sx={{ color: colorVar('on-surface-variant'), wordBreak: 'break-all' }}
                  >
                    {draft.configPath}
                  </Typography>
                }
              />
              <FieldRow
                label="secrets"
                control={
                  <Typography
                    variant="body2"
                    sx={{ color: colorVar('on-surface-variant'), wordBreak: 'break-all' }}
                  >
                    {draft.secretsPath}
                  </Typography>
                }
              />
            </SectionCard>
          </>
        ) : null}
      </StateBlock>

      <Snackbar
        open={Boolean(notice)}
        autoHideDuration={4000}
        onClose={() => setNotice(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={notice?.severity ?? 'success'}
          variant="filled"
          onClose={() => setNotice(null)}
          sx={{ alignItems: 'center' }}
        >
          {notice?.text}
        </Alert>
      </Snackbar>
    </PageScaffold>
  )
}
