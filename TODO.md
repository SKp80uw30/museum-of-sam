# Museum of Sam — Build Plan

Read `CLAUDE.md` first if you haven't already — it has the architecture
decision and context this plan assumes.

**How to use this file across sessions:** work one phase at a time. At the
end of every phase there is a `STOP` step — do not skip it. It exists
because this is a long, multi-session build and context gets compacted or
reset between sessions; the STOP step is what re-anchors the work on the
final target instead of drifting.

---

## Phase 8 — Easter Eggs & Discovery Scoring

Core mechanics (walking, frames, artwork) are done across all 4 built
worlds (reef, forest, jumping_castle, gallery_home — "old English castle"
remains unbuilt/deferred per Phase 7). This phase adds whimsy: 15 hidden
interactive Easter eggs per world (60 total), a 0/15 discovery counter per
scene, and a small toast/celebration on each first find.

Design pass done via the `design-whimsy-injector` persona (Whimsy Injector
agent) — see the per-world tables below. All 60 map onto 5 reusable
implementation primitives so the trigger/effect system is built once, then
driven per-egg by data (object reference, trigger type, effect type,
params):

1. **Hinge-open** — rotate a panel/frame open around an edge pivot, hold,
   swing shut (used for the "wall opens to reveal a hidden photo" family).
2. **Color-cycle** — lerp a material's emissive/color through a palette
   over time, then settle (lights, coral, bulbs).
3. **Particle burst** — one-shot spawned `Points`/sprite burst at a
   position, fades and despawns (fireworks, bubbles, confetti, sparkle).
4. **Squish-pulse** — scale a mesh up/down on a spring-ish tween and
   settle back (puffer fish, vinyl panels, bolsters, frames).
5. **Spawn-animate-despawn** — build a small temporary primitive mesh
   (bunny, crab, coin, bird, butterfly, etc.), animate it along a simple
   path, remove it when done.

Triggers:
- **click** — raycast from screen center against registered hotspot
  meshes while pointer-locked (crosshair already exists as the aim point).
- **walk-near** — per-frame XZ distance check between player and a
  hotspot world position; fires once (with a cooldown before it can
  re-fire) rather than every frame inside the radius.
- **jump-on** — jumping_castle only; fires on landing (`jumpHeight`
  crossing back to 0) if the player's XZ is within radius of a hotspot.

Scoring: `localStorage` key per scene (`museum-eggs-<sceneId>`), a
`Set` of found egg ids. Small HUD counter (e.g. "🥚 3/15") near the
existing bottom HUD, plus a one-time toast per new find. No backend/DB —
matches the "fine if it resets when they come back" instruction; splitting
per-scene in localStorage is close to free to add and doesn't conflict
with that, so it's included, but nothing else persistence-related should
be built beyond this.

Targeting real objects: eggs reference objects **by regex prefix + index**
picked at runtime during the existing `hallway.traverse()` pass (e.g. the
2nd `Rock_*` found, the 5th `Reef_Fish`), not by hardcoded exact names —
robust to the exact counts/ordering differing slightly from the estimates
below. 🆕-marked eggs are new cheap procedural primitives (box/sphere/cone
composites) spawned at a fixed hardcoded corridor position, not glTF
imports — no new asset pipeline.

- [x] Build the shared framework in `web/index.html`: hotspot registry,
      raycast/proximity/landing trigger dispatch, the 5 effect primitives,
      localStorage scoring + HUD counter + toast
- [x] **STOP:** check off this line, re-read `CLAUDE.md`, then continue

