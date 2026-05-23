# ==========================================
# 1. IMPORTS
# ==========================================
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 2. CONFIGURATION (À CONFIGURER AVEC VOS INFOS)
# ==========================================
# Mettez ici l'ID de votre classeur (présent dans l'URL de votre Google Sheet)
SPREADSHEET_ID = "1PJV98b4GkmHZsMF7uo9_eBUQG25JGaEdNJq0DvD9Z_4"
# Mettez ici le nom exact de l'onglet cible dans votre classeur
NOM_ONGLET = "Tempé plages"

# Récupération automatique de la clé d'accès Google stockée dans les secrets GitHub
google_secrets = json.loads(os.environ["GOOGLE_CREDENTIALS"])

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(google_secrets, scopes=scopes)
gc = gspread.authorize(creds)

# ==========================================
# 3. LISTE DES PLAGES AVEC LEURS URLS
# ==========================================
# Vous pourrez rajouter vos 84 autres plages à la suite dans ce tableau
DATA_PLAGES = [
    {"id_plage": 5, "nom_plage": "PERROS-GUIREC", "url": "https://meteofrance.com/meteo-plages/perros-guirec/2216851"}
]

# Un en-tête pour simuler un navigateur internet normal et éviter d'être bloqué par Météo France
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

results = []

# ==========================================
# 4. SCRAPING CHIRURGICAL SUR MÉTÉO FRANCE
# ==========================================
print("Début de la récupération des données sur Météo France...")

for plage in DATA_PLAGES:
    print(f"Extraction de la température pour : {plage['nom_plage']}...")
    sst_c = "Non disponible"
    
    try:
        # Téléchargement de la page web de la plage
        reponse = requests.get(plage["url"], headers=headers, timeout=15)
        
        if reponse.status_code == 200:
            # Analyse du code HTML de la page
            soup = BeautifulSoup(reponse.text, 'html.parser')
            
            # Application de votre sélecteur CSS précis
            element_mer = soup.select_one("#atmogramme_slider > div > ul > li.weather_details > div > ul > li.t_sea > strong")
            
            if element_mer:
                # Extraction du texte et nettoyage pour enlever le symbole "°"
                sst_c = element_mer.text.replace("°", "").strip()
            else:
                # Sécurité : si l'identifiant global bouge un jour, on teste juste la classe de fin
                secours = soup.select_one("li.t_sea > strong")
                if secours:
                    sst_c = secours.text.replace("°", "").strip()
        else:
            print(f"Erreur HTTP {reponse.status_code} pour la plage {plage['nom_plage']}")
            
    except Exception as e:
        print(f"Erreur technique lors du scraping de {plage['nom_plage']} : {e}")
        
    results.append({
        "ID_PLAGE": plage["id_plage"],
        "NOM_PLAGE": plage["nom_plage"],
        "SST_CELSIUS": sst_c
    })

# Création du tableau de données final
result_df = pd.DataFrame(results)

# ==========================================
# 5. ENVOI ET MISE EN FORME DANS GOOGLE SHEETS
# ==========================================
print(f"Connexion à Google Sheets (Classeur ID: {SPREADSHEET_ID})...")
wb = gc.open_by_key(SPREADSHEET_ID)

try:
    output_sheet = wb.worksheet(NOM_ONGLET)
except gspread.exceptions.WorksheetNotFound:
    print(f"L'onglet '{NOM_ONGLET}' n'existe pas. Création automatique...")
    output_sheet = wb.add_worksheet(title=NOM_ONGLET, rows="1000", cols="5")

# 1. Nettoyage complet de l'onglet avant l'écriture
output_sheet.clear()

# 2. Préparation de la phrase de date pour la cellule A1 (Heure de Paris GMT+2 en été)
maintenant = datetime.now(timezone(timedelta(hours=2)))
date_formatee = maintenant.strftime("%d/%m/%Y à %H:%M:%S")
phrase_import = [f"Dernière mise à jour Météo France : le {date_formatee}"]

# 3. Récupération des en-têtes et des lignes du tableau Python
en_tetes = result_df.columns.values.tolist()
lignes_donnees = result_df.values.tolist()

# 4. Assemblage final : Ligne 1 (Date), Ligne 2 (En-têtes), Lignes suivantes (Plages)
toutes_les_lignes = [phrase_import] + [en_tetes] + lignes_donnees

# 5. Envoi global vers Google Sheets
output_sheet.update(values=toutes_les_lignes, range_name="A1")

print(f"✨ L'onglet '{NOM_ONGLET}' a été mis à jour avec brio et l'heure est gravée en A1 !")
