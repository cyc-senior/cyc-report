// Capture screenshots of the running CYC app (cyc-monorepo) into figures/, using the
// Microsoft Edge / Chrome already installed, driven over the DevTools Protocol.
// No npm packages needed (Node 22+ for the global WebSocket).
//
// Usage (frontend on :3000 and backend on :4000 running):
//   node tools/capture_screens.mjs --config tools/screens.json --email you@example.com \
//        [--monorepo ../cyc-monorepo] [--only name1,name2] [--probe] [--browser <path to msedge/chrome>]
//
// Signs in as --email with `pnpm dev:url --email ...` (an existing user in the local DB,
// no Google needed); the sign-in link is never written to disk.
// --probe also prints each page's visible text and buttons, to find what to click.
//
// Config (JSON): { "baseUrl", "out", "viewport": {width,height,scale}, "vars": {...},
//   "beforeEach": "js run on every page right before the screenshot (e.g. hide dev overlays)",
//   "shots": [ { "name", "path" (may use {var}), "public": bool (shoot before sign-in),
//                "waitFor": "css selector" | "text:some text", "wait": ms,
//                "actions": [ {"click": "css"} | {"clickText": "text"} | {"eval": "js"} | {"wait": ms}
//                             | {"waitFor": "css|text:...|js:expr", "timeout": ms} | {"snap": "file name"}
//                             | {"mouse": [x, y]} (real click, CSS px) | {"type": "text"} | {"key": "Escape"} ],
//                "final": false (no screenshot at the end, e.g. when the actions snap),
//                "fullPage": bool, "clip": {x,y,width,height} } ] }
//   "snap" actions take screenshots mid-flow, e.g. while an AI job is running.
import { spawn, execFileSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => {
    if (a.startsWith('--')) acc.push([a.slice(2), all[i + 1] && !all[i + 1].startsWith('--') ? all[i + 1] : true])
    return acc
  }, []),
)
const config = JSON.parse(fs.readFileSync(args.config ?? 'tools/screens.json', 'utf8'))
const only = typeof args.only === 'string' ? new Set(args.only.split(',')) : null
const monorepo = path.resolve(args.monorepo ?? '../cyc-monorepo')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const fill = (s) => s.replace(/\{(\w+)\}/g, (_, k) => config.vars?.[k] ?? `{${k}}`)

function findBrowser() {
  if (typeof args.browser === 'string') return args.browser
  const candidates = [
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    path.join(os.homedir(), 'AppData/Local/Google/Chrome/Application/chrome.exe'),
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/microsoft-edge',
  ]
  const found = candidates.find((p) => fs.existsSync(p))
  if (!found) throw new Error('No Edge/Chrome found; pass --browser <path>')
  return found
}

function signInUrl(email) {
  const out = execFileSync('pnpm', ['--silent', 'dev:url', '--email', email], {
    cwd: monorepo, encoding: 'utf8', shell: process.platform === 'win32', stdio: ['ignore', 'pipe', 'inherit'],
  })
  const url = out.trim().split(/\r?\n/).pop()
  if (!url.startsWith('http')) throw new Error('dev:url did not print a URL')
  return url
}

class Cdp {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.pending = new Map(); this.listeners = []
    ws.addEventListener('message', (ev) => {
      const msg = JSON.parse(ev.data)
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id)
        this.pending.delete(msg.id)
        msg.error ? reject(new Error(`${msg.error.message}`)) : resolve(msg.result)
      } else if (msg.method) this.listeners.forEach((l) => l(msg))
    })
  }
  send(method, params = {}) {
    const id = ++this.id
    this.ws.send(JSON.stringify({ id, method, params }))
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }))
  }
  once(method, timeout = 30000) {
    return new Promise((resolve) => {
      const t = setTimeout(() => resolve(null), timeout)
      const l = (m) => { if (m.method === method) { clearTimeout(t); this.listeners = this.listeners.filter((x) => x !== l); resolve(m) } }
      this.listeners.push(l)
    })
  }
  async eval(expression) {
    const r = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? 'eval failed')
    return r.result.value
  }
}

async function goto(cdp, url) {
  const loaded = cdp.once('Page.loadEventFired')
  await cdp.send('Page.navigate', { url })
  await loaded
}

async function waitFor(cdp, what, timeout = 20000) {
  const expr = what.startsWith('text:')
    ? `document.body && document.body.innerText.includes(${JSON.stringify(what.slice(5))})`
    : what.startsWith('js:')
      ? `!!(${what.slice(3)})`
      : `!!document.querySelector(${JSON.stringify(what)})`
  const end = Date.now() + timeout
  while (Date.now() < end) {
    if (await cdp.eval(expr).catch(() => false)) return true
    await sleep(300)
  }
  console.warn(`  ! timed out waiting for ${what}`)
  return false
}

