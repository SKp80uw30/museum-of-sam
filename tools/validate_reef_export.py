"""Validate the reef GLB without reimporting rigged fish into Blender."""
import json, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'exports/underwater_reef.glb'; raw=p.read_bytes()
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
for skin in d.get('skins',[]):
    for joint in skin['joints']:valid(joint,'nodes')
for a in d.get('animations',[]):
    for sampler in a['samplers']:
        valid(sampler['input'],'accessors');valid(sampler['output'],'accessors')
    for channel in a['channels']:
        assert channel['sampler']<len(a['samplers']);valid(channel['target']['node'],'nodes')
names=[x.get('name','') for x in d['nodes']]
for name in ['Floor','WalkCam','Reef_Continuous_Seabed','Reef_Water_Surface']:assert name in names,name
assert not any('Preview_Water_Volume' in x for x in names)
counts={prefix:sum(x.startswith(prefix) for x in names) for prefix in ['FrameMount','Frame_left','Frame_right','Canvas_left','Canvas_right','Post_left','Post_right']}
assert counts['FrameMount']==32 and counts['Canvas_left']==16 and counts['Canvas_right']==16,counts
assert len(d['animations'])==24 and len(d['skins'])==48
assert len(d['extensions']['KHR_lights_punctual']['lights'])==2
report={'file_bytes':size,'nodes':len(d['nodes']),'meshes':len(d['meshes']),'materials':len(d['materials']),'images':len(d['images']),'animations':len(d['animations']),'skins':len(d['skins']),'mount_counts':counts,'checks':'GLB header, buffer ranges, node/accessor references, fish rigs, artwork counts, lights, and preview-volume exclusion passed'}
(ROOT/'renders/reef-review/export-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
