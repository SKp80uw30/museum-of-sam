"""Forest art pass via Blender MCP, run against the original backed-up forest.
Preserves mounts, canvases, floor name and existing theme routing.
"""
import bpy,math,random,json
import numpy as np
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=bpy.context.scene;rng=random.Random(110926)
assert not bpy.data.collections.get('Forest_Refined'),'Reload backups/forest-2026-09-11/forest_walkway.blend before rerunning'
col=bpy.data.collections.new('Forest_Refined');s.collection.children.link(col)
def mat(name,c,rough=.8,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;m.diffuse_color=(*c,1);return m

def mesh(name,v,f,mats,indices=None,uvscale=None):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);col.objects.link(ob)
 for m in mats:me.materials.append(m)
 if indices:
  for p,i in zip(me.polygons,indices):p.material_index=i
 if any(m.name.startswith(('Forest_Leaf_Natural','Forest_Fallen_Leaf')) for m in mats) or name=='Forest_Ivy_Stems':
  for p in me.polygons:p.use_smooth=True
 if any(m.name.startswith('Forest_Leaf_Natural') for m in mats):
  layer=me.uv_layers.new(name='UVMap');coords=[(0,.5),(.18,.175),(.48,0),(.78,.175),(1,.5),(.78,.825),(.48,1),(.18,.825),(.48,.5)]
  for poly in me.polygons:
   for li in poly.loop_indices:layer.data[li].uv=coords[me.loops[li].vertex_index%9]
 if uvscale:
  layer=me.uv_layers.new(name='UVMap')
  for p in me.polygons:
   for li in p.loop_indices:
    co=me.vertices[me.loops[li].vertex_index].co;layer.data[li].uv=(co.x/uvscale,co.y/uvscale)
 return ob

