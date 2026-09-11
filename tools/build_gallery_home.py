"""Gallery home theme — expensive designer-house hallway.
Run headless: blender --background <repo>/blender-scenes/gallery_home.blend --python this_file
(not via blender-mcp — see the coordination note in TODO.md's jumping-castle
write-up for why: that addon's live session is shared with any other
concurrent Blender user, so this script opens its own separate process).

Reference: Museum-locations/Create_a_beautiful_large_hallway_in_an_expensive_
designer_hou..._a6636782..._2.png (plus siblings _0/_1/_3 in the same set) —
cream/white raised-panel wainscoting, coffered ceiling with recessed
downlights and hanging lantern pendants, travertine/marble floor with a
dark inlaid border and a patterned runner rug, large abstract art flanked
by wall sconces, console tables with lamps, ending in a bright glazed door.
Branches from base_hallway.blend (32 FrameMounts, Floor, Sun, WalkCam) —
never from another theme's file.

PolyHaven textures for this pass were downloaded via the interactive
blender-mcp session (the only way to reach PolyHaven's API from this
project) while it happened to have forest_walkway.blend open for a
concurrent session — so rather than risk that shared scene, the downloaded
images were saved out to tools/_texture_cache/gallery_home/ and the 4
orphan materials that download created were removed again without saving
that file. This script loads the cached image files directly instead of
depending on blender-mcp at all.
"""
import bpy, bmesh, math, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "blender-scenes" / "base_hallway.blend"
OUT_BLEND = ROOT / "blender-scenes" / "gallery_home.blend"
GLB_OUT = ROOT / "exports" / "gallery_home.glb"
RENDER_DIR = ROOT / "renders" / "gallery-home-review"
TEX_DIR = ROOT / "tools" / "_texture_cache" / "gallery_home"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(ROOT / "tools"))
import hallway_kit as hk

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene = bpy.context.scene

