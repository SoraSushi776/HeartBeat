import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App'
import { MaterialYouProvider } from './theme/ThemeProvider'

const container = document.getElementById('root')
if (!container) {
  throw new Error('root container is missing')
}

createRoot(container).render(
  <StrictMode>
    <MaterialYouProvider>
      <App />
    </MaterialYouProvider>
  </StrictMode>
)
