import discord
from discord.ext import commands
from discord.ui import Select, View, Button, Modal, TextInput#Ajout récent pour les 3 derniers
from discord import app_commands, emoji
from discord.app_commands import Choice
from typing import Optional
import requests, time
#from traitement import *
#from recherche import *
import threading
import os
import json
import re
import random
import asyncio
import requests
import io
try:
    from PIL import Image
    PILActive = True
except:
    PILActive = False
    print("❌ PIL n'est pas installé. Les images ne pourront pas être redimensionnées.")

# Initialisation du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

lieu="Star-Wars-Galaxy-Rise/Star-Wars-Galaxy-Rise/"

# Variables globales
global SELECTION, CHOIX_POSSIBLES, CHOIX_TEXTE
SELECTION, CHOIX_POSSIBLES, CHOIX_TEXTE = "", [], ""

# Charger le fichier de lore
with open(str(lieu)+"lore.json", "r", encoding="utf-8") as f:
    lore_data = json.load(f)
#Charger des donné externe comme la liste des bannis : Farfadet
DATA_FILE = str(lieu)+"info.json"

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)


if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}
    user_data["Bannis"] = {"ListeBannis": ";"}
    save_data()


def fiche_creer(id):
    try:
        with open(str(lieu)+"fiches/" + str(id) + ".json", "r") as f:
            config = json.load(f)
        return True
    except:
        return False


def get_image_from_url(url, largeur=400):
    if PILActive:
        response = requests.get(url)
        if response.status_code != 200:
            print("❌ Impossible de récupérer l'image.")
            return 200
        image = Image.open(io.BytesIO(response.content))
        ratio = largeur / image.width
        nouvelle_hauteur = int(image.height * ratio)
        image_redim = image.resize((largeur, nouvelle_hauteur), Image.LANCZOS)
        buffer = io.BytesIO()
        image_redim.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(fp=buffer, filename="image_redim.png")
        print("✅ Image redimensionnée.")
        return file
    return 200
def rang_Suivant(rang):
    for i in user_data["Rangs"]:
        if rang in user_data["Rangs"][i]:
            index = user_data["Rangs"][i].index(rang)
            if index < len(user_data["Rangs"][i]) - 1:
                return user_data["Rangs"][i][index + 1]
            else:
                return "Rang maximum atteint"
    return "Aucun"


# Compétences liées aux rôles Discord : Farfadet
roles_competences = user_data["roles_competences"]
rolesPossibles = [user_data["Rangs"][i][0] for i in user_data["Rangs"]]
factionsPossibles = [
    "Ordre Jedi", "Ordre Sith", "Contrebandier"#,"Nouvelle République", "Empire Ressuscité"
]
tousRoles = [user_data["Rangs"][i] for i in user_data["Rangs"]]


#Ajout récent
class ChoixView(View):
    def __init__(self, options, color=None):
        super().__init__()
        self.value = None
        for label in options:
            if color and label == options[-1]:
                bouton = Button(label=label, style=discord.ButtonStyle.danger)
            else:
                bouton = Button(label=label, style=discord.ButtonStyle.primary)
            async def callback(inter, label=label):
                self.value = label
                await inter.response.defer(thinking=False, ephemeral=True)
                self.stop()
            bouton.callback = callback
            self.add_item(bouton)
#Ajout récent
class NombreModal(Modal):
    def __init__(self, question):
        super().__init__(title=str(question))
        self.nombre = TextInput(label="Entre ta réponse", placeholder="Ex: 42", required=True)
        self.add_item(self.nombre)
        self.value = None
    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.value = int(self.nombre.value)
            await interaction.response.defer(thinking=False, ephemeral=True)
            self.stop()
        except ValueError:
            await interaction.response.send_message("⚠️ Ce n'est pas un nombre valide", ephemeral=True)