**Framework result:** hotspots are registered as `{ id, trigger, getWorldPos, run, radius, cooldown, maxDistance, aimAngle }`
and dispatched three ways — `tryClickHotspot()` uses an **aim-cone test**
(angle from camera-forward + max distance) rather than exact mesh
raycasting, since it's far more forgiving for thin/small decorative props
and skinned meshes than a triangle-precise raycast; `updateProximityHotspots()`
does a per-frame XZ distance check for `walk` triggers; `onJumpLanding()`
hooks into the existing jump-physics landing edge in `tick()` for `jump`
triggers (inert outside jumping_castle, which is the only scene that ever
sets `jumping = true`). The 5 primitives (`squishPulse`, `colorCycleEffect`,
`particleBurst`, `hingeOpenEffect` + `makeHingePivot`, `spawnTemp`) all
drive a shared `eggAnimations` array ticked once per frame via
`updateEggAnimations(dt)`, called **after** `mixer.update(dt)` in `tick()`
specifically so additive effects on animated meshes (a fish's barrel-roll,
its follow-pull) layer on top of that frame's clip-driven pose instead of
being overwritten by it — plain absolute-set effects on static objects
don't care about this ordering but it's harmless for them either way.
Scoring is `localStorage['museum-eggs-<sceneId>']`, a JSON array read into
a `Set`; HUD (`#egg-hud`, top-center pill) updates on first find only.
The toast (`#egg-toast`) always shows on re-trigger too (2026-09-11 update)
— `markFound()` still plays the egg's effect either way, but shows
"✨ Found: <name> (n/15)" the first time and "👀 <name> — already located"
on every re-trigger after that, so clicking a found egg again visibly
confirms it's already been discovered. `window.__debug` gained `hotspots`,
`getEggsTotal()`, `getFoundEggs()`, `triggerHotspot(id)` for headless
testing (same debug-hook convention as the rest of the file).

**Hover affordance + universal confetti (2026-09-11 update):** aiming the
crosshair at any `click`-trigger egg now visibly marks it as interactive —
`findAimedClickHotspot(respectCooldown)` factors the aim-cone math out of
`tryClickHotspot()` so a per-frame `updateHotspotHoverHint()` (called every
tick, gated internally on `controls.isLocked || mobileActive`) can reuse it
with `respectCooldown=false`. On a hit, `#crosshair` gets a `.hotspot` class
(bigger, gold-outlined, pulsing) and `#hotspot-hint` shows the egg's name
— `✨ <name>` if undiscovered, `👀 <name>` if already found — so the
"already located" signal is visible before you even click, not just after.
`walk`/`jump` eggs have no hover equivalent (they fire automatically by
proximity, nothing to aim at first). Separately, every *new* find now also
fires `spawnConfettiCelebration()` from `markFound()` — a small multi-color
particle puff in front of the player, layered on top of whatever that
egg's own effect does, so discovery always reads the same way regardless
of world or effect type. Re-triggering an already-found egg does not
re-fire confetti (only the "already located" toast). `window.__debug`
gained `findAimedClickHotspot`, `updateHotspotHoverHint`, `getHoverHint()`
for headless verification (pointer lock doesn't engage under CDP
automation, so real aim/hover was verified by directly positioning
`camera` and calling these rather than moving a real mouse — see the
per-world verification notes above, which still hold for the click/walk/jump
dispatch itself; this update only touched the shared framework, not any
per-egg registration, and full trigger-every-hotspot regression checks were
re-run on all 4 worlds afterward with zero errors).

