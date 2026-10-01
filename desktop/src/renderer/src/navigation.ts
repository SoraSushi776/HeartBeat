import type { SvgIconComponent } from '@mui/icons-material'
import AdminPanelSettingsOutlinedIcon from '@mui/icons-material/AdminPanelSettingsOutlined'
import BookOutlinedIcon from '@mui/icons-material/BookOutlined'
import ExploreOutlinedIcon from '@mui/icons-material/ExploreOutlined'
import TuneOutlinedIcon from '@mui/icons-material/TuneOutlined'
import TravelExploreOutlinedIcon from '@mui/icons-material/TravelExploreOutlined'

import type { TranslationKey } from './i18n'

export type PageId = 'settings' | 'diagnostics' | 'diary' | 'friends' | 'messages'

export interface Destination {
  id: PageId
  labelKey: TranslationKey
  descriptionKey: TranslationKey
  icon: SvgIconComponent
}

export const DESTINATIONS: Destination[] = [
  {
    id: 'settings',
    labelKey: 'nav.settings',
    descriptionKey: 'page.settings.description',
    icon: TuneOutlinedIcon
  },
  {
    id: 'diagnostics',
    labelKey: 'nav.diagnostics',
    descriptionKey: 'page.diagnostics.description',
    icon: ExploreOutlinedIcon
  },
  {
    id: 'diary',
    labelKey: 'nav.diary',
    descriptionKey: 'page.diary.description',
    icon: BookOutlinedIcon
  },
  {
    id: 'friends',
    labelKey: 'nav.friends',
    descriptionKey: 'page.friends.description',
    icon: TravelExploreOutlinedIcon
  },
  {
    id: 'messages',
    labelKey: 'nav.messages',
    descriptionKey: 'page.messages.description',
    icon: AdminPanelSettingsOutlinedIcon
  }
]
