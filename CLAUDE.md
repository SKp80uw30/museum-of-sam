# Museum of Sam

A walkable, game-quality virtual art gallery, delivered as a web experience. The
player walks down themed hallways with framed artwork mounted on the walls.
There will be 5 themed scenes total; all 5 share one reusable hallway module.

See `TODO.md` for the current build plan and phase checklist — always read
both files before resuming work on this project, especially after a context
reset or new session.

## Architecture decision (2026-09-09)

Earlier prototype (`prototype-coral-reef/`) used World Labs' Marble API to
reconstruct a whole 3D world (Gaussian splats + collision mesh) from a single
source photo, rendered in Three.js via `@sparkjsdev/spark` with
`PointerLockControls` for WASD/mouse-look walking. This worked but isn't
reusable or precisely controllable — artwork frame positions had to be
hand-guessed against the reconstruction (see the hardcoded `FRAMES` array in
`prototype-coral-reef/index.html`), and each scene would need its own
expensive, uneditable world generation.

**Decision: stop using Marble/splat generation for the hallway scenes.**
Instead:

1. **Model everything by hand in Blender first** — geometry, materials,
   lighting, and prop dressing — using blender-mcp's asset tools (PolyHaven
   for HDRIs/textures, Sketchfab/PolyPizza for props like coral and fish,
   Hyper3D/Hunyuan3D for anything custom-generated). Iterate entirely inside
   Blender until the look matches the reference images in `Museum-locations/`
   before touching any web code.
2. **Build one reusable hallway module** as the shared base for all 5
   scenes. Reviewing two reference images (`Museum-locations/`'s forest
   walkway and underwater reef) showed neither is a literal enclosed
   box corridor — both are a walking path flanked by art, open overhead,
   with irregular frame sizing/placement. So the true shared base is
   narrower than originally assumed:
   - a walkable floor path (re-textured per theme)
   - a frame-mount data system: each mount stores position along the path,
     side, lateral offset from the centerline, absolute height, tilt, and
     frame width/height — general enough to render as either flush
     wall-frames (forest/gallery/castle-style themes) or freestanding
     post-mounted frames (reef-style themes)
   - the walk camera/eye-height rig

   **Walls and ceilings are NOT part of the shared base** — they're
   per-theme dressing added in Phase 2 (e.g. a flat wall behind flush
   frames for a gallery theme; nothing at all, just posts and coral, for
   the reef theme). Each scene is a re-theme of the same path + mount data,
   not a separate build.
3. **Export the finished Blender scene to glTF** and load it into a plain
   Three.js scene, reusing the `PointerLockControls` + collision-mesh walking
   approach from `prototype-coral-reef/index.html` — but rendering an
   ordinary textured mesh instead of Gaussian splats.

Rationale: a hand-modeled glTF hallway is fully controllable (exact frame
placement, swappable per-scene materials, much lighter to render) where the
splat approach was neither. Blender-first sequencing costs an early "is it
walkable" checkpoint (nothing is interactive until export) but buys real
control over composition and lighting quality, which is what the reference
images demand.

## Key locations

- `Museum-locations/` — AI-generated reference/mood-board images for the 5
  planned themes: underwater reef, forest walkway, jumping castle
  (yellow/green — the reference filenames say "art gallery" since that was
  the original prompt, but the images actually depict a giant inflatable
  bounce-castle tunnel; scene id `jumping_castle` throughout the codebase),
  old English castle, gallery home (an expensive designer-house hallway;
  scene id `gallery_home`). These are the visual target for each scene's
  Blender theming pass, **not** assets to import directly.
- `prototype-coral-reef/` — the earlier Marble/splat prototype. Useful as a
  reference for the Three.js walking mechanics (`PointerLockControls`,
  collision handling, pointer-lock UI/HUD) in `index.html`, but its
  splat-rendering approach (`generate-world.mjs`, `@sparkjsdev/spark`) is
  being retired for this new pipeline.
- `360-degree/` — earlier ComfyUI panorama experiment, superseded, kept for
  reference only.
