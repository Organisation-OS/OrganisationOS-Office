"""Prepare the exact upstream CEF dependency on a dedicated Windows x64 builder.
No compilation, extraction or executable launch. Other build dependencies remain separate.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
TOOLS='a9f9895b172b09595abcafe85d56fab163f9ecb7'
MODULE='62f04ad8553401181acdbe9a93a224b756e7f11c708c316086154cbfe1ffdedc'
ARCHIVE='0ef79ad22cc1b2e9364e6a165d1ee00f9348b46f6bb94615a48ed402145f741a'
DATA='382ce03a22c5bfb98848b1483a6716b81ee4aeb3'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def patch(raw):
 if hashlib.sha256(raw).hexdigest()!=MODULE:raise ValueError('Unexpected pinned upstream CEF module')
 s=raw.decode().replace('import glob','import glob\nimport hashlib')
 s=s.replace('https://github.com/ONLYOFFICE-data/build_tools_data/raw/refs/heads/master/cef/','https://raw.githubusercontent.com/ONLYOFFICE-data/build_tools_data/'+DATA+'/cef/')
 s=s.replace('    # extract\n',"    if platform != 'win_64':\n      raise RuntimeError('OrganisationOS Desktop lock supports only win_64')\n    with open(archive_name, 'rb') as archive:\n      actual = hashlib.sha256(archive.read()).hexdigest()\n    if actual != '"+ARCHIVE+"':\n      raise RuntimeError('CEF archive hash mismatch: extraction refused')\n\n    # extract\n")
 s=s.replace('      os.chdir(base_dir)\n      continue',"      raise RuntimeError('Use a fresh CEF build directory for the received dependency')")
 assert s.count(ARCHIVE)==1 and 'refs/heads/master/cef/'not in s
 compile(s,'pinned-cef.py','exec');return s.encode()
def main():
 p=argparse.ArgumentParser();p.add_argument('--build-tools',type=Path,required=True);p.add_argument('--core',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);p.add_argument('--check-only',action='store_true');a=p.parse_args()
 if subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.build_tools,text=True).strip()!=TOOLS:raise ValueError('Build tools commit mismatch')
 source=a.build_tools/'scripts/core_common/modules/cef.py';raw=source.read_bytes();replacement=patch(raw)
 if a.archive.stat().st_size!=95544651 or sha(a.archive)!=ARCHIVE:raise ValueError('Unreceived CEF archive')
 target=a.core/'Common/3dParty/cef/win_64'
 if (target/'build').exists():raise ValueError('CEF build cache already exists; use a fresh dedicated build tree')
 destination=target/'cef_binary.7z'
 if destination.exists()and sha(destination)!=ARCHIVE:raise ValueError('Refusing to overwrite an unrelated archive')
 receipt={'status':'CHECKED_ONLY'if a.check_only else'PREPARED_NOT_BUILT','toolsCommit':TOOLS,'originalModuleSha256':MODULE,'patchedModuleSha256':hashlib.sha256(replacement).hexdigest(),'archiveSha256':ARCHIVE,'dataCommit':DATA,'otherDependenciesClosed':False}
 if not a.check_only:
  target.mkdir(parents=True,exist_ok=True)
  if not destination.exists():shutil.copyfile(a.archive,destination)
  if sha(destination)!=ARCHIVE:raise ValueError('Copied archive failed verification')
  source.write_bytes(replacement)
  (target/'organisationos-cef-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt))
if __name__=='__main__':main()
