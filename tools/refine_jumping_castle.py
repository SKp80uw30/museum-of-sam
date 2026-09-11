"""Reference-led inflatable gallery pass. Run on the backed-up jumping-castle file.
Keeps all 32 artwork slots; changes theme-only lateral placement to flush mounting.
"""
import bpy, math, random, sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'));import hallway_kit as hk
s=bpy.context.scene;rng=random.Random(4811)
for name in ['Ribs','Ceiling','CeilingLights','FloorRidges','WallPanels']:
 c=bpy.data.collections.get(name)
 if c:
  for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
col=bpy.data.collections.new('JCastle_Reference_Finish');s.collection.children.link(col)
def mesh(name,v,f,mat,uvs=None,smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=smooth
 if uvs:
  layer=me.uv_layers.new(name='UVMap')
  for p in me.polygons:
   for li in p.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
 return ob

def material(name,c,rough=.4,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m

def image(name,rgb):
 h,w=rgb.shape[:2];im=bpy.data.images.new(name,width=w,height=h);im.colorspace_settings.name='Non-Color';rgba=np.ones((h,w,4),dtype=np.float32);rgba[:,:,:3]=rgb;im.pixels.foreach_set(rgba.ravel());im.pack();return im
N=1024;v,u=np.mgrid[0:N,0:N].astype(np.float32)/N
# Fine, directionally gathered creases plus irregular broad fabric wrinkles.
from vinyl_wrinkles import wrinkle_normal
normal=wrinkle_normal()
normal_image=image('JCastle_Vinyl_Wrinkles_1K',normal)
rough=np.clip(.32+.035*np.sin(u*math.tau*9)*np.cos(v*math.tau*11),.24,.4);rough_image=image('JCastle_Vinyl_Roughness_1K',np.stack([rough]*3,-1))
materials=[]
for name,color in [('JCastle_Sunflower_Vinyl',(.83,.43,.015)),('JCastle_Teal_Vinyl',(.012,.26,.17)),('JCastle_Deep_Green_Floor',(.014,.19,.09))]:
 m=material(name,color,.31);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.32;p.inputs['Coat Roughness'].default_value=.2
 nt=m.node_tree;n=nt.nodes.new('ShaderNodeTexImage');n.image=normal_image;nm=nt.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.6;nt.links.new(n.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],p.inputs['Normal']);r=nt.nodes.new('ShaderNodeTexImage');r.image=rough_image;nt.links.new(r.outputs['Color'],p.inputs['Roughness']);materials.append(m)
yellow,green,floormat=materials
seamyellow=material('JCastle_Yellow_Weld',(.49,.24,.012),.45);seamgreen=material('JCastle_Green_Weld',(.006,.09,.05),.46)
white=material('JCastle_White_Cotton_Mat',(.88,.87,.82),.88);black=material('JCastle_Thin_Bronze_Frame',(.075,.065,.045),.33,.35)
venue=material('JCastle_Venue_Ceiling',(.43,.54,.49),.85);metal=material('JCastle_Venue_Steel',(.15,.18,.17),.44,.45)
bulb=material('JCastle_Warm_Fixture',(.96,.9,.73),.35);p=bulb.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.85,.63,1);p.inputs['Emission Strength'].default_value=3

def box(name,loc,dim,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(mat)
 # World-projected UVs on every face, retained after the bevel is evaluated.
 uv=o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
 for poly in o.data.polygons:
  axis=max(range(3),key=lambda i:abs(poly.normal[i]))
  for li in poly.loop_indices:
   co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co.y,co.z) if axis==0 else (co.x,co.z) if axis==1 else (co.x,co.y)
 if bevel:
  mod=o.modifiers.new('Soft inflated corners','BEVEL');mod.width=bevel;mod.segments=6
  mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

# Wide quilted vertical chambers; alternate entire bays rather than narrow stripes.
for side in [-1,1]:
 for j in range(75):
  y0=j*.8;bay=int(y0/7);mat=yellow if bay%2==0 else green;verts=[];faces=[];uvs=[];nu=12;nz=30
  for iz in range(nz+1):
   z=iz*3.8/nz
   for iy in range(nu+1):
    t=iy/nu;y=y0+t*.8;bulge=.20*(math.sin(math.pi*t)**.65)*(math.sin(math.pi*iz/nz)**.18)
    wrinkle=.0035*math.sin(z*24+y*19)*math.sin(math.pi*t)
    verts.append((side*(1.97-bulge+wrinkle),y,z));uvs.append((y,z))
  for iz in range(nz):
   for iy in range(nu):
    k=iz*(nu+1)+iy;q=(k,k+1,k+nu+2,k+nu+1);faces.append(q if side<0 else tuple(reversed(q)))
  mesh('WallChamber_'+('L' if side<0 else 'R')+'_'+str(j),verts,faces,mat,uvs)
  box('Weld_'+str(side)+'_'+str(j),(side*1.965,y0,1.9),(.012,.018,3.75),seamyellow if bay%2==0 else seamgreen,.005)
