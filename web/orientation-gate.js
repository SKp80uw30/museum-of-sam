// ── Landscape-only gate for phones and tablets ──────────────────────────
// Both the birthday homepage and the museum itself are wide, walk-through
// experiences: portrait squeezes the garden panorama and the hallway view
// into an unusable letterbox, and on iPad the page visibly re-flows every
// time the device is turned. So on any touch device we (a) ask the browser
// to lock to landscape where that's allowed, and (b) cover the page with a
// "turn me sideways" gate whenever it's portrait anyway.
//
// (b) is not a fallback for the rare case — it is the main mechanism. Only
// Chrome/Android honours screen.orientation.lock(), and only while the page
// is fullscreen; iOS Safari has no lock API at all, which is exactly the
// iPad case this exists for. Loaded as a plain (non-module) script from
// both home.html and index.html, and self-contained so neither page needs
// matching markup or CSS.
(function () {
  // ?orientation=any turns the gate off (desktop review links, debugging);
  // ?orientation=force turns it on regardless of device, so the portrait
  // screen can be checked from a desktop browser.
  const override = new URLSearchParams(location.search).get('orientation')
  if (override === 'any') return

  // Coarse pointer alone would also catch touch-screen laptops and kiosk
  // displays, which can't rotate and would be gated forever on a portrait
  // monitor; requiring a real touch digitiser as well keeps this to phones
  // and tablets.
  const isHandheld = matchMedia('(pointer: coarse)').matches &&
    ((navigator.maxTouchPoints || 0) > 0 || 'ontouchstart' in window)
  if (!isHandheld && override !== 'force') return

  document.documentElement.classList.add('force-landscape')

  const style = document.createElement('style')
  style.textContent = `
  #orientation-gate { display: none; }
  @media (orientation: portrait) {
    html.force-landscape #orientation-gate {
      position: fixed; inset: 0; z-index: 2147483647;
      display: flex; align-items: center; justify-content: center;
      padding: 28px; text-align: center;
      background: #07161d; color: #f2e9d6;
      font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
      -webkit-user-select: none; user-select: none; touch-action: none;
    }
    html.force-landscape body { overflow: hidden !important; }
  }
  #orientation-gate .og-card { max-width: 340px; }
  #orientation-gate h2 {
    font: 400 26px/1.2 Georgia, 'Times New Roman', serif;
    letter-spacing: -0.02em; margin: 22px 0 10px;
  }
  #orientation-gate p { margin: 0 0 8px; font-size: 13px; line-height: 1.6; opacity: 0.8; }
  #orientation-gate .og-note { font-size: 11px; opacity: 0.55; margin-top: 16px; }
  #orientation-gate .og-phone {
    width: 62px; height: 96px; margin: 0 auto; border-radius: 12px;
    border: 2px solid #d8b984; position: relative;
    animation: og-turn 2.8s ease-in-out infinite;
  }
  #orientation-gate .og-phone::after {
    content: ''; position: absolute; left: 50%; bottom: 6px; width: 20px; height: 2px;
    margin-left: -10px; border-radius: 2px; background: #d8b984; opacity: 0.6;
  }
  @keyframes og-turn {
    0%, 32% { transform: rotate(0deg); }
    62%, 100% { transform: rotate(-90deg); }
  }
  @media (prefers-reduced-motion: reduce) {
    #orientation-gate .og-phone { animation: none; transform: rotate(-90deg); }
  }`
  document.head.appendChild(style)

  // screen.orientation.lock() rejects unless the document is fullscreen (and
  // throws outright where it isn't implemented), so every call is best-effort
  // and re-tried whenever fullscreen state changes or the device is turned.
  function tryLock () {
    const orientation = screen.orientation
    if (!orientation || typeof orientation.lock !== 'function') return
    try { orientation.lock('landscape').catch(() => {}) } catch {}
  }
  tryLock()
  document.addEventListener('fullscreenchange', tryLock)
  document.addEventListener('webkitfullscreenchange', tryLock)
  window.addEventListener('orientationchange', tryLock)
  // A user gesture is what unlocks fullscreen (and therefore the lock) in the
  // first place — the museum requests fullscreen on the tap that starts the
  // walk, so re-try just after any tap rather than only at load.
  window.addEventListener('pointerdown', () => setTimeout(tryLock, 0), { passive: true })

  function mount () {
    if (document.getElementById('orientation-gate')) return
    const gate = document.createElement('div')
    gate.id = 'orientation-gate'
    gate.setAttribute('role', 'alertdialog')
    gate.setAttribute('aria-live', 'assertive')
    gate.innerHTML = `<div class="og-card">
      <div class="og-phone" aria-hidden="true"></div>
      <h2>Turn your device sideways</h2>
      <p>The Museum of Sam is built wide — it only opens in landscape.</p>
      <p class="og-note">If the screen won’t turn, switch off Rotation Lock in Control Centre first.</p>
    </div>`
    document.body.appendChild(gate)
  }
  if (document.body) mount()
  else document.addEventListener('DOMContentLoaded', mount)
})()