# ── PBR material helper (Diffuse/Rough/nor_gl from the local texture cache)
def make_pbr_material(name, tex_prefix, mapping_scale=(1.0, 1.0, 1.0), tint=None, tint_fac=0.5, roughness_mul=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = mapping_scale
    nt.links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])

    diff_path = TEX_DIR / f"{tex_prefix}_Diffuse.jpg"
    rough_path = TEX_DIR / f"{tex_prefix}_Rough.jpg"
    nor_path = TEX_DIR / f"{tex_prefix}_nor_gl.jpg"

    diff_img = bpy.data.images.load(str(diff_path), check_existing=True)
    diff_node = nt.nodes.new("ShaderNodeTexImage")
    diff_node.image = diff_img
    nt.links.new(mapping.outputs["Vector"], diff_node.inputs["Vector"])
    if tint:
        # MIX (not MULTIPLY) toward the tint color — multiply can only ever
        # darken a texture, which is the wrong direction for lightening a
        # too-brown/tan source photo toward the reference's crisp cream wall.
        tint_node = nt.nodes.new("ShaderNodeMixRGB")
        tint_node.blend_type = 'MIX'
        tint_node.inputs["Fac"].default_value = tint_fac
        tint_node.inputs["Color2"].default_value = tint
        nt.links.new(diff_node.outputs["Color"], tint_node.inputs["Color1"])
        nt.links.new(tint_node.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        nt.links.new(diff_node.outputs["Color"], bsdf.inputs["Base Color"])

    rough_img = bpy.data.images.load(str(rough_path), check_existing=True)
    rough_img.colorspace_settings.name = 'Non-Color'
    rough_node = nt.nodes.new("ShaderNodeTexImage")
    rough_node.image = rough_img
    nt.links.new(mapping.outputs["Vector"], rough_node.inputs["Vector"])
    if roughness_mul != 1.0:
        mul_node = nt.nodes.new("ShaderNodeMath")
        mul_node.operation = 'MULTIPLY'
        mul_node.inputs[1].default_value = roughness_mul
        nt.links.new(rough_node.outputs["Color"], mul_node.inputs[0])
        nt.links.new(mul_node.outputs["Value"], bsdf.inputs["Roughness"])
    else:
        nt.links.new(rough_node.outputs["Color"], bsdf.inputs["Roughness"])

    nor_img = bpy.data.images.load(str(nor_path), check_existing=True)
    nor_img.colorspace_settings.name = 'Non-Color'
    nor_node = nt.nodes.new("ShaderNodeTexImage")
    nor_node.image = nor_img
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 0.5
    nt.links.new(mapping.outputs["Vector"], nor_node.inputs["Vector"])
    nt.links.new(nor_node.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tex_coord.location = (-800, 0)
    mapping.location = (-600, 0)
    diff_node.location = (-350, 250)
    rough_node.location = (-350, 0)
    nor_node.location = (-350, -250)
    nmap.location = (-100, -250)
    bsdf.location = (150, 100)
    out.location = (450, 100)
    return mat

marble_floor = make_pbr_material("GH_MarbleFloor", "interior_tiles", mapping_scale=(2.0, 20.0, 1.0),
                                  tint=(0.97, 0.94, 0.87, 1.0), tint_fac=0.3, roughness_mul=0.6)
marble_border = make_pbr_material("GH_MarbleBorder", "granite_tile_03", mapping_scale=(1.0, 15.0, 1.0), roughness_mul=0.4)
wall_plaster = make_pbr_material("GH_WallPlaster", "beige_wall_002", mapping_scale=(1.5, 1.5, 1.0),
                                  tint=(0.96, 0.94, 0.89, 1.0), tint_fac=0.72, roughness_mul=1.1)

rug_runner = make_pbr_material("GH_RugRunner", "dirty_carpet", mapping_scale=(1.0, 8.0, 1.0), roughness_mul=1.0)
rug_bsdf = rug_runner.node_tree.nodes["Principled BSDF"]
# override the carpet's own (dirty/beige) diffuse with a deep warm runner
# color while keeping its weave roughness/normal detail — done by mixing
# the loaded Diffuse texture almost fully toward a flat tint.
mix = rug_runner.node_tree.nodes.new("ShaderNodeMixRGB")
mix.blend_type = 'MULTIPLY'
mix.inputs["Fac"].default_value = 1.0
mix.inputs["Color2"].default_value = (0.22, 0.16, 0.12, 1.0)
diff_node = next(n for n in rug_runner.node_tree.nodes if n.type == 'TEX_IMAGE' and 'Diffuse' in n.image.name)
rug_runner.node_tree.links.new(diff_node.outputs["Color"], mix.inputs["Color1"])
rug_runner.node_tree.links.new(mix.outputs["Color"], rug_bsdf.inputs["Base Color"])

frame_dark = bpy.data.materials.new("GH_FrameDark")
frame_dark.use_nodes = True
fb = frame_dark.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.045, 0.04, 0.035, 1.0)
fb.inputs["Roughness"].default_value = 0.35

wood_dark = bpy.data.materials.new("GH_WoodDark")
wood_dark.use_nodes = True
wb = wood_dark.node_tree.nodes["Principled BSDF"]
wb.inputs["Base Color"].default_value = (0.10, 0.07, 0.05, 1.0)
wb.inputs["Roughness"].default_value = 0.45

leaf_mat = bpy.data.materials.new("GH_PlantLeaf")
leaf_mat.use_nodes = True
lb = leaf_mat.node_tree.nodes["Principled BSDF"]
lb.inputs["Base Color"].default_value = (0.07, 0.22, 0.09, 1.0)
lb.inputs["Roughness"].default_value = 0.75

def make_emission_material(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = color
    emit.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat

bulb_mat = make_emission_material("GH_Bulb", (1.0, 0.85, 0.62, 1.0), 8.0)
daylight_mat = make_emission_material("GH_Daylight", (1.0, 0.96, 0.88, 1.0), 5.0)

# ── Floor: marble + dark inlaid border + runner rug ─────────────────────
floor = bpy.data.objects["Floor"]
floor.data.materials.clear()
floor.data.materials.append(marble_floor)

def make_flat_strip(name, x, width, y0, y1, z, mat):
    bm = bmesh.new()
    hw = width / 2
    verts = [bm.verts.new(c) for c in ((x - hw, y0, z), (x + hw, y0, z), (x + hw, y1, z), (x - hw, y1, z))]
    bm.faces.new(verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    scene.collection.objects.link(obj)
    return obj

if "FloorDressing" in bpy.data.collections:
    fd_col = bpy.data.collections["FloorDressing"]
    for o in list(fd_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    fd_col = bpy.data.collections.new("FloorDressing")
    scene.collection.children.link(fd_col)

for idx, x in enumerate((-2.7, 2.7)):
    o = make_flat_strip(f"Border_{idx}", x, 0.22, 0.0, 60.0, 0.004, marble_border)
    fd_col.objects.link(o)
    scene.collection.objects.unlink(o)

rug = make_flat_strip("Rug_Runner", 0.0, 1.7, 3.0, 57.0, 0.006, rug_runner)
fd_col.objects.link(rug)
scene.collection.objects.unlink(rug)

# ── Wall panels per mount + continuous background wall ─────────────────
mounts = [o for o in bpy.data.objects if o.name.startswith("FrameMount_")]

if "WallPanels" in bpy.data.collections:
    wp_col = bpy.data.collections["WallPanels"]
    for o in list(wp_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    wp_col = bpy.data.collections.new("WallPanels")
    scene.collection.children.link(wp_col)

def make_panel(mount, pad=0.5, setback=0.05, thickness=0.04):
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
    obj.data.materials.append(wall_plaster)
    bevel = obj.modifiers.new("Bevel", 'BEVEL')
    bevel.width = 0.025
    bevel.segments = 3
    wp_col.objects.link(obj)
    return obj

for m in mounts:
    make_panel(m)

# continuous flat background wall behind the panels, full corridor height
def make_background_wall(name, x, y0, y1, z0, z1, mat):
    bm = bmesh.new()
    verts = [bm.verts.new(c) for c in ((x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1))]
    bm.faces.new(verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    scene.collection.objects.link(obj)
    return obj

if "Walls" in bpy.data.collections:
    wall_col = bpy.data.collections["Walls"]
    for o in list(wall_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    wall_col = bpy.data.collections.new("Walls")
    scene.collection.children.link(wall_col)

for side, x in (("left", -2.95), ("right", 2.95)):
    o = make_background_wall(f"Wall_{side}", x, 0.0, 60.0, 0.0, 3.6, wall_plaster)
    wall_col.objects.link(o)
    scene.collection.objects.unlink(o)

# ── Wall sconces beside each frame ──────────────────────────────────────
if "Sconces" in bpy.data.collections:
    sconce_col = bpy.data.collections["Sconces"]
    for o in list(sconce_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    sconce_col = bpy.data.collections.new("Sconces")
    scene.collection.children.link(sconce_col)

def make_sconce_mesh(name, w=0.10, h=0.16, d=0.05):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= w
        v.co.z *= h
        v.co.y *= d
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

sconce_mesh = make_sconce_mesh("Sconce_template")
for i, m in enumerate(mounts):
    yaw = m.rotation_euler.z
    half_w = m["frame_width"] / 2 + 0.22
    side_sign = 1 if (i % 2 == 0) else -1
    lx = side_sign * half_w
    dx = lx * math.cos(yaw)
    dy = lx * math.sin(yaw)
    setback = 0.03
    ndx = -setback * math.sin(yaw)
    ndy = setback * math.cos(yaw)
    obj = bpy.data.objects.new(f"Sconce_{i:03d}", sconce_mesh)
    obj.location = (m.location.x + dx + ndx, m.location.y + dy + ndy, 1.95)
    obj.rotation_euler = (0, 0, yaw)
    obj.data.materials.append(bulb_mat)
    sconce_col.objects.link(obj)

# ── Ceiling: flat plane + cove light strips + downlights + pendants ────
if "Ceiling" in bpy.data.collections:
    ceil_col = bpy.data.collections["Ceiling"]
    for o in list(ceil_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    ceil_col = bpy.data.collections.new("Ceiling")
    scene.collection.children.link(ceil_col)

CEILING_Z = 3.6
bm = bmesh.new()
verts = [bm.verts.new(c) for c in ((-3.0, 0.0, CEILING_Z), (3.0, 0.0, CEILING_Z), (3.0, 60.0, CEILING_Z), (-3.0, 60.0, CEILING_Z))]
bm.faces.new(verts)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
ceil_mesh = bpy.data.meshes.new("CeilingPlane_mesh")
bm.to_mesh(ceil_mesh)
bm.free()
ceil_obj = bpy.data.objects.new("CeilingPlane", ceil_mesh)
ceil_obj.data.materials.append(wall_plaster)
ceil_col.objects.link(ceil_obj)

# cove light strips along both edges
def make_cove_strip_mesh(name, radius=0.04, length=60.0, segs=6):
    bm = bmesh.new()
    verts = []
    for i in range(segs + 1):
        a = math.pi * (i / segs)
        x = math.sin(a) * radius
        z = -math.cos(a) * radius
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

cove_mesh = make_cove_strip_mesh("CoveStrip_template")
for side, x in (("left", -2.8), ("right", 2.8)):
    obj = bpy.data.objects.new(f"CoveLight_{side}", cove_mesh)
    obj.location = (x, 0.0, CEILING_Z - 0.02)
    obj.data.materials.append(bulb_mat)
    ceil_col.objects.link(obj)

# recessed downlights: grid of small emissive discs
def make_disc_mesh(name, radius=0.045, segs=10):
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, radius=radius, segments=segs, cap_ends=True)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

disc_mesh = make_disc_mesh("Downlight_template")
y = 2.0
i = 0
while y < 58.0:
    for x in (-1.1, 1.1):
        obj = bpy.data.objects.new(f"Downlight_{i:03d}", disc_mesh)
        obj.location = (x, y, CEILING_Z - 0.01)
        obj.rotation_euler = (math.pi, 0, 0)
        obj.data.materials.append(bulb_mat)
        ceil_col.objects.link(obj)
        i += 1
    y += 2.4

# hanging pendant lanterns: thin rod + small dark cage box + bulb, every ~16m
def make_box_mesh(name, sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def make_cyl_mesh(name, radius, height, segs=10):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=segs, radius1=radius, radius2=radius, depth=height)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

rod_mesh = make_cyl_mesh("PendantRod_template", 0.012, 0.5)
cage_mesh = make_box_mesh("PendantCage_template", 0.16, 0.16, 0.28)
pendant_bulb_mesh = make_disc_mesh("PendantBulb_template", radius=0.05, segs=8)

if "Pendants" in bpy.data.collections:
    pend_col = bpy.data.collections["Pendants"]
    for o in list(pend_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    pend_col = bpy.data.collections.new("Pendants")
    scene.collection.children.link(pend_col)

y = 8.0
i = 0
while y < 56.0:
    rod = bpy.data.objects.new(f"PendantRod_{i:03d}", rod_mesh)
    rod.location = (0.0, y, CEILING_Z - 0.25)
    rod.data.materials.append(frame_dark)
    pend_col.objects.link(rod)

    cage = bpy.data.objects.new(f"PendantCage_{i:03d}", cage_mesh)
    cage.location = (0.0, y, CEILING_Z - 0.64)
    cage.data.materials.append(frame_dark)
    pend_col.objects.link(cage)

    bulb = bpy.data.objects.new(f"PendantBulb_{i:03d}", pendant_bulb_mesh)
    bulb.location = (0.0, y, CEILING_Z - 0.64)
    bulb.rotation_euler = (math.pi / 2, 0, 0)
    bulb.data.materials.append(bulb_mat)
    pend_col.objects.link(bulb)
    i += 1
    y += 16.0

# ── Console tables + lamps (sparse) ─────────────────────────────────────
if "Consoles" in bpy.data.collections:
    con_col = bpy.data.collections["Consoles"]
    for o in list(con_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    con_col = bpy.data.collections.new("Consoles")
    scene.collection.children.link(con_col)

top_mesh = make_box_mesh("ConsoleTop_template", 0.9, 0.32, 0.04)
leg_mesh = make_cyl_mesh("ConsoleLeg_template", 0.015, 0.72)
lamp_base_mesh = make_cyl_mesh("LampBase_template", 0.05, 0.22)
lamp_shade_mesh = make_cyl_mesh("LampShade_template", 0.10, 0.16)

rng = random.Random(55)
candidates = [m for m in mounts if 4.0 < m.location.y < 56.0]
chosen = rng.sample(candidates, k=min(8, len(candidates)))
for i, m in enumerate(chosen):
    yaw = m.rotation_euler.z
    setback = 0.32
    dx = -setback * math.sin(yaw)
    dy = setback * math.cos(yaw)
    base_x = m.location.x + dx
    base_y = m.location.y + dy

    top = bpy.data.objects.new(f"ConsoleTop_{i:02d}", top_mesh)
    top.location = (base_x, base_y, 0.72)
    top.rotation_euler = (0, 0, yaw)
    top.data.materials.append(wood_dark)
    con_col.objects.link(top)

    for lx, ly in ((-0.4, -0.12), (0.4, -0.12), (-0.4, 0.12), (0.4, 0.12)):
        wx = base_x + lx * math.cos(yaw) - ly * math.sin(yaw)
        wy = base_y + lx * math.sin(yaw) + ly * math.cos(yaw)
        leg = bpy.data.objects.new(f"ConsoleLeg_{i:02d}_{lx}_{ly}", leg_mesh)
        leg.location = (wx, wy, 0.36)
        leg.data.materials.append(wood_dark)
        con_col.objects.link(leg)

    lamp_base = bpy.data.objects.new(f"LampBase_{i:02d}", lamp_base_mesh)
    lamp_base.location = (base_x, base_y, 0.85)
    lamp_base.data.materials.append(wood_dark)
    con_col.objects.link(lamp_base)

    lamp_shade = bpy.data.objects.new(f"LampShade_{i:02d}", lamp_shade_mesh)
    lamp_shade.location = (base_x, base_y, 1.04)
    lamp_shade.data.materials.append(bulb_mat)
    con_col.objects.link(lamp_shade)

# ── Potted plants (sparse) ───────────────────────────────────────────────
if "Plants" in bpy.data.collections:
    plant_col = bpy.data.collections["Plants"]
    for o in list(plant_col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
else:
    plant_col = bpy.data.collections.new("Plants")
    scene.collection.children.link(plant_col)

pot_mesh = make_cyl_mesh("PlantPot_template", 0.14, 0.28)

def make_leaf_blob_mesh(name, radius=1.0, noise=0.3, subdiv=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    rng2 = random.Random(hash(name) & 0xFFFF)
    import mathutils
    for v in bm.verts:
        jitter = mathutils.Vector((rng2.uniform(-noise, noise), rng2.uniform(-noise, noise), rng2.uniform(-noise, noise)))
        v.co += jitter
        v.co.z = abs(v.co.z) * 1.3
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

leaf_blob_mesh = make_leaf_blob_mesh("PlantLeaf_template", radius=0.22)

plant_mounts = rng.sample(mounts, k=6)
for i, m in enumerate(plant_mounts):
    yaw = m.rotation_euler.z
    setback = 0.30
    dx = -setback * math.sin(yaw)
    dy = setback * math.cos(yaw)
    px = m.location.x + dx + rng.uniform(-0.3, 0.3)
    py = m.location.y + dy + rng.uniform(-0.3, 0.3)

    pot = bpy.data.objects.new(f"PlantPot_{i:02d}", pot_mesh)
    pot.location = (px, py, 0.14)
    pot.data.materials.append(wood_dark)
    plant_col.objects.link(pot)

    for b in range(5):
        blob = bpy.data.objects.new(f"PlantLeaf_{i:02d}_{b}", leaf_blob_mesh)
        blob.location = (px + rng.uniform(-0.12, 0.12), py + rng.uniform(-0.12, 0.12), 0.32 + rng.uniform(0.0, 0.28))
        blob.rotation_euler = (0, 0, rng.uniform(0, math.pi * 2))
        s = rng.uniform(0.8, 1.3)
        blob.scale = (s, s, s)
        blob.data.materials.append(leaf_mat)
        plant_col.objects.link(blob)

# ── Far-end daylight glow (a vertical quad, not the horizontal-strip helper)
def make_vertical_quad(name, x0, x1, y, z0, z1, mat):
    bm = bmesh.new()
    verts = [bm.verts.new(c) for c in ((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1))]
    bm.faces.new(verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    scene.collection.objects.link(obj)
    return obj

glow = make_vertical_quad("FarDoorGlow", -2.7, 2.7, 59.5, 0.3, 3.3, daylight_mat)

# ── Frames: dark thin frames + muted "abstract art" canvases ───────────
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

art_tones = [
    (0.72, 0.68, 0.58, 1.0), (0.18, 0.16, 0.15, 1.0), (0.55, 0.42, 0.24, 1.0),
    (0.40, 0.38, 0.42, 1.0), (0.78, 0.74, 0.64, 1.0), (0.28, 0.24, 0.20, 1.0),
    (0.62, 0.50, 0.34, 1.0), (0.85, 0.82, 0.74, 1.0),
]
for m in mounts:
    color = art_tones[rng.randrange(len(art_tones))]
    hk.place_frame_and_canvas(m, frame_dark, frames_col, canvas_col,
                               molding_w=0.045, canvas_color=color)

# ── Lighting: warm neutral interior, not moody/colored atmosphere ──────
sun = bpy.data.objects["Sun"]
sun.data.energy = 7.0
sun.data.color = (1.0, 0.95, 0.87)
sun.data.angle = math.radians(3.0)
sun.rotation_euler = (math.radians(45), 0.0, math.radians(8))

if "Fill" not in bpy.data.objects:
    fill_data = bpy.data.lights.new("Fill", type='SUN')
    fill_obj = bpy.data.objects.new("Fill", fill_data)
    scene.collection.objects.link(fill_obj)
else:
    fill_obj = bpy.data.objects["Fill"]
    fill_data = fill_obj.data
fill_data.energy = 3.2
fill_data.color = (1.0, 0.92, 0.80)
fill_data.angle = math.radians(10.0)
fill_obj.rotation_euler = (math.radians(60), 0.0, math.radians(-100))

world = scene.world
nt = world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputWorld")
mix2 = nt.nodes.new("ShaderNodeMixShader")
lp = nt.nodes.new("ShaderNodeLightPath")
bg_cam = nt.nodes.new("ShaderNodeBackground")
bg_light = nt.nodes.new("ShaderNodeBackground")
bg_cam.inputs["Color"].default_value = (0.85, 0.83, 0.78, 1.0)
bg_cam.inputs["Strength"].default_value = 1.4
bg_light.inputs["Color"].default_value = (0.75, 0.73, 0.68, 1.0)
bg_light.inputs["Strength"].default_value = 0.85
out.location = (400, 0)
mix2.location = (200, 0)
lp.location = (-200, 150)
bg_cam.location = (-200, -50)
bg_light.location = (-200, -200)
nt.links.new(lp.outputs["Is Camera Ray"], mix2.inputs["Fac"])
nt.links.new(bg_light.outputs["Background"], mix2.inputs[1])
nt.links.new(bg_cam.outputs["Background"], mix2.inputs[2])
nt.links.new(mix2.outputs["Shader"], out.inputs["Surface"])

# ── UVs: real UV maps for everything with an image texture ─────────────
uv_targets = [floor] + [o for o in wp_col.objects] + [o for o in wall_col.objects] + [ceil_obj]
uv_targets += [o for o in fd_col.objects]
bpy.ops.object.select_all(action='DESELECT')
for o in uv_targets:
    o.select_set(True)
bpy.context.view_layer.objects.active = uv_targets[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# ── View-layer cleanup: exclude default Collection ──────────────────────
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
scene.cycles.samples = 48
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