- `tools/blender-mcp-addon.py` — the Blender MCP addon enabling Claude to
  drive Blender directly for this project.
- `exports/` — glTF/glb exports of each themed scene, one file per theme
  (e.g. `underwater_reef.glb`), the hand-off point from Blender to the
  Phase 5 Three.js loader.
- `tools/hallway_kit.py` — shared, theme-agnostic Blender Python toolkit:
  mount-empty generation (Phase 1) and parametric frame/canvas geometry
  (Phase 3). Every theme should `sys.path.insert` + `import hallway_kit`
  and call into it rather than re-deriving mount placement or frame-mesh
  logic per scene — see its module docstring for the three entry points.
  Per-theme *style* (frame material, molding proportions, wall-mount vs.
  freestanding-post) stays out of this file and is passed in as
  parameters/materials by the calling scene script, matching the
  walls/posts precedent below (shared logic, per-theme dressing).
- `tools/prepare_artwork.py` — converts `Photos/` into
  `web/artwork/photos/*.jpg` + `web/artwork/photos-manifest.json`. `Photos/`
  is scanned recursively, so just drop new photos — individually or as
  whole subfolders — anywhere under it and re-run the script; nothing else
  needs to change for them to enter the pool. The manifest is fully
  regenerated each run, so removed source files stop appearing too. See
  the 2026-09-11 TODO.md entry for what the runtime does with the
  resulting pool (random per-load assignment across every theme's
  canvases, plus a slow crossfade rotation) and a real export bug it
  uncovered (see below). (Folder was renamed from `photos-from-chaz/` and
  the script made recursive on 2026-09-12 — the old script only scanned
  the top level, so a pre-existing `us-photos/` subfolder had silently
  never been included until then.)

## Deployment

**One deployment: Netlify — https://museum-of-sam.netlify.app/**

Netlify is connected directly to this GitHub repo (`SKp80uw30/museum-of-sam`)
and auto-builds/publishes on every push to `main`. There is no manual deploy
step and nothing else to keep in sync — **`git push origin main` is the whole
deploy**. "Push so it's live" means exactly that, with no follow-up question
needed about which target.

Netlify publishes the **repo root**, not `web/`, so live URLs carry the `web/`
prefix: the artwork manifest is at `/web/artwork/photos-manifest.json`, and the
root `index.html` is just a redirect stub into `./web/home.html`. Keep this in
mind when curling the live site to verify a deploy.

Self-hosting on the `freedaiy` Tailscale Funnel box was **retired 2026-09-21**
and is no longer a deployment target. Don't rsync to it, don't treat its
contents as live, and don't ask which deployment is meant — Netlify is the only
one. (The box itself still exists for unrelated work; see the global CLAUDE.md.)

## Working conventions

- Keep the reusable hallway as its own `.blend` file (undressed/plain) so it
  never gets overwritten by a theme pass — each themed scene should branch
  from it, not replace it. Current base: `blender-scenes/base_hallway.blend`
  (60m corridor, 32 mounts as of the Phase 3 revision below — raise
  `target_count_per_side`/`corridor_length` in `hallway_kit.generate_frame_mounts`
  to add more per scene rather than hand-editing mounts).
