from bencode import *
from tracker import *
from peer import *

import sys
import hashlib

# Sources utilisé pour comprendre bitTorrent (former les requete http, decoder/encoder le bencode) :
#   https://www.bittorrent.org/beps/bep_0003.html
#   https://wiki.theory.org/BitTorrentSpecification#Tracker_HTTP.2FHTTPS_Protocol

if __name__ == "__main__":
    # On recupère le fichier passé en arg
    if len(sys.argv) < 2:
        print("Veuillez préciser le nom du .torrent à télécharger")
        print("Utilisation : python main.py exemple.torrent")
        exit()
    fichierTorrent = sys.argv[1]
    
    # On le lit et recupere son contenu
    f = open(fichierTorrent, "rb")
    bencodeTorrent = f.read()
    f.close()

    # On parse l'encodage bencode du torrent pour récuper l'addrese du tracker et le dico d'info du fichier
    # Les clé ainsi que les valeurs de ce dico seront stocké en binaire
    parseTorrent, _ = parseBencode(bencodeTorrent)
    urlTracker = parseTorrent[b'announce'].decode('utf-8')
    dicoInfoTorrent = parseTorrent[b'info']

    # On reencode en bencode le dico d'info du torrent, puis on l'utilise pour générer un hash (qu'on enverra ensuite au tracker)
    dicoInfoTorrentHash = hashlib.sha1(encodeBencode(dicoInfoTorrent)).digest() # .digest renvoi le hash calculé en binaire

    # On recupere la taille du fichier cible ainsi que son nom
    tailleFichier = dicoInfoTorrent[b'length']
    nomFichier = dicoInfoTorrent[b'name'].decode('utf-8')

    # On recupere la taille des pièces du torent et le hash de toutes les pieces dans une liste
    taillePieces = dicoInfoTorrent[b'piece length']
    HashPieces = dicoInfoTorrent[b'pieces'] # Tout les hash des pieces à la suite
    # Un hash fait 20 octet alors on avance de 20 en 20
    listeHashPieces = [HashPieces[i:i+20] for i in range(0, len(HashPieces), 20)]

    print(f"Le fichier à télécharger est {nomFichier} et fait {tailleFichier} octets")
    print(f"Ce fichier est divisé en {len(listeHashPieces)} pieces de {taillePieces} octets")

    # On creer notre peer id (de maniere fixe pour ce projet, on pourrait la généré aléatoirement)
    # Necessaire pour discuter avec le tracker
    peerId = b"-PY0001-fnapJdsqJesn"

    # On recupere les peer du torrent via une requete http au tracker
    peer = getPeerFromTracker(urlTracker,dicoInfoTorrentHash,peerId,tailleFichier)

    print(f"Tentative de connexion au pair {peer[0]} sur le port {peer[1]}")

    # On lance le téléchargement du fichier sur le paire selectioné, en le sauvegardant dans le dossier du projet
    donnéeTorrent = downloadFileFromPeer(peer[0], peer[1], dicoInfoTorrentHash, peerId, listeHashPieces, tailleFichier, taillePieces)

    print("Toutes les pieces sont téléchargés et validées, ecriture du fichier")

    # On ecrit les données telechargé dans un fichier
    fichier = open("projet_"+nomFichier , "wb")
    fichier.write(donnéeTorrent)
    fichier.close()
    print("-> Opération terminée avec succès.")


    