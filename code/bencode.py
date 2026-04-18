# Fonction récursive qui parse un bencode donnée en paramètre en un dico pythons
# i contient l'indice de lecture actuel de ce bencode
def parseBencode(data, i=0):

    # Condition d'arret (normalement inutile, que si on arrive a la fin fichier sans avoir fini de parser)
    if (i >= len(data)): 
        return None,i
    
    # On recupere la prochaine valeur bineaire du bencode (le code de type de donnée)
    c = data[i:i+1]

    # Le bencode contient un dico (comme pour les info du torrent), comme d3:taillei12e...e par exemple
    if (c == b'd'):
        dico = {}
        i +=1
        # Tant qu'on arrive pas à la fin du dico, on recupere en rappelant cette fonction les prochaine clé/valeur
        while (data[i:i+1] != b'e'):
            clé,i = parseBencode(data,i)
            valeur,i = parseBencode(data,i)
            dico[clé] = valeur
        return dico,i+1
    
    # Un entier est stocké à l'indice de lecture actuelle (exemple i12e)
    if (c == b'i'):
        indiceFin= data.find(b'e', i)
        return int(data[i+1:indiceFin]), indiceFin+1
    
    # Une liste est stocké à l'indice de lecture actuelle (exmple li12ei2ee)
    if (c == b'l'):
        liste = []
        i +=1
        # Tant qu'on arrive pas à la fin de la liste, on recupere en rappelant cette fonction la prochaine valeur
        while (data[i:i+1] != b'e'):
            prochainElement,i = parseBencode(data, i)
            liste.append(prochainElement)
        return liste, i+1
    
    # Une chaine est stocké à l'indice de lecture actuelle (exemple 2:lala)
    if c in b'0123456789':
        indiceDeuxPoint = data.find(b':', i)
        taille = int(data[i:indiceDeuxPoint])
        indiceDebutChaine = indiceDeuxPoint +1
        return data[indiceDebutChaine:(indiceDebutChaine+taille)], indiceDebutChaine+ taille
    
# Fonction récursive qui encode un objet py donnée en paramètre en un bencode
# Logique inverse de la fonction parseBencode fait plus tot
def encodeBencode(data):
    if isinstance(data,int): 
        # .encode() donne la valeur en octet de la chaine construite
        return f"i{data}e".encode()
    
    # On encode une chaine
    if isinstance(data,bytes): 
        return f"{len(data)}:".encode() + data
    
    if isinstance(data, list): 
        # .join() donne la valeur en octet de la concatenation d'objet donnée
        return b'l'+b''.join(encodeBencode(x) for x in data) +b'e'
    
    if isinstance(data,dict):
        res = b''.join(encodeBencode(clé)+encodeBencode(valeur) for (clé,valeur) in sorted(data.items()))
        return b'd'+ res +b'e'