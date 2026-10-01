import type { ReactNode } from 'react'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Typography from '@mui/material/Typography'

import { useTranslate } from '../i18n'
import { DESTINATIONS, type PageId } from '../navigation'
import { PageScaffold } from '../components/PageScaffold'

export function PendingPage({ page, hint }: { page: PageId; hint: string }): ReactNode {
  const t = useTranslate()
  const destination = DESTINATIONS.find((item) => item.id === page)

  return (
    <PageScaffold page={page} title={destination ? t(destination.labelKey) : ''}>
      <Card>
        <CardContent>
          <Typography variant="body1">{hint}</Typography>
        </CardContent>
      </Card>
      <Box sx={{ flexGrow: 1 }} />
    </PageScaffold>
  )
}
