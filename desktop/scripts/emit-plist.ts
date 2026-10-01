import { writeFileSync } from 'node:fs'

import { buildPlist } from '../src/main/app/autostart/macos'

const target = process.argv[2] ?? '/tmp/heartbeat-plist-check.plist'
writeFileSync(
  target,
  buildPlist({
    command: '/Applications/HeartBeat.app/Contents/MacOS/HeartBeat',
    arguments: ['--minimized'],
    workingDirectory: '/Applications'
  }),
  'utf8'
)
process.stdout.write(`wrote ${target}\n`)
