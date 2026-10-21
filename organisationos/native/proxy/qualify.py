"""Run inside a disposable network namespace; no production listener is used."""
from pathlib import Path
import hashlib, http.server, json, socket, subprocess, tempfile, threading, time, urllib.request, urllib.error
from proxy import block, extend, remove

subprocess.run(['ip', 'link', 'set', 'lo', 'up'], check=True)
checks = []
class Backend(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get('Upgrade') == 'websocket':
            assert self.headers.get('Connection') == 'upgrade'
            self.send_response(101); self.send_header('Upgrade', 'websocket'); self.send_header('Connection', 'Upgrade'); self.end_headers(); return
        body = json.dumps({'path':self.path, 'host':self.headers.get('Host'), 'forwardedHost':self.headers.get('X-Forwarded-Host'), 'scheme':self.headers.get('X-Forwarded-Proto'), 'forwarded':self.headers.get('Forwarded'), 'peer':self.headers.get('X-Forwarded-For')}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('X-Frame-Options', 'SAMEORIGIN'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *_): pass
server = http.server.ThreadingHTTPServer(('127.0.0.1',18080),Backend)
threading.Thread(target=server.serve_forever,daemon=True).start()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for host in ['portal.thecgp.com','portal.villesadp.ca']:
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp); p.chmod(0o755)
        base='server {\n listen 127.0.0.1:18081;\n server_name '+host+';\n add_header X-Frame-Options DENY always;\n add_header Content-Security-Policy "default-src \'self\'; frame-ancestors \'none\'" always;\n'+('  ' if host=='portal.thecgp.com' else '    ')+'location / { return 204; }\n}\n'
        after=extend(base,host); assert remove(after,host)==base
        for bad in [after, base+base]:
            try: extend(bad,host)
            except ValueError: pass
            else: raise AssertionError('Drift accepted')
        conf='pid '+str(p/'pid')+'; error_log '+str(p/'error.log')+'; events {} http { access_log off; '+after+'}\n'
        (p/'nginx.conf').write_text(conf)
        subprocess.run(['/usr/sbin/nginx','-t','-c',str(p/'nginx.conf')],check=True,capture_output=True)
        process=subprocess.Popen(['/usr/sbin/nginx','-c',str(p/'nginx.conf'),'-g','daemon off;'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for attempt in range(50):
                try:
                    with socket.create_connection(('127.0.0.1',18081),timeout=.2):break
                except OSError:time.sleep(.02)
            req=urllib.request.Request('http://127.0.0.1:18081/office/web-apps/api.js?synthetic=1',headers={'Host':host,'X-Forwarded-Host':'evil.example','X-Forwarded-Proto':'http','X-Forwarded-For':'203.0.113.4','Forwarded':'host=evil.example'})
            with opener.open(req) as r:
                data=json.load(r); assert r.headers['X-Frame-Options']=='SAMEORIGIN'; assert r.headers.get('Content-Security-Policy') is None
            assert data=={'path':'/web-apps/api.js?synthetic=1','host':host,'forwardedHost':host+'/office','scheme':'https','forwarded':None,'peer':'127.0.0.1'}
            for endpoint in ['/office/','/office/example/','/office/info','/office/metrics']:
                try:opener.open('http://127.0.0.1:18081'+endpoint)
                except urllib.error.HTTPError as e:assert e.code==404
                else:raise AssertionError('Auxiliary route exposed')
            with opener.open('http://127.0.0.1:18081/') as r:assert r.status==204 and r.headers['X-Frame-Options']=='DENY'
            with socket.create_connection(('127.0.0.1',18081)) as sock:
                sock.sendall(('GET /office/doc/synthetic/c HTTP/1.1\r\nHost: '+host+'\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n').encode());assert b'101 Switching Protocols' in sock.recv(4096)
            checks.append({'host':host,'roundTripRemoval':True,'driftRefused':True,'nginxSyntax':True,'fixedOriginAndPrefix':True,'spoofedHeadersDiscarded':True,'portalHeadersPreserved':True,'engineFrameHeadersPreserved':True,'auxiliaryRoutesDenied':True,'websocket101':True})
        finally:
            process.terminate();process.wait(timeout=5)
server.shutdown()
print(json.dumps({'status':'PASS','checks':checks,'sourceSha256':hashlib.sha256(Path(__file__).with_name('proxy.py').read_bytes()).hexdigest(),'scope':'isolated real nginx and synthetic HTTP/WebSocket peer; not an editor reception'}))
