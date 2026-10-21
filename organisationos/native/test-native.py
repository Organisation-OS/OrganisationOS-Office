#!/usr/bin/env python3
import unittest,tempfile,json,base64,copy,sys,types
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import native_install as n
from cp_publish import archive
import controller,firewall
class NativeOffice(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
  for name in n.FILES:
   source=Path(__file__).resolve().parents[2]/'LICENSE'if name=='LICENSE'else Path(__file__).with_name(name);(self.root/name).write_bytes(source.read_bytes())
  self.raw=archive(self.root);self.m={'schema':'oos-office-runtime-release-v1','instanceId':'27c0be38-60bd-4dce-bb28-ef0088716a25','installationId':'27c0be38-60bd-4dce-bb28-ef0088716a25','sequence':1,'operation':'install','recipe':{'version':'0.1.0','sourceCommit':'a'*40,'sha256':n.digest(self.raw),'size':len(self.raw)},'image':{'version':'10.0.0.2','engineCommit':'caa398a5e4b29141b45b2efc56a06911990c1957','imageId':n.IMAGE,'sha256':'b'*64,'size':3059617792}}
 def test_recipe_is_closed_and_reproducible(self):self.assertEqual(self.raw,archive(self.root));self.assertEqual(set(n.unpack(self.raw,self.m['recipe'])),n.FILES)
 def test_real_native_signature(self):
  key=Ed25519PrivateKey.generate();pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw);e={'schema':'oos-signed-v1','purpose':n.PURPOSE,'algorithm':'Ed25519','issuer':n.digest(pub),'payload':self.m};e['signature']=base64.b64encode(key.sign(n.canonical(e))).decode();self.assertEqual(n.verify(e,pub),self.m);e['payload']['instanceId']='b7a1f6b1-c4aa-4de7-95fb-29d509d3398d'
  with self.assertRaises(Exception):n.verify(e,pub)
 def test_cross_instance_and_unqualified_image_refused(self):
  for key,value in [('instanceId','b7a1f6b1-c4aa-4de7-95fb-29d509d3398d'),('operation','execute')]:
   m=copy.deepcopy(self.m);m[key]=value
   with self.assertRaises(ValueError):n.validate(m)
  m=copy.deepcopy(self.m);m['image']['imageId']='sha256:'+'c'*64
  with self.assertRaises(ValueError):n.validate(m)
 def test_split_api_hosts_are_signed_and_instance_scoped(self):
  m=copy.deepcopy(self.m);m['schema']='oos-office-runtime-release-v2';m['publicApiOrigin']='https://portal.thecgp.com';self.assertEqual(n.api_hosts(n.validate(m)),['portal.thecgp.com:10.9.5.74'])
  m['instanceId']=m['installationId']='b7a1f6b1-c4aa-4de7-95fb-29d509d3398d';m['publicApiOrigin']='https://api.villesadp.ca';self.assertEqual(n.api_hosts(n.validate(m)),['portal.villesadp.ca:10.100.8.13','api.villesadp.ca:10.100.8.13'])
  m['publicApiOrigin']='https://portal.thecgp.com'
  with self.assertRaises(ValueError):n.validate(m)
 def test_changed_recipe_refused(self):
  with self.assertRaises(ValueError):n.unpack(self.raw+b'x',self.m['recipe'])
 def test_no_instance_secret_packaged(self):self.assertFalse(n.FILES&{'jwt','key.pem','runtime.json','config.xml'})
 def test_egress_is_scoped_and_host_initiation_blocked(self):
  r=firewall.rules('172.30.242.2','10.9.5.74');self.assertEqual(r['input'][-1][-1],{'drop':None});self.assertEqual(r['forward'][-1][-1],{'drop':None});self.assertEqual(r['forward'][1][1]['match']['right'],'10.9.5.74');self.assertEqual(r['forward'][1][2]['match']['right'],443)
 def gate(self,binding,rooms):
  (self.root/'policy').write_text(json.dumps({'runtime':{}}));(self.root/'supervisor').write_text(json.dumps({'root':str(self.root),'policy':str(self.root/'policy')}))
  class Runtime:
   def __init__(self,p):pass
   def sql(self,q):return b'document_connector_bindings\ndocument_office_rooms\n'if q=='SHOW TABLES;'else str(binding if 'bindings'in q else rooms).encode()
  with patch.dict(sys.modules,{'generic_runtime':types.SimpleNamespace(GenericRuntime=Runtime)}):controller.stop_allowed({'supervisor':str(self.root/'supervisor'),'instanceId':self.m['instanceId']})
 def test_stop_refused_with_live_binding_or_open_room(self):
  for binding,rooms in [(1,0),(0,1)]:
   with self.assertRaises(ValueError):self.gate(binding,rooms)
 def test_stop_allows_unbound_empty_instance(self):self.gate(0,0)
if __name__=='__main__':unittest.main()
