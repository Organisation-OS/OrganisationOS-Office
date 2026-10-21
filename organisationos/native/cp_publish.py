#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Native CP builds the recipe capsule, validates the source-built OCI export, signs and audits."""
from pathlib import Path
import argparse,os,json,tarfile,io,gzip,hashlib,fcntl,tempfile,shutil
from native_install import canonical,digest,validate,unpack,FILES,PURPOSE,IMAGE
P=Path
def archive(inputs):
 b=io.BytesIO()
 with gzip.GzipFile(fileobj=b,mode='wb',filename='',mtime=0)as gz:
  with tarfile.open(fileobj=gz,mode='w',format=tarfile.USTAR_FORMAT)as t:
   for n in sorted(FILES):
    p=inputs/n;assert p.is_file()and not p.is_symlink();raw=p.read_bytes();i=tarfile.TarInfo(n);i.size=len(raw);i.mode=0o444;t.addfile(i,io.BytesIO(raw))
 return b.getvalue()
def atomic(p,raw):
 fd,temp=tempfile.mkstemp(prefix='.pending-',dir=p.parent)
 with os.fdopen(fd,'wb')as f:os.fchmod(f.fileno(),0o600);f.write(raw);f.flush();os.fsync(f.fileno())
 os.replace(temp,p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['preflight','publish']);ap.add_argument('--actor',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--inputs',required=True);ap.add_argument('--image',required=True);a=ap.parse_args();assert os.geteuid()!=0;os.umask(0o077);os.environ.setdefault('DJANGO_SETTINGS_MODULE','controlplane.settings')
 import django;django.setup()
 from django.db import transaction
 from fleet.models import User,Installation,AuditEvent
 from fleet.policy import require_write
 from fleet.signatures import signed,verify,issuer,public_bytes
 from fleet.services import audit
 actor=User.objects.get(pk=a.actor);require_write(actor,'releases');m=validate(json.loads(P(a.manifest).read_bytes()));instance=Installation.objects.get(pk=m['instanceId']);raw=archive(P(a.inputs));unpack(raw,m['recipe']);image=P(a.image);assert image.is_file()and not image.is_symlink()and image.stat().st_size==m['image']['size']
 with image.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==m['image']['sha256']
 with tarfile.open(image)as t:
  index=json.loads(t.extractfile('index.json').read());assert index['manifests'][0]['digest']==IMAGE;blob=t.extractfile('blobs/sha256/'+IMAGE.split(':')[1]).read();assert digest(blob)==IMAGE.split(':')[1]
 root=P('/var/lib/organisasion-os-control-plane/office-runtime');app=root/m['instanceId'];state=app/'current.json';payloadHash=digest(canonical(m))
 def admission():
  prior=json.loads(state.read_bytes())if state.exists()else{'sequence':0}
  assert m['sequence']==prior['sequence']and prior.get('payloadSha256')==payloadHash or m['sequence']==prior['sequence']+1
 admission()
 if a.action=='preflight':print(json.dumps({'status':'PREFLIGHT_PASS','instanceId':m['instanceId'],'recipeSha256':digest(raw),'imageId':IMAGE,'imageArchiveSha256':m['image']['sha256'],'privatePublication':True}));return
 app.mkdir(parents=True,mode=0o700,exist_ok=True)
 for p in [root,app]:assert p.stat().st_uid==os.geteuid()and not p.stat().st_mode&0o077 and not p.is_symlink()
 with (app/'publish.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);admission();key=issuer();envelope=signed(m,PURPOSE,key=key);verify(envelope,PURPOSE,public_bytes(key));manifestSha=digest(canonical(envelope))
  for p,b in [(app/(digest(raw)+'.recipe.tar.gz'),raw),(app/(str(m['sequence'])+'.signed.json'),canonical(envelope))]:
   if p.exists():assert p.read_bytes()==b and not p.is_symlink()
   else:atomic(p,b)
  # The image is shared privately between the two instance-scoped releases.
  obj=root/(m['image']['sha256']+'.image.tar')
  if not obj.exists():
   fd,temp=tempfile.mkstemp(prefix='.image-',dir=root)
   with os.fdopen(fd,'wb')as out,image.open('rb')as src:os.fchmod(out.fileno(),0o600);shutil.copyfileobj(src,out,1024*1024);out.flush();os.fsync(out.fileno())
   os.replace(temp,obj)
  with obj.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==m['image']['sha256']
  with transaction.atomic():
   event=AuditEvent.objects.filter(action='updates.office-runtime.install',resource='Installation',resource_id=str(instance.pk),after__manifestSha256=manifestSha).first()
   if event is None:event=audit(actor,'updates.office-runtime.install',instance,after={'manifestSha256':manifestSha,'recipeSha256':digest(raw),'imageId':IMAGE,'imageArchiveSha256':m['image']['sha256'],'localOnly':True,'credentialImported':False},provenance='cli')
  receipt={'status':'PUBLISHED_PRIVATE','sequence':m['sequence'],'payloadSha256':payloadHash,'manifestSha256':manifestSha,'recipeSha256':digest(raw),'imageArchiveSha256':m['image']['sha256'],'imageId':IMAGE,'auditId':str(event.pk),'secretIncluded':False};atomic(state,canonical(receipt));p=app/(str(m['sequence'])+'.receipt.json')
  if p.exists():assert p.read_bytes()==canonical(receipt)
  else:atomic(p,canonical(receipt))
  print(json.dumps(receipt))
if __name__=='__main__':main()
