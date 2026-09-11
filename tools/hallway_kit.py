"""
Museum of Sam — shared hallway/frame kit.

Reusable across all 5 themed scenes. This module is NOT per-theme dressing —
it is the toolkit that Phase 1 (mount generation) and Phase 3 (frame
geometry) call into for every scene, so neither step gets hand-rewritten
per theme. Per-theme visual style (wood vs. gilt vs. brushed metal, molding
proportions, wall vs. freestanding-post mounting) is passed in as
parameters/materials by the calling scene script, not hardcoded here.

Usage from Blender's Python console / blender-mcp execute_blender_code:

    import sys
    sys.path.insert(0, "/Users/stevekelly/Pictures/museum-of-sam/tools")
    import hallway_kit as hk
    import importlib; importlib.reload(hk)  # while iterating

See the three entry points below:
    hk.generate_frame_mounts(...)   -- Phase 1: mount empties + metadata
    hk.build_frame_mesh(...)        -- Phase 3: parametric frame geometry
    hk.place_frame_and_canvas(...)  -- Phase 3: frame + swappable-art canvas
                                        for one mount, tilt-synced
"""

import bpy
import bmesh
import math
import random


# ---------------------------------------------------------------------------
# Phase 1 — mount generation
# ---------------------------------------------------------------------------

def generate_frame_mounts(
    collection_name="FrameMounts",
    corridor_length=60.0,
    target_count_per_side=16,
    start_margin=2.5,
    end_margin=2.5,
    width_range=(0.7, 2.1),
    aspect_range=(0.7, 1.3),
    height_clamp=(0.6, 2.0),
    gap_range=(0.9, 2.6),
    lateral_offset_range=(1.5, 2.6),
    center_z_range=(1.1, 1.9),
    tilt_range=(-10.0, 10.0),
    seed_left=1,
    seed_right=2,
    clear_existing=True,
):
    """
    Populate `collection_name` with FrameMount empties along both walls of
    a corridor running along +Y, matching the irregular-by-design spacing
    documented in CLAUDE.md (independent per-wall random seed, varied
    width/height/gaps/tilt — not an evenly-spaced grid).

    Places up to `target_count_per_side` mounts per wall, walking forward
    with randomized gaps until either the target count is reached or
    `corridor_length - end_margin` runs out (whichever first). Returns a
    dict with the actual counts placed per side, so callers can tell if
    corridor_length needs to grow to hit their target.

    Deliberately count-driven rather than length-driven: to reach ~30+
    mounts in a scene, raise `target_count_per_side` (and give
    `corridor_length` enough headroom) rather than hand-tuning gaps.
    """
    if collection_name in bpy.data.collections:
        col = bpy.data.collections[collection_name]
        if clear_existing:
            for o in list(col.objects):
                bpy.data.objects.remove(o, do_unlink=True)
    else:
        col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(col)

    usable_length = corridor_length - start_margin - end_margin
    counts = {}

    for wall_side, seed, yaw in (("left", seed_left, math.radians(90)),
                                  ("right", seed_right, math.radians(-90))):
        rng = random.Random(seed)
        y = start_margin
        placed = 0
        idx = 0
        while placed < target_count_per_side:
            width = rng.uniform(*width_range)
            aspect = rng.uniform(*aspect_range)
            height = min(max(width * aspect, height_clamp[0]), height_clamp[1])
            gap = rng.uniform(*gap_range)

            if placed > 0:
                y += gap
            center_y = y + width / 2
            if center_y > start_margin + usable_length:
                break

            idx += 1
            lateral_offset = rng.uniform(*lateral_offset_range)
            center_z = rng.uniform(*center_z_range)
            tilt_deg = rng.uniform(*tilt_range)
            x = -lateral_offset if wall_side == "left" else lateral_offset

            name = f"FrameMount_{wall_side}_{idx:02d}"
            empty = bpy.data.objects.new(name, None)
            empty.empty_display_type = 'PLAIN_AXES'
            empty.empty_display_size = 0.3
            empty.location = (x, center_y, center_z)
            empty.rotation_euler = (0.0, 0.0, yaw)
            empty["wall_side"] = wall_side
            empty["frame_width"] = round(width, 3)
            empty["frame_height"] = round(height, 3)
            empty["lateral_offset"] = round(lateral_offset, 3)
            empty["tilt_deg"] = round(tilt_deg, 2)
            col.objects.link(empty)

            y += width
            placed += 1

        counts[wall_side] = placed
        if placed < target_count_per_side:
            print(f"[hallway_kit] WARNING: only placed {placed}/{target_count_per_side} "
                  f"mounts on '{wall_side}' wall before running out of corridor_length "
                  f"({corridor_length}m) — increase corridor_length to fit more.")

    return counts


# ---------------------------------------------------------------------------
# Phase 3 — frame geometry
# ---------------------------------------------------------------------------