**Redesign: literal Easter eggs + a birthday-cast character hunt
(2026-09-11).** User feedback on the above: the disguised-real-object
design wasn't legible (no way to tell a decorated Sconce from a plain one)
and effects didn't read as "found." Replaced entirely — every hotspot
across all 4 worlds (still the exact same 60 ids/locations/triggers) is now
a literal two-piece chocolate-egg prop, obviously not part of the scene.
Opening one always does the same three things: the lid pops up and tips
aside, a character from the birthday cast grows up out of the shell with a
floating "`<Name> found!`" label, and `markFound()`'s existing confetti +
toast confirm the find — so "finding an egg" now means "finding a specific
character," not an arbitrary effect. The cast is 22 characters — the same
16 people + Honey the dog `garden-people.js`/`living-home.js` draw for the
homepage's living garden, imported directly from `garden-characters.mjs`
(`CHARACTERS`, `birthdayName`, `HONEY_FILE`) so the roster can't drift out
of sync, plus 5 birds restated with the same names/colors (living-home.js
has no exported bird list — they're inlined there). 60 eggs cycling through
22 characters means repeats across worlds are expected and fine, matching
a mascot-style hunt rather than a strict 1:1 catalog. Each world gets a
different offset into the roster (reef 0, forest 6, castle 12, gallery 18)
so the same character doesn't always land on the same world.

Key pieces in `web/index.html`: `POPUP_CHARACTERS` (roster + per-kind visual
params), `buildEasterEgg()`/`EGG_RADIUS`/`EGG_SCALE_Y`/`EGG_REST_Y` (the
shell — two hemisphere meshes split at the equator, `EGG_REST_Y` is the
ground-rest offset for floor-anchored eggs), `buildPersonFigure()` /
`buildDogFigure()` / parameterized `buildBird()` (simplified ~10-primitive
"toy figure" stand-ins for the homepage's full ~30-primitive rig — cheap
enough to build fresh on every open without hurting frame rate),
`makeEggLabelSprite()` (canvas-texture sprite, same technique as the
garden's `textSign()`), `openEasterEgg()` (the one shared reveal timeline),
and `placeEasterEgg()`/`buildEggAt()` (build-and-register in one call — the
latter used directly by the 3 castle eggs that need custom trigger logic
alongside the standard reveal: Super Bounce Ridge's real jump-height boost,
and Applause Lights/Confetti Cannon's jump-counting sentinel trick, both
unchanged from the original design, just swapped to open an egg instead of
their old bespoke effect). The hover hint (previous entry) no longer shows
the egg's name before it's found — `"🥚 Click to open"` pre-find,
`"👀 <Name> (found)"` post-find — so the character stays a surprise.

This fully replaced every per-egg `run()` body in all 4 `init*Eggs()`
functions; the position/trigger/radius/cooldown logic for all 60 was kept
exactly as-is (same real-node lookups, same fixed corridor coordinates).
Consequently `colorCycleEffect`, `hingeOpenEffect`/`makeHingePivot`,
`spawnTemp`, and `findMeshChild` lost every call site and were deleted
(no longer part of the framework, since no egg touches a real object's
material or hinges a real panel anymore); `squishPulse` and `particleBurst`
remain (used by the egg's anticipation-squish and by `spawnConfettiCelebration`
respectively). The old one-off prop builders (`buildChest`, `buildOyster`,
`buildCrab`, `buildBottle`, `buildJellyfish`, `buildSquirrel`,
`buildMushroomCluster`, `buildButterfly`, `buildSpider`, `buildBunny`) were
deleted along with them.

**Verified:** JS syntax-checked. Loaded all 4 scenes fresh (localStorage
cleared + reloaded, since `foundEggs` is only read from storage at module
init — an in-session `localStorage.removeItem` alone doesn't reset the
already-loaded `Set`, which tripped up verification once before the reload
fixed it). Confirmed the imported roster resolves with no errors and each
world's 15 hotspot names match the expected character slice (e.g. reef:
Jay…English Steve; forest: Thea…Kingfisher; castle: El…Nay; gallery:
Rainbow Lorikeet…steve). Triggered every hotspot on every world via
`triggerHotspot(id)` and stepped ~8s of simulated time — zero errors, all
`🥚 15/15`, and every egg group ended with exactly 9 children (2 shells + 7
decorative dots, confirming the spawned character figure and label sprite
were fully cleaned up with no leaks). Directly re-verified the castle
counting eggs' far/near sentinel sequencing still holds post-rewrite
(far,far,near,near for Applause Lights; far×4,near,near for Confetti
Cannon) and that Super Bounce Ridge's custom `run()` still executes without
error. Confirmed via screenshot that the hover hint hides the character
name until found (`"🥚 Click to open"` → `"👀 Jay (found)"`), and via
screenshot at a corridor `&distance=` viewpoint that an unopened egg reads
as an obvious, colorful, clearly-not-scenery prop sitting on the sand.
Zoomed screenshots during an open cycle show the lid lifted, the character
figure (correct hair/shirt colors) mid-pop, the "`<Name> found!`" label,
and confetti particles, all rendering together correctly.

**Deferred to the real playtest:** same caveat as every prior pass — real
mouse-aim clicking and real jump-landing physics weren't exercised (CDP
automation doesn't engage pointer lock), only their debug-hook equivalents.

**One real bug hit and fixed:** the very first hotspot registration pass
filtered candidate nodes with `obj.isMesh`, which silently produced empty
lists for every real-object egg (`Cannot read properties of undefined
(reading 'length')` in `pick()`, only surfaced once actually loaded in a
browser — direct-parsing the glb's node names first, per this project's
established validation habit, would have caught it before writing any
targeting code). Root cause: this scene's per-instance nodes (`Rock_Medium_*`,
`Post_left_*`, `CoralDense_*`, `Clownfish`, etc.) are Blender-exported
transform-empty wrappers around a child mesh, not meshes themselves — the
same "container empty, not the mesh" shape as `FrameMount_*`. Fixed by
collecting by name prefix only (no `isMesh` filter — position/scale-based
effects work fine directly on the wrapper) and adding `findMeshChild(obj)`
to drill into the first mesh descendant for the one egg that needs
`.material` (Mood Coral's color-cycle). **Any future world's targeting
code should collect by name prefix alone and drill in only where a
material/geometry is actually needed, not gate the initial collection on
`isMesh`.**

### World 1 — Underwater Reef (15 eggs) — DONE 2026-09-11

Real node names confirmed by direct-parsing `exports/underwater_reef.glb`
(12-byte header + JSON chunk, no Blender needed — same technique as the
project's existing GLB validators) rather than guessed from the Phase 2/3
build notes, which use looser descriptive names than what actually landed
in the export.

- [x] Geode Rock — click `Rock_Medium_*` — cracks open (squish), gold sparkle-firework burst
- [x] Blooming Brain Coral — click `CoralDense_left_*` — blooms outward (squish), releases bubbles upward
- [x] Show-off Fish — click `Clownfish` — barrel-rolls (additive Z-roll layered after its swim clip), resumes
- [x] Bubble Post — click `Post_left_*` — bubble stream rises from a knot, pops with light glints
- [x] Synced Seaweed Wave — walk-near a `Seaweed` cluster — staggered squish-pulse ripples through 4 neighboring blades
- [x] 🆕 Buried Chest — click a chest prop in the sand — lid pops open, gold coin burst, chime beat, closes
- [x] Puffer Alarm — click `YellowTang`/`Clownfish` — inflates 1.8x (scale-only, safe alongside its swim clip), deflates
- [x] Sunbeam Coin Shower — click a light shaft (`shaftGroup` child) — coin-colored flecks shimmer and fall
- [x] Curious Follower — walk-near a `Clownfish` — additive pull toward the player over 3s, then releases
- [x] Sand Puff — walk-near a fixed floor spot — sand-colored particle puff kicks up and settles
- [x] 🆕 Oyster's Pearl — click a clam prop — shell opens, glowing pearl rises/pulses, shell closes over it
- [x] Mood Coral — click `Reef_Branch_Colony_*` — cloned-material color-cycle teal→violet→teal, settles
- [x] 🆕 Hidden Crab — walk-near a crab prop tucked by a `Rock_Medium_*` — quick sideways dart, freezes
- [x] 🆕 Message in a Bottle — click a bottle prop near a `Post_*` — rocks in place, paper-scroll tease, re-rolls
- [x] 🆕 Drifting Jellyfish — click a jellyfish prop near the ceiling — glows/pulses, drifts up, respawns 6m further down

**Verified:** loaded via `python3 -m http.server` + `claude-in-chrome`,
`?scene=reef&review=1` — zero console errors on load. All 15 hotspots
registered (`window.__debug.getEggsTotal() === 15`). Triggered every
hotspot via `window.__debug.triggerHotspot(id)` and stepped the render
loop forward (`window.__debug.step(200, 0.05)`, 10s of simulated time) —
zero runtime errors across all 15 effects, `🥚 15/15` HUD, correct final
toast. Screenshot near the buried-chest position (`&distance=14`) confirms
the HUD pill renders correctly top-center and the chest prop sits on the
sand without clipping/overlap issues; existing reef rendering (coral,
artwork photos, lighting) shows no regression.

**Deferred to the real playtest:** the aim-cone click dispatch
(`tryClickHotspot`, angle+distance based) and the mobile tap-vs-drag-look
disambiguation were only exercised indirectly (via the `triggerHotspot`
debug bypass, which calls `run()` directly and skips the aim/distance
math) — pointer lock doesn't engage under CDP automation (see the Phase 5
testing note above), so aiming/clicking a specific in-world object via
real mouse-look wasn't verified this pass. Worth a manual playtest pass
before considering World 1 fully signed off.

### World 2 — Forest Walkway (15 eggs) — DONE 2026-09-11

Real node names confirmed by direct-parsing `exports/forest_walkway.glb`
(same header+JSON-chunk technique as World 1) rather than the TODO's
original guesses. `Fern_1_*`/`Fern_-1_*` per-instance nodes get merged into
`InstancedMesh` batches by `instanceForestFerns()` before egg init runs, so
"Startled Fern" targets a fixed corridor position instead — same precedent
as reef's Sand Puff. No per-instance "vine"/"pothos" nodes exist (they're
single merged meshes `Forest_Ivy_Stems`/`Forest_Wall_Ivy`), so those two
eggs anchor to that mesh's world position and animate a small spawned prop
rather than the merged geometry itself.

