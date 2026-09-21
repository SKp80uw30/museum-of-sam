# Birthday opening — integration notes

The default entry is `home.html` (also reached from `/` and `web/index.html`
without an explicit `scene` or `review` query). Existing scene URLs are unchanged.
The installed app manifest also starts at `home.html`.

The opening is deliberately isolated from the game code: `home.html`, `home.css`,
`home.js`, `home-journey.mjs` and `home-assets/`. It uses Canvas 2D for an illustrated
architectural salon and a cinematic, not-to-scale journey through Australia,
Earth, the solar system, the Milky Way and the universe. The stars assemble into
“This much!”; returning restores the salon with four ordinary accessible links.
Portal thumbnails are snapshots, not live views of Claude's ongoing game work.

Normal playback is 36 seconds, plus a 2.6-second return. Reduced-motion playback
uses six short dissolves over 9 seconds and a 0.6-second return. Skip/Escape jumps
to the message; replay is available from the portal room. Hidden tabs pause playback.
No audio/autoplay permission is required. Keyboard focus moves to the next CTA.
`home.html?home=portals` goes straight to the four doors, used by the small Home
link added to the shared experience page. Mobile uses a two-by-two portal layout.

Shared integration changes: tiny entry redirect and Home link in `index.html`,
manifest entry URL, service-worker shell list/cache revision/network-first handling
for the new homepage files. Preserve Claude's gameplay/whimsy code. No theme GLBs
were changed during this homepage task.

Check: `node tools/check_birthday_home.mjs` exercises the real controller with
DOM/canvas stubs plus pure timeline tests. This is not a pixel/browser test.
Browser preview was blocked by automatic approval review's account usage limit;
visual checks at desktop/mobile sizes and a full real-browser playback remain.

## Narrative revision
Applied `design-visual-storyteller.md`: invitation → escalating declarations →
star-written answer. The welcome now says “We love you so much…” and asks the
visitor to “click here to see how much”. Each scene repeats “We love you”, followed
by “more than…” the room, country, world, solar system, Milky Way and universe.
The chapter caption is visually attached to a six-landmark progress trail; the
current landmark is highlighted and identified with `aria-current="step"`.
Screen-reader announcements include the full declaration, rather than only a
place name. The final answer resolves “So, how much do we love you?” with “This
much!” and “More than all of that. And more every day.”

## Sam's living garden — 2026-09-11
The normal homepage now uses an actual Three.js/WebGL coastal garden from
`living-home.js`, rendered locally with the existing vendored Three.js build.
The earlier Canvas salon remains only a WebGL fallback. The birthday film and
its narrative are preserved; departure captures the visible garden, and return
reactivates it. Homepage-only changes keep Claude's game files independent.

Visual direction: saturated teal/aqua/blue, layered garden island and beach,
lagoon, tide lines, palms, trees, climbing flowers, a lotus pool and butterflies.
Thea and Steve are deliberately stylised keepsake figures, not claimed likenesses.
Honey is a procedural cream/caramel cockalier with articulated floppy ears and tail.
Birds: cockatoo, rainbow lorikeet, kookaburra, kingfisher and seagull.

13 interactive targets: five birds, Honey, Thea, Steve, garden globe, kindness
flowers, lotus, seashell and boat. Click geometry directly or use the accessible
Little surprises menu. Events trigger bounded animations, live-region messages
and, only when enabled, synthesised notes/chirps or a filtered-noise sea wash.
No autoplay audio. Pause and reduced motion stop ambient updates; the page also
pauses when hidden. Flowers/foliage are instanced to limit draw calls. Recorded
initial scene stats: 305 draw calls, 534,981 submitted triangles, 13 targets.

All four portals and the active birthday CTA are centred and fixed in welcome
and return states. Desktop fits in one viewport. At <=700px the garden itself is
a 1200px-or-wider horizontal panorama starting at its centre; native horizontal
scroll/swipe, keyboard region focus and explicit left/right arrows are available.
The controls do not pan. No vertical document scrolling is needed.

Verified in the connected browser: desktop composition, a 390x844 iframe viewport,
mobile right-pan with fixed controls, Honey/bird/family/kindness messages, pause,
and no runtime console errors during these interactions. The iframe exercises
responsive layout, not a physical phone's touch hardware. Review assets live in
`renders/home-review/`. Node controller/timeline regression checks also pass.
Original homepage files: `backups/birthday-home-before-living-garden/`.
The full normal-speed film also completed successfully in the browser, reached
“This much!”, and returned through the final CTA to the live garden. Screenshot
`this-much.png` records the verified reveal. A short-height layout keeps controls
separate when the viewport is in landscape orientation.