# Menu déroulant
class RoleSelect(Select):

    def __init__(self):
        global SELECTION, CHOIX_POSSIBLES, CHOIX_TEXTE
        options = [
            discord.SelectOption(label=str(i),
                                 description="Choisi " + str(i),
                                 emoji="⚫") for i in CHOIX_POSSIBLES
        ]  #🟢🔵🔴⚪⚫
        super().__init__(placeholder=str(CHOIX_TEXTE),
                         min_values=1,
                         max_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        SELECTION = self.values[0]
        if CHOIX_POSSIBLES == rolesPossibles:
            role = discord.utils.get(interaction.guild.roles, name=SELECTION)
            if not role:
                await interaction.response.send_message(
                    f"❌ Le rôle `{SELECTION}` n'existe pas.", ephemeral=True)
                return
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ Tu as reçu le rôle " +
                                                    str(SELECTION) + "!",
                                                    ephemeral=True)


class RoleView(View):

    def __init__(self):
        super().__init__(timeout=None)  # Pas de timeout
        self.add_item(RoleSelect())



class AccepterView(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__()  #timeout=30 veut dire 30 secondes pour répondre
        self.author = author
        self.value = None
        self.add_item(discord.ui.Button(label="Wiki", url=user_data["Wiki"]))
    @discord.ui.button(label="✅ Je l'ai lu et accepté", style=discord.ButtonStyle.success)
    async def oui(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "oui"
        await interaction.response.defer(thinking=False, ephemeral=True)
        self.stop()

    @discord.ui.button(label="❌ Annulé", style=discord.ButtonStyle.danger)
    async def non(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "non"
        await interaction.response.defer(thinking=False, ephemeral=True)
        self.stop()

class OuiNonView(discord.ui.View):
    def __init__(self, author: discord.User):
        super().__init__()  #timeout=30 veut dire 30 secondes pour répondre
        self.author = author
        self.value = None
    @discord.ui.button(label="✅ Oui", style=discord.ButtonStyle.success)
    async def oui(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "oui"
        await interaction.response.defer(thinking=False, ephemeral=True)
        self.stop()

    @discord.ui.button(label="❌ Non", style=discord.ButtonStyle.danger)
    async def non(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "non"
        await interaction.response.defer(thinking=False, ephemeral=True)
        self.stop()

# Démarrage
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")
    try:  # Permet de mettre les slashs : Farfadet
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} commande(s) slash synchronisée(s).")
    except Exception as e:
        print(f"Erreur de sync : {e}")


#Messages et réactions relou : Farfadet
@bot.event
async def on_message(message):
    mots_interdits = [
        "fdp", "connard", "con", "salope", "pute", "enculé",
        "enfoiré", "enfoire", "ntm", "nique", "niquer", "bite", "baiser",
        "baise", "tg", "gueule", "pd", "putain", "merde", "salop", "connasse", "encule", "enculer", "enculee", "enculeur", "enculeuse", "enculeurs", "enculeuses", "enculés", "enculées", "niqueur", "niqueurs", "niqueuse", "niqueuses", "niqués", "niquées", "pute", "putes", "putain", "putains", "putes", "putains", "salopes", "salop", "salops", "salopes", "salopards", "saloparde", "salopardes", "salopard"
    ]
    nom = message.author.name
    pseudo = message.author.display_name
    contenu = message.content
    bannis = user_data.get("Bannis")["ListeBannis"].split(";")
    if isinstance(message.channel, discord.TextChannel):
        nom_salon = message.channel.name
    else:
        nom_salon = "DM"
    if nom in bannis and nom_salon.startswith("ticket-")not in nom_salon:
        await message.delete()
        await message.author.send(
            str(pseudo) + ", tu n'as pas le droit de parler dans le serveur " +
            str(message.guild.name) +
            " car tu en as été banni.\nDemande à un admin pour être débannis.")
        return
    try:
        if message.channel.category is not None:
            nom_categorie = message.channel.category.name
        else:
            nom_categorie = "Aucune catégorie"
    except AttributeError:
        nom_categorie = "DM"
    if nom_categorie in ["Discussion hors-RP", "Projet"]:
        mots = re.split(r"[^a-zA-ZÀ-ÿ]+", contenu)
        mots = [mot for mot in mots if mot]
        for mot in mots_interdits:
            if mot in mots:
                await message.delete()
    elif contenu!="":
        reponse, personne, supprSace, pActive = "", "", False, False
        if contenu[0] == '[' and ']' in contenu:
            for i in range(len(contenu)):
                if supprSace:
                    if contenu[i] == " ":
                        continue
                    else:
                        supprSace = False
                if pActive and contenu[i] != ']':
                    personne += contenu[i]
                if contenu[i] == '[':
                    if personne.lower() == "narration":
                        reponse += "*"
                    personne = ""
                    pActive = True
                    reponse += "\n**"
                elif contenu[i] == ']':
                    pActive = False
                    reponse += " :** "
                    if personne.lower() == "narration":
                        reponse += "*"
                        supprSace = True
                else:
                    reponse += contenu[i]
            if personne.lower() == "narration":
                reponse += "*"
            await message.delete()
            await message.channel.send(reponse)
    await bot.process_commands(message)


#Ban un joueur : Farfadet
@bot.tree.command(name="mute", description="(admin)Empêche un joueur de parler")
async def ban(interaction: discord.Interaction, nom: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Tu n'as pas la permission d'utiliser cette commande.",
            ephemeral=True)
        return
    try:
        user_data["Bannis"] = {
            "ListeBannis":
            str(user_data.get("Bannis")["ListeBannis"]) + str(nom) + str(";")
        }
        save_data()
        await interaction.response.send_message(str(nom) + " a été banni !")
    except:
        await interaction.response.send_message("Aucun joueur n'a été banni !",
                                                ephemeral=True)


#Déban un joueur : Farfadet
@bot.tree.command(name="demute", description="(admin)Annule le mute d'un joueur")
async def deban(interaction: discord.Interaction, nom: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Tu n'as pas la permission d'utiliser cette commande.",
            ephemeral=True)
        return
    try:
        debanActif = False
        nom = str(nom)
        l = (user_data.get("Bannis")["ListeBannis"]).split(";")
        listeBannis = ";"
        for i in l:
            if i != nom and i != "":
                listeBannis += str(i) + str(";")
            elif i == nom:
                debanActif = True
        user_data["Bannis"] = {"ListeBannis": listeBannis}
        save_data()
        if not debanActif:
            await interaction.response.send_message(str(nom) +
                                                    " n'est pas banni.",
                                                    ephemeral=True)
            return
        await interaction.response.send_message(str(nom) + " a été débanni !")
    except:
        await interaction.response.send_message(
            "Une erreur s'est produite.\nAucun joueur n'a été débanni !",
            ephemeral=True)



#Choisir sa fiche : Farfadet
@bot.tree.command(name="fiche", description="Enregistre ta fiche")
@app_commands.describe(faction="Ta classe préférée")
@app_commands.choices(
    faction=[Choice(name=nom, value=nom) for nom in factionsPossibles])
async def fiche(interaction: discord.Interaction, nom: str, espece: str,
                alignement: str, faction: app_commands.Choice[str],
                grade: str):
    nom_utilisateur = str(interaction.user.id)
    if fiche_creer(nom_utilisateur):
        await interaction.response.send_message(
            "❌ Tu as déjà créé une fiche. Demande à un admin pour la modifier.",
            ephemeral=True)
        return
    view = AccepterView(author=interaction.user)
    await interaction.response.send_message("Avant de créer votre fiche personnage et commencer à jouer, vous devez lire et accepter les règles du RP. Elle sont disponible en faisant `/wiki` ou en cliquant sur le boutton que voici.", view=view, ephemeral=True)
    await view.wait()
    await interaction.delete_original_response()
    if view.value == "non":
        await interaction.followup.send("N'oubliez pas d'aller lire le wiki en faisant `/wiki`. ❌", ephemeral=True)
        return
    if view.value != "oui":
        return
    data = {
        "Nom": nom,
        "Espèce": espece,
        "Alignement": alignement,
        "Faction": faction.value,
        "Grade": grade
    }
    os.makedirs("fiches", exist_ok=True)
    with open(f"fiches/{nom_utilisateur}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    role=discord.utils.get(interaction.guild.roles, name=user_data["Rangs"][faction.value][0])
    await interaction.user.add_roles(role)
    await interaction.followup.send(
        "✅ Fiche enregistrée ! Tape `/voirfiche` pour l'afficher.\nTu es désormais "+str(role)+" !",
        ephemeral=True)


#Modifier la fiche d'un joueur : Farfadet
@bot.tree.command(name="editfiche", description="(admin)Modifier une fiche")
@app_commands.describe(faction="Ta classe préférée")
@app_commands.choices(
    faction=[Choice(name=nom, value=nom) for nom in factionsPossibles])
async def editfiche(interaction: discord.Interaction,
                    joueur: discord.Member,
                    nom: Optional[str] = None,
                    espece: Optional[str] = None,
                    alignement: Optional[str] = None,
                    faction: Optional[app_commands.Choice[str]] = None,
                    grade: Optional[str] = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Tu n'as pas la permission d'utiliser cette commande.",
            ephemeral=True)
        return
    user_id = str(joueur.id)
    pseudo = joueur.display_name
    member = joueur.name
    user_role = joueur.roles
    if not fiche_creer(user_id):
        await interaction.response.send_message(str(pseudo) +
                                                " n'a pas créé sa fiche.",
                                                ephemeral=True)
        return
    try:
        with open(str(lieu)+"fiches/" + str(user_id) + ".json", "r") as f:
            fiche = json.load(f)
        try:
            faction = faction.value
            rang = [role.name for role in user_role]
            if user_data["Rangs"][fiche["Faction"]][0]in rang:
                roleSuppr = discord.utils.get(interaction.guild.roles, name=user_data["Rangs"][fiche["Faction"]][0])
                await joueur.remove_roles(roleSuppr)
            dejaRole = False
            for i in user_data["Rangs"][str(faction)]:
                if i in rang:
                    dejaRole = True
            if not dejaRole:
                roleAjout = discord.utils.get(interaction.guild.roles, name=user_data["Rangs"][str(faction)][0])
                await joueur.add_roles(roleAjout)
        except:
            faction = None
        parametres = (("Nom", nom), ("Espèce", espece), ("Alignement", alignement),
                      ("Faction", faction), ("Grade", grade))
        for i in range(len(parametres)):
            if parametres[i][1] != None:
                fiche[parametres[i][0]] = parametres[i][1]
        with open(str(lieu)+"fiches/" + str(user_id) + ".json", "w") as f:
            json.dump(fiche, f, ensure_ascii=False, indent=2)
        await interaction.response.send_message(
            "✅ La fiche de " + str(pseudo) +
            " a été modifiée. Tape `/voirfiche` pour l'afficher",
            ephemeral=True)
    except Exception  as e:
        print(e)
        await interaction.response.send_message("❌ Une erreur c'est produite.",
                                                ephemeral=True)
    return


#Lancer un dé : Farfadet
@bot.tree.command(name="roll", description="lance un dé aléatoire")
async def roll(interaction: discord.Interaction, num: Optional[int] = 20):
    await interaction.response.send_message("🎲 Le dé affiche ")
    for i in range(16):
        affiche = str(random.randint(1, int(num)))
        await interaction.edit_original_response(content="🎲 Le dé affiche **" +
                                                 affiche + "**")
        await asyncio.sleep(0.005 * i**2)
    await interaction.edit_original_response(
        content="🎲 Tu as fais **" + (" " * (len(str(num)) - len(affiche))) +
        affiche + "** sur un dé de **" + str(num) + "** !")


# Afficher la fiche personnage : Farfadet
@bot.tree.command(name="voirfiche", description="Affiche la fiche")
async def voirfiche(interaction: discord.Interaction,
                    nom: Optional[discord.Member] = None):
    if nom == None:
        user_id = str(interaction.user.id)
        pseudo = interaction.user.display_name
        member = interaction.user
        user_role = member.roles
    else:
        user_id = str(nom.id)
        pseudo = nom.display_name
        member = nom.name
        user_role = nom.roles
    try:
        with open(str(lieu)+"fiches/"+str(user_id)+".json", "r", encoding="utf-8") as f:
            fiche = json.load(f)

        embed = discord.Embed(title="📖 Fiche de personnage", color=0x3498db)
        for champ, valeur in fiche.items():
            if champ != "Compétences":
                embed.add_field(name=champ, value=valeur, inline=False)
        #user_roles = [role.name for role in user_role]
        try:
            competences_du_joueur = fiche["Compétences"].split(", ")
            if competences_du_joueur:
                embed.add_field(name="🧠 Compétences",
                                value=", ".join(competences_du_joueur),
                                inline=False)  #🎓
        except:
            pass
        rang = [role.name for role in user_role if role.name in user_data["Rangs"][fiche["Faction"]]]
        if rang:
            rang=rang[0]
        else:
            rang="Aucun"
        embed.add_field(name="Rang",value=rang, inline=True)#🔑
        embed.add_field(name="Rang suivant",value=rang_Suivant(rang), inline=True)#🔑
        faction=str(fiche["Faction"])
        with open(str(lieu)+"Images/LienImages.json", "r") as f:
            liens = json.load(f)
        embed.set_image(url=liens["Faction"][faction])
        embed.set_footer(text=f"JediRiseBot – {pseudo}")  #ctx.author.name
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except FileNotFoundError:
        if nom == None:
            await interaction.response.send_message(
                "❌ Aucune fiche trouvée. Utilise `/fiche` pour en créer une.",
                ephemeral=True)
        else:
            await interaction.response.send_message("❌ " + str(pseudo) +
                                                    " n'a pas créé de fiche.",
                                                    ephemeral=True)



#modifier la compétence d'un joueur : Farfadet
@bot.tree.command(name="competence",
                  description="(admin) Ajoute une compétence pour un joueur")
@app_commands.describe(role="Choisis une compétence")
async def competence(interaction: discord.Interaction, nom: discord.Member,
                     role: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Tu n'as pas la permission d'utiliser cette commande.",
            ephemeral=True)
        return
    competence = role
    user_id = str(nom.id)
    pseudo = nom.display_name
    member = nom.name
    user_role = nom.roles
    fiche_path = str(lieu)+"fiches/"+str(user_id)+".json"
    reponse = ""
    if os.path.exists(fiche_path):
        with open(fiche_path, "r", encoding="utf-8") as f:
            fiche = json.load(f)
        if competence in fiche["Compétences"].split(", "):
            await interaction.response.send_message(
                "❌ La compétence " + str(competence) +
                " est déjà présente sur la fiche de " + str(pseudo) + " !",
                ephemeral=True)
            return
        try:
            fiche["Compétences"] = fiche["Compétences"] + ", " + str(
                competence)
        except:
            fiche["Compétences"] = str(competence)
        with open(fiche_path, "w", encoding="utf-8") as f:
            json.dump(fiche, f, ensure_ascii=False, indent=2)
        reponse += "🧠 La compétence " + str(
            competence) + " a été ajoutées à la fiche de " + str(member) + " !"
        try:
            roleAjout = discord.utils.get(interaction.guild.roles,
                                          name=competence)
            await nom.add_roles(roleAjout)
            reponse += "\nLe rôle " + str(competence) + " a été ajouté."
        except:
            reponse += "\n❌ Le rôle " + str(competence) + " n'existe pas."
    else:
        reponse += "ℹ️" + str(pseudo) + " doit d'abord créer sa fiche."
    await interaction.response.send_message(reponse, ephemeral=True)


@competence.autocomplete("role")
async def autocomplete_roles(interaction: discord.Interaction, current: str):
    suggestions = [
        app_commands.Choice(name=nom, value=nom) for nom in roles_competences
        if current.lower() in nom.lower()
    ]
    return suggestions[:25]


#Lien vers le wiki : Farfadet
class LienButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="Wiki", url=user_data["Wiki"]))

@bot.tree.command(name="wiki", description="Lire le wiki du serveur")
async def wiki(interaction: discord.Interaction):
    await interaction.response.send_message("Il est fortement conseillé de lire le wiki pour connaître les règles du RP et d'autres information utile au RP.", view=LienButton(), ephemeral=True)


#Rang suivant : Farfadet
@bot.tree.command(name="rang_suivant", description="(admin)Donne le rang suivant")
async def rang_suivant(interaction: discord.Interaction, membre: discord.Member):
    user_id = str(membre.id)
    pseudo = membre.display_name
    member = membre.name
    user_role = membre.roles
    try:
        with open(str(lieu)+"fiches/"+str(user_id)+".json", "r", encoding="utf-8") as f:
            fiche = json.load(f)
    except FileNotFoundError:
        await interaction.response.send_message("❌ " + str(pseudo) + " n'a pas créé de fiche.", ephemeral=True)
        return
    rang = [role.name for role in user_role if role.name in user_data["Rangs"][fiche["Faction"]]]
    if rang:
        rang=rang[0]
    else:
        rang="Aucun"
    rangSuivant=rang_Suivant(rang)
    if rangSuivant=="Rang maximum atteint":
        await interaction.response.send_message("❌ "+str(pseudo)+" a atteint le rang maximum.", ephemeral=True)
        return
    if rang=="Aucun":
        await interaction.response.send_message("❌ "+str(pseudo)+" n'a pas de rang.", ephemeral=True)
        return
    view = OuiNonView(author=interaction.user)
    await interaction.response.send_message("Êtes-vous sûr de vouloir faire passer "+str(pseudo)+" du rang **"+str(rang)+"** au rang **"+str(rangSuivant)+ "** ?", view=view, ephemeral=True)
    await view.wait()
    await interaction.delete_original_response()
    if view.value == "non":
        await interaction.followup.send("❌ Commande annulé !", ephemeral=True)
    if view.value != "oui":
        return
    roleSuppr = discord.utils.get(interaction.guild.roles, name=rang)
    roleAjout = discord.utils.get(interaction.guild.roles, name=rangSuivant)
    if not roleAjout:
        await interaction.followup.send(
            f"❌ Le rôle `{rangSuivant}` n'existe pas.", ephemeral=True)
        return
    await membre.remove_roles(roleSuppr)
    await membre.add_roles(roleAjout)
    await interaction.followup.send("✅ "+str(pseudo)+" est passé du rang "+str(rang)+" au rang "+str(rangSuivant)+" !", ephemeral=True)


#Créer un salon : Farfadet
@bot.tree.command(name="ticket",
                  description="Permet de poser une question au staff")
async def creer_salon(interaction: discord.Interaction):
    guild = interaction.guild
    membre = interaction.user
    salon = interaction.channel
    question="**Pourquoi voulez-vous créer un ticket ?**"
    choix=["Obtenir des informations", "Modification de sa fiche", "Problème technique", "Autre"]
    ticket = False
    if salon.name.startswith("ticket-"):
        choix.append("Fermer le ticket")
        ticket = True
    view = ChoixView(choix, color=ticket)
    await interaction.response.send_message(question, view=view, ephemeral=True)
    await view.wait()
    if view.value != "Fermer le ticket":
        num = user_data["Ticket"]
        user_data["Ticket"] = num + 1
        save_data()
        nom = "ticket-" + str(num) + "-" + str(view.value)
        # On définit les permissions :
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False),  # Personne n'y a accès (sauf les admins)
            membre: discord.PermissionOverwrite(
                view_channel=True)  # Seulement ce membre peut voir
        }
        salon = await guild.create_text_channel(name=nom, overwrites=overwrites)
        await interaction.followup.send(
            f"🎟️ Votre ticket a été créé : {salon.mention}", ephemeral=True)
    else:
        await interaction.followup.send(
            f"🗑️ Le ticket **{salon.name}** a été fermé.", ephemeral=True)
        await salon.delete()


#Début des ajouts
class QuizView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)  # pas de limite de temps
        self.user_id = user_id
    @discord.ui.button(label="Question suivante ➡️", style=discord.ButtonStyle.primary, emoji=None)
    async def suivant(self, interaction: discord.Interaction, button: discord.ui.Button):
        await poser_question(interaction, self)