- Frame/artwork mounts are irregular by design, not an evenly-spaced grid —
  varied width/height, randomized gaps, independently randomized per wall
  (different seed each side so they don't mirror), with some tilt/height
  jitter for an organic, non-uniform feel. Each mount empty carries
  `wall_side`, `frame_width`, `frame_height`, `lateral_offset`, `tilt_deg`
  custom properties for Phase 3 to build real frame geometry against.
- `tilt_deg` is stored on the mount empty at Phase 1; `hallway_kit.place_frame_and_canvas`
  applies it to **both** the frame mesh and its backing canvas by
  default (they'd otherwise visibly diverge/skew apart at mounts with
  larger tilt values — hit and fixed once already). Don't apply tilt to
  one without the other if bypassing that helper.
- The reef and forest GLBs export their `Canvas_*` quads with **no
  TEXCOORD_0 at all** (gallery_home and jumping_castle export them fine) —
  invisible until real (non-flat-color) artwork actually needs to sample
  the texture, which is why it went unnoticed through the whole placeholder
  phase. `web/index.html`'s `ensureCanvasUV()` reconstructs a planar UV at
  runtime as a workaround, so this isn't currently blocking anything — but
  if reef/forest are ever re-exported, worth checking whether the new
  export carries real UVs (then `ensureCanvasUV` just no-ops). Related
  quirk in the same two themes: the canvas mesh has an *applied* rotation
  baked into its local axes, so "height" sits on local Y instead of Z like
  hallway_kit authors it — and reversed in direction, too. Any future code
  touching these canvases by local axis (not just UV reconstruction) needs
  to detect this per-mesh rather than assume Z is height.
- When duplicating an existing themed scene's prop scatter to extend
  corridor coverage (rather than re-running the original placement
  logic), duplicate whole parent→children hierarchies with an explicit
  old→new object map and remap `.parent`/`modifier.object` for every
  member — the same rigged-asset duplication bug from the coral/fish
  scatter below recurs here too. Snapshot the root-object list *before*
  the duplication loop starts; re-querying the collection mid-loop for
  "objects with no parent" will pick up objects you already duplicated
  in an earlier band and double-duplicate them.
- Before exporting a theme to glTF, check the view layer for collections
  whose `exclude` flag is still `False` but shouldn't be exported —
  specifically the default `Collection` (often holds leftover
  unorganized/template objects from an asset import) and any
  `glTF_not_exported` collection (Blender's own auto-created home for
  armature bone-display helpers when a rigged asset was imported — a
  real Blender convention, not a stale note). Both were found still
  exporting, unhidden, at the scene origin in the reef theme's Phase 4
  pass.
- To sanity-check an exported `.glb`, don't round-trip it back through
  Blender's `bpy.ops.import_scene.gltf()` when the scene has rigged
  assets — its importer crashes on `bpy.context.object` inside
  `armature_display()` when run headlessly (no interactive UI sets an
  "active object" in that code path). Parse the glb directly instead:
  12-byte header + JSON chunk via Python's `struct`/`json`, check
  declared vs. actual file length, confirm every accessor/node index
  resolves in range. Faster, and sidesteps the importer bug entirely.
- Always compare in-progress renders against the matching `Museum-locations`
  reference image for that theme before calling a theming pass done.
- Sketchfab and Poly Pizza API keys are configured (as of 2026-09-09) and
  live in Blender's addon preferences — global to the Blender install, not
  saved per-`.blend`-file, so they carry over automatically to every scene
  file without re-entering them. Poly Pizza is preferred over Sketchfab for
  props in this project: far lighter geometry, better suited to the
  real-time web target. When duplicating a downloaded Poly Pizza/Sketchfab
  asset to scatter multiple copies, see the two duplication bugs logged in
  `TODO.md` Phase 2 (baked parent-scale gets lost if you overwrite `.scale`
  instead of multiplying it; Armature modifiers need their `.object`
  target manually remapped to the new duplicated skeleton) — both will
  recur with any rigged/parented asset in the remaining 4 themes.
- Lighting recipe that actually works in EEVEE Next (see `TODO.md` Phase 2
  for the full story): don't use a world-level Volume Scatter for haze/fog
  — it renders fully black regardless of density, seemingly a renderer
  limitation. Don't crank the world background's strength either — above
  ~1.0 it acts as ambient fill and washes every material toward pastel via
  multiplied diffuse response. Instead split the world background through a
  Light Path "Is Camera Ray" → Mix Shader (full strength for what camera
  sees, ~0.2 for its lighting contribution), keep the key Sun neutral/white
  so material colors read true, and add a separate low-energy blue-tinted
  fill light for shadow-side color mood. Haze/fog is deferred to Phase 6
  post-processing instead of scene-level volumetrics.

## Reef realism revision (2026-09-11)

The reef now includes a continuous seabed, packed sand ripple/caustic textures,
organic branching coral, rubble and seagrass, and a rippled water surface.
See the dated review at the end of `TODO.md` for reproduction, validation, and
limits. Original assets are preserved in `backups/reef-2026-09-11/`.

`tools/refine_underwater_reef.py` must be run against that backed-up original
scene, not against an already-refined output. It writes the current reef scene,
review renders, and GLB. The final `.blend` uses Cycles with a **bounded** preview
fog volume; exclude `Reef_Preview_Atmosphere` from any future export. The existing
warning against unbounded world volumes still applies. Runtime handles animated
surface textures, teal depth fog, and directional shadows; these are not baked
into the GLB. Keep `Sun`/`Fill` runtime intensities aligned with the art pass;
Blender 5.2.1 exported identical lux values for both lights.

## Forest finishing revision (2026-09-11)

The forest now has a leaf canopy and branch structure, individual boardwalk
planks, aged overgrown gallery walls, ivy, ferns, forest ground, and path lamps.
`tools/refine_forest_walkway.py` reproduces the pass from the original in
`backups/forest-2026-09-11/`. Use a separate MCP command to open that original
before executing the script; loading and editing in the same command invalidates
Blender's UI context. See the dated TODO entry for verification and file counts.

Keep the existing `THEMES` registry and `?scene=forest` routing in `web/index.html`.
Forest-only canopy wind, lighting, atmosphere and boardwalk walking bounds live
there. Leaf wind is also applied to the shadow material. Neither theme should
inherit the other's environment settings. Use smooth foliage normals when
exporting; flat normals inflated the forest GLB with unnecessary split vertices.

The forest's current sky is a blue daytime gradient with drifting clouds from
`web/forest-sky.js`. Daylight haze, ambient fill and grading are forest-only
settings. `tools/set_forest_daylight.py` applies the matching packed still sky
and lighting to Blender after the forest refinement pass. Cloud movement is
runtime-only; preserve that sky module when editing the shared scene loader.

### Jumping castle reference finish — 2026-09-11
The castle now follows the supplied yellow/green inflatable gallery reference:
whole yellow/teal bays, 150 smooth wall chambers, seven inflated floor channels,
nine large crossbeams, an industrial venue roof and 32 slim frames with white mats.
All artwork slot names and longitudinal placement remain; castle-only mounts are
flush at x=±1.70 with tilt removed. Artwork remains placeholder content.
`tools/refine_jumping_castle.py` rebuilds from the original castle backup (pass
that .blend to background Blender); `tools/vinyl_wrinkles.py` supplies packed
UV-based vinyl normals. Original files are in `backups/jumping-castle-2026-09-11/`.
Castle runtime uses a RoomEnvironment reflection approximation, warm lighting,
castle-specific bounds and floor-following spawn height. Preserve other theme
settings when editing the shared loader. Final GLB is 9,575,428 bytes with 11 lights.
Run `tools/validate_jumping_castle_export.py` and browser
`?scene=jumping_castle&review=1&verify=1` for export and movement checks.

### Birthday homepage / concurrent-work boundary
`web/home.html` is now the default experience entry; `?scene=...` routes still
load the existing game. `web/home.html?home=portals` returns directly to the four
museum doors. Birthday animation is isolated in `home.js`, `home.css` and
`home-journey.mjs`; see `web/BIRTHDAY-HOME.md` for integration and verification.
Preserve the small entry redirect and Home link when changing shared index.html.
The birthday sequence is illustrated and not astronomically to scale. Portal
images are snapshots; updating gameplay does not require touching homepage code.

### Character roster (single source of truth)
`web/garden-characters.mjs`'s `CHARACTERS` list is the one place a person is
defined. The homepage garden (`garden-people.js`) builds a full avatar from it,
and the museum's easter eggs (`web/index.html`'s `POPUP_CHARACTERS`) build a
simplified toy figure from the same row — so adding a person is one line there
plus, if they need a new prop, a clause in both builders. Reference photos live
in `characters/` (untracked, never loaded at runtime — they only supply the
display name via the filename stem, so name files the way the name should read).
Add a matching block to `characters/messages.txt` too.