# Seven fully inflated longitudinal floor channels, not a flat floor with thin rails.
verts=[];faces=[];uvs=[];channels=7;ns=16;ny=240;cw=3.6/channels
for lane in range(channels):
 off=len(verts)
 for j in range(ny+1):
  y=j*60/ny
  for i in range(ns+1):
   t=i/ns;x=-1.8+(lane+t)*cw
   z=.15*(math.sin(math.pi*t)**.65)-.025+.006*math.sin(y*4+lane)*math.sin(math.pi*t)
   verts.append((x,y,z));uvs.append((x,y))
 for j in range(ny):
  for i in range(ns):
   k=off+j*(ns+1)+i;faces.append((k,k+1,k+ns+2,k+ns+1))
o=mesh('Inflated_Floor',verts,faces,floormat,uvs);floor=bpy.data.objects['Floor'];floor.data=o.data;bpy.data.objects.remove(o,do_unlink=True)
for side in [-1,1]:box('EdgeBolster_'+str(side),(side*1.82,30,.06),(.18,60,.20),green,.085)
# Fewer, much deeper crossbeams. Open bays reveal the exhibition hall overhead.
for j,y in enumerate(range(0,61,7)):
 box('CeilingBeam_'+str(j),(0,y,3.48),(4.25,1.10,.84),green if j%3==2 else yellow,.29)
box('JCastle_Venue_Roof',(0,30,5.65),(14,78,.12),venue)
for j in range(0,67,6):
 box('JCastle_Roof_Truss_'+str(j),(0,j,5.40),(13,.085,.22),metal,.025)
for x in [-4,-2,0,2,4]:box('JCastle_Roof_Purlin_'+str(x),(x,30,5.51),(.045,78,.09),metal,.012)
for j in range(9):
 y=3.5+j*7
 box('CeilingTrack_'+str(j),(.5,y,4.95),(.025,.025,1.15),metal,.009)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.09,location=(.5,y,4.4));o=bpy.context.object;o.name='CeilingBulb_'+str(j)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(bulb)
 light=bpy.data.lights.new('JCastle_CeilingLight_'+str(j),'POINT');light.energy=95;light.color=(1,.94,.82);light.shadow_soft_size=.5
 o=bpy.data.objects.new(light.name,light);col.objects.link(o);o.location=(.5,y,4.3)
# Make each gallery display lie flush against the wall with a generous white mat.
for mount in bpy.data.collections['FrameMounts'].objects:
 side=-1 if mount.location.x<0 else 1;suffix=mount.name.replace('FrameMount_','');mount.location.x=side*1.70;mount['lateral_offset']=1.70;mount['tilt_deg']=0;mount.rotation_euler.x=0
 frame=bpy.data.objects['Frame_'+suffix];canvas=bpy.data.objects['Canvas_'+suffix]
 frame.location=mount.location;frame.rotation_euler=(0,0,mount.rotation_euler.z)
 frame.data=hk.build_frame_mesh(mount['frame_width'],mount['frame_height'],.018,.035,mesh_name=frame.name+'_Refined')[0];frame.data.materials.clear();frame.data.materials.append(black)
 canvas.location=mount.location;canvas.location.x-=side*.007;canvas.rotation_euler=frame.rotation_euler;canvas.scale=(.76,1,.76)
 w=mount['frame_width'];h=mount['frame_height'];matboard=mesh('PictureMat_'+suffix,[(-w/2,0,-h/2),(w/2,0,-h/2),(w/2,0,h/2),(-w/2,0,h/2)],[(0,1,2,3)],white,[(0,0),(1,0),(1,1),(0,1)],False);matboard.location=mount.location;matboard.location.x+=side*.002;matboard.rotation_euler=frame.rotation_euler
# A softly lit final yellow chamber completes the view down the passage.
box('JCastle_End_Wall',(0,61,1.9),(4.2,.36,3.8),yellow,.16)
sun=bpy.data.objects['Sun'];sun.data.energy=1.8;sun.data.color=(1,.96,.86);sun.rotation_euler=(math.radians(35),math.radians(-15),math.radians(15));sun.data.angle=.12
fill=bpy.data.objects['Fill'];fill.data.energy=1.5;fill.data.color=(.87,.94,1)
world=s.world;world.use_nodes=True;world.node_tree.nodes.clear();bg=world.node_tree.nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.62,.67,.70,1);bg.inputs['Strength'].default_value=.6;out=world.node_tree.nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],out.inputs['Surface'])
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=1
s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100;s.camera.location=(0,1,1.6)
s['reference_revision']='48f3fa50..._0: yellow/teal inflated bays, wrinkled vinyl, seven air channels, white-matted art, open venue roof'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender-scenes/jumping_castle.blend'))
s.render.filepath=str(ROOT/'renders/jumping-castle-review/after.png');bpy.ops.render.render(write_still=True)
s.camera.location.y=25;s.render.filepath=str(ROOT/'renders/jumping-castle-review/after-midpoint.png');bpy.ops.render.render(write_still=True);s.camera.location.y=1
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.view_layer.objects:
 if o.visible_get():o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/jumping_castle.glb'),export_format='GLB',use_selection=True,export_lights=True,export_cameras=True,export_apply=True)
print('Reference-aligned jumping castle complete')