async function capture(cdp, file, shot = {}) {
  if (config.beforeEach) await cdp.eval(config.beforeEach).catch((e) => console.warn(`  ! beforeEach: ${e.message}`))
  await sleep(200)
  const params = { format: 'png', captureBeyondViewport: !!shot.fullPage }
  if (shot.clip) params.clip = { ...shot.clip, scale: 1 }
  else if (shot.fullPage) {
    const { contentSize } = await cdp.send('Page.getLayoutMetrics')
    params.clip = { x: 0, y: 0, width: config.viewport.width, height: Math.ceil(contentSize.height), scale: 1 }
  }
  const { data } = await cdp.send('Page.captureScreenshot', params)
  fs.writeFileSync(file, Buffer.from(data, 'base64'))
  console.log(`  saved ${file}  (${new Date().toLocaleTimeString()})`)
}

let OUT_DIR = '.'
async function act(cdp, a) {
  if (a.waitFor) return waitFor(cdp, a.waitFor, a.timeout ?? 20000)
  if (a.snap) return capture(cdp, path.join(OUT_DIR, `${a.snap}.png`))
  if (a.wait) return sleep(a.wait)
  if (a.eval) return cdp.eval(a.eval)
  if (a.mouse) {
    const [x, y] = a.mouse
    for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased'])
      await cdp.send('Input.dispatchMouseEvent', { type, x, y, button: 'left', clickCount: 1 })
    return sleep(a.after ?? 600)
  }
  if (a.type) { await cdp.send('Input.insertText', { text: a.type }); return sleep(a.after ?? 300) }
  if (a.key) {
    await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: a.key })
    await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: a.key })
    return sleep(a.after ?? 300)
  }
  const find = a.click
    ? `document.querySelector(${JSON.stringify(a.click)})`
    : `[...document.querySelectorAll('button,a,[role=button],[role=tab],[role=menuitem]')].find(e => e.innerText.trim().includes(${JSON.stringify(a.clickText)}))`
  const ok = await cdp.eval(`(() => { const e = ${find}; if (!e) return false; e.scrollIntoView({block:'center'}); e.click(); return true })()`)
  if (!ok) console.warn(`  ! nothing to click for ${JSON.stringify(a)}`)
  await sleep(a.after ?? 600)
}

async function probe(cdp) {
  const info = await cdp.eval(`({ url: location.href, extra: window.__probe,
    text: document.body.innerText.slice(0, 1500),
    buttons: [...document.querySelectorAll('button,a,[role=button],[role=tab]')].map(e => e.innerText.trim().replace(/\\s+/g,' ')).filter(Boolean).slice(0, 60) })`)
  if (info.extra) console.log(`  probe: ${info.extra}`)
  console.log(`  url: ${info.url}\n  buttons: ${JSON.stringify(info.buttons)}\n  text: ${info.text.replace(/\n+/g, ' | ')}`)
}

async function shoot(cdp, shot, outDir) {
  const url = /^https?:/.test(shot.path) ? fill(shot.path) : config.baseUrl.replace(/\/$/, '') + fill(shot.path)
  console.log(`- ${shot.name}: ${url}`)
  await goto(cdp, url)
  if (shot.waitFor) await waitFor(cdp, shot.waitFor)
  await sleep(shot.wait ?? 1500)
  for (const a of shot.actions ?? []) await act(cdp, a)
  if (args.probe) await probe(cdp)
  if (shot.final === false) return
  await capture(cdp, path.join(outDir, `${shot.name}.png`), shot)
}

async function main() {
  if (!args.email) throw new Error('pass --email <user in the local DB>')
  const outDir = path.resolve(config.out); fs.mkdirSync(outDir, { recursive: true })
  OUT_DIR = outDir
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'cyc-capture-'))
  const port = 9300 + Math.floor(Math.random() * 500)
  const vp = config.viewport ?? { width: 1440, height: 900, scale: 2 }
  const browser = spawn(findBrowser(), [
    '--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', `--window-size=${vp.width},${vp.height}`, 'about:blank',
  ], { stdio: 'ignore' })
  try {
    let target
    for (let i = 0; i < 50 && !target; i++) {
      await sleep(200)
      target = await fetch(`http://127.0.0.1:${port}/json/list`).then((r) => r.json()).then((l) => l.find((t) => t.type === 'page')).catch(() => null)
    }
    if (!target) throw new Error('browser did not start')
    const ws = new WebSocket(target.webSocketDebuggerUrl)
    await new Promise((r, j) => { ws.addEventListener('open', r); ws.addEventListener('error', j) })
    const cdp = new Cdp(ws)
    await cdp.send('Page.enable'); await cdp.send('Runtime.enable')
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: vp.width, height: vp.height, deviceScaleFactor: vp.scale ?? 2, mobile: false })

    const shots = config.shots.filter((s) => !only || only.has(s.name))
    for (const s of shots.filter((s) => s.public)) await shoot(cdp, s, outDir)

    const priv = shots.filter((s) => !s.public)
    if (priv.length) {
      console.log(`- signing in as ${args.email}`)
      await goto(cdp, signInUrl(args.email))
      const end = Date.now() + 20000
      while (Date.now() < end && (await cdp.eval('location.pathname').catch(() => '')).startsWith('/auth')) await sleep(300)
      console.log(`  now at ${await cdp.eval('location.pathname')}`)
      for (const s of priv) await shoot(cdp, s, outDir)
    }
    ws.close()
  } finally {
    browser.kill()
    await sleep(500)
    fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5 })
  }
}

main().catch((e) => { console.error(e.message); process.exit(1) })
