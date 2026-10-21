# Cycle serveur natif — Office 10.0.0.2

Le Control Plane fabrique la capsule de service, vérifie l'export OCI du moteur
compilé, signe le manifeste propre à l'installation et publie les deux objets en
privé. Le bootstrap local vérifie la clé CP déjà approuvée par le superviseur
natif, l'UUID d'installation, les empreintes et la séquence. Aucun pull d'image,
import de credential, binding GED, compte employé ni données métier n'est fourni
par cette livraison. Le même moteur est réutilisé pour les deux organisations.

Le prérequis système est installé par apt Ubuntu signé, versions épinglées :
docker.io 29.1.3-0ubuntu4.1, containerd 2.2.2-0ubuntu1.1 et runc 1.4.0-0ubuntu1.
Le conteneur a 5 Gio de mémoire et swap total, 2 CPU, 512 processus, logs bornés,
état privé persistant et JWT généré une fois sur l'hôte. Seul 127.0.0.1:18080 est
publié. Le filtre propre au service autorise uniquement les connexions sortantes
vers le proxy Portal de son instance en TCP/443 ; DNS externe désactivé, nom du
Portal résolu explicitement. Les autres règles, services et volumes sont conservés.

Le lancement systemd est idempotent. L'arrêt contrôlé exige un binding Office
suspendu et aucune salle OPEN dans le registre natif, contrôlés par le runtime SQL
installé. Fermer d'abord les éditeurs, attendre les admissions GED, puis suspendre
le binding ; ne pas suspendre le binding avant les callbacks attendus. Un refus
n'arrête pas le conteneur. L'unité oneshot n'utilise aucun processus attaché pouvant
transmettre un signal fatal au moteur lors de ce refus. Un arrêt électrique de la
VM/Docker reste une coupure : le moteur conserve ses sessions en mémoire seulement.
Après un redémarrage, son époque change et le portail doit demander la reprise.
Aucun reçu ne prétend sauver des modifications non admises avant la coupure.

La santé locale n'est pas une réception TLS publique ni une activation de la GED.
Il reste à fournir la destination HTTPS validée pour le moteur, à configurer sa
publication par le mécanisme réseau autorisé et à enregistrer/tester/activer le
connecteur avec réauthentification native. Ne jamais publier le secret JWT ni le
préremplir dans un paquet employé. La réception DOCX/XLSX/PPTX isolée demeure
acquise ; la réception de ce raccordement final est distincte.