Each world's eggs draw characters by index with a per-world offset (reef 0,
forest 6, castle 12, gallery 18). Adding people shifts who lands where, so after
a roster change check the four slices still cover everyone; eggs that must show
one specific person use `popupIndexOf(name)` instead of the cycle (the reef's
last three do). Bump the `?v=` on the `garden-characters.mjs`/`garden-people.js`
imports and `sw.js`'s `CACHE_NAME` whenever these change, or cached clients keep
the old cast.

### PARTY letter puzzle
`web/party-letters.js` runs the homepage's five-tile PARTY puzzle and the video
panel it drives (`web/video/el-nay-partay.mp4`, encoded with
`-movflags +faststart`). Each correct letter plays one 20-second window of the
file by seeking a single `<video>` element; the fifth also asks `home.js` for
thirty seconds of the existing nightclub lights (`startParty({duration, music})`
→ `living.party(duration)`). The windows depend on HTTP byte-range support —
Netlify has it, `python3 -m http.server` does not, and without it every window
silently plays from 0. Details and the letter→window table are in
`web/BIRTHDAY-HOME.md`.

### Landscape lock and tilt-look toggle (2026-09-23)
`web/orientation-gate.js` is a plain (non-module) script loaded by both
`home.html` and `index.html`. On touch devices (coarse pointer **and** a real
touch digitiser — a touch-screen laptop on a portrait monitor must not be
gated forever) it asks for `screen.orientation.lock('landscape')` and, more
importantly, covers the page with a "turn your device sideways" screen
whenever the viewport is portrait. The lock API is the optional half: only
Chrome/Android honours it, and only in fullscreen, so on iPad/iOS the CSS
gate is the whole mechanism. `manifest.json` is `"orientation": "landscape"`
for the installed PWA. `?orientation=any` disables the gate;
`?orientation=force` turns it on from a desktop browser for testing (flip the
`(orientation: portrait)` media rule via CSSOM to see it without a real
rotation).

