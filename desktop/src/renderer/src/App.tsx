import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import Box from '@mui/material/Box'

import { AppTopBar } from './components/AppTopBar'
import { NavigationRail } from './components/NavigationRail'
import { SetupWizard } from './components/SetupWizard'
import { DiaryPage } from './pages/DiaryPage'
import { DiagnosticsPage } from './pages/DiagnosticsPage'
import { FriendsPage } from './pages/FriendsPage'
import { MessagesPage } from './pages/MessagesPage'
import { SettingsPage } from './pages/SettingsPage'
import { useLanguage } from './i18n'
import { useShell } from './shell/store'
import { colorVar } from './theme/material-you'
import { bridge } from './utils/bridge'
import type { ConfigBundle } from '@shared/ipc'

export function App(): ReactNode {
  const page = useShell((state) => state.page)
  const setPage = useShell((state) => state.setPage)
  const setLanguage = useLanguage((state) => state.setLanguage)
  const [bundle, setBundle] = useState<ConfigBundle | null>(null)
  const [wizardOpen, setWizardOpen] = useState(false)

  useEffect(() => {
    void bridge.config
      .load()
      .then((loaded) => {
        setBundle(loaded)
        setLanguage(loaded.config.ui.language)
        setWizardOpen(!loaded.config.setup_completed)
      })
      .catch(() => undefined)
  }, [setLanguage])

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', backgroundColor: colorVar('surface') }}>
      <NavigationRail active={page} onSelect={setPage} />
      <Box sx={{ flexGrow: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        <AppTopBar page={page} />
        {page === 'settings' ? <SettingsPage /> : null}
        {page === 'diagnostics' ? <DiagnosticsPage /> : null}
        {page === 'diary' ? <DiaryPage /> : null}
        {page === 'friends' ? <FriendsPage /> : null}
        {page === 'messages' ? <MessagesPage /> : null}
      </Box>
      {bundle ? (
        <SetupWizard
          open={wizardOpen}
          bundle={bundle}
          onFinished={(next) => {
            setBundle(next)
            setWizardOpen(false)
          }}
        />
      ) : null}
    </Box>
  )
}