- [x] Waving Branch — click a `Forest_Canopy_Leaves_*` blob — dips down then springs back up
- [x] 🆕 Shy Squirrel — walk-near the base of a `Trunk_*` — peeks out, darts up and out of view
- [x] Firefly Gathering — click a `PathLight_*` — firefly particle swarm converges, disperses
- [x] 🆕 Startled Bird — click near `Forest_Ivy_Stems` — bird bursts up and flies off
- [x] Secret Portrait — click a `WallPatch_left_*` — hinges open revealing a tiny hidden painting, swings shut
- [x] Magic Lantern — click a second `PathLight_*` — warm amber briefly pulses violet-blue, returns to normal
- [x] Startled Fern — walk-near a fixed fern-cluster spot — bounces/particle rustle
- [x] Climbing Pothos — click near `Forest_Wall_Ivy` — a spawned vine visibly grows upward fast, pauses, retracts
- [x] 🆕 Mushroom Ring — click a mushroom cluster prop at a `Trunk_*` base — mushrooms pop up one by one, sink back
- [x] Leaf Confetti — click a second `Forest_Canopy_Leaves_*` — leaf-sprite shower falls and drifts past the player
- [x] Woodpecker Trunk — walk-near a distinct `Trunk_*` — shake/knock, bark-chip flecks fall
- [x] Sunbeam Wink — click a fixed high sky point — gold sparkle-rain shaft falls to the boardwalk
- [x] 🆕 Wandering Butterfly — click a butterfly perched near a `WallPatch_right_*` — spirals off, vanishes
- [x] Creaky Plank — walk-near a spawned boardwalk plank overlay — visibly dips/wobbles with a creak, settles
- [x] 🆕 Web Watcher — click a spiderweb prop — dew-sparkle shimmer, spider retreats and stays hidden (reappears after 8s)

