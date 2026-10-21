# Raccordement natif Office sous le portail

Cette capsule ajoute uniquement `/office/` au NGINX existant. Le moteur reste
sur `127.0.0.1:18080`, dans son cycle de service signé indépendant. Les origines
retenues sont `https://portal.thecgp.com/office` et
`https://portal.villesadp.ca/office`. Aucun secret n'entre dans la configuration.

Le préfixe transmis dans `X-Forwarded-Host` suit le mécanisme amont
[ONLYOFFICE document-server-proxy](https://github.com/ONLYOFFICE/document-server-proxy/blob/master/nginx/proxy-to-virtual-path.conf).
Les hôtes sont constants ; les en-têtes d'origine présentés par le client ne
sélectionnent jamais l'amont. L'accès aux exemples et pages d'information est
refusé. Les politiques de la page Portal restent inchangées ; les réponses du
moteur conservent leurs propres en-têtes de cadre. Les URL signées et paramètres
WebSocket ne sont pas inscrits dans les journaux de cette route.

`qualify.py` utilise un véritable NGINX, un pair HTTP/WebSocket synthétique et
un espace réseau isolé sur DEV. Il vérifie la normalisation du chemin, les
en-têtes, les refus, le 101 WebSocket et la restitution exacte du fichier initial.
Ce test n'est pas une réception de l'éditeur, du proxy externe, ni du coffre.

Le CP signe le manifeste, les empreintes avant/après, les sources et la preuve.
`install.py preflight` vérifie l'identité native, la signature, le bundle actif,
la syntaxe dans un espace de montage privé et l'absence de dérive. `install`
remplace les seuls fichiers scellés sous verrou natif, puis recharge NGINX sans
redémarrer le moteur. Une erreur restitue les fichiers antérieurs et recharge
NGINX. `revert` exige encore exactement les fichiers installés et conserve les
reçus. Aucune migration SQL, attribution de droits ou liaison au coffre.

La séparation initiale du gateway TheCGP a un reçu historique conservé. Son
outil `progress_gateway provision` refuserait à raison cette extension
supplémentaire : avant de rejouer cette opération d'infrastructure, retirer la
capsule avec son action `revert`, puis préparer un successeur signé pour la
nouvelle configuration. La réconciliation ordinaire et les mises à jour Core
ne rejouent pas cette séparation. Ne pas réécrire les empreintes du reçu
historique pour simuler son état initial.

Après installation : contrôler santé, marqueur d'epoch, JavaScript API,
commande version avec JWT natif et refus d'un JWT invalide sur HTTPS ; contrôler
les WebSockets réellement transmis par NGINX Proxy Manager. L'activation du
connecteur Office reste soumise à la réauthentification native et à sa liaison
GED. Une réponse 200 de l'API JavaScript seule ne prouve pas une sauvegarde GED.
