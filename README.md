# Projet Réseau - Client BitTorrent Minimal (fichier en une seule partie pour le moment)

Ce dépôt contient l'implémentation d'un client BitTorrent simplifié développé en Python. Il est capable de lire un fichier `.torrent`, de contacter un tracker HTTP, d'effectuer le handshake avec un pair et de télécharger un fichier d'une seule pièce. 

Le code n'utilise aucune bibliothèque externe pour le réseau ou l'encodage Bencode (uniquement `socket`, `hashlib`, `struct`, etc.).

## 1. Prérequis et Configuration de qBittorrent

Le projet est conçu pour être testé en boucle locale (localhost). qBittorrent est utilisé à la fois comme tracker et comme seeder. 

**Paramètres stricts à appliquer dans qBittorrent :**

1. **Tracker intégré :**
   * Allez dans *Outils > Options > Avancé*.
   * Cochez **Activer le tracker intégré**. (Le port par défaut est le 9000).
2. **Autorisation du bouclage local (Crucial) :**
   * Toujours dans *Outils > Options > Avancé*.
   * Cochez impérativement **Autoriser plusieurs connexions depuis la même adresse IP**. Sans cela, qBittorrent fermera instantanément la connexion TCP du script.
3. **Désactivation du chiffrement forcé :**
   * Allez dans *Outils > Options > BitTorrent*.
   * Réglez le *Mode de chiffrement* sur **Préférer le texte clair** ou **Désactivé**.

*Note : Il est conseillé de redémarrer qBittorrent après avoir appliqué ces modifications.*

## 2. Création du fichier .torrent

Le dépôt contient un fichier source de test : `data.txt`. Vous devez générer le fichier `.torrent` associé pour lancer l'exécution :

1. Dans qBittorrent, ouvrez **Outils > Créateur de torrent**.
2. **Source :** Cliquez sur *Sélectionner le fichier* et choisissez `data.txt`.
3. **Tracker :** Dans le champ *URL des Trackers*, inscrivez exactement : `http://127.0.0.1:9000/announce`
4. **Taille de la pièce :** Sélectionnez une taille strictement supérieure au poids de `data.txt` (par exemple **64 Kio**). C'est ce qui garantit que le client n'aura qu'une seule pièce à télécharger.
5. Cochez la case **Commencer le seed immédiatement**.
6. Cliquez sur **Créer le torrent** et sauvegardez le fichier sous le nom `data.torrent` à la racine du projet, au même niveau que le script Python.

## 3. Exécution

Vérifiez que le torrent fraîchement créé apparaît bien "En émission" (Seeding) dans qBittorrent.

Lancez ensuite le client depuis un terminal :

```bash
python projet.py
```

Le déroulement attendu affiché dans la console couvre les étapes suivantes :
1. Décodage du fichier `.torrent` (format Bencode).
2. Requête HTTP au tracker local et récupération de la liste des pairs.
3. Ouverture du socket TCP et Handshake avec le pair qBittorrent.
4. Échange des messages du protocole (Interested, Unchoke, Request, Piece).
5. Vérification de l'intégrité via le hachage SHA-1.
6. Écriture du fichier final sous le nom `dl_data.txt`.