### World 3 — Jumping Castle (15 eggs) — DONE 2026-09-11

Real node names confirmed by direct-parsing `exports/jumping_castle.glb`.
The TODO's original "`Rib_*`"/"`InteriorRidge_*`"/"`WallPanel_*`" names
don't exist in the actual export — the corridor's inflatable-wall geometry
is all `WallChamber_L_*`/`WallChamber_R_*` (150 total), so every
wall-surface egg targets those instead. "Super Bounce Ridge" required one
small, well-scoped edit to `tryJump()` (a new `bounceBoostMultiplier`
module variable, consumed once) to actually double next-jump height rather
than just being a visual-only effect. "Applause Lights" (3x same spot) and
"Ceiling Confetti Cannon" (5x any spot) are counting eggs: since the shared
dispatcher only fires when `getWorldPos()` returns a point within radius of
the landing, returning a deliberately far-away sentinel until the count
threshold is reached lets `getWorldPos`'s side effect (incrementing a
closure counter) run every landing without the effect firing early —
verified directly by calling `getWorldPos()` repeatedly with the camera
positioned at each hotspot and confirming it returns "far" until the
3rd/5th call, then "near" from then on.

- [x] Super Bounce Ridge — jump-on a `WallChamber_L_*` — next jump boosts ~2x height (real physics change via `bounceBoostMultiplier`), chamber compresses/rebounds
- [x] Boing Bolster — jump-on an `EdgeBolster_*` — wobbles like jelly
- [x] Disco Bulb — click a `CeilingBulb_*` — rainbow color-cycle for ~4s, settles back to warm white
- [x] Puffy Panel — click a `WallChamber_L_*` — inflates further, holds, deflates back
- [x] Confetti Rib — click a `WallChamber_R_*` — small confetti burst
- [x] 🆕 Bouncing Bunny — jump-on a floor spot in the tunnel center — bunny prop spawns and hops across the corridor, vanishes
- [x] Jelly Frame — click a `Frame_left_*` — squash-stretch jiggle wobble, stabilizes
- [x] Applause Lights — jump-on the same spot 3x — nearby `CeilingBulb_*` cluster flash-chases like stadium lights
- [x] Squeaky Toy Bolster — click a second `EdgeBolster_*` — rapid inflate/deflate pulse
- [x] Sleepy Beam — walk-near a `CeilingBeam_*` — sags slightly, bounces back with a creak
- [x] Domino Ribs — jump-on near a `WallChamber_L_*` — ripple wave triggers down several neighboring chambers
- [x] Blushing Panel — click a second `WallChamber_R_*` — pink blush flashes on, fades back to plain vinyl
- [x] Ceiling Confetti Cannon — jump 5x total this session (any spot) — confetti bursts from between two `CeilingBeam_*`
- [x] Almost-Pop Bulb — click a third `CeilingBulb_*` — flickers urgently, releases a sparkle-firework burst instead of popping
- [x] Glowing Footprints — walk-near the tunnel floor center — faint glowing footprints trail behind the player, fade after a few seconds

