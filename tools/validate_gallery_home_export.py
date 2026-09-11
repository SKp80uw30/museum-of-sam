"""Validate the gallery_home GLB without reimporting into Blender."""
import json, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'exports/gallery_home.glb'; raw=p.read_bytes()
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
for name in ['Floor','WalkCam','Sun','Fill','CeilingPlane','FarDoorGlow']:assert name in names,name
counts={prefix:sum(x.startswith(prefix) for x in names) for prefix in
        ['FrameMount','Frame_left','Frame_right','Canvas_left','Canvas_right',
         'WallPanel_left','WallPanel_right','Wall_','Border_','Sconce_',
         'Downlight_','CoveLight_','PendantRod_','ConsoleTop_','PlantPot_']}
assert counts['FrameMount']==32 and counts['Canvas_left']==16 and counts['Canvas_right']==16,counts
assert counts['Frame_left']==16 and counts['Frame_right']==16,counts
assert counts['WallPanel_left']==16 and counts['WallPanel_right']==16,counts
assert counts['Wall_']==2 and counts['Border_']==2 and counts['CoveLight_']==2,counts
assert counts['Sconce_']==32 and counts['Downlight_']>0 and counts['PendantRod_']>0,counts
assert counts['ConsoleTop_']>0 and counts['PlantPot_']>0,counts
assert 'extensions' in d and 'KHR_lights_punctual' in d.get('extensions',{}), 'lights missing from export'
lights=d['extensions']['KHR_lights_punctual']['lights']
assert len(lights)>=2, lights
assert any(x.get('camera') is not None for x in d['nodes']), 'no camera node found'
report={'file_bytes':size,'nodes':len(d['nodes']),'meshes':len(d['meshes']),
        'materials':len(d['materials']),'images':len(d.get('images',[])),
        'counts':counts,'lights':len(lights),
        'checks':'GLB header, buffer ranges, node/accessor references, mount/frame/wall/furniture counts, lights and camera passed'}
out=ROOT/'renders/gallery-home-review/export-validation.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
