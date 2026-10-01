import { execFile } from 'node:child_process'

import { logger } from './logger'
import { currentPlatform } from './adapters/platform'
import type { Platform } from './protocol'

function appleString(text: string): string {
  return `"${text.replaceAll('\\', '\\\\').replaceAll('"', '\\"')}"`
}

function powerShellQuote(text: string): string {
  return `'${text.replaceAll("'", "''")}'`
}

function xmlEscape(text: string): string {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

export function macosCommand(title: string, message: string): string[] {
  return ['osascript', '-e', `display notification ${appleString(message)} with title ${appleString(title)}`]
}

export function windowsCommand(title: string, message: string): string[] {
  const toast = [
    '<toast><visual><binding template="ToastText02">',
    `<text id="1">${xmlEscape(title)}</text>`,
    `<text id="2">${xmlEscape(message)}</text>`,
    '</binding></visual></toast>'
  ].join('')
  const script = [
    '[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;',
    '[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null;',
    '$xml = New-Object Windows.Data.Xml.Dom.XmlDocument;',
    `$xml.LoadXml(${powerShellQuote(toast)});`,
    '$toast = New-Object Windows.UI.Notifications.ToastNotification($xml);',
    `[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(${powerShellQuote('HeartBeat')}).Show($toast)`
  ].join(' ')
  return ['powershell', '-NoProfile', '-NonInteractive', '-Command', script]
}

export function linuxCommand(title: string, message: string): string[] {
  return ['notify-send', '--app-name=HeartBeat', title, message]
}

type CommandBuilder = (title: string, message: string) => string[]

const BUILDERS: Record<Platform, CommandBuilder> = {
  macos: macosCommand,
  windows: windowsCommand,
  linux: linuxCommand
}

export function notificationCommand(title: string, message: string): string[] {
  return BUILDERS[currentPlatform()](title, message)
}

export function showNotification(title: string, message: string): void {
  const [command, ...args] = notificationCommand(title, message)
  execFile(command, args, () => {
    logger.debug(`Notification sent: ${title}`)
  })
}