### World 4 — Gallery Home (15 eggs) — DONE 2026-09-11

Real node names confirmed by direct-parsing `exports/gallery_home.glb`.
`ConsoleTop_*`/`LampShade_*` share matching 2-digit indices (00-07, one
lamp per console), used to pair "Welcoming Lamp"/"House Chime" with a
specific console+lamp rather than picking independently.

- [x] Candlelight Wink — click a `Sconce_*` — dims/flickers like a candle for a couple seconds, returns to steady glow
- [x] Mood Lamp — click a `LampShade_*` — color temperature sweeps warm amber → cool white → back
- [x] Breezy Pendant — click a `PendantCage_*` — gently swings on its cord, settles after a few oscillations
- [x] Shedding Plant — click a `PlantPot_*` — two `PlantLeaf_02_*` clones detach, drift down with a sway, fade near the floor
- [x] Rippling Rug — walk-near `Rug_Runner` — woven pattern briefly ripples
- [x] Hidden Portrait — click a `WallPanel_left_*` — swings open on a hinge revealing a small hidden painting, closes after a few seconds
- [x] Doorway Glow Pulse — click `FarDoorGlow` — daylight glow brightens, soft particle streaks sweep toward the player, fade
- [x] Welcoming Lamp — walk-near a distinct `ConsoleTop_*` — its paired `LampShade_*` brightens as the player approaches
- [x] Museum Spotlight — click a `Downlight_*` — real `THREE.SpotLight` cone + floor-highlight disc appear for a few seconds
- [x] Golden Vein — click `Border_0` — thin gold shimmer flash, fades
- [x] Ceiling Breath — click `CoveLight_left` — both cove strips pulse once with a soft golden "breathing" glow
- [x] 🆕 Startled Songbird — walk-near a `PlantPot_*` with a hidden bird — flutters up and out of frame
- [x] Fairy Dust Sconce — click a second `Sconce_*` — fine golden sparkle motes drift gently upward for a few seconds
- [x] Living Portrait — click a `Frame_left_*` — subtle parallax/shimmer tilt as if something shifted, settles still
- [x] House Chime — walk-near a distinct `ConsoleTop_*` — its paired lamp glow pulses once

