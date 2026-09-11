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
All 17 images in `characters/` were inspected as visual references only. No photos
are loaded into the scene, copied to the homepage assets, or used as textures.
`garden-characters.mjs` maps each filename to a stylised colour/accessory design;
`garden-people.js` builds 16 animated figures in the existing toy-like style.
The prior Thea and Steve figures are replaced, not duplicated. Existing Honey now
wears the reference's pink/lime tutu. Filenames supply display names (underscores
become spaces; original case retained), and every character uses the exact text
“{name} says Happy Birthday Sammy”. Character actions remain keyboard-accessible
through Little surprises as well as directly clickable on their geometry.

Distinguishing details include glasses, hair flowers, a bow tie/white moustache,
braided or curly hair, flower necklaces, a feathered crown, a hat and sunglasses.
Rigid details merge by material within each figure to reduce rendering overhead;
arms retain wave animations. Garden total: 27 interactive targets. All 17 character
greetings were clicked and checked in the browser, with no console errors.
Original garden files are in `backups/home-before-characters/`.
