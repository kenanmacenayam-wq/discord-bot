import requests
from traitement import *
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, unquote
from googletrans import Translator
import time
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}
session = requests.Session()
session.headers.update(headers)
session.cookies.set("SOCS", "CAESNQgKEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjUxMDIyLjA2X3AwGgJmciACGgYIgODlxwY")
TIMEOUT = 10
url = "https://duckduckgo.com/html/"
translator = Translator()
lieu="Star-Wars-Galaxy-Rise/Star-Wars-Galaxy-Rise/"
def extract_links_from_ddg(html, max_links=10):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for a in soup.select("a.result__a"):
        href = a.get("href")
        if href:
            found.append(href)
    if len(found) < max_links:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            found.append(href)
    normalized = []
    for href in found:
        parsed = urlparse(href)
        if parsed.path.startswith("/l/") and parsed.query:
            qs = parse_qs(parsed.query)
            if "uddg" in qs:
                real = unquote(qs["uddg"][0])
                href = real
        if href.startswith("//"):
            href = "https:" + href
        if href.startswith("/"):
            href = urljoin("https://duckduckgo.com", href)
        normalized.append(href)
    cleaned = []
    seen = set()
    for link in normalized:
        if not link:
            continue
        if "duckduckgo.com" in link:
            continue
        if link in seen:
            continue
        seen.add(link)
        cleaned.append(link)
        if len(cleaned) >= max_links:
            break
    return cleaned
def lire_lien(url, partieLu='sommaire'):
    if "wikipedia.org/wiki/" in url:
        titre = url.split("/wiki/")[-1]
        titre = titre.split("?")[0]
        api_url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{titre}"
        if partieLu=='tout':
            api_url = f"https://fr.wikipedia.org/api/rest_v1/page/html/{titre}"
        r = requests.get(api_url,headers=headers,timeout=TIMEOUT)
        if r.status_code == 200:
            if partieLu=='tout':
                soup = BeautifulSoup(r.text, "html.parser")
                paragraphs = soup.find_all("p")
                texte = "\n\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
                return texte
            return r.json().get("extract")
    try:
        response = requests.get(url, headers=headers)
    except:
        time.sleep(0.5)
        try:
            response = requests.get(url, headers=headers)
        except:
            return "Introuvable !"
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphes = soup.find_all("p")
    texte = "\n".join(p.get_text() for p in paragraphes)
    if partieLu=='tout':
        return texte
    else:
        return str(".".join(texte[:500].split(".")[:-1]))+"."
def rechercher(query, partieLu='sommaire', enregistrer=False, chemin=''):
    params = {"q": query}
    response = session.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    liens = extract_links_from_ddg(html)
    toutTexte=[]
    for lien in liens:
        texte = lire_lien(lien, partieLu)
        if texte:
            toutTexte.append(texte)
    if toutTexte==[]:
        return (str(liens)+'\n\n\n'+str(html))
    if enregistrer:
        query=list(query)
        for i in ['?','/',':','*','"','<','>','|','\\']:
            while i in query:
                query.remove(i)
        query="".join(query)
        with open(str(lieu)+str(chemin)+str(query)+".txt", "w", encoding="utf-8") as f:
            f.write("\n\n\n".join(toutTexte))
    return toutTexte
def traduire(texte, l1="auto", l2="fr"):
    return translator.translate(texte, src=l1, dest=l2).text
def resumer(texte, traduit=False):
    tousMots=[]
    for i in list(texte):
        newTexte(i)
        tousMots.append(motpresent()[0])
    newTexte(" ".join([" ".join(tousMots[i]) for i in range(len(tousMots))]))
    listes=motpresent()
    nbMots=0
    for i in listes[1].values():
        if i>=4:
            nbMots+=1
    motsPartout=listes[0][:nbMots]
    for i in list(motsPartout):
        if len(i)<=3:
            motsPartout.remove(i)
    newTexte("\n\n".join(texte))
    nomP=nomPropre(motsPartout, commun=True)
    for j in range(len(texte)):
        texte[j]=list(texte[j])
        for i in range(len(texte[j])-1):
            if texte[j][i].islower() and texte[j][i+1].isupper():
                texte[j].insert(i+1,'\n')
        texte[j]="".join(texte[j])
    docPrincipal={}
    for k in list(texte):
        phrases=k.split('.')
        for j in ['!','?','.',':','—','<','>','«','»','\n']:
            phrases=[p for i in phrases for p in i.split(j)]
        for j in phrases:
            score=[0,0]
            for i in list(re.split(r"[^a-zA-ZÀ-ÿ]+", j)):
                if len(i)>3:
                    if i.lower() in motsPartout:
                        score[0]+=len(i)
                    score[1]+=len(i)
            if score[1]<30:
                continue
            if (score[0]/score[1])>=0.3:
                docPrincipal.update({str(j)+'.':score[0]/score[1]})
    val=[i for i in docPrincipal.values()]
    val.sort(reverse=True)
    principal=[""]*len(val)
    for i in docPrincipal.items():
        indice=val.index(i[1])
        while principal[indice]!="":
            indice+=1
        principal[indice]=i[0]
    textePur=["".join(re.split(r"[^a-zA-ZÀ-ÿ]+", i)).lower() for i in principal]
    for i in range(len(textePur)):
        if principal[i][0]==" ":
            principal[i]=list(principal[i])
            principal[i].remove(" ")
            principal[i]="".join(principal[i])
        if textePur[i] in textePur[:i]:
            principal[i]=""
    while "" in principal:
        principal.remove("")
    texteFinal=""
    if len(nomP)>=2:
        texteFinal=nomP[0]+" "+nomP[1]+"\n\n"
    texteFinal+="\n".join(principal[:10])
    if traduit:
        return traduire(texteFinal)
    else:
        return texteFinal
def ouvrir(nom, chemin=""):
    nom=list(nom)
    for i in ['?','/',':','*','"','<','>','|','\\']:
        while i in nom:
            nom.remove(i)
    nom="".join(nom)+'.txt'
    try:
        return open(str(lieu)+str(chemin)+str(nom), encoding="utf-8").read().split('\n\n\n')
    except:
        return "Fichier introuvable !"
def requete(query):
    texte=ouvrir(str(query), chemin="requetes/")
    if texte=="Fichier introuvable !":
        texte=rechercher(str(query),partieLu='tout', enregistrer=True, chemin='requetes/')
    return resumer(texte)
