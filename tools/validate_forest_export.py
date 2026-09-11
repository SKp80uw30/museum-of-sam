"""Validate the forest_walkway GLB without reimporting into Blender."""
import json, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'exports/forest_walkway.glb'; raw=p.read_bytes()
magic,version,size=struct.unpack_from('<4sII',raw)
assert magic==b'glTF' and version==2 and size==len(raw)
n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
d=json.loads(raw[20:20+n])
def valid(i,key):assert isinstance(i,int) and 0<=i<len(d.get(key,[])),(key,i)
for node in d['nodes']:
    for key,table in [('mesh','meshes'),('skin','skins'),('camera','cameras')]:
        if key in node:valid(node[key],table)
    for child in node.get('children',[]):valid(child,'nodes')
for a in d['accessors']:
    if 'bufferView' in a:valid(a['bufferView'],'bufferViews')
for v in d['bufferViews']:
    valid(v['buffer'],'buffers');assert v.get('byteOffset',0)+v['byteLength']<=d['buffers'][v['buffer']]['byteLength']
for m in d['meshes']:
    for pr in m['primitives']:
        for i in pr['attributes'].values():valid(i,'accessors')
        if 'indices' in pr:valid(pr['indices'],'accessors')
        if 'material' in pr:valid(pr['material'],'materials')
names=[x.get('name','') for x in d['nodes']]
for name in ['Floor','WalkCam','Sun','Fill','Forest_Ground','Forest_Boardwalk_Edging','Forest_Overgrown_Gallery_Walls','Forest_Fern_Fronds','Forest_Wall_Ivy','Forest_Distant_Crowns']:assert name in names,name
# the raw unscattered source template objects must NOT be present as their own nodes
# (they were excluded via the default 'Collection' view-layer exclude flag)
for stray in ('Fern_1','Grass_3','Vines','pothos_vine_large_D'):
    assert stray not in names, f'stray unexcluded source object exported: {stray}'
counts={prefix:sum(x.startswith(prefix) for x in names) for prefix in
        ['FrameMount','Frame_left','Frame_right','Canvas_left','Canvas_right',
         'WallPatch_left','WallPatch_right','Trunk_','CanopyBlob_','Fern_','Grass_',
         'HangVine_','WallVine_','PathLight_']}
assert counts['FrameMount']==32 and counts['Canvas_left']==16 and counts['Canvas_right']==16,counts
assert counts['Frame_left']==16 and counts['Frame_right']==16,counts
assert counts['WallPatch_left']==16 and counts['WallPatch_right']==16,counts
assert counts['Trunk_']==15,counts
assert counts['CanopyBlob_']==0,'Old solid canopy blobs leaked into the new export'
for m in d['meshes']:
 if m.get('name','').startswith(('Forest_Canopy_Leaves','Forest_Fern_Fronds','Forest_Wall_Ivy','Forest_Distant_Crowns')):
  for primitive in m['primitives']:
   assert 'TEXCOORD_0' in primitive['attributes'], 'Leaf texture UVs missing'
# The authored artwork placements must match the incoming Claude scene.
original=ROOT/'backups/forest-2026-09-11/forest_walkway.glb'
oldraw=original.read_bytes();oldlen=struct.unpack_from('<I',oldraw,12)[0];old=json.loads(oldraw[20:20+oldlen]);oldnodes={n.get('name'):n for n in old['nodes']}
for node in d['nodes']:
 name=node.get('name','')
 if name.startswith(('FrameMount','Frame_left','Frame_right','Canvas_left','Canvas_right')):
  for key in ['translation','rotation','scale','matrix']:
   before=oldnodes[name].get(key);after=node.get(key)
   assert before==after or (before is not None and after is not None and len(before)==len(after) and all(abs(a-b)<1e-5 for a,b in zip(before,after))), (name,key,before,after)

assert 'extensions' in d and 'KHR_lights_punctual' in d.get('extensions',{}), 'lights missing from export'
lights=d['extensions']['KHR_lights_punctual']['lights']
assert len(lights)>=2, lights
assert any(x.get('camera') is not None for x in d['nodes']), 'no camera node found'
report={'file_bytes':size,'nodes':len(d['nodes']),'meshes':len(d['meshes']),
        'materials':len(d['materials']),'images':len(d.get('images',[])),
        'mount_counts':counts,'lights':len(lights),
        'checks':'GLB header, buffer ranges, node/accessor references, mount/frame/wall counts, preserved artwork transforms, leaf UVs, new environment meshes, lights and camera passed'}
out=ROOT/'renders/forest-review/export-validation.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
