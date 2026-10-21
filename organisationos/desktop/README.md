# OrganisationOS Office Desktop — Powered by ONLYOFFICE

Candidat séparé du serveur DocumentServer. Aucun exécutable Desktop OrganisationOS
compilé ou publié à ce checkpoint. Aucun binaire officiel renommé n'est utilisé.
Les recherches des sources et passations locales DEV/Core/Portal/Tools, Control
Plane et Ville n'ont pas retrouvé un fork Desktop antérieur. Les passations
BuddyCore consultées décrivent les contrats Portal et GED, pas une recette Desktop.
Ce constat porte sur les emplacements examinés, pas sur des sources inconnues.

## Construction à reprendre sur un builder Windows x64 autorisé

La source amont retenue est DesktopEditors v10.0.0 et ses gitlinks exacts, indiqués
dans sources.lock.json. Les composants core/sdkjs/web-apps diffèrent de ceux du
serveur reçu : ne pas remplacer leurs pins par les sorties Linux du serveur.
Les sources desktop-apps et desktop-sdk ont été récupérées et examinées sur DEV.
Le lien amont web-apps pointe vers web-apps-pro : sa disponibilité et les droits
associés restent à résoudre, sans substituer silencieusement web-apps public.

La recette amont est build_tools/configure.py puis make.py, module desktop,
plateforme win_64, update=0. Elle appelle vcvarsall.bat et Qt qmake pour MSVC;
les scripts d'emballage sont desktop-apps/package/inno. Les versions et empreintes
réelles de MSVC, Windows SDK, Qt, CEF, Python, Node et Inno doivent être fixées dans
un reçu avant compilation. Aucun builder Windows authentifié ni cette chaîne
n'est disponible dans les cinq machines Linux du mandat. Le poste utilisateur
n'est pas un builder et ne sera pas sollicité cette nuit.

Étapes de reprise :
1. Retrouver éventuellement le fork Desktop antérieur et rapprocher ses patches.
2. Sur builder dédié, récupérer chaque commit du lock et fermer les dépendances
   tierces ; conserver licences/notices et sources correspondantes.
3. Préparer l'identité OrganisationOS avec les mécanismes branding de build_tools,
   conserver les mentions ONLYOFFICE et les notices amont. Ne pas simuler le
   branding en renommant un installateur téléchargé.
4. Configurer `python configure.py --module desktop --platform win_64 --update 0
   --vs-version <version reçue> --vs-path <répertoire vcvarsall>
   --qt-dir <racine Qt reçue>`, puis `python make.py`. Cette commande est une
   procédure à compléter après préflight, pas une construction déjà reçue.
5. Construire deux fois, inventorier les PE AMD64, dépendances et signatures;
   consigner commit/arbre, outils, logs, hashes et écarts non reproductibles.
6. Emballer le moteur commun avec le seul provider propre à l'instance, puis
   faire fabriquer/signer le manifeste par le Control Plane et installer le
   catalogue avec scripts/software/catalogue_install.py. Aucun secret embarqué.

## Intégration réellement nécessaire

Le code amont `desktop-apps/common/loginpage/src/dialogconnect.js` utilise
`entryPage` pour éviter la saisie d'URL. Cela ne prouve aucune authentification.
Le provider OrganisationOS doit recevoir portal:login seulement après une session
native validée; portal:logout doit accompagner l'invalidation de cette session.
`open:document` doit ouvrir une route éditeur authentifiée autorisée par editorPage,
pas une URL de blob permanent. Le parcours doit réutiliser OfficeRooms, le coffre
Office et OfficeReturns/VersionAdmission, avec ACL et antivirus courants, CAS,
idempotence et récupération privée. Ces adaptateurs HTTP/Portal ne sont pas encore
installés : les configs de provider restent candidates et aucun bouton fictif
n'est publié comme fonctionnel.

Les détections desktop=true, User-Agent et AscDesktopEditor sont uniquement des
indices d'interface, jamais une preuve d'identité ou une autorisation. Les données
hors ligne passent par la projection Syncthing autorisée et l'admission GED;
un enregistrement local ne signifie pas une nouvelle version GED publiée.

Les profils d'instance et la fiche candidate sont conservés dans le dépôt Core
privé, séparément du moteur générique. Le manifeste signé OrganisationOS et la
signature Authenticode Windows sont deux contrôles distincts. Aucune signature
Windows n'est revendiquée sans binaire. Réception sur profil propre reportée.

Sources amont :
- https://github.com/ONLYOFFICE/DesktopEditors/tree/v10.0.0
- https://github.com/ONLYOFFICE/build_tools
- https://api.onlyoffice.com/docs/desktop-editors/usage-api/adding-a-dms-provider
- https://api.onlyoffice.com/docs/desktop-editors/usage-api/adding-a-dms-provider/login-and-logout
- https://api.onlyoffice.com/docs/desktop-editors/usage-api/adding-a-dms-provider/opening-documents
