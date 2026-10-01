import type { ReactNode } from 'react'
import Box from '@mui/material/Box'
import FormControlLabel from '@mui/material/FormControlLabel'
import Slider from '@mui/material/Slider'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'

import { colorVar } from '../theme/material-you'

interface SliderFieldProps {
  value: number
  min: number
  max: number
  step: number
  suffix?: string
  onChange: (value: number) => void
}

export function SliderField({ value, min, max, step, suffix, onChange }: SliderFieldProps): ReactNode {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
      <Slider
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(_event, next) => onChange(Array.isArray(next) ? next[0] : next)}
        sx={{ flexGrow: 1, maxWidth: 320 }}
      />
      <Typography
        variant="body2"
        sx={{ color: colorVar('on-surface-variant'), minWidth: 56, textAlign: 'right' }}
      >
        {value}
        {suffix ?? ''}
      </Typography>
      <TextField
        type="number"
        value={value}
        onChange={(event) => {
          const parsed = Number(event.target.value)
          if (Number.isFinite(parsed)) {
            onChange(Math.min(Math.max(parsed, min), max))
          }
        }}
        slotProps={{ htmlInput: { min, max, step } }}
        sx={{ width: 104 }}
      />
    </Box>
  )
}

interface SwitchFieldProps {
  checked: boolean
  onChange: (value: boolean) => void
  label?: string
}

export function SwitchField({ checked, onChange, label }: SwitchFieldProps): ReactNode {
  return (
    <FormControlLabel
      control={<Switch checked={checked} onChange={(event) => onChange(event.target.checked)} />}
      label={label ?? ''}
    />
  )
}
