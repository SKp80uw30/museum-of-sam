// The PARTY letter puzzle.
//
// Five tiles (P A R T Y) start shuffled and scattered; five empty boxes sit
// along the bottom-right. Getting a letter into its own box turns that box
// green and plays one twenty-second window of `video/el-nay-partay.mp4`:
// P→0-20s, A→20-40s, R→40-60s, T→60-80s, Y→80s straight through to the end,
// because the fifth correct letter is also the finale: it calls onSolved(),
// which is where home.js takes over and runs the existing nightclub lights
// over the top of the closing forty seconds.
//
// One <video> element does all six windows — the file streams with its moov
// atom up front (`-movflags +faststart`), so seeking to 80s costs a range
// request, not a download of the whole two minutes. `stopAt` is what turns a
// continuous file into segments: a timeupdate handler pauses at the window's
// end, and is simply left null for the windows meant to run on.
const WORD = 'PARTY'
// One twenty-second window per letter, as [start, pause-at].
const SEGMENTS = [[0, 20], [20, 40], [40, 60], [60, 80], [80, 100]]
// The fifth letter is the finale, so it does not stop at 100: it opens its own
// window and runs straight on through the closing 100-120s in one take.
const FINALE = [SEGMENTS[4][0], null]
// Desktop scatter, in viewport percentages. These hug the left and right
// margins on purpose: the welcome card owns the top centre, the four museum
// doors own the bottom centre, and the garden pills own the bottom left.
const SPOTS = [[4, 27], [91, 24], [7, 47], [92, 45], [4, 67]]

