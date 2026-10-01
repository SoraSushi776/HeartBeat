import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import { enUS } from './en-US'
import { zhCN, type Dictionary, type TranslationKey } from './zh-CN'

export type Language = 'zh-CN' | 'en-US'

export const LANGUAGES: { value: Language; labelKey: TranslationKey }[] = [
  { value: 'zh-CN', labelKey: 'language.zh' },
  { value: 'en-US', labelKey: 'language.en' }
]

const DICTIONARIES: Record<Language, Dictionary> = {
  'zh-CN': zhCN,
  'en-US': enUS
}

interface LanguageState {
  language: Language
  setLanguage: (language: Language) => void
}

export const useLanguage = create<LanguageState>()(
  persist(
    (set) => ({ language: 'zh-CN', setLanguage: (language) => set({ language }) }),
    { name: 'heartbeat-language' }
  )
)

export function useTranslate(): (key: TranslationKey, params?: Record<string, string | number>) => string {
  const language = useLanguage((state) => state.language)
  const dictionary = DICTIONARIES[language]
  return (key, params) => {
    const template = dictionary[key] ?? key
    if (!params) {
      return template
    }
    return Object.entries(params).reduce(
      (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
      template
    )
  }
}

export type { Dictionary, TranslationKey }