async def poser_question(interaction: discord.Interaction, viewSuivant: QuizView):
    user_id = str(interaction.user.id)
    with open(str(lieu)+"quiz.json", "r") as f:
        quiz = json.load(f)
    question = random.choice([champs for champs, valeur in quiz["question"].items()])
    try:
        valeur=quiz["score"][user_id]
    except:
        quiz["score"][user_id] = [0,0]
    if quiz["question"][question][0] == "choix":
        labels = quiz["question"][question][2:]
        view = ChoixView(labels)
        await interaction.response.send_message("**"+str(question)+"**", view=view, ephemeral=True)
        await view.wait()
        if view.value:
            if view.value == quiz["question"][question][1]:
                quiz["score"][user_id][0] += 1
                await interaction.edit_original_response(content="**"+str(question)+"** *"+str(view.value)+"*\nBonne réponse !", view=viewSuivant)
            else:
                quiz["score"][user_id][1] += 1
                await interaction.edit_original_response(content="**"+str(question)+"** *"+str(view.value)+"*\nMauvaise réponse !\nLa bonne réponse était "+str(quiz["question"][question][1]), view=viewSuivant)
        else:
            await interaction.edit_original_response(content="Temps écouler !", view=None)
    elif quiz["question"][question][0] == "nombre":
        valeur=NombreModal(question)
        await interaction.response.send_modal(valeur)
        await valeur.wait()
        if valeur.value:
            if valeur.value == int(quiz["question"][question][2]):
                quiz["score"][user_id][0] += 1
                await interaction.followup.send("**"+str(question)+"** *"+str(valeur.value)+"*\nBonne réponse !", view=viewSuivant, ephemeral=True)
            elif int(quiz["question"][question][1]) <= valeur.value and valeur.value <= int(quiz["question"][question][3]):
                 await interaction.followup.send("**"+str(question)+"** *"+str(valeur.value)+"*\nPresque !\nLa bonne réponse était "+str(quiz["question"][question][2]), view=viewSuivant, ephemeral=True)
            else:
                quiz["score"][user_id][1] += 1
                await interaction.followup.send("**"+str(question)+"\n** *"+str(valeur.value)+"*Mauvaise réponse !\nLa bonne réponse était "+str(quiz["question"][question][2]), view=viewSuivant, ephemeral=True)
    with open(str(lieu)+"quiz.json", "w") as f:
        json.dump(quiz, f, indent=4)


