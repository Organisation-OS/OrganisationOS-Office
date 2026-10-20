# OrganisationOS Office — Powered by ONLYOFFICE

Fork de ONLYOFFICE DocumentServer v10.0.0, préparé le 20 octobre 2026. Ce dépôt contient une version modifiée de la distribution source ONLYOFFICE développée par Ascensio System SIA. Les modifications actuelles portent sur les références de construction et les notices OrganisationOS. Le moteur et les interfaces amont n’ont pas encore été modifiés. Aucun binaire OrganisationOS Office n’a été construit, publié ou exécuté.

Les composants directs et build_tools sont épinglés dans `sources.lock.json`. Les URL des sous-modules sont absolues afin qu’un clone du fork ne cherche pas des dépôts Organisation-OS inexistants. Les notices, marques, crédits et licence amont sont conservés. Le titre ci-dessus identifie l’intégration ; il ne prétend pas à une édition officielle ni à une approbation de l’éditeur.

## Construction et qualification restantes

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
