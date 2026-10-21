"""Closed native Office virtual-path extension; no upstream from request input."""
import re

BEGIN = '# BEGIN OrganisationOS Office virtual path v1'
END = '# END OrganisationOS Office virtual path v1'


def block(host):
    if host not in ('portal.thecgp.com', 'portal.villesadp.ca'):
        raise ValueError('Unqualified organisation origin')
    return '''    %s
    location = /office { return 308 https://%s/office/; }
    location = /office/ { return 404; }
    location ~ ^/office/(?:welcome|example|info|metrics)(?:/|$) { return 404; }
    location /office/ {
        proxy_pass http://127.0.0.1:18080/;
        proxy_http_version 1.1;
        set $oos_office_connection close;
        if ($http_upgrade != "") { set $oos_office_connection upgrade; }
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $oos_office_connection;
        proxy_set_header Host %s;
        proxy_set_header X-Forwarded-Host %s/office;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Forwarded "";
        proxy_connect_timeout 5s;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_intercept_errors off;
        proxy_buffering off;
        client_max_body_size 32m;
        # Preserve engine frame/CSP headers, not the Portal's parent-page policy.
        add_header X-Content-Type-Options nosniff always;
        # Signed cache URLs and WebSocket credentials must not enter proxy logs.
        access_log off;
        error_log /dev/null crit;
    }
    %s
''' % (BEGIN, host, host, host, END)


def extend(before, host):
    if BEGIN in before or END in before or re.search(r'location\s+[^\n]*?/office', before):
        raise ValueError('Existing Office route needs its signed receipt')
    needle = '  location / {' if host == 'portal.thecgp.com' else '    location / {'
    if before.count(needle) != 1:
        raise ValueError('Expected one native Portal fallback')
    return before.replace(needle, block(host) + needle, 1)


def remove(after, host):
    addition = block(host)
    if after.count(addition) != 1:
        raise ValueError('Changed Office extension')
    return after.replace(addition, '', 1)