## Reference-inspired birthday guests
Every image in `characters/` was inspected as a visual reference only. No photos
are loaded into the scene, copied to the homepage assets, or used as textures.
`garden-characters.mjs` maps each filename to a stylised colour/accessory design;
`garden-people.js` builds one animated figure per entry in the existing toy-like
style. Adding a person is a single row in `CHARACTERS` — nothing else has to
change, because the museum's easter-egg roster reads the same list (see below).
The prior Thea and Steve figures are replaced, not duplicated. Existing Honey now
wears the reference's pink/lime tutu. Filenames supply display names (underscores
become spaces; original case retained), and every character uses the exact text
“{name} says Happy Birthday Sammy”. Character actions remain keyboard-accessible
through Little surprises as well as directly clickable on their geometry.

Distinguishing details include glasses, hair flowers, a bow tie/white moustache,
braided or curly hair, flower necklaces, a feathered crown, a hat and sunglasses.
Added 2026-09-16 with Veda, Dicky and Tashi: `mask` (a black helmet with a chrome
visor — a flat box faceplate, because details laid on the dome sphere sink into
it), `goggles` (prismatic steampunk lenses worn up on the forehead), `floral`,
`turtleneck`, `lips`, `beardColor` and `streak` (the spiky/pixie highlight colour,
previously hardcoded to one mid-brown that read wrong on bleached or jet-black
hair).
Rigid details merge by material within each figure to reduce rendering overhead;
arms retain wave animations. All character greetings were clicked and checked in
the browser, with no console errors.
Original garden files are in `backups/home-before-characters/`.

## PARTY letter puzzle — 2026-09-21
`web/party-letters.js` owns a five-tile puzzle on the homepage garden (welcome
and portals states only, like the rest of the garden UI). Five shuffled tiles —
P, A, R, T, Y — scatter down the left and right margins on desktop; five empty
boxes sit in the bottom-right corner. A tile can be dragged into a box or
tapped/keyboard-activated to pick it up and then dropped by activating a box.
A wrong box shakes and says so; the right box turns green and plays one window
of `web/video/el-nay-partay.mp4`:

| letter | window |
| --- | --- |
| P | 0–20s |
| A | 20–40s |
| R | 40–60s |
| T | 60–80s |
| Y | 80s → the end (the finale runs straight through the closing 100–120s) |

Activating a box that is already filled replays its window, and once all five
are placed an “↺ All 2 min” button in the panel plays the file end to end.

One `<video>` element serves every window. The file is encoded with
`-movflags +faststart`, so seeking to 80s is a byte-range request rather than a
full download, and `preload="metadata"` keeps the 22MB off the wire until the
first letter lands. **Byte-range support is required for the windows to work at
all** — Python's `http.server` does not implement `Range`, which makes the video
report `seekable: [0, 0]` and every window play from 0. Netlify serves ranges
correctly; test locally with a range-capable server.

The fifth correct letter also calls `onSolved()`, which is `home.js` running
`startParty({duration:30000, music:false})` — the existing nightclub lasers and
jumping characters for thirty seconds, deliberately without a Spotify track
because the video carries its own audio. `living-home.js`'s `party()` now takes
a duration (default still 10000, which is what the 🎉 Party pill uses).

The video panel is the bottom-right quarter of the screen, with ⤢ to expand it
to nearly the full viewport, × to close, and the browser's own controls for
sound, scrubbing and native fullscreen. Its z-index stays below `#party-overlay`
(1000) so the finale's lasers sweep *over* the picture.

Phones have no free margin to scatter tiles into, so on `max-width:700px` the
puzzle collapses behind a round 🅿️ button and opens as one bottom stack —
boxes, then loose letters, then the player — with the swipe hint and replay link
stepping aside while it is open.

Verified in Chrome at 1440×900 and 390×844: each letter seeks to its own window,
T's window pauses exactly at 80.0s, the finale starts at 80s and runs past 100s
without pausing, party-mode is still on at 25s and off by 32s, drag-and-drop and
tap-to-place both land correctly, and the puzzle hides and pauses its audio
during the birthday film and returns intact afterwards.