@bot.tree.command(name="quiz", description="Défi tes amis dans un quiz !")
async def quiz(interaction: discord.Interaction):
    view = QuizView(interaction.user.id)
    await poser_question(interaction, view)


@bot.tree.command(name="stats", description="Regarde qui est meilleur au quiz !")
async def stats(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("Cette commande doit être utilisée sur un serveur.", ephemeral=True)
        return
    with open(str(lieu)+"quiz.json", "r") as f:
        quiz = json.load(f)
    embed = discord.Embed(title="📖 Stats", color=0x3498db)
    embed.set_footer(text=f"JediRiseBot – {interaction.user.display_name}")
    tableau = []
    for champ, valeur in quiz["score"].items():
        member = guild.get_member(champ)
        if member is None:
            try:
                member = await guild.fetch_member(champ)
            except discord.NotFound:
                continue
            except discord.Forbidden:
                continue
        pourcentage = round(valeur[0]/(valeur[0]+valeur[1])*100,2)
        score=str(valeur[0])+" ✅  "+str(valeur[1])+" ❌"+"  ("+str(pourcentage)+"%)"
        tableau.append([pourcentage, member.display_name, score])
    tableau.sort(reverse=True)
    classement = 1
    emojis = ["🥇", "🥈","🥉"]
    for valeurs in tableau:
        if classement<=3:
            emoji=emojis[classement-1]
        else:
            emoji=str(classement)+"."
        embed.add_field(name=emoji+" "+valeurs[1], value=valeurs[2], inline=False)
        classement+=1
    await interaction.response.send_message(embed=embed, ephemeral=True)



#Code initial de Sapin6508
# Commande test
@bot.command()
async def test(ctx):
    await ctx.send("✅ Bot opérationnel.")

"""
# Commande mute
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, membre: discord.Member, *, raison="Aucune raison fournie"):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        await ctx.send(
            "❌ Le rôle `Muted` n'existe pas. Crée-le d'abord et configure ses permissions."
        )
        return

    await membre.add_roles(role, reason=raison)
    await ctx.send(f"🔇 {membre.mention} a été mute. Raison : {raison}")
"""
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Le bot est en ligne !"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
keep_alive()


def auto_ping(url):
    def ping():
        while True:
            try:
                requests.get(url)
                print("Ping réussi ✅")
            except:
                print("Ping raté ❌")
            time.sleep(300)  # 5 minutes
    t = threading.Thread(target=ping)
    t.start()
url="https://discord-bot-38wq.onrender.com"
auto_ping(url)
# Lancer le bot
bot.run(os.getenv("DISCORD_TOKEN"))
#Created by Farfadet, inspired by Sapin6508, and improved by ChatGPT
