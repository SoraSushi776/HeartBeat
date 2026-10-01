import type { ReactNode } from 'react'
import { useEffect } from 'react'
import Box from '@mui/material/Box'

import { AppTopBar } from './components/AppTopBar'
import { NavigationRail } from './components/NavigationRail'
import { DiagnosticsPage } from './pages/DiagnosticsPage'
import { PendingPage } from './pages/PendingPage'
import { SettingsPage } from './pages/SettingsPage'
import { useLanguage } from './i18n'
import { useShell } from './shell/store'
import { colorVar } from './theme/material-you'
import { bridge } from './utils/bridge'

export function App(): ReactNode {
  const page = useShell((state) => state.page)
  const setPage = useShell((state) => state.setPage)
  const setLanguage = useLanguage((state) => state.setLanguage)
  const isMac = bridge.app.platform === 'darwin'

  useEffect(() => {
    void bridge.config
      .load()
      .then((bundle) => setLanguage(bundle.config.ui.language))
      .catch(() => undefined)
  }, [setLanguage])

  return (
    <Box sx={{ display: 'flex', height: '100%', backgroundColor: colorVar('surface') }}>
      <NavigationRail active={page} onSelect={setPage} />
      <Box sx={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <AppTopBar page={page} isMac={isMac} />
        {page === 'settings' ? <SettingsPage /> : null}
        {page === 'diagnostics' ? <DiagnosticsPage /> : null}
        {page === 'diary' ? <PendingPage page="diary" hint="日记列表 + Markdown 编辑与预览" /> : null}
        {page === 'friends' ? <PendingPage page="friends" hint="友链列表 + 表单" /> : null}
        {page === 'messages' ? <PendingPage page="messages" hint="留言列表 + 封禁管理" /> : null}
      </Box>
    </Box>
  )
}
