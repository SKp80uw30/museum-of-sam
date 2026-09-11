"""Match the forest's Blender preview to the runtime daylight sky.
Cloud animation is implemented by web/forest-sky.js; this is a packed still sky.
Run against the finished forest, independently of other open Blender scenes.
"""
import bpy, numpy as np, math
from pathlib import Path
root=Path(__file__).resolve().parents[1];s=bpy.context.scene
w,h=1536,768;v,u=np.mgrid[0:h,0:w].astype(np.float32);u/=w;v/=h
lat=(v-.5)*math.pi;lon=u*math.tau;elevation=np.clip(np.sin(lat),0,1)
zenith=np.array([.075,.31,.74]);horizon=np.array([.58,.78,.91]);rgb=horizon[None,None,:]*(1-elevation[:,:,None]**.42)+zenith[None,None,:]*elevation[:,:,None]**.42
cloud=np.zeros((h,w));rng=np.random.default_rng(81)
for center_lon,center_lat in [(0.5,.64),(1.7,.88),(3.0,.42),(4.5,.95),(5.6,.52)]:
 field=np.zeros_like(cloud)
 for j in range(5):
  dx=(lon-center_lon-rng.uniform(-.12,.12)+math.pi)%math.tau-math.pi
  dy=lat-center_lat-rng.uniform(-.035,.045)
  field+=np.exp(-((dx/rng.uniform(.10,.18))**2+(dy/rng.uniform(.055,.10))**2)*2)
 cloud=np.maximum(cloud,np.clip((field-.35)/1.6,0,1))
cloud*=np.clip((elevation-.08)*5,0,1)
cloudrgb=np.stack([.82+cloud*.18,.88+cloud*.12,.94+cloud*.06],-1);rgb=rgb*(1-cloud[:,:,None])+cloudrgb*cloud[:,:,None]
im=bpy.data.images.get('Forest_Blue_Day_Sky')
if im:bpy.data.images.remove(im)
im=bpy.data.images.new('Forest_Blue_Day_Sky',width=w,height=h);rgba=np.ones((h,w,4),dtype=np.float32);rgba[:,:,:3]=rgb;im.pixels.foreach_set(rgba.ravel());im.pack()
world=s.world;world.use_nodes=True;nodes=world.node_tree.nodes;links=world.node_tree.links;nodes.clear()
out=nodes.new('ShaderNodeOutputWorld');env=nodes.new('ShaderNodeTexEnvironment');env.image=im
visible=nodes.new('ShaderNodeBackground');visible.inputs['Strength'].default_value=.8;ambient=nodes.new('ShaderNodeBackground');ambient.inputs['Strength'].default_value=.55
links.new(env.outputs['Color'],visible.inputs['Color']);links.new(env.outputs['Color'],ambient.inputs['Color'])
path=nodes.new('ShaderNodeLightPath');mix=nodes.new('ShaderNodeMixShader');links.new(path.outputs['Is Camera Ray'],mix.inputs[0]);links.new(ambient.outputs[0],mix.inputs[1]);links.new(visible.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
bpy.data.objects['Sun'].data.energy=3.6;bpy.data.objects['Sun'].data.angle=.09
bpy.data.objects['Fill'].data.energy=2.0;s['forest_sky_revision']='Blue day, soft sun, sparse clouds; animated sky lives in web/forest-sky.js'
s.camera.location.y=1
bpy.ops.wm.save_as_mainfile(filepath=str(root/'blender-scenes/forest_walkway.blend'))
s.cycles.samples=16;s.render.filepath=str(root/'renders/forest-review/daylight-blender.png');bpy.ops.render.render(write_still=True)
