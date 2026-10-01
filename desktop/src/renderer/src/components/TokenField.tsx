import type { ReactNode } from 'react'
import { useState } from 'react'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import IconButton from '@mui/material/IconButton'
import TextField from '@mui/material/TextField'
import AddIcon from '@mui/icons-material/Add'
import CloseIcon from '@mui/icons-material/Close'

import { useTranslate } from '../i18n'

interface TokenFieldProps {
  values: string[]
  placeholder: string
  onChange: (values: string[]) => void
}

export function TokenField({ values, placeholder, onChange }: TokenFieldProps): ReactNode {
  const t = useTranslate()
  const [draft, setDraft] = useState('')

  const commit = (): void => {
    const entries = draft
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0 && !values.includes(item))
    if (entries.length > 0) {
      onChange([...values, ...entries])
    }
    setDraft('')
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, width: '100%' }}>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
        <TextField
          value={draft}
          placeholder={placeholder}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault()
              commit()
            }
          }}
          sx={{ flexGrow: 1 }}
        />
        <IconButton onClick={commit} aria-label={t('common.add')}>
          <AddIcon fontSize="small" />
        </IconButton>
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
        {values.map((value) => (
          <Chip
            key={value}
            label={value}
            onDelete={() => onChange(values.filter((item) => item !== value))}
            deleteIcon={<CloseIcon fontSize="small" />}
          />
        ))}
      </Box>
    </Box>
  )
}
