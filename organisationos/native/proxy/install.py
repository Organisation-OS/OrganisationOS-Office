"""CP-signed native nginx extension; exact preimage, atomic replacement, rollback."""
from pathlib import Path
import base64, fcntl, hashlib, json, os, stat, subprocess, sys, time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from proxy import extend, remove

ROOT=Path('/var/lib/organisation-office-proxy-20261021')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
can=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()

def atomic(path,raw,mode,uid,gid):
    temp=path.with_name('.'+path.name+'.office-proxy')
    fd=os.open(temp,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb') as f:
        f.write(raw); f.flush();os.fchown(f.fileno(),uid,gid);os.fchmod(f.fileno(),mode);os.fsync(f.fileno())
    os.replace(temp,path)
    fd=os.open(path.parent,os.O_DIRECTORY);os.fsync(fd);os.close(fd)

def main(action):
    assert action in ['preflight','install','revert'] and os.geteuid()==0
    os.umask(0o077)
    assert time.time()+4200<json.loads(Path('/var/lib/oos-admin-window/receipt.json').read_bytes())['expiresEpoch']
    doc=json.loads((ROOT/'signed-document.json').read_bytes());env=doc['envelope'];m=env['payload']
    assert m['schema']=='oos-office-native-proxy-v1' and sha(can(m))==doc['manifest_sha256']
    targets={'portal.thecgp.com':('/opt/organisation-native-updater-thecgp-20261006/supervisor.json','/opt/organisation-r4-thecgp/progress-gateway/nginx.conf','27c0be38-60bd-4dce-bb28-ef0088716a25'), 'portal.villesadp.ca':('/opt/organisation-native-updater-ville-20261016-r2/supervisor.json','/etc/nginx/sites-available/organisation-portal','b7a1f6b1-c4aa-4de7-95fb-29d509d3398d')}
    supervisor,nginx,identity=targets[m['host']]
    s=json.loads(Path(supervisor).read_bytes());c=json.loads(Path(s['config']).read_bytes());actual=json.loads((Path(s['state'])/'identity.json').read_bytes())
    Ed25519PublicKey.from_public_bytes(base64.b64decode(c['public_key'],validate=True)).verify(base64.b64decode(env['signature'],validate=True),can({k:v for k,v in env.items()if k!='signature'}))
    assert env['purpose']=='bundle' and actual['installation_id']==identity==m['instanceId']
    assert sha((ROOT/'proxy.py').read_bytes())==m['proxySourceSha256'] and sha((ROOT/'qualification.json').read_bytes())==m['qualificationSha256']
    assert sha((ROOT/'install.py').read_bytes())==m['installerSha256']
    before=(ROOT/'nginx.before').read_bytes();after=(ROOT/'nginx.after').read_bytes()
    assert after==extend(before.decode(),m['host']).encode() and remove(after.decode(),m['host']).encode()==before
    assert sha(before)==m['nginx']['before'] and sha(after)==m['nginx']['after'] and m['nginx']['path']==nginx
    policyPath=Path(s['policy']);policy=json.loads(policyPath.read_bytes());prefix=Path(policy['prefix']);state=json.loads((prefix/'deployment.json').read_bytes())
    assert state['phase']=='idle' and state['active']==state['last_healthy'] and state['active']==m['activeBundle']
    assert subprocess.check_output(['systemctl','is-active','nginx.service'],text=True).strip()=='active'
    path=Path(nginx);assert path.is_file() and not path.is_symlink()
    files={path:(before,after)}
    if m['nativePolicy'] is not None:
        b=(ROOT/'policy.before.private.json').read_bytes();a=(ROOT/'policy.after.private.json').read_bytes();expected=json.loads(b)
        rows=[r for r in expected['runtime']['protected_files'] if r['path']==nginx]
        assert len(rows)==1 and rows[0]['sha256']==sha(before);rows[0]['sha256']=sha(after)
        assert expected==json.loads(a) and sha(b)==m['nativePolicy']['before'] and sha(a)==m['nativePolicy']['after']
        files[policyPath]=(b,a)
    saved=ROOT/'installation-receipt.json'
    if saved.exists() and action=='install':
        receipt=json.loads(saved.read_bytes());assert receipt['manifestSha256']==doc['manifest_sha256'] and receipt['status']=='INSTALLED' and all(p.read_bytes()==a for p,(b,a)in files.items());print(json.dumps({'status':'REPLAY_NOOP','manifestSha256':doc['manifest_sha256']}));return
    index=1 if action=='revert' else 0
    assert all(p.read_bytes()==pair[index] for p,pair in files.items()),'Native configuration drift'
    for p in files:
        st=p.stat();assert st.st_uid==0 and not st.st_mode&0o022
    # Syntax test in a private mount namespace; live nginx and files are untouched.
    candidate=str(ROOT/('nginx.before'if action=='revert'else'nginx.after'))
    syntax=['/usr/sbin/nginx','-t']+(['-c',nginx]if m['host']=='portal.thecgp.com'else[])
    command=['unshare','--mount','--propagation','private','/usr/bin/python3','-c','import subprocess,sys;subprocess.run(["mount","--bind",sys.argv[1],sys.argv[2]],check=True);subprocess.run(sys.argv[3:],check=True)',candidate,nginx,*syntax]
    r=subprocess.run(command,capture_output=True,timeout=30);(ROOT/('syntax-'+action+'.log')).write_bytes(r.stdout+r.stderr);r.check_returncode()
    if action=='preflight':print(json.dumps({'status':'PREFLIGHT_PASS','manifestSha256':doc['manifest_sha256']}));return
    with open(prefix/'deployment.lock','r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert json.loads((prefix/'deployment.json').read_bytes())==state
        assert all(p.read_bytes()==pair[index] for p,pair in files.items())
        attrs={p:(stat.S_IMODE(p.stat().st_mode),p.stat().st_uid,p.stat().st_gid) for p in files};changed=[]
        try:
            for p,pair in files.items():atomic(p,pair[1-index],*attrs[p]);changed.append(p)
            subprocess.run(['systemctl','reload','nginx.service'],check=True,timeout=30)
            assert subprocess.check_output(['systemctl','is-active','nginx.service'],text=True).strip()=='active'
            receipt={'status':'REVERTED'if action=='revert'else'INSTALLED','manifestSha256':doc['manifest_sha256'],'at':int(time.time()),'host':m['host'],'configurationOnly':True,'engineRestarted':False,'applicationBundle':state['active'],'nginxSha256':sha(path.read_bytes())}
            atomic(saved,can(receipt),0o600,0,0);print(json.dumps(receipt))
        except BaseException:
            for p in reversed(changed):atomic(p,files[p][index],*attrs[p])
            subprocess.run(['systemctl','reload','nginx.service'],check=True,timeout=30)
            (ROOT/'rollback.json').write_bytes(can({'at':int(time.time()),'configurationRestored':True,'engineRestarted':False}));raise

if __name__=='__main__':main(sys.argv[1])
