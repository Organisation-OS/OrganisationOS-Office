# OrganisationOS Office — Powered by ONLYOFFICE

Fork de ONLYOFFICE DocumentServer v10.0.0, préparé le 20 octobre 2026. Ce dépôt contient une version modifiée de la distribution source ONLYOFFICE développée par Ascensio System SIA. Les modifications actuelles portent sur les références de construction et les notices OrganisationOS. Le correctif nommé `server-redact-jwt-logs.patch` supprime les jetons rejetés et les charges JWT décodées des traces du serveur. Les interfaces légales amont restent intactes. Une première construction du serveur a terminé avec un code de sortie 0 depuis le commit `ae8c62b82da45f45116a991ae5c9ea641d0423ee` ; son reçu est dans `first-build-receipt-20261020.json`. Le moteur n’a pas encore reçu sa qualification de fonctionnement et aucun serveur issu du fork n’est distribué en production. Une seconde construction propre est en cours ; la reproductibilité n’est pas encore acquise.

Les composants directs et build_tools sont épinglés dans `sources.lock.json`. Les URL des sous-modules sont absolues afin qu’un clone du fork ne cherche pas des dépôts Organisation-OS inexistants. Les notices, marques, crédits et licence amont sont conservés. Le titre ci-dessus identifie l’intégration ; il ne prétend pas à une édition officielle ni à une approbation de l’éditeur.

## Construction et qualification

Utiliser un environnement DEV dédié Ubuntu 24.04 x64 selon la recette amont, au moins 4 cœurs, 8 Go de mémoire, 100 Go SSD libres et 4 Go swap. Les prérequis hôte ne doivent pas être installés implicitement sur une production. Le serveur est le seul produit demandé.

1. Extraire le commit exact du fork et conserver son arbre ; `git submodule update --init --recursive` respecte les gitlinks, sans `--remote`. Vérifier récursivement les SHA et enregistrer tous les composants transitifs.
2. Installer build_tools au SHA épinglé dans un répertoire frère des composants. Inspecter et verrouiller les téléchargements de dépendances système, Python, Qt, Node et bibliothèques. Le verrou de dépendances transitives et le miroir d’artefacts restent à produire sur le banc ; les références directes seules ne prouvent pas une construction reproductible.
3. La commande amont `automate.py` active les mises à jour par défaut. Pour une construction épinglée, préparer explicitement les composants, exécuter `configure.py --module server --update 0` avec les options du banc qualifié, puis `make.py`. Ne jamais lancer la recette amont non bornée contre des worktrees existants.
4. Ajouter les notices et la source correspondante à l’archive de distribution ; construire deux fois dans des répertoires propres, comparer les inventaires et documenter toute partie non déterministe avant signature CP. Aucun conteneur amont inchangé ne peut être étiqueté comme un binaire du fork.
5. Qualifier DOCX/XLSX/PPTX, coédition, reprise et callbacks dans la GED avec secrets d’instance externes, restrictions réseau et antivirus. L’archive, les dépendances, la configuration et les contrôles de santé doivent suivre le cycle natif d’installation, mise à jour et retrait.

## Licence et accès au code

La [licence exacte](../LICENSE) est AGPLv3 avec conditions additionnelles de conservation des notices, date et description des modifications, attribution à ONLYOFFICE / Ascensio System SIA et accès visible aux notices légales. Certains contenus non logiciels relèvent de CC BY-SA 4.0. La politique de marques est référencée dans la licence ; aucune suppression ou substitution des mentions amont n’est prévue.

Le fork et ses modifications sont publiés dans ce dépôt. Chaque distribution devra proposer dans son interface les notices, le commit exact et l’archive complète du code correspondant, y compris scripts et modifications de construction. Le simple lien vers un dépôt privé ou la mention Powered by n’est pas une offre de source suffisante. L’intégration propriétaire ou la suppression des marques nécessiteraient une analyse distincte ; aucune exemption AGPL n’est supposée ici.

Les limites réelles de l’édition v10.0.0 et de cette construction doivent être mesurées et documentées lors de la qualification. Aucun nombre illimité de connexions ni de sessions de coédition n’est annoncé à partir d’une FAQ d’une autre version.

