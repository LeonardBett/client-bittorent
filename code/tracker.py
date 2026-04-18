from bencode import *

import urllib.parse
import socket
import struct

# Recupere un peer dispo pour le fichier .torrent, en contactant son tracker par http
def getPeerFromTracker(urlTracker, dicoInfoTorrentHash, peerId, tailleFichier):
    # On parse l'url du tracker (récuprer dans le .torrent) pour extraire ses infos
    parseUrl = urllib.parse.urlparse(urlTracker)

    # On extrait le port avec 80 par défaut si il n'est pas préciser dans l'url du .torrent
    portTracker = parseUrl.port
    if (portTracker == None):
        portTracker= 80
    
    # On construit la requete http qu'on enverra au tracker pour recuperer les peer du fichier .torrent
    # .quote utilisé pour éviter les problemes de caracteres des données bineaires
    req = f"GET {parseUrl.path}?info_hash={urllib.parse.quote(dicoInfoTorrentHash)}&peer_id={urllib.parse.quote(peerId)}"
    req += f"&port=6881&uploaded=0&downloaded=0&left={tailleFichier}&compact=1 HTTP/1.1\r\n"
    req += f"Host: {parseUrl.hostname}\r\nConnection: close\r\n\r\n"

    print(f"Tentative de connexion au tracker {parseUrl.hostname} sur le port {portTracker }")

    # On ouvre au connexion tcp sur l'adresse au tracker puis on lui envoi la requete formée
    socketTracker = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socketTracker.connect((parseUrl.hostname,portTracker))
    socketTracker.sendall(req.encode())

    # On lit la reponse du tracker a notre requete par paquet de 4096 octets
    rep = b""
    c = socketTracker.recv(4096)
    while (len(c)>0):
        rep +=c
        c = socketTracker.recv(4096)
    socketTracker.close()

    # On recupere le body de la reponse (qui contient nos infos en bencode) et on le parse
    bodyRep = rep.split(b"\r\n\r\n")[1]
    bodyRepParse,_ = parseBencode(bodyRep)
    
    # On verifie que la reponse ne contient pas d'erreur
    if (b'failure reason' in bodyRepParse):
        print(f"Le tracker a renvoyé l'erreur {bodyRepParse[b'failure reason'].decode('utf-8')}")
        exit()

    # On extrait l'info sur les peers de la reponse du tracker et on renvoi un peer dispo
    torrentPeer = extractPeerFromTrackerRep(bodyRepParse)
    return torrentPeer

# Extrait la liste des pair d'une reponse parsé du tracker
def extractPeerFromTrackerRep(bodyRepParse):
    # On recupere dans la reponse la chaine des peers stocké en binaire par la clé peers
    peersBinaire = bodyRepParse.get(b'peers',b'')

    # On parcours cette chaine et on construit une liste de peers a partir d'elle
    # Un peers est codé par 4 octet pour l'ip et 2 pour son port
    peers =[]
    for i in range(0,len(peersBinaire),6):
        # struct.unpack pour lire et separer les 4 octet de l'ip et les 2 du port
        ipBinaire,peerPort = struct.unpack('!4sH', peersBinaire[i:i+6])
        # socket.inet_ntoa pour passer l'addresse binaire en asci
        peers.append((socket.inet_ntoa(ipBinaire),peerPort))

    print(f"{len(peers)} pairs données par le tracker")
    
    # On parcours la liste de peer crée pour verifier qu'il a bien un peer qui peut partager le fichier
    # On filtre le port 6881 car c'est celui qu'on a specifié lors de la requete au tracker et
    # celui ci nous enregistrera donc comme un peer dispo, et on ne veut pas se connecter à nous meme
    peer = -1
    for ip, p in peers:
        if (p !=6881):
            peer = (ip,p)
            break
    if (peer==-1):
        print("Aucun pair disponible pour ce torrent")
        exit()

    # On renvoi un peer valide
    return peer