"""Read-only verification of an installed signed Office extension after native upgrades."""
from pathlib import Path
import base64,hashlib,importlib.util,json,os,subprocess
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
ROOT=Path('/var/lib/organisation-office-proxy-20261021')
sha=lambda b:hashlib.sha256(b).hexdigest()
can=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def envelope(e,public):
    assert e['schema']=='oos-signed-v1' and e['purpose']=='bundle' and e['algorithm']=='Ed25519' and e['issuer']==sha(public)
    Ed25519PublicKey.from_public_bytes(public).verify(base64.b64decode(e['signature'],validate=True),can({k:v for k,v in e.items()if k!='signature'}))
    return e['payload']
def custody(path):
    st=path.stat();assert not path.is_symlink() and st.st_uid==0 and not st.st_mode&0o022

def main():
    assert os.geteuid()==0
    custody(ROOT);d=json.loads((ROOT/'signed-document.json').read_bytes());m=d['envelope']['payload']
    known={'portal.thecgp.com':('/opt/organisation-native-updater-thecgp-20261006/supervisor.json','/opt/organisation-r4-thecgp/progress-gateway/nginx.conf','27c0be38-60bd-4dce-bb28-ef0088716a25'),'portal.villesadp.ca':('/opt/organisation-native-updater-ville-20261016-r2/supervisor.json','/etc/nginx/sites-available/organisation-portal','b7a1f6b1-c4aa-4de7-95fb-29d509d3398d')}
    supervisor,nginx,iid=known[m['host']];s=json.loads(Path(supervisor).read_bytes());config=json.loads(Path(s['config']).read_bytes());public=base64.b64decode(config['public_key'],validate=True)
    assert envelope(d['envelope'],public)==m and m['schema']=='oos-office-native-proxy-v1' and sha(can(m))==d['manifest_sha256']
    assert json.loads((Path(s['state'])/'identity.json').read_bytes())['installation_id']==m['instanceId']==iid and m['nginx']['path']==nginx
    for n,pin in [('proxy.py','proxySourceSha256'),('install.py','installerSha256'),('qualification.json','qualificationSha256')]:
        p=ROOT/n;custody(p);assert sha(p.read_bytes())==m[pin]
    spec=importlib.util.spec_from_file_location('signed_office_proxy',ROOT/'proxy.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    before=(ROOT/'nginx.before').read_bytes();after=(ROOT/'nginx.after').read_bytes();assert sha(before)==m['nginx']['before'] and sha(after)==m['nginx']['after']
    assert module.extend(before.decode(),m['host']).encode()==after and module.remove(after.decode(),m['host']).encode()==before
    receipt=json.loads((ROOT/'installation-receipt.json').read_bytes());assert receipt['status']=='INSTALLED' and receipt['manifestSha256']==d['manifest_sha256'] and receipt['applicationBundle']==m['activeBundle'] and receipt['nginxSha256']==sha(after)
    path=Path(nginx);custody(path);assert path.read_bytes()==after
    policy=json.loads(Path(s['policy']).read_bytes());state=json.loads((Path(policy['prefix'])/'deployment.json').read_bytes());assert state['phase']=='idle' and state['active']==state['last_healthy']
    active=envelope(state['active_offer']['manifest'],public);assert sha(can(active))==state['active']==state['active_offer']['manifest_sha256']
    if m['nativePolicy'] is not None:
        pins=[r for r in policy['runtime']['protected_files']if r['path']==nginx];assert len(pins)==1 and pins[0]['sha256']==sha(after)
    assert subprocess.check_output(['systemctl','is-active','nginx.service'],text=True).strip()=='active'
    return {'status':'VERIFIED_INSTALLED','manifestSha256':d['manifest_sha256'],'installationBundle':m['activeBundle'],'currentSignedBundle':state['active'],'configurationUnchanged':True,'mutation':False}
if __name__=='__main__':print(json.dumps(main()))
