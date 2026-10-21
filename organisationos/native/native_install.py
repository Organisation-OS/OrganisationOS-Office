#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""CP-signed, instance-scoped Office runtime; existing vault activation is separate."""
from pathlib import Path
import argparse,base64,hashlib,io,json,os,re,stat,subprocess,tarfile,tempfile,fcntl,secrets,ipaddress
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
P=Path;PURPOSE='organisation-office-runtime-v1';IMAGE='sha256:c79aa0259070234ef10cbdb5ab11d6305870ce69ac0929b97066543ef68c317a';FILES={'controller.py','firewall.py','LICENSE'}
INSTANCES={'27c0be38-60bd-4dce-bb28-ef0088716a25':('10.9.5.74','portal.thecgp.com','172.30.242.0/28','172.30.242.2'),'b7a1f6b1-c4aa-4de7-95fb-29d509d3398d':('10.100.8.13','portal.villesadp.ca','172.30.243.0/28','172.30.243.2')}
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();digest=lambda b:hashlib.sha256(b).hexdigest()
def require(v):
 if not v:raise ValueError('Native Office release precondition refused')
def trusted(p):
 p=P(p);s=p.lstat();require(p.resolve()==p and s.st_uid==0 and not s.st_mode&0o022 and stat.S_ISREG(s.st_mode) and s.st_nlink==1);return p

def directory(p,mode=0o755):
 p=P(p)
 if not p.exists():p.mkdir(mode=mode);p.chmod(mode)
 s=p.lstat();require(p.resolve()==p and s.st_uid==0 and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==mode)
def write(p,b,mode=0o644):
 p=P(p);b=b if isinstance(b,bytes)else canonical(b)+b'\n'
 if p.exists():trusted(p);require(p.read_bytes()==b and stat.S_IMODE(p.stat().st_mode)==mode);return
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
 with os.fdopen(fd,'wb')as f:os.fchmod(f.fileno(),mode);f.write(b);f.flush();os.fsync(f.fileno())
def run(args,timeout=120):
 r=subprocess.run(args,capture_output=True,timeout=timeout);require(r.returncode==0);return r.stdout

def validate(m):
 require(set(m)=={'schema','instanceId','installationId','sequence','operation','recipe','image'})
 require(m['schema']=='oos-office-runtime-release-v1'and m['instanceId']in INSTANCES and m['installationId']==m['instanceId']and type(m['sequence'])is int and m['sequence']>0 and m['operation']=='install')
 r=m['recipe'];require(set(r)=={'version','sourceCommit','sha256','size'}and r['version']=='0.1.0'and re.fullmatch('[a-f0-9]{40}',r['sourceCommit'])and re.fullmatch('[a-f0-9]{64}',r['sha256'])and type(r['size'])is int and 0<r['size']<200000)
 i=m['image'];require(set(i)=={'version','engineCommit','imageId','sha256','size'}and i['version']=='10.0.0.2'and i['engineCommit']=='caa398a5e4b29141b45b2efc56a06911990c1957'and i['imageId']==IMAGE and re.fullmatch('[a-f0-9]{64}',i['sha256'])and type(i['size'])is int and 0<i['size']<4*1024**3);return m

def verify(e,key):
 require(set(e)=={'schema','purpose','algorithm','issuer','payload','signature'}and e['schema']=='oos-signed-v1'and e['purpose']==PURPOSE and e['algorithm']=='Ed25519'and e['issuer']==digest(key));Ed25519PublicKey.from_public_bytes(key).verify(base64.b64decode(e['signature'],validate=True),canonical({k:v for k,v in e.items()if k!='signature'}));return validate(e['payload'])