**Verified (Worlds 2-4):** JS syntax-checked (`node --check` on the
extracted module script). Loaded each scene via `python3 -m http.server`
(project root, so `../exports/*.glb` resolves) + `claude-in-chrome`,
`?scene=<id>&review=1` — zero console errors on load for all three. All 45
hotspots registered (`getEggsTotal() === 15` per scene). Triggered every
hotspot via `window.__debug.triggerHotspot(id)` and stepped the render loop
(`window.__debug.step(200, 0.05)`, 10s simulated) — zero runtime errors
across all 45 effects, correct `🥚 15/15` HUD on every scene. The two
jump-counting eggs (castle) were additionally verified by calling their
`getWorldPos()` directly with the camera positioned at each hotspot and
confirming the far/far/near pattern lands on the 3rd and 5th call
respectively, not earlier. Screenshots of all three scenes confirm the HUD
pill renders correctly top-center and no new geometry clips/overlaps
existing scene content.

**Deferred to the real playtest** (same caveat as World 1): the aim-cone
click dispatch and jump-landing dispatch were only exercised indirectly via
the `triggerHotspot`/direct-`getWorldPos` debug bypasses — pointer lock
doesn't engage under CDP automation, so real mouse-aim clicking and real
jump-physics landings weren't verified this pass for any of the 4 worlds.
Worth a manual playtest pass before considering Phase 8 fully signed off.

- [x] **STOP:** all 4 worlds' 15 eggs implemented and verified in-browser
      (counter increments correctly, effects fire, no console errors);
      re-read `CLAUDE.md` before starting any further Phase 8 work.

### Birthday homepage — 2026-09-11
- [x] Separate architectural welcome room with birthday greeting and “click here”.
- [x] Animated room → Australia → Earth → solar system → Milky Way → universe sequence; stars assemble “This much!”.
- [x] “click here to start” returns to four portal choices; links retain existing scene routes.
- [x] Default web/root/PWA entry, return-Home link, responsive layout, keyboard focus, skip/replay and reduced motion.
- [x] JavaScript syntax and controller/timeline regression check (`node tools/check_birthday_home.mjs`).
- [ ] Real-browser desktop/mobile visual review and full playback: browser tool blocked by automatic approval review due account usage limit.
Integration details: `web/BIRTHDAY-HOME.md`. Homepage assets/code are isolated from concurrent Claude game work. The requested gallery_home Blender polish was paused when the user redirected this task to the birthday opening; its original files were backed up in `backups/gallery-home-2026-09-11/`, but no gallery geometry changes have been made.

### Birthday narrative clarity — 2026-09-11
- [x] Applied `design-visual-storyteller.md` to the invitation, escalating love declarations and final payoff.
- [x] Connected narrative captions to a labelled Home → Australia → Earth → Solar system → Milky Way → Universe progress trail.
- [x] Added active/completed landmark styling, full accessible story announcements and mobile typography.
- [x] Controller check passes, including exactly one current story milestone at each stage and full “We love you more than…” announcements.

