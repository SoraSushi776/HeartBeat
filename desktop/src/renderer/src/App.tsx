import type { ReactNode } from 'react'
import Box from '@mui/material/Box'

import { AppTopBar } from './components/AppTopBar'
import { NavigationRail } from './components/NavigationRail'
import { colorVar } from './theme/material-you'
import { useShell } from './shell/store'
import { PendingPage } from './pages/PendingPage'

export function App(): ReactNode {
  const page = useShell((state) => state.page)
  const setPage = useShell((state) => state.setPage)
  const isMac = window.heartbeat?.app.platform === 'darwin'

  return (
    <Box sx={{ display: 'flex', height: '100%', backgroundColor: colorVar('surface') }}>
      <NavigationRail active={page} onSelect={setPage} />
      <Box sx={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <AppTopBar page={page} isMac={isMac} />
        {page === 'settings' ? <PendingPage page="settings" hint="服务端 / 推送 / 隐私 / 截图 / 站点文案" /> : null}
        {page === 'diagnostics' ? <PendingPage page="diagnostics" hint="音乐 / 进程 / 系统负载 / 推送结果" /> : null}
        {page === 'diary' ? <PendingPage page="diary" hint="日记列表 + Markdown 编辑与预览" /> : null}
        {page === 'friends' ? <PendingPage page="friends" hint="友链列表 + 表单" /> : null}
        {page === 'messages' ? <PendingPage page="messages" hint="留言列表 + 封禁管理" /> : null}
      </Box>
    </Box>
  )
}
