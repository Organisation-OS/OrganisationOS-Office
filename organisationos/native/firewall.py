#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Own table only; container can reach only its native Portal proxy on TCP/443."""
import json,subprocess,pathlib,os

def rules(ip,proxy):
 match=lambda left,right:{'match':{'op':'==','left':left,'right':right}}
 src=match({'payload':{'protocol':'ip','field':'saddr'}},ip);est=match({'ct':{'key':'state'}},'established');dst=match({'payload':{'protocol':'ip','field':'daddr'}},proxy);port=match({'payload':{'protocol':'tcp','field':'dport'}},443)
 return {'forward':[[src,est,{'accept':None}],[src,dst,port,{'accept':None}],[src,{'drop':None}]],'input':[[src,est,{'accept':None}],[src,{'drop':None}]]}
def main():
 assert os.geteuid()==0;p=pathlib.Path('/etc/organisationos-office/runtime.json');s=p.lstat();assert p.resolve()==p and s.st_uid==0 and not s.st_mode&0o022;c=json.loads(p.read_bytes());table='organisationos_office';expected=rules(c['containerIp'],c['proxyIp'])
 existing=subprocess.run(['/usr/sbin/nft','-j','list','table','inet',table],capture_output=True)
 if existing.returncode==0:
  objects=json.loads(existing.stdout)['nftables'];actual={name:[]for name in expected};chains=[]
  for o in objects:
   if 'rule'in o:r=o['rule'];assert r['chain']in actual;actual[r['chain']].append(r['expr'])
   elif 'chain'in o:ch=o['chain'];assert ch['type']=='filter'and ch['hook']==ch['name']and ch['prio']==-5 and ch['policy']=='accept';chains.append(ch['name'])
   else:assert set(o)<=set(['metainfo','table'])
  assert actual==expected and sorted(chains)==sorted(expected);print('UNCHANGED');return
 commands=[{'add':{'table':{'family':'inet','name':table}}}]
 for name,exprs in expected.items():
  commands.append({'add':{'chain':{'family':'inet','table':table,'name':name,'type':'filter','hook':name,'prio':-5,'policy':'accept'}}})
  commands.extend({'add':{'rule':{'family':'inet','table':table,'chain':name,'expr':expr}}}for expr in exprs)
 subprocess.run(['/usr/sbin/nft','-j','-f','-'],input=json.dumps({'nftables':commands}).encode(),check=True,capture_output=True);print('INSTALLED')
if __name__=='__main__':main()