def box(v,f,center,dim):
 off=len(v);x,y,z=center;dx,dy,dz=[a/2 for a in dim]
 v.extend([(x+a*dx,y+b*dy,z+c*dz) for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
 f.extend(tuple(off+i for i in q) for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])

def tube(v,f,start,end,r0,r1,sides=9):
 start=Vector(start);end=Vector(end);axis=(end-start).normalized();ref=Vector((0,1,0)) if abs(axis.y)<.9 else Vector((1,0,0));a=axis.cross(ref).normalized();b=axis.cross(a).normalized();off=len(v)
 for t,r in [(0,r0),(.5,(r0+r1)*.53),(1,r1)]:
  c=start.lerp(end,t)
  for j in range(sides):
   an=j*math.tau/sides;v.append(tuple(c+r*(a*math.cos(an)+b*math.sin(an))))
 for k in range(2):
  for j in range(sides):
   n=off+k*sides+j;nn=off+k*sides+(j+1)%sides;f.append((n,nn,nn+sides,n+sides))
 f.append(tuple(off+2*sides+j for j in range(sides)))

def make_image(name,rgb,noncolor=False):
 h,w=rgb.shape[:2];im=bpy.data.images.new(name,width=w,height=h)
 if noncolor:im.colorspace_settings.name='Non-Color'
 a=np.ones((h,w,4),dtype=np.float32);a[:,:,:3]=rgb;im.pixels.foreach_set(a.ravel());im.pack();return im

def tex(m,im,socket):
 n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;m.node_tree.links.new(n.outputs['Color'],socket);return n

N=1024;v,u=np.mgrid[0:N,0:N].astype(np.float32)/N
rand=np.random.default_rng(33)
# Wood grain and a worn silvery surface: a tile shared by individual planks.
grain=np.sin(v*math.tau*29+1.5*np.sin(u*math.tau*3)+.8*np.sin(u*math.tau*7+v*12))
fine=np.sin(v*math.tau*91+2*np.sin(u*math.tau*4))
shade=np.clip(.40+.009*grain+.005*fine+.018*np.sin(v*math.tau*7)+.025*np.sin(u*math.tau*2+v*7)+rand.normal(0,.009,(N,N)),.1,.7)
woodim=make_image('Forest_Weathered_Wood_1K',np.stack([shade,shade*.91,shade*.75],-1))
height=.0003*grain+.00015*fine;gy,gx=np.gradient(height,3/N);normal=np.stack([-gx,-gy,np.ones_like(gx)],-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
woodnorm=make_image('Forest_Wood_Normal_1K',normal*.5+.5,True)
wood=mat('Forest_Silvered_Oak',(.3,.27,.2),.87);p=wood.node_tree.nodes.get('Principled BSDF');tex(wood,woodim,p.inputs['Base Color']);nm=wood.node_tree.nodes.new('ShaderNodeNormalMap');tex(wood,woodnorm,nm.inputs['Color']);wood.node_tree.links.new(nm.outputs['Normal'],p.inputs['Normal'])
vv=[];ff=[]
for j in range(241):
 y=j*.25;box(vv,ff,(rng.uniform(-.026,.026),y,-.072),(3+rng.uniform(-.035,.035),.241,.144))
old=bpy.data.objects['Floor'];ob=mesh('Forest_Boardwalk',vv,ff,[wood]);old.data=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
uv=old.data.uv_layers.new(name='UVMap')
for poly in old.data.polygons:
 for li in poly.loop_indices:
  co=old.data.vertices[old.data.loops[li].vertex_index].co;board=int(poly.index/6);uv.data[li].uv=(co.x/3+(board%7)*.13,(co.y-board*.25)*2+board*.117)
bev=old.modifiers.new('Worn plank edges','BEVEL');bev.width=.009;bev.segments=2
# Leave the edge bevel editable; the glTF exporter evaluates modifiers.
# Continuous forest substrate with organic material variation; no floating path edges.
soilshade=.10+.025*np.sin(u*math.tau*8)*np.sin(v*math.tau*7)+rand.normal(0,.012,(N,N))
soil=mat('Forest_Humus_Moss',(.12,.12,.07),.98);p=soil.node_tree.nodes.get('Principled BSDF');tex(soil,make_image('Forest_Humus_1K',np.stack([soilshade*.85,soilshade,soilshade*.52],-1)),p.inputs['Base Color'])
vv=[];ff=[];nx=48;ny=140
for j in range(ny+1):
 y=-12+j*.6
 for i in range(nx+1):
  x=-14.4+i*.6;z=-.19+max(0,min(1,(abs(x)-1.7)/3))*(.15*math.sin(y*.7+x)+.1*math.sin(x*2-y*.3));vv.append((x,y,z))
for j in range(ny):
 for i in range(nx):
  k=j*(nx+1)+i;ff.append((k,k+1,k+nx+2,k+nx+1))
ground=mesh('Forest_Ground',vv,ff,[soil],uvscale=3)
for p in ground.data.polygons:p.use_smooth=True
# Narrow raised edging and support timbers; dappled boards remain the focal route.
vv=[];ff=[]
for side in [-1,1]:
 for j in range(20):box(vv,ff,(side*1.515,j*3+1.35,-.04),(.095,2.96,.16))
mesh('Forest_Boardwalk_Edging',vv,ff,[wood],uvscale=2)
# A weathered, moss-stained wall connects the previously floating display panels.
plaster=mat('Forest_Aged_Lime_Plaster',(.32,.31,.23),.94)
p=plaster.node_tree.nodes.get('Principled BSDF')
wallshade=.38+.055*np.sin(u*math.tau*4+np.sin(v*math.tau*3))+.025*np.sin(v*math.tau*24)*np.sin(u*math.tau*19)+rand.normal(0,.014,(N,N))
patch=np.clip((np.sin(v*math.tau*2+np.sin(u*math.tau*4))+.3)*.3,0,.5)
wallrgb=np.stack([wallshade*(1-patch*.5),wallshade*(.96-patch*.12),wallshade*(.76-patch*.55)],-1)
wallim=make_image('Forest_Patinated_Plaster_1K',wallrgb);tex(plaster,wallim,p.inputs['Base Color'])
for o in bpy.data.collections['WallPatches'].objects:
 o.data.materials.clear();o.data.materials.append(plaster)
vv=[];ff=[]
for side in [-1,1]:
 for j in range(30):
  y=j*2;h=3.6+.35*math.sin(j*.72)+rng.uniform(-.15,.15);x=side*(3.05+.13*math.sin(j*.4));box(vv,ff,(x,y+1,h/2-.16),(.24,2.035,h))
wall=mesh('Forest_Overgrown_Gallery_Walls',vv,ff,[plaster]);uv=wall.data.uv_layers.new(name='UVMap')
for poly in wall.data.polygons:
 for li in poly.loop_indices:
  co=wall.data.vertices[wall.data.loops[li].vertex_index].co;uv.data[li].uv=(co.y/3,co.z/3)
# Gilt frames: less mirror-like, rich antique brass.
m=bpy.data.materials['Forest_GiltFrame'];p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.36,.24,.085,1);p.inputs['Metallic'].default_value=.7;p.inputs['Roughness'].default_value=.32
# Support each mount physically. Frame transforms and artwork are untouched.
vv=[];ff=[]
for mount in bpy.data.collections['FrameMounts'].objects:
 x,y,z=mount.location;side=-1 if x<0 else 1;back=x+side*.16
 box(vv,ff,(back,y,z/2),(.10,.12,z))
 box(vv,ff,((back+side*3.05)/2,y,z), (abs(side*3.05-back),.095,.095))
mesh('Forest_Display_Supports',vv,ff,[wood],uvscale=2)
# Remove solid canopy blobs and coarse plant placeholders; keep the source ferns.
canopy_centers=[(o.location.copy(),o.dimensions.copy()) for o in bpy.data.collections['Canopy'].objects]
for cname in ['Canopy','HangingVines','WallVines']:
 for o in list(bpy.data.collections[cname].objects):bpy.data.objects.remove(o,do_unlink=True)
for o in list(bpy.data.collections['Understory'].objects):
 if o.name.startswith('Grass_'):bpy.data.objects.remove(o,do_unlink=True)
for o in bpy.data.collections['Understory'].objects:
 if o.name.startswith('Fern_'):
  o.location.x=math.copysign(max(1.8,abs(o.location.x)),o.location.x)
# Tapered branch skeletons, exposed roots and distant tree trunks.
bark=bpy.data.materials['bark_brown_02'];vv=[];ff=[]
for trunk in bpy.data.collections['Trunks'].objects:
 x,y,_=trunk.location;h=trunk.dimensions.z;r=trunk.dimensions.x*.45;side=1 if x>0 else -1
 for j in range(5):
  ang=j*math.tau/5+rng.random()*.5;tube(vv,ff,(x,y,.4),(x+math.cos(ang)*rng.uniform(.8,1.4),y+math.sin(ang)*rng.uniform(.8,1.4),-.1),r*.5,.035)
 for j in range(4):
  start=Vector((x,y,h*rng.uniform(.48,.75)));end=start+Vector((-side*rng.uniform(1.4,3.2),rng.uniform(-1.6,1.6),rng.uniform(.7,1.9)))
  tube(vv,ff,start,end,r*.5,.045)
  for k in range(3):
   tip=end+Vector((rng.uniform(-1,1),rng.uniform(-1.3,1.3),rng.uniform(.2,.7)));tube(vv,ff,end,tip,.047,.009,7)
for i in range(46):
 side=rng.choice([-1,1]);x=side*rng.uniform(4.5,13);y=rng.uniform(-5,68);h=rng.uniform(7,13);tube(vv,ff,(x,y,-.2),(x+rng.uniform(-.8,.8),y+rng.uniform(-.7,.7),h),rng.uniform(.12,.25),.05,9)
branches=mesh('Forest_Branches_Roots_Background_Trunks',vv,ff,[bark],uvscale=2)
for p in branches.data.polygons:p.use_smooth=True
# Curved leaf silhouettes, no alpha overdraw.
leafmats=[mat('Forest_Leaf_Natural_'+str(i),c,.68) for i,c in enumerate([(.07,.15,.018),(.11,.21,.026),(.15,.24,.038),(.19,.28,.055),(.08,.18,.035)])]
for m in leafmats:
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.035

lv,lu=np.mgrid[0:256,0:256].astype(np.float32)/256
vein=np.exp(-((lv-.5)/.018)**2)*.2+np.exp(-(np.sin((lu+abs(lv-.5)*.8)*math.tau*10)/.11)**2)*.06
for i,m in enumerate(leafmats):
 p=m.node_tree.nodes.get('Principled BSDF');color=np.array(p.inputs['Base Color'].default_value[:3]);rgb=np.clip(color[None,None,:]*(.9+vein[:,:,None]),0,1)
 tex(m,make_image('Forest_Leaf_Veins_'+str(i),rgb),p.inputs['Base Color']);p.inputs['Emission Color'].default_value=(*[float(c*.4) for c in color],1);p.inputs['Emission Strength'].default_value=.65

def leaf(v,f,center,length,width,angle,tilt=0):
 c=Vector(center);a=Vector((math.cos(angle),math.sin(angle),tilt)).normalized();b=Vector((-math.sin(angle),math.cos(angle),.1));off=len(v)
 for along,across,lift in [(0,0,0),(.18,-.65,0),(.48,-1,0),(.78,-.65,-.02),(1,0,-.06),(.78,.65,-.02),(.48,1,0),(.18,.65,0),(.48,0,.065)]:v.append(tuple(c+a*(along*length)+b*(across*width)+Vector((0,0,lift*length))))
 f.extend((off+j,off+(j+1)%8,off+8) for j in range(8))
# Batch canopy in 10m bands so distant sections can be culled.
for band in range(7):
 vv=[];ff=[];ids=[]
 centers=[(c,d) for c,d in canopy_centers if band*10-3<=c.y<(band+1)*10-3]
 for c,d in centers:
  for k in range(290):
   # Ellipsoidal layered crown; lots of small gaps for sunlight.
   az=rng.random()*math.tau;rr=math.sqrt(rng.random());x=c.x+math.cos(az)*d.x*.55*rr;y=c.y+math.sin(az)*d.y*.55*rr;z=c.z+rng.uniform(-.42,.5)*d.z
   leaf(vv,ff,(x,y,z),rng.uniform(.15,.31),rng.uniform(.045,.085),rng.random()*math.tau,rng.uniform(-.5,.5));ids.extend([rng.randrange(5)]*8)
 mesh('Forest_Canopy_Leaves_'+str(band),vv,ff,leafmats,ids)
# Distant tree grove closes the far vista without blocking the 60m walkway.
vv=[];ff=[];ids=[];sv=[];sf=[]
for i in range(22):
 x=rng.uniform(-10,10);y=rng.uniform(65,78);h=rng.uniform(5,10)
 tube(sv,sf,(x,y,-.2),(x+rng.uniform(-.4,.4),y,h),rng.uniform(.15,.32),.07)
 for j in range(240):
  a=rng.random()*math.tau;r=math.sqrt(rng.random())*2.4
  leaf(vv,ff,(x+math.cos(a)*r,y+math.sin(a)*r,h+rng.uniform(-1,1)),rng.uniform(.2,.42),rng.uniform(.07,.12),rng.random()*math.tau,rng.uniform(-.3,.3));ids.extend([rng.randrange(5)]*8)
mesh('Forest_Distant_Crowns',vv,ff,leafmats,ids);mesh('Forest_Distant_Trunks',sv,sf,[bark],uvscale=2)
# Ivy cascades and climbing stems on the gallery walls.
vv=[];ff=[];ids=[];sv=[];sf=[]
for side in [-1,1]:
 for i in range(105):
  y=rng.uniform(0,60);x=side*rng.uniform(2.7,2.93);h=rng.uniform(1,4.3);previous=Vector((x,y,-.1))
  for j in range(int(h/.13)):
   z=j*.13;center=Vector((x-.05*side*math.sin(j*.7),y+.13*math.sin(j*.4),z));tube(sv,sf,previous,center,.009,.007,5);previous=center
   leaf(vv,ff,center,rng.uniform(.12,.23),rng.uniform(.05,.09),rng.random()*math.tau,rng.uniform(-.5,1));ids.extend([rng.randrange(5)]*8)
mesh('Forest_Wall_Ivy',vv,ff,leafmats,ids);mesh('Forest_Ivy_Stems',sv,sf,[leafmats[0]])
# Airy fern fronds and wild grasses, concentrated beside the walkable planks.
vv=[];ff=[];ids=[]
for k in range(165):
 x=rng.choice([-1,1])*rng.uniform(1.72,2.85);y=rng.uniform(-1,61);size=rng.uniform(.42,.8)
 for frond in range(7):
  angle=frond*math.tau/7+rng.uniform(-.15,.15);a=Vector((math.cos(angle),math.sin(angle),0));base=Vector((x,y,-.12));length=size*rng.uniform(.7,1)
  for step in range(1,13):
   t=step/13;center=base+a*(length*t)+Vector((0,0,size*.8*math.sin(t*2.1)));ll=size*.22*(math.sin(t*math.pi)**.7)
   for side in [-1,1]:
    leaf(vv,ff,center,ll,ll*.22,angle+side*1.0,-.1);ids.extend([rng.randrange(3)]*8)
mesh('Forest_Fern_Fronds',vv,ff,leafmats[:3],ids)
# Mossy stones and a handful of fallen leaves, all batched to limit draw calls.
stone=mat('Forest_Mossy_Stone',(.12,.15,.09),.95)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1);temp=bpy.context.object;tv=[v.co.copy() for v in temp.data.vertices];tf=[tuple(p.vertices) for p in temp.data.polygons];bpy.data.objects.remove(temp,do_unlink=True)
vv=[];ff=[]
for k in range(160):
 x=rng.choice([-1,1])*rng.uniform(1.65,2.85);y=rng.uniform(-1,61);r=rng.uniform(.09,.28);off=len(vv)
 vv.extend((x+q.x*r,y+q.y*r*1.3,-.14+(q.z+.4)*r*.75) for q in tv);ff.extend(tuple(off+i for i in face) for face in tf)
