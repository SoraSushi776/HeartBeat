import type { Language } from './config/schema'

export const mainStrings = {
  'zh-CN': {
    'menu.open': '打开设置',
    'menu.quit': '退出',
    'menu.status': '推送状态',
    'menu.status.on': '推送已开启',
    'menu.status.off': '推送已关闭',
    'notify.message.title': '新留言',
    'notify.message.body': '收到一条新留言'
  },
  'en-US': {
    'menu.open': 'Open Dashboard',
    'menu.quit': 'Quit',
    'menu.status': 'Push status',
    'menu.status.on': 'Push enabled',
    'menu.status.off': 'Push disabled',
    'notify.message.title': 'New message',
    'notify.message.body': 'A new guestbook message arrived'
  }
} as const

export type MainStringKey = keyof (typeof mainStrings)['zh-CN']

export function translate(language: Language, key: MainStringKey): string {
  return mainStrings[language][key]
}

export function translator(language: Language): (key: MainStringKey) => string {
  return (key) => translate(language, key)
}
