"""Deterministic reef art pass. Run with Blender --background <source.blend> --python this_file.
Packed UV textures and mesh dressing export to glTF; bounded water fog is preview-only.
Original source/export backups: backups/reef-2026-09-11/.
"""
import bpy, math, random, json
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
rng=random.Random(190911)
s=bpy.context.scene
# The pass is deliberately rerun from the backed-up source for deterministic results.
for name in ['Reef_Seabed_Detail','Reef_Surface','Reef_Preview_Atmosphere']:
    old=bpy.data.collections.get(name)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(old)
def collection(name):
    c=bpy.data.collections.new(name); s.collection.children.link(c); return c
bed=collection('Reef_Seabed_Detail');water=collection('Reef_Surface');atmo=collection('Reef_Preview_Atmosphere')
def mesh_obj(name,verts,faces,col,mat,uvscale=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(mat)
    if uvscale:
        uv=me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            for li in p.loop_indices:
                v=me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv=(v.x/uvscale,v.y/uvscale)
    return ob
def image(name,rgb,noncolor=False):
    h,w=rgb.shape[:2];im=bpy.data.images.new(name,width=w,height=h)
    if noncolor: im.colorspace_settings.name='Non-Color'
    rgba=np.ones((h,w,4),dtype=np.float32);rgba[:,:,:3]=rgb
    im.pixels.foreach_set(rgba.ravel());im.pack();return im
def material(name,color,rough=.8):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m,p
def tex(m,im,socket):
    n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;m.node_tree.links.new(n.outputs['Color'],socket);return n
N=1024
v,u=np.mgrid[0:N,0:N].astype(np.float32)/N
# Tileable, warped Voronoi edge illumination: thin irregular caustic networks.
x=u*7+.32*np.sin(v*math.tau*3)+.12*np.sin(u*math.tau*2)
y=v*7+.28*np.sin(u*math.tau*2)+.16*np.cos(v*math.tau*3)
a=np.floor(x);b=np.floor(y);d1=np.full_like(x,100);d2=d1.copy()
for j in range(-1,2):
    for i in range(-1,2):
        cx=a+i;cy=b+j
        hx=np.mod(np.sin(np.mod(cx,7)*127.1+np.mod(cy,7)*311.7)*43758.5453,1)
        hy=np.mod(np.sin(np.mod(cx,7)*269.5+np.mod(cy,7)*183.3)*43758.5453,1)
        d=(cx+.2+.6*hx-x)**2+(cy+.2+.6*hy-y)**2
        d2=np.minimum(d2,np.maximum(d1,d));d1=np.minimum(d1,d)
caustic=np.exp(-((np.sqrt(d2)-np.sqrt(d1))/.057)**2)
phase=math.tau*(v*19+.23*np.sin(u*math.tau*3)+.1*np.sin(v*math.tau*2+u*math.tau))
ripple=np.sin(phase)
noise=np.random.default_rng(15).normal(0,.008,(N,N))
base=np.clip(.70+.018*ripple+noise+.16*caustic,0,1)
sand_img=image('Reef_Sand_Albedo_1K',np.stack([base*.96,base,base*.94],-1))
height=.0025*np.sin(phase)+.0007*np.sin(u*math.tau*80)*np.cos(v*math.tau*70)
gy,gx=np.gradient(height,4/N);normal=np.stack([-gx,-gy,np.ones_like(gx)],-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
sand_norm=image('Reef_Sand_Normal_1K',normal*.5+.5,True)
mat,p=material('Reef_Calcareous_Ripple_Sand',(.65,.69,.63),.86)
tex(mat,sand_img,p.inputs['Base Color']);tn=mat.node_tree.nodes.new('ShaderNodeNormalMap');tex(mat,sand_norm,tn.inputs['Color']);mat.node_tree.links.new(tn.outputs['Normal'],p.inputs['Normal'])
floor=bpy.data.objects['Floor'];floor.data.materials.clear();floor.data.materials.append(mat)
uv=floor.data.uv_layers.active or floor.data.uv_layers.new()
for poly in floor.data.polygons:
    for li in poly.loop_indices:
        vtx=floor.matrix_world@floor.data.vertices[floor.data.loops[li].vertex_index].co
        uv.data[li].uv=(vtx.x/4,vtx.y/4)
# Broad continuous seabed removes the floating corridor silhouette.
verts=[];faces=[];nx=80;ny=150
for j in range(ny+1):
    y=-15+j*100/ny
    for i in range(nx+1):
        x=-28+i*56/nx
        z=-.045+min(1,max(0,(abs(x)-2.8)/3))*(.16*math.sin(x*.62+y*.24)+.11*math.cos(y*.52-x*.31))
        verts.append((x,y,z))
for j in range(ny):
    for i in range(nx):
        k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
ob=mesh_obj('Reef_Continuous_Seabed',verts,faces,bed,mat,4)
for p0 in ob.data.polygons:p0.use_smooth=True
# Subdued natural coral colors and rough, porous surfaces, using portable PBR values.
colors=[(.32,.12,.085),(.36,.25,.10),(.22,.32,.24),(.31,.16,.24),(.22,.29,.33)]
for idx in range(5):
    m=bpy.data.materials.get('CoralFlat_'+str(idx))
    if m:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:
            for l in list(p.inputs['Base Color'].links):m.node_tree.links.remove(l)
            p.inputs['Base Color'].default_value=(*colors[idx],1);p.inputs['Roughness'].default_value=.88
# Smooth the faceted untextured colonies without adding geometry.
for o in bpy.data.collections['Reef_Coral_Dense'].objects:
    if o.type=='MESH' and any(slot.material and slot.material.name.startswith('CoralFlat') for slot in o.material_slots):
        for poly in o.data.polygons:poly.use_smooth=True
# Reef rubble in clusters outside the 2.5m clear walking channel, combined into five meshes.
rockmats=[material('Reef_Rubble_'+str(i),c)[0] for i,c in enumerate([(.23,.28,.23),(.32,.33,.27),(.39,.37,.29),(.28,.32,.30),(.36,.30,.25)])]
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
template=bpy.context.object;tv=[v.co.copy() for v in template.data.vertices];tf=[tuple(p.vertices) for p in template.data.polygons];bpy.data.objects.remove(template,do_unlink=True)
for idx,m in enumerate(rockmats):
    vv=[];ff=[]
    for k in range(100):
        side=rng.choice([-1,1]);y=rng.uniform(-3,66);x=side*rng.uniform(1.7,6.5)
        radius=rng.uniform(.07,.26);rz=rng.uniform(.45,.95);off=len(vv);ang=rng.random()*math.tau
        for q in tv:
            xx=q.x*radius*(1+.12*rng.random());yy=q.y*radius*1.3
            vv.append((x+xx*math.cos(ang)-yy*math.sin(ang),y+xx*math.sin(ang)+yy*math.cos(ang),-.025+(q.z+.6)*radius*rz))
        ff.extend(tuple(off+t for t in f) for f in tf)
    ob=mesh_obj('Reef_Rubble_Batch_'+str(idx),vv,ff,bed,m)
    for poly in ob.data.polygons:poly.use_smooth=True
# Low sea grass tufts stitch colonies into substrate; one draw call, no alpha cards.
grass,p=material('Reef_Seagrass_Olive',(.10,.20,.105),.86)
vv=[];ff=[]
for k in range(200):
    x=rng.choice([-1,1])*rng.uniform(2,5.8);y=rng.uniform(-1,64)
    for blade in range(rng.randint(4,8)):
        ang=rng.random()*math.tau;h=rng.uniform(.12,.42);w=rng.uniform(.012,.029);off=len(vv)
        for seg in range(4):
            t=seg/3;lean=.16*t*t
            for sign in [-1,1]:vv.append((x+math.cos(ang)*lean+sign*w*(1-t*.92)*math.sin(ang),y+math.sin(ang)*lean+sign*w*(1-t*.92)*math.cos(ang),.005+h*t))
        ff.extend((off+j*2,off+j*2+1,off+j*2+3,off+j*2+2) for j in range(3))
mesh_obj('Reef_Seagrass_Tufts',vv,ff,bed,grass)
# Rippled reflective surface; packed color/normal maps also survive glTF.
surface_glint=(.5+.5*np.sin(math.tau*(u*3+v*5)+2*np.sin(v*math.tau*3)))**6
surface_rgb=np.stack([.13+.16*surface_glint,.39+.21*surface_glint,.46+.22*surface_glint],-1)
surfim=image('Reef_Surface_Color_1K',surface_rgb)
wave=.065*np.sin(u*math.tau*4+.6*np.sin(v*math.tau*3))+.04*np.cos(v*math.tau*6+np.sin(u*math.tau*2))
gy,gx=np.gradient(wave,6/N);norm=np.stack([-gx,-gy,np.ones_like(gx)],-1);norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
surfnorm=image('Reef_Surface_Normal_1K',norm*.5+.5,True)
wm,p=material('Reef_Water_Surface',(.18,.45,.5),.22);p.inputs['Metallic'].default_value=.5
tex(wm,surfim,p.inputs['Base Color']);n=wm.node_tree.nodes.new('ShaderNodeNormalMap');tex(wm,surfnorm,n.inputs['Color']);wm.node_tree.links.new(n.outputs['Normal'],p.inputs['Normal'])
p.inputs['Emission Color'].default_value=(.065,.19,.23,1);p.inputs['Emission Strength'].default_value=.35
verts=[];faces=[];nx=100;ny=140
for j in range(ny+1):
    y=-15+j*100/ny
    for i in range(nx+1):
        x=-30+i*.6;z=4.6+.045*math.sin(x*2.1+y*1.2)+.025*math.sin(y*3-x*.8);verts.append((x,y,z))
for j in range(ny):
    for i in range(nx):
        k=j*(nx+1)+i;faces.append((k+nx+1,k+nx+2,k+1,k))
ob=mesh_obj('Reef_Water_Surface',verts,faces,water,wm,6)
for poly in ob.data.polygons:poly.use_smooth=True
# Replace angular, untextured colonies with tapered branching coral.
coral_col=collection('Reef_Organic_Coral')
coral_mats=[material('Reef_Organic_Coral_'+str(i),c,.9)[0] for i,c in enumerate(colors)]
def tube(vv,ff,start,end,r0,r1):
    axis=(end-start).normalized();ref=Vector((0,1,0)) if abs(axis.y)<.9 else Vector((1,0,0))
    a=axis.cross(ref).normalized();b=axis.cross(a).normalized();off=len(vv);sides=7
    for t,r in [(0,r0),(.5,(r0+r1)*.56),(1,r1)]:
        center=start.lerp(end,t)
        for n in range(sides):
            ang=n*math.tau/sides;vv.append(tuple(center+r*(a*math.cos(ang)+b*math.sin(ang))))
    for row in range(2):
        for n in range(sides):
            k=off+row*sides+n;l=off+row*sides+(n+1)%sides;ff.append((k,l,l+sides,k+sides))
    ff.append(tuple(off+2*sides+n for n in range(sides)))
replaced=[]
for o in list(bpy.data.collections['Reef_Coral_Dense'].objects):
    if o.type!='MESH' or not any(slot.material and slot.material.name.startswith(('CoralFlat','CoralColorVariant')) for slot in o.material_slots):continue
    corners=[o.matrix_world@Vector(c) for c in o.bound_box];center=sum(corners,Vector())/8
    height=min(1.4,max(.6,o.dimensions.z*.65));x=center.x;y=center.y
    vv=[];ff=[]
    def branch(start,direction,length,radius,depth):
        end=start+direction.normalized()*length;tube(vv,ff,start,end,radius,radius*.38 if depth else .004)
        if depth:
            for n in range(2):
                direction2=direction+Vector((rng.uniform(-.65,.65),rng.uniform(-.65,.65),rng.uniform(.05,.4)))
                branch(end,direction2,length*rng.uniform(.56,.76),radius*.57,depth-1)
    for j in range(8):
        start=Vector((x+rng.uniform(-.28,.28),y+rng.uniform(-.28,.28),.015))
        branch(start,Vector((rng.uniform(-.5,.5),rng.uniform(-.5,.5),1)),height*rng.uniform(.27,.48),.045,3)
    co=mesh_obj('Reef_Branch_Colony_'+str(len(replaced)),vv,ff,coral_col,coral_mats[len(replaced)%5])
    for poly in co.data.polygons:poly.use_smooth=True
    replaced.append(o.name)
    bpy.data.objects.remove(o,do_unlink=True)
# Additional textured outboard colonies break the single-file display-row silhouette.
source_col=bpy.data.collections['Reef_Coral_Dense']
roots=[o for o in source_col.objects if o.parent is None and any(c.type=='MESH' for c in o.children_recursive)]
textured=[r for r in roots if any(c.type=='MESH' and any(sl.material and sl.material.name=='default' for sl in c.material_slots) for c in r.children_recursive)]
for i in range(16):
    root=textured[i%len(textured)];members=[root]+list(root.children_recursive);mapping={}
    for old in members:
        new=old.copy();source_col.objects.link(new);mapping[old]=new
    for old,new in mapping.items():
        if old.parent in mapping:new.parent=mapping[old.parent]
        for mod in new.modifiers:
            if mod.type=='ARMATURE' and mod.object in mapping:mod.object=mapping[mod.object]
    new=mapping[root];new.name='Reef_Outboard_Cluster_'+str(i);new.location.x=(-1 if i%2 else 1)*rng.uniform(4.6,7);new.location.y=2+(i//2)*8+rng.uniform(-1,1);new.scale*=rng.uniform(.6,.95);new.rotation_euler.z+=rng.random()*math.tau

# Ground scaled outboard hierarchies after applying their final transforms.
bpy.context.view_layer.update()
for root in [o for o in source_col.objects if o.name.startswith('Reef_Outboard_Cluster')]:
    bottoms=[(c.matrix_world@Vector(p)).z for c in root.children_recursive if c.type=='MESH' for p in c.bound_box]
    if bottoms:root.location.z-=min(bottoms)+.025
# Water preview: finite volume only (never world volume). Runtime uses its existing depth fog.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,30,2))
ob=bpy.context.object;ob.name='Reef_Preview_Water_Volume';ob.dimensions=(100,150,40)
for c in list(ob.users_collection):c.objects.unlink(ob)
atmo.objects.link(ob)
vm=bpy.data.materials.new('Reef_Preview_Water');vm.use_nodes=True;vm.node_tree.nodes.clear();out=vm.node_tree.nodes.new('ShaderNodeOutputMaterial');vol=vm.node_tree.nodes.new('ShaderNodeVolumePrincipled');vol.inputs['Density'].default_value=.012;vol.inputs['Color'].default_value=(.22,.64,.72,1);vol.inputs['Anisotropy'].default_value=.25;vm.node_tree.links.new(vol.outputs['Volume'],out.inputs['Volume']);ob.data.materials.append(vm)
# Surface should not block the directional sunlight in the preview.
if hasattr(bpy.data.objects['Reef_Water_Surface'],'visible_shadow'):bpy.data.objects['Reef_Water_Surface'].visible_shadow=False
bpy.data.objects['Sun'].data.energy=3.2;bpy.data.objects['Sun'].data.angle=.14
bpy.data.objects['Fill'].data.energy=1.4
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.7
s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100
s['reef_design_revision']='2026-09-11: continuous seabed, ripple textures, reef rubble, seagrass, water surface; preview-only bounded fog'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender-scenes/underwater_reef.blend'))
s.render.filepath=str(ROOT/'renders/reef-review/after.png');bpy.ops.render.render(write_still=True)

s.camera.location.y=25
s.render.filepath=str(ROOT/'renders/reef-review/after-midpoint.png');bpy.ops.render.render(write_still=True)
s.camera.location.y=1
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.view_layer.objects:
    if ob.visible_get() and ob.name!='Reef_Preview_Water_Volume':ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/underwater_reef.glb'),export_format='GLB',use_selection=True,export_lights=True,export_cameras=True,export_animations=True)