export function createPartyGame({ onMessage = () => {}, onSolved = () => {} } = {}) {
 const game = document.querySelector('#party-game')
 const lettersHost = document.querySelector('#party-letters')
 const slotsHost = document.querySelector('#party-slots')
 const toggle = document.querySelector('#party-toggle')
 const panel = document.querySelector('#party-video')
 const video = document.querySelector('#party-video-el')
 const wholeButton = panel.querySelector('[data-pv=whole]')
 if (!game || !video) return null

 let picked = null, drag = null, solved = 0, stopAt = null

 // --- the video -----------------------------------------------------------
 video.addEventListener('timeupdate', () => { if (stopAt != null && video.currentTime >= stopAt) { video.pause(); stopAt = null } })
 function openPanel() { panel.hidden = false; document.body.classList.add('party-video-open') }
 function closePanel() { video.pause(); stopAt = null; panel.hidden = true; panel.classList.remove('expanded'); document.body.classList.remove('party-video-open') }
 function play([start, end]) {
  openPanel()
  stopAt = end
  const go = () => {
   video.currentTime = start
   // The placement click is the user gesture, so sound is normally allowed;
   // if a browser refuses anyway, fall back to muted rather than silently
   // not playing at all.
   video.play().catch(() => { video.muted = true; video.play().catch(() => {}); onMessage('Tap the video’s speaker to turn the sound on.') })
  }
  if (video.readyState >= 1) go(); else video.addEventListener('loadedmetadata', go, { once: true })
 }
 panel.querySelector('[data-pv=close]').addEventListener('click', closePanel)
 panel.querySelector('[data-pv=size]').addEventListener('click', event => {
  const big = panel.classList.toggle('expanded')
  event.currentTarget.setAttribute('aria-label', big ? 'Make the video smaller' : 'Make the video bigger')
  event.currentTarget.textContent = big ? '⤡' : '⤢'
 })
 wholeButton.addEventListener('click', () => play([0, null]))

 // --- tiles and boxes -----------------------------------------------------
 function deselect() { picked?.classList.remove('picked'); picked?.setAttribute('aria-pressed', 'false'); picked = null; game.classList.remove('picking') }
 function pickUp(tile) {
  if (picked === tile) { deselect(); return }
  deselect(); picked = tile; tile.classList.add('picked'); tile.setAttribute('aria-pressed', 'true'); game.classList.add('picking')
 }
 function place(slot) {
  const want = Number(slot.dataset.index)
  if (slot.classList.contains('filled')) { play(solved === WORD.length && want === WORD.length - 1 ? FINALE : SEGMENTS[want]); return }   // replay a letter you've already earned
  if (!picked) { onMessage('Pick up a letter first, then choose a box.'); return }
  if (want !== Number(picked.dataset.index)) {
   slot.classList.add('wrong'); setTimeout(() => slot.classList.remove('wrong'), 620)
   onMessage(`Not that box — ${picked.textContent} belongs somewhere else in PARTY.`)
   return
  }
  const tile = picked; deselect()
  tile.disabled = true; tile.classList.add('placed'); tile.removeAttribute('aria-pressed')
  slot.append(tile); slot.classList.add('filled')
  slot.setAttribute('aria-label', `Box ${want + 1}: ${tile.textContent}, correct. Play this part again.`)
  solved += 1
  if (solved < WORD.length) {
   play(SEGMENTS[want])
   onMessage(`${tile.textContent} is in! Playing ${SEGMENTS[want][0]}–${SEGMENTS[want][1]} seconds.`)
  } else {
   slotsHost.classList.add('complete')
   wholeButton.hidden = false
   play(FINALE)
   onMessage('🎉 P-A-R-T-Y! The last forty seconds, all in one go — lights on.')
   onSolved()
  }
 }

 // Dragging and tapping are deliberately split: the pointer events only ever
 // handle a real drag (7px of travel or more), and a plain tap is left to fall
 // through to the tile's own click event. That keeps one code path for mouse
 // taps, touch taps, Enter/Space on the focused button and assistive tech,
 // instead of re-implementing activation on pointerup and missing three of
 // those four. `swallowClick` covers the click a finished drag still emits.
 let swallowClick = false
 function startDrag(event, tile) {
  if (event.button > 0) return
  swallowClick = false
  drag = { tile, id: event.pointerId, x: event.clientX, y: event.clientY, moved: false }
  tile.setPointerCapture?.(event.pointerId)
 }
 function moveDrag(event) {
  if (!drag || event.pointerId !== drag.id) return
  const dx = event.clientX - drag.x, dy = event.clientY - drag.y
  if (!drag.moved && Math.hypot(dx, dy) < 7) return
  if (!drag.moved) { drag.moved = true; drag.tile.classList.add('dragging'); pickUp(drag.tile) }
  drag.tile.style.setProperty('--dx', `${dx}px`); drag.tile.style.setProperty('--dy', `${dy}px`)
  event.preventDefault()
 }
 function endDrag(event) {
  if (!drag || event.pointerId !== drag.id) return
  const { tile, moved } = drag; drag = null
  tile.classList.remove('dragging'); tile.style.removeProperty('--dx'); tile.style.removeProperty('--dy')
  if (!moved) return                                  // a tap — the click handler takes it
  swallowClick = true
  // The tile is pointer-events:none while dragging, so this hit-tests through it.
  const target = document.elementFromPoint(event.clientX, event.clientY)?.closest('.party-slot')
  if (target) place(target); else deselect()
 }

 // Shuffle until the tiles are genuinely out of order — an accidental
 // already-solved row would give the puzzle away before it starts.
 const order = [...WORD].map((_, i) => i)
 do { for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1));[order[i], order[j]] = [order[j], order[i]] } }
 while (order.every((value, i) => value === i))

 order.forEach((letterIndex, position) => {
  const tile = document.createElement('button')
  tile.type = 'button'; tile.className = 'party-letter'; tile.textContent = WORD[letterIndex]
  tile.dataset.index = String(letterIndex)
  tile.setAttribute('aria-pressed', 'false')
  tile.setAttribute('aria-label', `Letter ${WORD[letterIndex]}. Pick it up, then choose a box.`)
  tile.style.setProperty('--x', `${SPOTS[position][0]}%`); tile.style.setProperty('--y', `${SPOTS[position][1]}%`)
  tile.addEventListener('pointerdown', event => startDrag(event, tile))
  tile.addEventListener('pointermove', moveDrag)
  tile.addEventListener('pointerup', endDrag)
  tile.addEventListener('pointercancel', endDrag)
  tile.addEventListener('click', () => { if (swallowClick) { swallowClick = false; return } pickUp(tile) })
  lettersHost.append(tile)
 })
 for (let i = 0; i < WORD.length; i++) {
  const slot = document.createElement('button')
  slot.type = 'button'; slot.className = 'party-slot'; slot.dataset.index = String(i)
  slot.setAttribute('aria-label', `Box ${i + 1} of 5, empty`)
  slot.addEventListener('click', () => place(slot))
  slotsHost.append(slot)
 }

 toggle.addEventListener('click', () => {
  const open = document.body.classList.toggle('party-open')
  toggle.setAttribute('aria-expanded', String(open))
 })
 addEventListener('keydown', event => { if (event.key === 'Escape') deselect() })

 return {
  // The birthday film takes the whole screen; nothing of the puzzle (or its
  // audio) should survive into it.
  setActive(on) { game.hidden = !on; if (!on) { deselect(); video.pause() } },
  solved: () => solved === WORD.length,
 }
}