def build_frame_mesh(width, height, molding_w=None, depth=None, mesh_name="Frame_mesh"):
    """
    Parametric picture-frame border: 4 butt-jointed bars (top/bottom span
    the full outer width, left/right fit between them), asymmetric depth
    so a canvas plane sitting at local y=0 lands recessed just behind the
    front lip (avoids z-fighting without moving the canvas).

    `width`/`height` are the artwork OPENING size (matches a mount's
    stored frame_width/frame_height) — bars extend outward from there.
    molding_w/depth auto-scale from size when left None; pass explicit
    values for a different per-theme style (thin gallery frame, chunky
    castle frame, etc).
    """
    if molding_w is None:
        molding_w = min(0.11, max(0.045, min(width, height) * 0.075))
    if depth is None:
        depth = molding_w * 0.6

    bm = bmesh.new()
    hw, hh = width / 2, height / 2
    y0, y1 = -depth * 0.75, depth * 0.25

    def add_box(cx, cz, sx, sz):
        x0, x1 = cx - sx / 2, cx + sx / 2
        z0, z1 = cz - sz / 2, cz + sz / 2
        coords = [
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ]
        vs = [bm.verts.new(c) for c in coords]
        faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        for f in faces:
            bm.faces.new([vs[i] for i in f])

    add_box(0, hh - molding_w / 2, width + molding_w, molding_w)
    add_box(0, -hh + molding_w / 2, width + molding_w, molding_w)
    inner_h = height - molding_w
    add_box(-hw + molding_w / 2, 0, molding_w, inner_h)
    add_box(hw - molding_w / 2, 0, molding_w, inner_h)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh, molding_w, depth


def make_swappable_art_material(name, base_color=(0.6, 0.6, 0.6, 1.0)):
    """
    Canvas material with an Image Texture node wired into Base Color. The
    node is pre-filled with a small solid-color placeholder image (not
    left unassigned — an empty Image Texture node renders black/magenta
    and overrides Base Color's default_value, so leaving it empty makes
    every placeholder canvas look broken until Phase 5). Phase 5 swaps
    real artwork in per-canvas with:

        mat.node_tree.nodes["ArtImage"].image = bpy.data.images.load(path)

    which is a straight `.image` reassignment — no node-graph rewiring —
    so the placeholder image existing now doesn't change that contract.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    img_node = nodes.new("ShaderNodeTexImage")
    img_node.name = "ArtImage"
    img_node.location = (-300, 300)

    placeholder_img = bpy.data.images.new(f"{name}_placeholder", width=8, height=8, alpha=False)
    pixels = list(base_color[:3]) + [1.0]
    placeholder_img.pixels = pixels * (8 * 8)
    placeholder_img.pack()
    img_node.image = placeholder_img

    bsdf.inputs["Base Color"].default_value = base_color
    links.new(img_node.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def place_frame_and_canvas(mount, frame_material, frames_collection, canvas_collection,
                            molding_w=None, depth=None, canvas_color=None, bevel_width=None,
                            bevel_segments=2):
    """
    Build and place one frame + its backing canvas for a single FrameMount
    empty, reading width/height/tilt straight off the mount's custom
    properties. Applies the SAME tilt to both frame and canvas so they
    stay coplanar (see CLAUDE.md working-conventions note — Phase 2's
    placeholder canvases previously only got yaw rotation, which visibly
    diverged from a tilted frame; this function is the fix, applied by
    default for every future theme).

    Returns (frame_obj, canvas_obj).
    """
    width = mount["frame_width"]
    height = mount["frame_height"]
    tilt = mount.get("tilt_deg", 0.0)
    suffix = mount.name.replace("FrameMount_", "")
    rot = (math.radians(tilt), 0.0, mount.rotation_euler.z)

    mesh, molding_w, depth = build_frame_mesh(width, height, molding_w, depth,
                                               mesh_name=f"Frame_{suffix}_mesh")
    frame_obj = bpy.data.objects.new(f"Frame_{suffix}", mesh)
    frame_obj.location = mount.location.copy()
    frame_obj.rotation_euler = rot
    frame_obj.data.materials.append(frame_material)

    if bevel_width is None:
        bevel_width = min(0.012, molding_w * 0.18)
    bevel = frame_obj.modifiers.new("Bevel", 'BEVEL')
    bevel.width = bevel_width
    bevel.segments = bevel_segments
    frames_collection.objects.link(frame_obj)

    ctx = bpy.context
    ctx.view_layer.objects.active = frame_obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)

    canvas_mesh = bpy.data.meshes.new(f"Canvas_{suffix}_mesh")
    bm = bmesh.new()
    hw, hh = width / 2, height / 2
    verts = [bm.verts.new((x, 0.0, z)) for x, z in
             ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
    face = bm.faces.new(verts)
    # Real UV coords, not left implicit — glTF has no "Generated" coordinate
    # fallback like Blender's Texture Coordinate node does, and without a UV
    # layer every Image Texture sample collapses to a single (0,0,0) pixel.
    # Invisible today since the Phase 3 placeholder is a solid color (every
    # pixel is identical either way), but it would silently break real
    # artwork the moment Phase 5's manifest swap loads an actual photo.
    uv_layer = bm.loops.layers.uv.new()
    for loop, uv in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv_layer].uv = uv
    bm.to_mesh(canvas_mesh)
    bm.free()

    canvas_obj = bpy.data.objects.new(f"Canvas_{suffix}", canvas_mesh)
    canvas_obj.location = mount.location.copy()
    canvas_obj.rotation_euler = rot
    color = canvas_color if canvas_color else (0.6, 0.6, 0.6, 1.0)
    canvas_mat = make_swappable_art_material(f"Art_{suffix}", base_color=color)
    canvas_obj.data.materials.append(canvas_mat)
    canvas_collection.objects.link(canvas_obj)

    return frame_obj, canvas_obj
