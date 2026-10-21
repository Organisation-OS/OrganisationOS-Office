"""Bounded native delivery with retained-container and control-file recovery."""
from pathlib import Path
import json,sys,subprocess,time,hashlib,os,tempfile
D=Path(__file__).parent;S=Path('/var/lib/organisation-office-runtime');mode,supervisor=sys.argv[1:];assert mode in ['preflight','install','replay'];assert time.time()+4200<json.loads(Path('/var/lib/oos-admin-window/receipt.json').read_bytes())['expiresEpoch']
def run(args,timeout=180):return subprocess.run(args,capture_output=True,text=True,timeout=timeout)
def inspect(name):
 r=run(['docker','container','inspect',name]);return json.loads(r.stdout)[0]if r.returncode==0 else None
before=inspect('organisationos-office');assert before is not None
paths=[S/'current.json',Path('/etc/organisationos-office/runtime.json'),Path('/etc/systemd/system/organisationos-office.service'),Path('/etc/systemd/system/organisationos-office-firewall.service')];saved={p:(p.read_bytes(),p.stat().st_mode&0o777)for p in paths};state=json.loads(saved[paths[0]][0]);jwt=hashlib.sha256(Path('/etc/organisationos-office/jwt').read_bytes()).hexdigest()
if mode=='install' and not (D/'before').exists():
 B=D/'before';B.mkdir(mode=0o700)
 for i,(p,(raw,perm))in enumerate(saved.items()):(B/(str(i)+'.private')).write_bytes(raw)
cmd=['python3',str(D/'native_install.py'),'--supervisor',supervisor,'--envelope',str(D/'manifest.json'),'--predecessor-envelope',str(D/'predecessor.json'),'--recipe',str(D/'recipe.tar.gz'),'--image','/var/lib/organisation-office-runtime-stage-20261021/image.tar']+(['--preflight']if mode=='preflight'else[])
r=run(cmd,900);(D/(mode+'.log')).write_text(r.stdout+r.stderr)
if r.returncode:
 assert state['sequence']<3,'Replay failed; preserve installed state for diagnosis'
 marker=S/'api-origin-migration.json';current=inspect('organisationos-office');old=None;m=None
 if marker.exists():
  m=json.loads(marker.read_bytes());old=inspect(m['retainedContainer']);assert m['fromContainer']==before['Id']
  if old:
   assert old['Id']==before['Id']
   if current:
    assert current['Id']!=old['Id'] and current['Config']['Labels'].get('organisationos.instance')==before['Config']['Labels']['organisationos.instance']
    c=json.loads(Path('/etc/organisationos-office/runtime.json').read_bytes());controller=Path('/opt/organisationos-office/releases')/c['recipeSha256']/'controller.py'
    if current['State']['Running']:run(['python3',str(controller),'stop']).check_returncode()
    run(['systemctl','stop','organisationos-office.service']).check_returncode();run(['docker','rename','organisationos-office','organisationos-office-api-failed-'+current['Id'][:12]]).check_returncode()
   run(['docker','rename',m['retainedContainer'],'organisationos-office']).check_returncode()
  else:assert current and current['Id']==before['Id']
  marker.rename(D/('failed-migration-'+str(int(time.time()))+'.json'))
 else:assert current and current['Id']==before['Id']
 for p,(raw,perm)in saved.items():
  fd,t=tempfile.mkstemp(prefix='.rollback-',dir=p.parent)
  with os.fdopen(fd,'wb')as f:os.fchmod(f.fileno(),perm);f.write(raw);f.flush();os.fsync(f.fileno())
  os.replace(t,p)
 run(['systemctl','daemon-reload']).check_returncode();run(['systemctl','start','organisationos-office.service']).check_returncode();(D/'rollback.json').write_text(json.dumps({'restoredPriorContainer':before['Id'],'controlFilesRestored':True,'noDataVolumeRemoved':True}));raise RuntimeError('Native Office delivery refused; prior service restored')
assert jwt==hashlib.sha256(Path('/etc/organisationos-office/jwt').read_bytes()).hexdigest()
if mode=='preflight':assert all(p.read_bytes()==v[0]for p,v in saved.items()) and inspect('organisationos-office')['Id']==before['Id']
print(r.stdout)
