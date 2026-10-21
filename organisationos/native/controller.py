#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Native Office service. No container secret is returned by this interface."""
from pathlib import Path
import os,sys,json,subprocess,hashlib,stat,urllib.request
P=Path

def require(v):
 if not v:raise ValueError('Office runtime precondition refused')
def run(args,timeout=120):
 p=subprocess.run(args,capture_output=True,timeout=timeout);require(p.returncode==0);return p.stdout

def configuration():
 p=P('/etc/organisationos-office/runtime.json');s=p.lstat();require(p.resolve()==p and s.st_uid==0 and not s.st_mode&0o022 and stat.S_ISREG(s.st_mode));return json.loads(p.read_bytes())
def stop_allowed(c):
 s=json.loads(P(c['supervisor']).read_bytes());p=json.loads(P(s['policy']).read_bytes());sys.path.insert(0,str((P(s['root'])/'current').resolve()))
 if p['runtime'].get('adapter')=='historical-web-v1':
  from historical_web_runtime import HistoricalWebRuntime
  runtime=HistoricalWebRuntime(p,defer_preserved_writers=True)
  from historical_web_backup import sql
  query=lambda statement:sql(runtime,statement)
 else:
  from generic_runtime import GenericRuntime
  runtime=GenericRuntime(p)
  query=runtime.sql
 tables=set(query('SHOW TABLES;').decode().splitlines())
 if 'document_connector_bindings'in tables:require(query("SELECT COUNT(*) FROM document_connector_bindings WHERE organisation_id='"+c['instanceId']+"' AND engine='OFFICE' AND enabled=1;").strip()==b'0')
 if 'document_office_rooms'in tables:require(query("SELECT COUNT(*) FROM document_office_rooms WHERE organisation_id='"+c['instanceId']+"' AND state='OPEN';").strip()==b'0')
 # Suspend the native binding only after the last editor's acknowledged close.
 # A nonzero count refuses container stop; the retained engine is never force-killed here.

def main():
 require(os.geteuid()==0 and len(sys.argv)==2 and sys.argv[1]in ['start','stop','health']);c=configuration();name='organisationos-office';action=sys.argv[1]
 inspect=json.loads(run(['/usr/bin/docker','inspect',name]))[0];require(inspect['Config']['Labels'].get('organisationos.instance')==c['instanceId']);require(inspect['Config']['Image']==c['imageId'])
 if action=='stop':stop_allowed(c);run(['/usr/bin/docker','stop','--time','120',name],timeout=150);print('{"status":"STOPPED_NO_OPEN_ROOMS"}');return
 if action=='start':run(['/usr/bin/docker','start',name]);print('{"status":"STARTED_HEALTH_NOT_YET_PROVEN"}');return
 require(inspect['State']['Running'])
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
 with opener.open('http://127.0.0.1:18080/healthcheck',timeout=10)as r:require(r.status==200 and r.read(32).strip()==b'true')
 with opener.open('http://127.0.0.1:18080/web-apps/organisationos/runtime.json',timeout=10)as r:epoch=json.loads(r.read(4096));require(epoch['schema']=='organisationos-office-runtime-epoch-v1' and epoch['sessionPersistence']=='MEMORY_ONLY')
 print(json.dumps({'status':'HEALTHY_LOCAL_ONLY','instanceId':c['instanceId'],'imageId':c['imageId'],'runtimeEpoch':epoch['epoch'],'scope':'LOCAL_ENGINE_ONLY','publicTlsAndGedReception':'NOT_ASSESSED'}))
if __name__=='__main__':
 try:main()
 except Exception:sys.exit('Office service operation refused; running container and private details retained.')