Tilt-to-look in `index.html` is now **opt-in** (default off), persisted in
localStorage as `museum-of-sam.tilt-look` and toggled by the `#motion-toggle`
pill (touch devices only, top-right next to the credits ⓘ, above the entry
overlay so it can be set before walking in). Off simply never attaches the
`deviceorientation` listener, leaving the existing drag-to-look path as the
only thing steering the camera. The preference is only applied to the sensor
once the walk has started, so nobody gets an iOS permission prompt on a screen
they haven't entered.

`applyDeviceOrientation` no longer follows the classic
DeviceOrientationControls algorithm to the letter. That algorithm keeps the
horizon level by rolling the camera by `screen.orientation.angle`, which
assumes the browser reports that angle the way the algorithm expects; on a
landscape iPad it doesn't, and the entire view sat on its side with the
horizon turning along with the device, so there was no way to right it. We now
take only the direction the back of the device points out of the device
quaternion and rebuild the camera as yaw + pitch with roll forced to zero.
**Don't reintroduce a roll term** — roll is never wanted in a first-person
walk, and rolling a camera about its own Z axis doesn't change where it looks,
so the screen angle never affected the facing anyway. Verified against
simulated sensor values: `gamma` maps 1:1 to pitch and `alpha` 1:1 to yaw from
either landscape hold, with roll 0 throughout (`window.__debug.setMotionLook`
/ `simulateOrientation` drive this from the console).

### Living homepage garden
`web/living-home.js` now owns the independent 3D homepage garden and its 13
interactive surprises. Existing game/whimsy files remain separate. The homepage
keeps its birthday film and fixed central portal links. On mobile only the garden
panorama scrolls horizontally. Preserve `living-ready` and the active-state CSS
when editing the home layout; the film snapshots the rendered garden on departure.
See `web/BIRTHDAY-HOME.md` for the detailed handoff and verification notes.
