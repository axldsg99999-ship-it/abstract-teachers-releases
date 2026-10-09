"""Restore byte-for-byte the locally signed APK. No signing keys needed."""
from pathlib import Path
import subprocess,json,hashlib
repo='axldsg99999-ship-it/abstract-teachers-releases';tag='v6.10.0'
expected='02d6d41b5b4c59c6211c528d96125e4bce3271f5f526b0a05af0cccd60219f95'
def gh(*args):return subprocess.check_output(['gh',*args],text=True)
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
root=Path('restore-v6100');root.mkdir(exist_ok=True)
gh('release','download',tag,'--repo',repo,'--pattern','recovery-v6100*','--dir',str(root))
m=json.loads((root/'recovery-v6100.json').read_text());assert m['target_sha256']==expected
gh('release','download',m['base_tag'],'--repo',repo,'--pattern',m['base_name'],'--dir',str(root))
base=root/m['base_name'];assert sha(base)==m['base_sha256']
payload=root/'payload.bin'
with payload.open('wb') as out:
 for part in m['parts']:
  p=root/part['name'];assert p.stat().st_size==part['size'] and sha(p)==part['sha256']
  out.write(p.read_bytes())
target=root/m['target_name']
with base.open('rb') as a,payload.open('rb') as b,target.open('wb') as out:
 for kind,start,count in m['ops']:
  assert kind in ['old','new'] and start>=0 and count>=0
  f=a if kind=='old' else b;f.seek(start)
  while count:
   data=f.read(min(count,1024*1024));assert data
   out.write(data);count-=len(data)
assert target.stat().st_size==m['target_size'] and sha(target)==expected
release=json.loads(gh('api',f'repos/{repo}/releases/407371559'));assert release['draft'] and release['tag_name']==tag
existing=next((x for x in release['assets'] if x['name']==m['target_name']),None)
if existing:
 if existing['state']=='starter':gh('api','--method','DELETE',f'repos/{repo}/releases/assets/{existing["id"]}');existing=None
 else:assert existing['state']=='uploaded' and existing['digest']=='sha256:'+expected
if not existing:gh('release','upload',tag,str(target),'--repo',repo)
release=json.loads(gh('api',f'repos/{repo}/releases/407371559'))
asset=next(x for x in release['assets'] if x['name']==m['target_name'])
assert asset['state']=='uploaded' and asset['size']==m['target_size'] and asset['digest']=='sha256:'+expected
print('Verified reconstructed signed APK:',asset['size'],asset['digest'],flush=True)
