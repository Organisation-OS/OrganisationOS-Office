#!/usr/bin/python3
"""Publish a non-secret runtime identity on every actual DocService start, including supervisor restarts."""
from pathlib import Path
import json, os, time, uuid
root=Path('/var/www/onlyoffice/documentserver/web-apps/organisationos')
marker=root/'runtime.json'
temporary=root/('runtime-'+str(uuid.uuid4())+'.tmp')
raw=json.dumps({'schema':'organisationos-office-runtime-epoch-v1','epoch':str(uuid.uuid4()),'startedAt':int(time.time()),'sessionPersistence':'MEMORY_ONLY'},sort_keys=True,separators=(',',':')).encode()
fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
os.replace(temporary,marker)
fd=os.open(root,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
os.execv('/var/www/onlyoffice/documentserver/server/DocService/docservice',['docservice'])
