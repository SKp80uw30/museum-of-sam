// Minimal service worker — exists mainly to satisfy PWA installability
// (needs a registered SW with a fetch handler) so the app can be added to
// the home screen and launched fullscreen, no browser chrome.
//
// Only the small, rarely-changing app shell is cached. glTF exports and
// artwork photos are NOT cached here — those change often (re-exports,
// new photos) and CLAUDE.md already documents cache-busting query strings
// on the JS modules; adding a second caching layer on top of that would
// just reintroduce the staleness problem it was designed to avoid.
const CACHE_NAME = 'museum-of-sam-shell-v11-tilt-fix'
const SHELL_URLS = [
  './',
  './index.html',
  './manifest.json',
  './home.html',
  './home.css',
  './home.js',
  './home-journey.mjs',
  './living-home.js',
  './garden-people.js',
  './garden-characters.mjs',
  './party-letters.js',
  './orientation-gate.js',
  './forest-sky.js',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
  './icons/apple-touch-icon.png',
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS)).then(() => self.skipWaiting())
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)
  if (event.request.method !== 'GET' || url.origin !== location.origin) return
  const isShellAsset = SHELL_URLS.some((shellUrl) => url.pathname.endsWith(shellUrl.replace('./', '/')))
  if (!isShellAsset) return

  // index.html (and '/') carries all of the app's actual behavior and
  // changes on every deploy — unlike the icons/manifest below, it must
  // never be served stale-first. Scene switching also appends a
  // `?scene=...` query string to this same URL, and caches.match keys on
  // the full URL by default, so without ignoreSearch every distinct scene
  // link would pin its own independently-stale cached copy (this is what
  // broke a freshly-deployed feature from ever appearing until a manual
  // cache clear). Go to the network first always; only fall back to
  // whatever's cached if the network is unreachable (offline PWA use).
  const isHtmlShell = url.pathname === '/' || url.pathname.endsWith('/index.html') || /\/(?:home(?:-journey)?|living-home|garden-people|garden-characters|party-letters|orientation-gate)\.(?:html|css|js|mjs)$/.test(url.pathname)
  if (isHtmlShell) {
    event.respondWith(
      fetch(event.request).then((response) => {
        if (response.ok) caches.open(CACHE_NAME).then((cache) => cache.put(event.request, response.clone()))
        return response
      }).catch(() => caches.match(event.request, { ignoreSearch: true }))
    )
    return
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request).then((response) => {
        if (response.ok) caches.open(CACHE_NAME).then((cache) => cache.put(event.request, response.clone()))
        return response
      }).catch(() => cached)
      return cached || network
    })
  )
})
