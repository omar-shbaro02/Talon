import { spawn } from 'node:child_process'
import { dirname, resolve } from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const isWindows = process.platform === 'win32'
const npmCommand = isWindows ? 'npm.cmd' : 'npm'
const pythonCommand = process.env.PYTHON || 'python'
const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const backendEnv = {
  ...process.env,
  DATABASE_URL: process.env.DATABASE_URL || 'sqlite:///./talon_local.db',
}

const processes = [
  {
    name: 'backend',
    color: '\x1b[36m',
    command: pythonCommand,
    args: ['-m', 'uvicorn', 'app.main:app', '--reload', '--port', '8000'],
    cwd: resolve(rootDir, 'backend'),
    env: backendEnv,
  },
  {
    name: 'frontend',
    color: '\x1b[35m',
    command: npmCommand,
    args: ['run', 'dev'],
    cwd: resolve(rootDir, 'frontend'),
    env: process.env,
  },
]

const reset = '\x1b[0m'
const children = new Set()
let shuttingDown = false

function prefixLines(source, name, color) {
  source.on('data', (chunk) => {
    chunk
      .toString()
      .split(/\r?\n/)
      .filter(Boolean)
      .forEach((line) => {
        console.log(`${color}[${name}]${reset} ${line}`)
      })
  })
}

function stopAll(exitCode = 0) {
  if (shuttingDown) return
  shuttingDown = true

  for (const child of children) {
    if (!child.killed) {
      child.kill(isWindows ? undefined : 'SIGTERM')
    }
  }

  setTimeout(() => process.exit(exitCode), 300)
}

for (const proc of processes) {
  const child = spawn(proc.command, proc.args, {
    cwd: proc.cwd,
    env: proc.env,
    shell: isWindows,
    windowsHide: false,
  })

  children.add(child)
  prefixLines(child.stdout, proc.name, proc.color)
  prefixLines(child.stderr, proc.name, proc.color)

  child.on('exit', (code) => {
    children.delete(child)
    if (!shuttingDown && code !== 0) {
      console.error(`${proc.color}[${proc.name}]${reset} exited with code ${code}`)
      stopAll(code ?? 1)
    }
  })

  child.on('error', (error) => {
    console.error(`${proc.color}[${proc.name}]${reset} failed to start: ${error.message}`)
    stopAll(1)
  })
}

process.on('SIGINT', () => stopAll(0))
process.on('SIGTERM', () => stopAll(0))
