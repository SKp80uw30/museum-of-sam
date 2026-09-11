"""Jumping castle theme — giant inflatable yellow/green vinyl tunnel.
Named for what it actually is, not "art gallery" — the reference images
(despite their source filename) depict a bounce-castle tunnel repurposed
as an exhibit space, not a conventional flat-walled gallery.
Run headless: blender --background <repo>/blender-scenes/jumping_castle.blend --python this_file
(not via blender-mcp — that addon's live session is shared with any other
concurrent Blender user, e.g. another agent editing a different theme in the
same running Blender window; this script opens its own separate process).

Reference: Museum-locations/Art_gallery_hallway_inside_giant_yellow_and_green...png
Branches from base_hallway.blend (32 FrameMounts, Floor, Sun, WalkCam) — never
from another theme's file.
"""
import bpy, bmesh, math, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "blender-scenes" / "base_hallway.blend"
OUT_BLEND = ROOT / "blender-scenes" / "jumping_castle.blend"
GLB_OUT = ROOT / "exports" / "jumping_castle.glb"
RENDER_DIR = ROOT / "renders" / "jumping-castle-review"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(ROOT / "tools"))
import hallway_kit as hk

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene = bpy.context.scene

# ── Materials ────────────────────────────────────────────────────────────
def make_vinyl_material(name, color, roughness=0.28, bump_strength=0.15):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.4
        bsdf.inputs["Coat Roughness"].default_value = 0.15
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.6
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    noise.location = (-600, -200)
    bump.location = (-300, -200)
    bsdf.location = (0, 0)
    out.location = (300, 0)
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

yellow_vinyl = make_vinyl_material("JCastle_YellowVinyl", (0.85, 0.58, 0.05, 1.0))
green_vinyl = make_vinyl_material("JCastle_GreenVinyl", (0.03, 0.32, 0.16, 1.0))
green_floor = make_vinyl_material("JCastle_GreenFloor", (0.02, 0.26, 0.13, 1.0), roughness=0.22)

frame_white = bpy.data.materials.new("JCastle_FrameWhite")
frame_white.use_nodes = True
frame_white.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.92, 0.92, 0.90, 1.0)
frame_white.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5

frame_black = bpy.data.materials.new("JCastle_FrameBlack")
frame_black.use_nodes = True
frame_black.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.04, 0.04, 0.04, 1.0)
frame_black.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.4

bulb_mat = bpy.data.materials.new("JCastle_Bulb")
bulb_mat.use_nodes = True
bnt = bulb_mat.node_tree
for n in list(bnt.nodes):
    bnt.nodes.remove(n)
emit = bnt.nodes.new("ShaderNodeEmission")
emit.inputs["Color"].default_value = (1.0, 0.82, 0.45, 1.0)
emit.inputs["Strength"].default_value = 12.0
bout = bnt.nodes.new("ShaderNodeOutputMaterial")
bnt.links.new(emit.outputs["Emission"], bout.inputs["Surface"])

# ── Floor: glossy green vinyl ───────────────────────────────────────────
floor = bpy.data.objects["Floor"]
floor.data.materials.clear()
floor.data.materials.append(green_floor)

# ── Wall backing panels: puffy vinyl panel behind each frame mount ─────
if "WallPanels" in bpy.data.collections:
    wp_col = bpy.data.collections["WallPanels"]
    for o in list(wp_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    wp_col = bpy.data.collections.new("WallPanels")
    scene.collection.children.link(wp_col)

mounts = [o for o in bpy.data.objects if o.name.startswith("FrameMount_")]

def make_panel(mount, pad=0.4, setback=0.08, thickness=0.06, idx=0):
    width = mount["frame_width"] + pad
    height = mount["frame_height"] + pad
    tilt = mount.get("tilt_deg", 0.0)
    yaw = mount.rotation_euler.z
    suffix = mount.name.replace("FrameMount_", "")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= width
        v.co.z *= height
        v.co.y *= thickness
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"WallPanel_{suffix}_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(f"WallPanel_{suffix}", mesh)
    dx = -setback * math.sin(yaw)
    dy = setback * math.cos(yaw)
    obj.location = (mount.location.x + dx, mount.location.y + dy, mount.location.z)
    obj.rotation_euler = (math.radians(tilt), 0.0, yaw)
    mat = green_vinyl if idx % 5 == 0 else yellow_vinyl
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Bevel", 'BEVEL')
    bevel.width = min(0.05, thickness * 0.8)
    bevel.segments = 3
    wp_col.objects.link(obj)
    return obj

for i, m in enumerate(mounts):
    make_panel(m, idx=i)

# ── Ribs: continuous vertical tube-pillar background wall ──────────────
def make_rib_mesh(name, radius=0.22, height=4.2, segs=8):
    bm = bmesh.new()
    verts = []
    for i in range(segs + 1):
        a = math.pi * (i / segs) - math.pi / 2
        x = math.sin(a) * radius
        y = math.cos(a) * radius
        verts.append(bm.verts.new((x, y, 0.0)))
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    ret = bmesh.ops.extrude_edge_only(bm, edges=edges)
    top_verts = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top_verts, vec=(0, 0, height))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

