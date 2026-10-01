import type { ReactNode } from 'react'
import Box from '@mui/material/Box'

interface PageScaffoldProps {
  children?: ReactNode
  fill?: boolean
}

export function PageScaffold({ children, fill = false }: PageScaffoldProps): ReactNode {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, minHeight: 0, px: 3, pb: 2 }}>
      {fill ? (
        <Box sx={{ flexGrow: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>{children}</Box>
      ) : (
        <Box
          sx={{
            flexGrow: 1,
            minHeight: 0,
            overflowY: 'auto',
            overflowX: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            '& > *': { flexShrink: 0 }
          }}
        >
          {children}
        </Box>
      )}
    </Box>
  )
}
