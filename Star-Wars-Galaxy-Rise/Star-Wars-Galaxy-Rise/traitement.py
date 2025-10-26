import configparser
import json
import re
global fichier, fichierL, fichierD, fichierM
fichier, fichierL, fichierD, fichierM="","",[""],[""]
def newTexte(texte, genre="texte"):
    global fichier, fichierL, fichierD, fichierM
    if genre=="fichier":
        fichier=(open(str(texte), encoding="utf-8").read())
    else:
        fichier=texte
    fichierL=fichier.lower()
    fichierD=fichier.split('\n')
    fichierM=re.split(r"[^a-zA-ZÀ-ÿ]+", fichier)
def chercher(texte, case=False, classe="tout", orthographe=False):
    if classe=="tout":
        if str(texte.__class__)=="<class 'str'>" or str(texte.__class__)=="<class 'int'>":
            if case or orthographe:
                texte=[str(texte)]
            else:
                texte=[str(texte).lower()]
        else:
            if case or orthographe:
                texte=[str(mot) for mot in texte]
            else:
                texte=[str(mot).lower() for mot in texte]
        everyMots=[]
        if orthographe:
            score={}
            for mot in texte:
                score.update({mot:0})
        i=0
        for ligne in fichierD:
            for mot in texte:
                if orthographe:
                    if mot.lower() in ligne.lower():
                        for m in re.split(r"[^a-zA-ZÀ-ÿ]+", ligne):
                            if m.lower()==mot.lower():
                                if m==mot:
                                    score[mot]+=1
                                else:
                                    score[mot]-=1
                else:
                    if(not(case)and mot in ligne.lower())or(case and mot in ligne):
                        everyMots.append(i)
            i+=1
        if orthographe:
            return [mot[0] for mot in score.items() if mot[1]>=1]
        return everyMots
    elif classe=="nombre":
        listeNombre=[]
        lettre=0
        while lettre<len(fichier):
            nombre=""
            while fichier[lettre] in ["0","1","2","3","4","5","6","7","8","9"," "]:
                if fichier[lettre]!=" ":
                    nombre+=fichier[lettre]
                lettre+=1
            if nombre!="":
                listeNombre.append(int(nombre))
            lettre+=1
        return listeNombre
def lire(debut, fin=-1, autour=0):
    if str(debut.__class__) == "<class 'int'>":
        if fin==-1:
            fin=debut+1
        return [fichierD[i] for i in range(debut, fin)]
    liste=[i+j for j in range(-autour, autour+1) for i in debut]
    return [fichierD[i] for i in range(len(fichierD)) if i in liste]
def motpresent():
    dico={}
    for mot in fichierM:
        if mot.lower() in dico.keys():
            dico[str(mot.lower())]+=1
        else:
            dico.update({str(mot.lower()):1})
    trie=[]
    for couple in dico.items():
        i=0
        while (i<len(trie) and dico[trie[i]]>=couple[1]):
            i+=1
        trie.insert(i, couple[0])
    return  trie, dico
def formater(forme, inclu=False):
    if str(forme.__class__) == "<class 'str'>":
        forme=[forme]
    nb=0
    nbMax=len(forme)
    renvoitTotal=[]
    renvoit=[]
    i=0
    last=""
    while i < len(fichier):
        j=0
        while j<len(forme[nb])and fichier[i+j]==(forme[nb])[j]:
            j+=1
        if j==len(forme[nb]):
            if nb>0:
                renvoit.append(last)
            nb+=1
            if nb==nbMax:
                renvoitTotal.append(list(renvoit))
                renvoit=[]
                nb=0
            last=""
            i+=j
        last+=fichier[i]
        i+=1
    return renvoitTotal
def affiche(texte, saut=False):
    for i in texte:
        print(i)
        if saut:
            print()
def nomPropre(texte=None, commun=False):
    f=list(fichierD)
    for j in ['!','?','.',':','—','<','>','«','»']:
        f=[k for i in f for k in i.split(j)]
    f=[j.lower() for j in [k for i in f for k in [h for h in re.split(r"[^a-zA-ZÀ-ÿ]+", i) if h!=''][1:]] if len(j)>1 and j[0].isupper() and j[1].islower()]
    if texte==None:
        if commun:
            return chercher(f,orthographe=True)
        return f
    elif str(texte.__class__) == "<class 'str'>":
        if commun:
            texte=list(texte.lower())
            texte[0]=texte[0].upper()
            texte="".join(texte)
            print(texte)
            return chercher(texte,orthographe=True)==[texte]
        return texte.lower() in f
    else:
        texte=list(texte)
        for i in range(len(texte)):
            texte[i]=list(texte[i].lower())
            texte[i][0]=texte[i][0].upper()
            texte[i]="".join(texte[i])
        l=[i for i in texte if i.lower() in f]
        if commun:
            return chercher(l,orthographe=True)
        return l