### Sam's living 3D birthday garden — 2026-09-11
- [x] Applied `design-whimsy-injector.md`, Sam's stated palette/interests and 25eight's people-first context.
- [x] Real 3D teal/aqua coastal garden, beach/lagoon, trees/palms, 100+ flowers, butterflies and moving water.
- [x] Animated Honey, Thea/Steve keepsake figures and five bird species.
- [x] 13 clickable surprises, accessible action menu, optional sound, pause and reduced motion.
- [x] Persistent centre CTA + four portal links; single-screen desktop and horizontal mobile panorama.
- [x] Browser desktop/mobile-viewport review, right-pan with fixed controls and sample whimsy interactions; no console errors.
- [x] Controller/timeline regression and JavaScript syntax checks.
The browser access limit noted for the earlier homepage pass is no longer blocking this work. See `web/BIRTHDAY-HOME.md` for files, scope and verification details.

### Reference-inspired homepage characters
- [x] Reviewed all 17 character reference files; used colours/features only, never displayed the photos.
- [x] Added 16 stylised people, replacing the original Thea/Steve; updated Honey with a pink/lime tutu.
- [x] Scattered figures around the side gardens, with name signs and wave reactions.
- [x] Exact filename-derived “{name} says Happy Birthday Sammy” messages; all 17 verified via browser clicks without errors.
- [x] Character manifest coverage and birthday controller regression checks passed.

### Four new characters + Jay renamed to J-Don — 2026-09-12
- [x] Renamed `characters/Jay.JPG` to `J-Don.JPG` (source file already renamed by user); updated the one code
      reference in `garden-characters.mjs` — `birthdayName()` derives the displayed/egg name from the filename,
      so this alone fixes both the homepage figure and every egg-hunt occurrence. Historical dated log entries
      elsewhere in this file that quote old screenshots (e.g. "👀 Jay (found)") are left as accurate history,
      not live references.
- [x] Reviewed the 4 new reference photos (`characters/Liam.png`, `Nancy.png`, `Orla.png`, `Kieran.png`) for
      hair colour/style and rough shirt colour only, per the existing convention — never displayed the photos.
      Added all 4 to `CHARACTERS` in `garden-characters.mjs` with a smaller `scale:0.82` for the three kids
      (Liam, Nancy, Orla; Kieran is an adult, default scale) and `x,z` slotted into gaps in the existing left/right
      garden clusters (2 per side) with >=1.8 unit spacing from neighbors, clear of the centre CTA/pergola.
- [x] No other code changes needed for either homepage avatars or the egg hunt: `garden-people.js` builds
      homepage figures directly from `CHARACTERS`, and `POPUP_CHARACTERS` in `web/index.html` is built from
      `CHARACTERS` + `HONEY_FILE` + 5 birds and indexed with `% POPUP_CHARACTERS.length`, so both picked up
      the roster growing from 22 to 26 automatically — new characters now appear as egg-hunt finds in forest,
      jumping_castle and gallery_home (their offset slice doesn't reach reef, same as pre-existing Chaz).
- [x] Bumped the shared `garden-characters.mjs?v=` cache-busting query (2 → 3) in `garden-people.js`,
      `living-home.js` and `web/index.html`, the `garden-people.js?v=` query (2 → 3) in `living-home.js`,
      and the service-worker `CACHE_NAME` in `web/sw.js` (`v5-characters` → `v6-characters`) so both the
      module cache-busting and the PWA shell precache pick up the new roster on next deploy.
- [x] Verified: `node --check` on the 3 touched JS/mjs files, `node tools/check_birthday_home.mjs` regression
      pass, and a live browser pass — homepage garden renders all 4 new figures with correct name signs and no
      overlap/clipping; all 4 museum worlds report `getEggsTotal() === 15` with zero console errors; confirmed
      via `window.__debug.hotspots` that Liam/Nancy/Orla/Kieran appear in forest, castle and gallery_home
      hotspot lists and J-Don (not Jay) appears in reef, castle and gallery_home; triggered the Liam hotspot
      in forest end-to-end (open animation + confetti + toast + HUD increment to 1/15) with no errors.
