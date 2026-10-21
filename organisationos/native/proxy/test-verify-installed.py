from pathlib import Path
import base64,copy,importlib.util,json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
p=Path(__file__).with_name('verify-installed.py');s=importlib.util.spec_from_file_location('office_installed_verifier',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
key=Ed25519PrivateKey.generate();public=key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
e={'schema':'oos-signed-v1','purpose':'bundle','algorithm':'Ed25519','issuer':v.sha(public),'payload':{'name':'Réception synthétique','version':1}}
e['signature']=base64.b64encode(key.sign(v.can(e))).decode();assert v.envelope(e,public)==e['payload'];checks=1
for field,value in [('schema','wrong'),('purpose','distribution'),('algorithm','none'),('issuer','0'*64),('payload',{'version':2}),('signature',base64.b64encode(b'x'*64).decode())]:
 bad=copy.deepcopy(e);bad[field]=value
 try:v.envelope(bad,public)
 except Exception:checks+=1
 else:raise AssertionError(field+' tampering accepted')
print(json.dumps({'status':'PASS','checks':checks,'privateKeys':'synthetic only','productionWrites':0}))