rib_mesh = make_rib_mesh("Rib_template")
if "Ribs" in bpy.data.collections:
    ribs_col = bpy.data.collections["Ribs"]
    for o in list(ribs_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    ribs_col = bpy.data.collections.new("Ribs")
    scene.collection.children.link(ribs_col)

RIB_LATERAL = 3.0
RIB_SPACING = 0.5
i = 0
y = 0.0
while y < 60.0:
    for side in (1, -1):
        obj = bpy.data.objects.new(f"Rib_{i:03d}", rib_mesh)
        yaw = math.pi if side > 0 else 0.0
        obj.location = (side * RIB_LATERAL, y, 0.0)
        obj.rotation_euler = (0, 0, yaw)
        is_accent = (i // 2) % 6 == 5
        mat = green_vinyl if is_accent else yellow_vinyl
        obj.data.materials.append(mat)
        obj.material_slots[0].link = 'OBJECT'
        obj.material_slots[0].material = mat
        ribs_col.objects.link(obj)
        i += 1
    y += RIB_SPACING
print("Ribs:", len(ribs_col.objects))

# ── Ceiling: periodic rounded crossbeams spanning the corridor width ───
def make_ceiling_beam_mesh(name, radius=0.35, span=7.0, segs=8):
    bm = bmesh.new()
    verts = []
    for i in range(segs + 1):
        a = math.pi * (i / segs) - math.pi / 2
        y = math.sin(a) * radius
        z = -math.cos(a) * radius
        verts.append(bm.verts.new((0.0, y, z)))
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    ret = bmesh.ops.extrude_edge_only(bm, edges=edges)
    far_verts = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=far_verts, vec=(span, 0, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

CEILING_Z = 4.2
CEILING_SPAN = 7.0
beam_mesh = make_ceiling_beam_mesh("CeilingBeam_template", span=CEILING_SPAN)

if "Ceiling" in bpy.data.collections:
    ceil_col = bpy.data.collections["Ceiling"]
    for o in list(ceil_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    ceil_col = bpy.data.collections.new("Ceiling")
    scene.collection.children.link(ceil_col)

if "CeilingLights" in bpy.data.collections:
    cl_col = bpy.data.collections["CeilingLights"]
    for o in list(cl_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    cl_col = bpy.data.collections.new("CeilingLights")
    scene.collection.children.link(cl_col)

BEAM_LENGTH = 1.0
GAP = 0.35
y = 1.0
i = 0
while y < 59.0:
    obj = bpy.data.objects.new(f"CeilingBeam_{i:03d}", beam_mesh)
    obj.location = (-CEILING_SPAN / 2, y, CEILING_Z)
    obj.data.materials.append(yellow_vinyl)
    ceil_col.objects.link(obj)
    i += 1
    y += BEAM_LENGTH + GAP

# small emissive bulb spheres in each gap (separate simple mesh, cheap)
def make_bulb_mesh(name, radius=0.09):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

bulb_mesh = make_bulb_mesh("Bulb_template")
y = 1.0 + BEAM_LENGTH + GAP / 2
j = 0
while y < 59.0:
    obj = bpy.data.objects.new(f"CeilingBulb_{j:03d}", bulb_mesh)
    obj.location = (0.0, y, CEILING_Z - 0.15)
    obj.data.materials.append(bulb_mat)
    cl_col.objects.link(obj)
    j += 1
    y += BEAM_LENGTH + GAP
print("Ceiling beams:", len(ceil_col.objects), "bulbs:", len(cl_col.objects))

# ── Floor ridges: rolled edge bolsters + interior air-channel ridges ───
def make_ridge_mesh(name, radius=0.15, length=60.0, segs=8):
    bm = bmesh.new()
    verts = []
    for i in range(segs + 1):
        a = math.pi * (i / segs) - math.pi / 2
        x = math.sin(a) * radius
        z = math.cos(a) * radius
        verts.append(bm.verts.new((x, 0.0, z)))
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    ret = bmesh.ops.extrude_edge_only(bm, edges=edges)
    far_verts = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=far_verts, vec=(0, length, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

if "FloorRidges" in bpy.data.collections:
    fr_col = bpy.data.collections["FloorRidges"]
    for o in list(fr_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    fr_col = bpy.data.collections.new("FloorRidges")
    scene.collection.children.link(fr_col)

edge_mesh = make_ridge_mesh("EdgeBolster_template", radius=0.16)
interior_mesh = make_ridge_mesh("InteriorRidge_template", radius=0.10)
for idx, x in enumerate((-3.0, 3.0)):
    obj = bpy.data.objects.new(f"EdgeBolster_{idx}", edge_mesh)
    obj.location = (x, 0.0, 0.0)
    obj.data.materials.append(green_vinyl)
    fr_col.objects.link(obj)
for idx, x in enumerate((-1.0, 1.0)):
    obj = bpy.data.objects.new(f"InteriorRidge_{idx}", interior_mesh)
    obj.location = (x, 0.0, 0.0)
    obj.data.materials.append(green_floor)
    fr_col.objects.link(obj)
print("Floor ridges:", len(fr_col.objects))

# ── Frames: thin white/black gallery frames + muted photography canvases
if "Frames" not in bpy.data.collections:
    frames_col = bpy.data.collections.new("Frames")
    scene.collection.children.link(frames_col)
else:
    frames_col = bpy.data.collections["Frames"]
    for o in list(frames_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)

if "Canvases" not in bpy.data.collections:
    canvas_col = bpy.data.collections.new("Canvases")
    scene.collection.children.link(canvas_col)
else:
    canvas_col = bpy.data.collections["Canvases"]
    for o in list(canvas_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)

rng = random.Random(77)
photo_tones = [
    (0.68, 0.64, 0.56, 1.0), (0.30, 0.30, 0.31, 1.0), (0.74, 0.69, 0.52, 1.0),
    (0.45, 0.50, 0.54, 1.0), (0.80, 0.75, 0.66, 1.0), (0.38, 0.40, 0.38, 1.0),
    (0.58, 0.52, 0.60, 1.0), (0.85, 0.82, 0.76, 1.0),
]
for m in mounts:
    frame_mat = frame_white if rng.random() < 0.6 else frame_black
    color = photo_tones[rng.randrange(len(photo_tones))]
    hk.place_frame_and_canvas(m, frame_mat, frames_col, canvas_col,
                               molding_w=0.05, canvas_color=color)
print("Frames+canvases:", len(frames_col.objects))

# ── Lighting: warm key + soft green fill + split world background ──────
sun = bpy.data.objects["Sun"]
sun.data.energy = 4.2
sun.data.color = (1.0, 0.88, 0.65)
sun.data.angle = math.radians(4.0)
sun.rotation_euler = (math.radians(40), 0.0, math.radians(10))

if "Fill" not in bpy.data.objects:
    fill_data = bpy.data.lights.new("Fill", type='SUN')
    fill_obj = bpy.data.objects.new("Fill", fill_data)
    scene.collection.objects.link(fill_obj)
else:
    fill_obj = bpy.data.objects["Fill"]
    fill_data = fill_obj.data
fill_data.energy = 1.6
fill_data.color = (0.55, 0.85, 0.55)
fill_data.angle = math.radians(9.0)
fill_obj.rotation_euler = (math.radians(65), 0.0, math.radians(-110))

world = scene.world
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputWorld")
mix = nt.nodes.new("ShaderNodeMixShader")
lp = nt.nodes.new("ShaderNodeLightPath")
bg_cam = nt.nodes.new("ShaderNodeBackground")
bg_light = nt.nodes.new("ShaderNodeBackground")
bg_cam.inputs["Color"].default_value = (0.55, 0.40, 0.08, 1.0)
bg_cam.inputs["Strength"].default_value = 1.2
bg_light.inputs["Color"].default_value = (0.40, 0.32, 0.10, 1.0)
bg_light.inputs["Strength"].default_value = 0.4
out.location = (400, 0)
mix.location = (200, 0)
lp.location = (-200, 150)
bg_cam.location = (-200, -50)
bg_light.location = (-200, -200)
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt.links.new(bg_light.outputs["Background"], mix.inputs[1])
nt.links.new(bg_cam.outputs["Background"], mix.inputs[2])
nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

# ── View-layer cleanup: exclude default Collection (import leftovers) ──
def find_layer_col(layer_col, name):
    if layer_col.name == name:
        return layer_col
    for c in layer_col.children:
        found = find_layer_col(c, name)
        if found:
            return found
    return None

vl = bpy.context.view_layer
default_lc = find_layer_col(vl.layer_collection, "Collection")
if default_lc:
    default_lc.exclude = True

# ── Render review stills ────────────────────────────────────────────────
cam = bpy.data.objects["WalkCam"]
scene.camera = cam
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 960
scene.render.resolution_y = 720

orig_loc = cam.location.copy()
scene.render.filepath = str(RENDER_DIR / "entrance.png")
bpy.ops.render.render(write_still=True)

cam.location = (0.0, 26.0, 1.6)
scene.render.filepath = str(RENDER_DIR / "midpoint.png")
bpy.ops.render.render(write_still=True)
cam.location = orig_loc

# ── Save + export ───────────────────────────────────────────────────────
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))

bpy.ops.export_scene.gltf(
    filepath=str(GLB_OUT),
    export_format='GLB',
    export_lights=True,
    export_cameras=True,
    export_apply=True,
)
print("DONE. Exported:", GLB_OUT)