ob=mesh('Forest_Moss_Stones',vv,ff,[stone]);
for p in ob.data.polygons:p.use_smooth=True
litterm=[mat('Forest_Fallen_Leaf_'+str(i),c,.92) for i,c in enumerate([(.22,.13,.045),(.30,.21,.07),(.13,.17,.045)])];vv=[];ff=[];ids=[]
for k in range(340):
 x=rng.uniform(-1.45,1.45);y=rng.uniform(0,60);leaf(vv,ff,(x,y,.008),rng.uniform(.045,.12),rng.uniform(.014,.032),rng.random()*math.tau);ids.extend([rng.randrange(3)]*8)
mesh('Forest_Leaf_Litter',vv,ff,litterm,ids)
# Small bronze-capped path lamps instead of exposed luminous polyhedra.
bronze=mat('Forest_Lamp_Bronze',(.075,.055,.03),.4,.65);vv=[];ff=[]
for o in bpy.data.collections['PathLights'].objects:
 o.scale*=.42;o.location.x=math.copysign(1.57,o.location.x);o.location.z=.19
 x,y,z=o.location;box(vv,ff,(x,y,.07),(.10,.10,.14));box(vv,ff,(x,y,.25),(.14,.14,.035))
mesh('Forest_Path_Lamp_Housings',vv,ff,[bronze])
p=bpy.data.materials['Forest_PathLight'].node_tree.nodes.get('Principled BSDF')
if p:p.inputs['Emission Color'].default_value=(1,.58,.19,1);p.inputs['Emission Strength'].default_value=2.5
# Natural warm key and cooler ambient fill, rather than green light on every surface.
sun=bpy.data.objects['Sun'];sun.data.energy=3.8;sun.data.color=(1,.86,.66);sun.data.angle=.08;sun.rotation_euler=(math.radians(24),math.radians(-28),math.radians(-25))
fill=bpy.data.objects['Fill'];fill.data.energy=1.75;fill.data.color=(.72,.82,1)
# Neutral sky with a softer ambient contribution for textured, readable shadow sides.
w=s.world;w.use_nodes=True;w.node_tree.nodes.clear();out=w.node_tree.nodes.new('ShaderNodeOutputWorld');bg=w.node_tree.nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.40,.52,.57,1);bg.inputs['Strength'].default_value=.6;w.node_tree.links.new(bg.outputs[0],out.inputs['Surface'])
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.8
s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100;s.camera.location.y=1
s['forest_design_revision']='2026-09-11: leaf canopy, branches, weathered boardwalk, overgrown gallery walls, ivy, ferns, forest ground and path lamps'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender-scenes/forest_walkway.blend'))
s.render.filepath=str(ROOT/'renders/forest-review/after.png');bpy.ops.render.render(write_still=True)
print('Forest first design pass saved and rendered')

s.camera.location.y=25
s.render.filepath=str(ROOT/'renders/forest-review/after-midpoint.png');bpy.ops.render.render(write_still=True)
s.camera.location.y=1
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.view_layer.objects:
 if o.visible_get():o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/forest_walkway.glb'),export_format='GLB',use_selection=True,export_lights=True,export_cameras=True,export_animations=True)
print('Forest export complete')