## Mises à jour amont

Suivre les versions et avis de sécurité officiels. Créer une branche de succession, mettre à jour séparément les pins et les empreintes de licence, examiner les écarts, rejouer les tests de sauvegarde/concurrence/isolement puis signer une nouvelle version immuable. Conserver l’artefact précédent et les contenus en attente ; le retour du code ne restaure pas les données métier. Les changements OrganisationOS restent dans ce répertoire ou dans des patches nommés avec motif et test associé.

## Reprise de la construction propre du 20 octobre 2026

La seconde construction utilise le conteneur épinglé par digest dans le reçu du banc, avec `xz-utils` nécessaire aux outils LLVM amont. Le marqueur `packages_complete` appartient aux dépendances du conteneur et doit être supprimé avant `deps.py` lors d’une reprise dans un nouveau conteneur ; le garder depuis le worktree ne prouve pas la présence des paquets système.

L’acquisition réseau initiale de V8 a été interrompue après un blocage. La reprise a utilisé uniquement un clone Git des sources au commit `a2d8eca22ad478a95ca67bb2421a9a2535113925`, puis une synchronisation gclient vers cette référence exacte et ses hooks officiels. Aucun objet compilé du moteur n’a été réutilisé. L’outil Ninja téléchargé précédemment a été réutilisé avec son empreinte `09f0e5a8a2cf762b24b4d3ed464ffb2529e650d2efc36bab31da36aa93791efc` ; il s’agit d’un outil de construction, distinct des sorties du moteur. Cette reprise est une intervention documentée, pas encore une recette autonome entièrement qualifiée.

Les avertissements de copie concernant Metrics/modern-syslog et l’exemple Node doivent encore être rapprochés du périmètre serveur exécuté. Le succès de compilation ne constitue pas une réception DOCX/XLSX/PPTX, de coédition, d’antivirus ou de callbacks GED.

## Correctif de confidentialité du serveur

La réception réelle de la version épinglée a montré que `checkJwt` journalisait un jeton rejeté au niveau WARN et la charge décodée au niveau DEBUG. Le correctif nommé supprime ces valeurs et le message libre de l’erreur ; seule sa classe est conservée. La recette applique le patch une fois et refuse une base incompatible. Une qualification doit soumettre un JWT synthétique identifiable puis vérifier son absence dans les journaux de l’image reconstruite. Aucun secret réel n’a été utilisé pendant ce constat.


## Réception I et correction de la preuve de sauvegarde (21 octobre 2026)

La construction I depuis `e0f4e9fb795e89bc6718b0f390f9e706faa82cb7` démarre et qualifie réellement l'édition DOCX/XLSX/PPTX, six retours avec contenu et la confidentialité des journaux (sept contrôles). Elle reste refusée pour l'admission GED : le champ baseSha256 décrit Editor.bin après conversion et non le document source initial ; externalChangeInfo peut être présent pour une sauvegarde intermédiaire ordinaire sans que ses changements synthétiques soient appliqués. Aucun de ces résultats n'autorise une mise en production ni ne prouve la reproductibilité binaire.

La preuve v2 distingue sourceSha256 (octets téléchargés avant conversion, témoin interne borné conservé dans le cache de la session) et baseSha256 (base convertie). Le condensat de séquence lie les deux. Une source absente ou invalide rend la preuve non fiable ; le consommateur doit garder le contenu en récupération privée. Le témoin n'est ni une URL ni un secret. L'indicateur de changements externes est activé uniquement au point où la branche de repli est effectivement utilisée. Le serveur conserve cette preuve bornée dans le retour signé même lorsque l'historique détaillé dépasse la limite amont.

Le numéro de construction suivant est 10.0.0.2. `test-snapshot-identity.cjs` couvre 21 assertions du helper ; la réception réelle de la nouvelle construction et son admission GED restent obligatoires. Sur un arbre ayant déjà reçu l'ancien patch v1, retirer exactement ce patch conservé avant d'appliquer v2, sans réinitialiser les autres modifications. Ne pas présenter une qualification du helper comme une réception du convertisseur reconstruit.
