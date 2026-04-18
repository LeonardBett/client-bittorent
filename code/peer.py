import socket
import struct
import hashlib

# Fonction utile pour boucler sur un receive en attendant d'avoir recu la taille demandé
def receiveAll(socket, taille):
    buff = b""
    while (len(buff)<taille) :
        data = socket.recv(taille - len(buff))
        if (len(data) ==0):
            print("Erreur lors de la lecture d'un socket")
            exit()
        buff +=data
    return buff

# Commence la connexion avec le peer, lui envoi puis verifie le handshake puis attends de recevoir le message unshoke
def handshakeUnchoke(peerIp, peerPort, dicoInfoTorrentHash, peerId):
    # On ouvre un socket sur le peer (le .bind sert pour les tests en locals)
    peerSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    peerSocket.settimeout(10)
    peerSocket.bind(('127.0.0.2',0)) 
    peerSocket.connect((peerIp, peerPort))
    
    # On construit puis envoie le message handshake du protocole bittorrent (sur 68 octets)
    # Explication du message : > veut dire big endian (ecrit de gauhe a droite), B=19 la longeur du message, 19s=bitorrent l'id du proto, 
    # 8s=(huit octet a 0) le parametre pas utilisé pour notre client, 20s le hash des info de notre fichier et 20s notre peerId
    handshakeMessage = struct.pack('>B19s8s20s20s',19,b'BitTorrent protocol',(b'\x00'*8), dicoInfoTorrentHash, peerId)
    peerSocket.sendall(handshakeMessage)

    # On verifie la bonne forme de la reponse a notre handshake
    handshakeResponse = receiveAll(peerSocket,68)
    if (handshakeResponse[28:48] !=dicoInfoTorrentHash):
        print("Mauvais handshake recu")
        exit()
    print("Le handshake recu par le pair est valide")

    # On construit et envoi le message interested pour ne plus etre choked par ce pair
    peerSocket.sendall(struct.pack('>IB',1,2)) 
    print("Envoi de la requete interested au pair")

    # On attends le message unchoke avant de demander les données
    unchoked=False
    while (unchoked==False) :
        # On recoit seulement 4 octects pour avoir la taille de ce qui arrive
        tailleMessage = receiveAll(peerSocket, 4)
        if (tailleMessage==0):
            print("Erreur lors de la lecture d'un socket")
            exit()
        # On extrait du binaire la taille des messages qui arrive
        tailleData = struct.unpack('>I',tailleMessage)[0]

        # Message keep alive recu, on l'ignore
        if (tailleData== 0): 
            continue
        
        # On recoit un octet pour recuperer puis traduire binairement l'id du message recu
        messageId =struct.unpack('>B',receiveAll(peerSocket,1))[0]
        # On recoit le reste du message (inutile donc on le garde pas)
        receiveAll(peerSocket,tailleData-1)
        
        if (messageId==5):
            print("Message bitfield recu du pair")
        elif (messageId==1) :
            print("Message unchoke recu du pair, debut du télechargement")
            unchoked = True

    # On renvoi le socket pret a telecharger avec le peer
    return peerSocket

# Telecharge chez un peer une piece en particulier
def downloadPiece(peerSocket, pieceId, taillePiece):
    # On telecharge bout par bout de taille 16ko
    tailleBloc = 16384

    pieceData = b""
    offset = 0

    # On fait la demande du premier bloc de la piece
    tailleBlocActuel =min(tailleBloc, taillePiece-offset)
    # I=13 la taille du message, B=6 le type de message (request)
    peerSocket.sendall(struct.pack('>IBIII', 13,6, pieceId,offset,tailleBlocActuel))
    
    # On boucle sur toute la taille de la piece
    while (len(pieceData)<taillePiece) :
        # On recoi la taille du message de reponse a notre demande de bloc
        tailleMessage = receiveAll(peerSocket,4)
        if(tailleMessage==0):
            print("Erreur lors de la lecture d'un socket")
            exit()
        # On extrait du binaire la taille des messages qui arrive
        tailleData = struct.unpack('>I',tailleMessage)[0]

         # Message keep alive recu, on l'ignore
        if (tailleData==0): 
            continue
        
        # On recoit un octet pour recuperer puis traduire binairement l'id du message recu
        messageId =struct.unpack('>B', receiveAll(peerSocket, 1))[0]

        # On recoit le payload du message, soit la piece qu'on a demandé
        messageData = receiveAll(peerSocket,tailleData-1)
        
        # On verifie que la reponse recu est bien l'id du message piece
        if (messageId==7):
            # On ingore les 8 premiers octect de la reponse qui sont des infos sur la piece et on lit le reste, les données du bloc
            blocData = messageData[8:]
            pieceData +=blocData
            offset += len(blocData)
            
            # Si on a pas fini de dl la piece, on demande le prochain bloc
            if (offset<taillePiece):
                tailleBlocActuel = min(tailleBloc, taillePiece-offset)
                # I=13 la taille du message, B=6 le type de message (request)
                peerSocket.sendall(struct.pack('>IBIII', 13, 6, pieceId, offset, tailleBlocActuel))
                
    # On renvoi la piece telechargé
    return pieceData

# Telecharge un fichier torrent chez un peer
def downloadFileFromPeer(peerIp, peerPort, dicoInfoTorrentHash, peerId, listeHashPieces, tailleFichier, taillePieces):

    # On se connecte à la paire avec le handshake, puis on attends le message unchoke
    peerSocket = handshakeUnchoke(peerIp,peerPort, dicoInfoTorrentHash, peerId)

    # On lance la boucle de telechargement pour chaque piece
    donnéeRecu = b""
    idPiece = 0
    for piece_hash in listeHashPieces:
        # On verifie qu'on n'est pas a la derniere piece pour adapter sa taille
        if (idPiece==len(listeHashPieces)-1) :
            taillePiece = tailleFichier-(idPiece*taillePieces)
        else:
            taillePiece = taillePieces
            
        print(f"Telechargement de la piece {idPiece}")

        # On fait la demande de telechargement de la piece actuel
        donnéePiece = downloadPiece(peerSocket, idPiece, taillePiece)
        
        # On calcul (et passe en binaire) le hash de la piece recu pour le comparer avec celui attendu
        if (hashlib.sha1(donnéePiece).digest() == piece_hash):
            donnéeRecu +=donnéePiece
        else:
            print(f"Le hash de la piece {idPiece} est incorrect")
            exit()
        
        idPiece+=1

    # On ferme la conneixon et renvoi les données téléchargé et verifié     
    peerSocket.close()
    return donnéeRecu

    

    
