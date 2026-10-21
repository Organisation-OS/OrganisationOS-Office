# Dependency/init layer only. Every document-server executable and web asset is replaced below.
FROM onlyoffice/documentserver@sha256:ca17889f10b11141cc6441836aebdd2835cf3e1b49681b2fd6e155c94b7850b3 AS runtime-base
FROM runtime-base
USER root
RUN rm -rf /var/www/onlyoffice/documentserver /var/www/onlyoffice/documentserver-example && mkdir -p /var/www/onlyoffice/documentserver
COPY documentserver/ /var/www/onlyoffice/documentserver/
# Pinned upstream JSON configuration helper; this is not a document-server engine.
COPY --from=runtime-base /var/www/onlyoffice/documentserver/npm/ /var/www/onlyoffice/documentserver/npm/
COPY configuration/default.json /etc/onlyoffice/documentserver/default.json
COPY configuration/production-linux.json /etc/onlyoffice/documentserver/production-linux.json
COPY provenance.json /var/www/onlyoffice/documentserver/web-apps/organisationos/provenance.json
COPY source.html /var/www/onlyoffice/documentserver/web-apps/organisationos/source.html
COPY oos-entrypoint.sh /usr/local/bin/oos-office-entrypoint
COPY oos-docservice-start.py /usr/local/bin/oos-docservice-start
COPY ds-organisationos.conf /etc/onlyoffice/documentserver/nginx/includes/ds-organisationos.conf
RUN chmod 0755 /usr/local/bin/oos-office-entrypoint /usr/local/bin/oos-docservice-start && \
    sed -i "s@^command=/var/www/onlyoffice/documentserver/server/DocService/docservice$@command=/usr/local/bin/oos-docservice-start@" /etc/supervisor/conf.d/ds-docservice.conf && \
    cd /var/www/onlyoffice/documentserver && cp server/LICENSE.txt LICENSE.txt && cp server/3rd-Party.txt 3rd-Party.txt && cp -a server/license license && mkdir -p fonts && \
    LD_LIBRARY_PATH="$PWD/server/FileConverter/bin" server/tools/allfontsgen \
      --input="$PWD/core-fonts" --allfonts-web="$PWD/sdkjs/common/AllFonts.js" \
      --allfonts="$PWD/server/FileConverter/bin/AllFonts.js" --images="$PWD/sdkjs/common/Images" \
      --selection="$PWD/server/FileConverter/bin/font_selection.bin" --output-web=fonts --use-system=true && \
    LD_LIBRARY_PATH="$PWD/server/FileConverter/bin" server/tools/allthemesgen \
      --converter-dir="$PWD/server/FileConverter/bin" --src="$PWD/sdkjs/slide/themes" --output="$PWD/sdkjs/common/Images" && \
    chown -R ds:ds /var/www/onlyoffice/documentserver
ENV GENERATE_FONTS=false EXAMPLE_ENABLED=false ADMINPANEL_ENABLED=false WELCOME_PAGE_ENABLED=false METRICS_ENABLED=false JWT_ENABLED=true WOPI_ENABLED=false ALLOW_META_IP_ADDRESS=false ALLOW_PRIVATE_IP_ADDRESS=false
ENTRYPOINT ["/usr/local/bin/oos-office-entrypoint"]