def unpack(raw,spec):
 require(len(raw)==spec['size']and digest(raw)==spec['sha256']);files={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz')as t:
  for i in t:
   require(i.name in FILES and i.name not in files and i.isfile()and i.uid==i.gid==i.mtime==0 and i.mode==0o444 and not i.pax_headers and i.size<100000);files[i.name]=t.extractfile(i).read()
 require(set(files)==FILES);return files

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--supervisor',required=True);ap.add_argument('--envelope',required=True);ap.add_argument('--recipe',required=True);ap.add_argument('--image',required=True);ap.add_argument('--preflight',action='store_true');a=ap.parse_args();require(os.geteuid()==0)
 s=json.loads(trusted(a.supervisor).read_bytes());c=json.loads(trusted(s['config']).read_bytes());identity=json.loads(trusted(P(s['state'])/'identity.json').read_bytes());e=json.loads(P(a.envelope).read_bytes());m=verify(e,base64.b64decode(c['public_key'],validate=True));require(identity['installation_id']==m['instanceId']);files=unpack(P(a.recipe).read_bytes(),m['recipe']);image=trusted(a.image);require(image.stat().st_size==m['image']['size'])
 with image.open('rb')as f:require(hashlib.file_digest(f,'sha256').hexdigest()==m['image']['sha256'])
 import shutil
 require(shutil.disk_usage('/var/lib').free>60*1024**3);require(int(next(x.split()[1]for x in P('/proc/meminfo').read_text().splitlines()if x.startswith('MemAvailable:')))*1024>6*1024**3)
 require(run(['/usr/bin/docker','version','--format','{{.Server.Version}}']).strip()==b'29.1.3')
 proxy,hostname,subnet,ip=INSTANCES[m['instanceId']];network=ipaddress.ip_network(subnet)
 nets=run(['/usr/bin/docker','network','ls','--format','{{.Name}}']).decode().splitlines()
 if 'organisationos-office'not in nets:
  routes=json.loads(run(['/usr/sbin/ip','-j','route','show']))
  require(not any(r.get('dst')not in [None,'default']and ipaddress.ip_network(r['dst'],strict=False).version==4 and ipaddress.ip_network(r['dst'],strict=False).overlaps(network)for r in routes))
 if a.preflight:print(json.dumps({'status':'PREFLIGHT_PASS','instanceId':m['instanceId'],'imageId':IMAGE,'privateListener':'127.0.0.1:18080','proxyEgress':proxy+':443','publicExposureCreated':False}));return
 os.umask(0o077);root=P('/var/lib/organisation-office-runtime');directory(root,0o700)
 with (root/'install.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);state=json.loads((root/'current.json').read_bytes())if (root/'current.json').exists()else {'sequence':0};envSha=digest(canonical(e));require(m['sequence']==state['sequence']and state.get('manifestSha256')==envSha or m['sequence']==state['sequence']+1)
  require(state.get('recipeSha256')in [None,m['recipe']['sha256']])
  directory('/opt/organisationos-office');directory('/opt/organisationos-office/releases');release=P('/opt/organisationos-office/releases')/m['recipe']['sha256'];directory(release)
  for name,raw in files.items():write(release/name,raw,0o444)
  directory('/etc/organisationos-office',0o700);secret=P('/etc/organisationos-office/jwt')
  if not secret.exists():write(secret,secrets.token_urlsafe(64).encode(),0o400)
  trusted(secret);require(secret.stat().st_mode&0o777==0o400 and re.fullmatch(b'[A-Za-z0-9_-]{64,128}',secret.read_bytes()))
  storage=P('/var/lib/organisationos-office');directory(storage,0o700)
  for name in ['lib','log','data','fonts']:
   child=storage/name
   if not child.exists():child.mkdir(mode=0o755)
   require(child.resolve()==child and child.is_dir()) # The private root is immutable; engine-owned volume contents persist.
  desc={'schema':1,'instanceId':m['instanceId'],'supervisor':str(trusted(a.supervisor)),'imageId':IMAGE,'containerIp':ip,'proxyIp':proxy,'portalOrigin':'https://'+hostname,'privateListener':'127.0.0.1:18080','recipeSha256':m['recipe']['sha256']};write('/etc/organisationos-office/runtime.json',desc,0o600)
  if subprocess.run(['/usr/bin/docker','image','inspect',IMAGE],capture_output=True).returncode!=0:run(['/usr/bin/docker','image','load','--input',str(image)],timeout=600)
  require(json.loads(run(['/usr/bin/docker','image','inspect',IMAGE]))[0]['Id']==IMAGE)
  if 'organisationos-office'not in nets:run(['/usr/bin/docker','network','create','--driver','bridge','--subnet',subnet,'--gateway',str(network[1]),'--opt','com.docker.network.bridge.name=oos-office0','--label','organisationos.instance='+m['instanceId'],'organisationos-office'])
  n=json.loads(run(['/usr/bin/docker','network','inspect','organisationos-office']))[0];require(n['Driver']=='bridge'and not n['EnableIPv6']and n['Labels'].get('organisationos.instance')==m['instanceId']and len(n['IPAM']['Config'])==1 and n['IPAM']['Config'][0].get('Subnet')==subnet and n['IPAM']['Config'][0].get('Gateway')==str(network[1]) and not n['IPAM']['Config'][0].get('IPRange'))
  run(['/usr/bin/python3',str(release/'firewall.py')])
  exists=subprocess.run(['/usr/bin/docker','inspect','organisationos-office'],capture_output=True)
  if exists.returncode!=0:
   cmd=['/usr/bin/docker','create','--name','organisationos-office','--label','organisationos.instance='+m['instanceId'],'--label','organisationos.recipe='+m['recipe']['sha256'],'--network','organisationos-office','--ip',ip,'--publish','127.0.0.1:18080:80','--memory','5368709120','--memory-swap','5368709120','--cpus','2','--pids-limit','512','--security-opt','no-new-privileges:true','--log-driver','local','--log-opt','max-size=10m','--log-opt','max-file=3','--restart','no','--dns','127.0.0.1','--add-host',hostname+':'+proxy,'--env','ALLOW_PRIVATE_IP_ADDRESS=true','--env','ALLOW_META_IP_ADDRESS=false','--mount','type=bind,src='+str(secret)+',dst=/run/secrets/organisationos-office-jwt,readonly']
   for name,dest in [('lib','/var/lib/onlyoffice'),('log','/var/log/onlyoffice'),('data','/var/www/onlyoffice/Data'),('fonts','/usr/share/fonts/truetype/custom')]:cmd+=['--mount','type=bind,src='+str(storage/name)+',dst='+dest]
   run(cmd+[IMAGE])
  current=json.loads(run(['/usr/bin/docker','inspect','organisationos-office']))[0];require(current['Config']['Labels']=={'organisationos.instance':m['instanceId'],'organisationos.recipe':m['recipe']['sha256']}or all(current['Config']['Labels'].get(k)==v for k,v in {'organisationos.instance':m['instanceId'],'organisationos.recipe':m['recipe']['sha256']}.items()));require(current['Config']['Image']==IMAGE and current['HostConfig']['PortBindings']=={'80/tcp':[{'HostIp':'127.0.0.1','HostPort':'18080'}]})
  hc=current['HostConfig'];require(hc['Memory']==5368709120 and hc['MemorySwap']==5368709120 and hc['NanoCpus']==2000000000 and hc['PidsLimit']==512 and hc['Dns']==['127.0.0.1'] and hc['ExtraHosts']==[hostname+':'+proxy] and not hc['Privileged'])
  require(set(current['NetworkSettings']['Networks'])=={'organisationos-office'})
  expectedMounts={'/run/secrets/organisationos-office-jwt':(str(secret),False),'/var/lib/onlyoffice':(str(storage/'lib'),True),'/var/log/onlyoffice':(str(storage/'log'),True),'/var/www/onlyoffice/Data':(str(storage/'data'),True),'/usr/share/fonts/truetype/custom':(str(storage/'fonts'),True)}
  require({x['Destination']:(x['Source'],x['RW'])for x in current['Mounts']}==expectedMounts)
  firewall='[Unit]\nDescription=OrganisationOS Office restricted egress\nAfter=docker.service\nBefore=organisationos-office.service\n[Service]\nType=oneshot\nRemainAfterExit=yes\nExecStart=/usr/bin/python3 '+str(release/'firewall.py')+'\n[Install]\nWantedBy=multi-user.target\n'
  service='[Unit]\nDescription=OrganisationOS Office Powered by ONLYOFFICE\nAfter=docker.service organisationos-office-firewall.service\nRequires=docker.service organisationos-office-firewall.service\n[Service]\nType=oneshot\nRemainAfterExit=yes\nExecStart=/usr/bin/python3 '+str(release/'controller.py')+' start\nExecStop=/usr/bin/python3 '+str(release/'controller.py')+' stop\nTimeoutStartSec=180\nTimeoutStopSec=180\n[Install]\nWantedBy=multi-user.target\n'
  write('/etc/systemd/system/organisationos-office-firewall.service',firewall.encode());write('/etc/systemd/system/organisationos-office.service',service.encode());run(['/usr/bin/systemctl','daemon-reload']);run(['/usr/bin/systemctl','enable','--now','organisationos-office-firewall.service','organisationos-office.service'])
  receipt={'schema':'oos-office-runtime-installation-v1','status':'INSTALLED_LOCAL_RECEPTION_PENDING','instanceId':m['instanceId'],'sequence':m['sequence'],'manifestSha256':envSha,'recipeSha256':m['recipe']['sha256'],'imageId':IMAGE,'imageArchiveSha256':m['image']['sha256'],'privateListener':'127.0.0.1:18080','publicExposureCreated':False,'vaultCredentialImported':False,'gedBindingActivated':False,'secretGeneratedLocally':True,'noWorkstationChange':True,'bootstrapSha256':digest(P(__file__).read_bytes())}
  write(root/(envSha+'.receipt.json'),receipt,0o600);fd,temp=tempfile.mkstemp(prefix='.current-',dir=root)
  with os.fdopen(fd,'wb')as f:os.fchmod(f.fileno(),0o600);f.write(canonical(receipt));f.flush();os.fsync(f.fileno())
  os.replace(temp,root/'current.json');print(json.dumps(receipt))
if __name__=='__main__':main()
