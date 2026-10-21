from pathlib import Path
import sys,json
sys.path.insert(0,'/home/thecgp-admin/achats-panel-20261017');from transport import remote
B=Path(__file__).parent
code=r'''from pathlib import Path
import json,subprocess,urllib.request,hashlib,time
D=Path('/var/lib/organisation-office-lifecycle-20261021');c=json.loads(Path('/etc/organisationos-office/runtime.json').read_bytes());controller=Path('/opt/organisationos-office/releases')/c['recipeSha256']/'controller.py'
def health():
 r=subprocess.run(['python3',str(controller),'health'],capture_output=True,text=True);assert r.returncode==0,r.stderr;return json.loads(r.stdout)
a=health();before=json.loads(subprocess.check_output(['docker','inspect','organisationos-office']))[0];jwt=hashlib.sha256(Path('/etc/organisationos-office/jwt').read_bytes()).hexdigest();r=subprocess.run(['python3',str(D/'wrapper.py'),'replay',c['supervisor']],capture_output=True,text=True,timeout=900);(D/'replay-driver.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr;b=health();after=json.loads(subprocess.check_output(['docker','inspect','organisationos-office']))[0];assert a['runtimeEpoch']==b['runtimeEpoch'] and before['Id']==after['Id'] and before['State']['StartedAt']==after['State']['StartedAt'] and jwt==hashlib.sha256(Path('/etc/organisationos-office/jwt').read_bytes()).hexdigest()
origin=json.loads(Path('/var/lib/organisation-office-runtime/current.json').read_bytes())['apiOrigin'];r=subprocess.run(['docker','exec','organisationos-office','curl','-sS','--max-time','20','-o','/dev/null','-w','%{http_code} %{content_type}',origin+'/api/v1/auth/me'],capture_output=True,text=True,timeout=30);assert r.returncode==0 and r.stdout.startswith('200 application/json'),r.stdout+r.stderr
p={'status':'PASS','localHealth':b,'sameContainerOnReplay':True,'sameEpochOnReplay':True,'sameSecretOnReplay':True,'actualEngineToNativeApi':{'origin':origin,'result':r.stdout,'authenticatedSession':False},'imageUnchanged':True,'publicOfficeTlsQualified':False,'realGedProviderActivated':False};(D/'local-reception.json').write_text(json.dumps(p,indent=2));print(json.dumps(p))
'''
for h in ['thecgp18','ville50']:
 r=remote(h,['/usr/bin/python3','-'],code.encode(),True,timeout=1000);print(h,r.stdout.decode(),r.stderr.decode());r.check_returncode();(B/(h+'-office-lifecycle-reception.json')).write_bytes(r.stdout)
