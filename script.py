import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# CONFIGURATION GOOGLE SHEETS
# ==========================================
SPREADSHEET_ID = "1PJV98b4GkmHZsMF7uo9_eBUQG25JGaEdNJq0DvD9Z_4"
NOM_ONGLET = "Tempé plages"

# Connexion Google (via votre secret GitHub)
google_secrets = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(google_secrets, scopes=scopes)
gc = gspread.authorize(creds)

# ==========================================
# LISTE DES PLAGES AVEC LEURS URLS MÉTÉO FRANCE
# ==========================================
# Il suffira de lister vos plages avec leur lien direct comme ceci :
LISTE_PLAGES = [
    {"id_plage": 5, "nom_plage": "PERROS-GUIREC", "url": "https://meteofrance.com/meteo-plages/perros-guirec/2216851"},
    # {"id_plage": 39, "nom_plage": "AGDE", "url": "L'URL DE LA PLAGE D'AGDE"},
    # Vous pourrez lister vos 85 plages ici...
]

results = []

# Un en-tête pour faire croire au site que le script est un navigateur normal (évite d'être bloqué)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("Début de la récupération sur Météo France...")

for plage in LISTE_PLAGES:
    print(f"Scraping de {plage['nom_plage']}...")
    sst_c = "Non disponible"
    
    try:
        # Téléchargement du code de la page de la plage
        reponse = requests.get(plage["url"], headers=headers, timeout=10)
        
        if reponse.status_code == 200:
            # On demande à BeautifulSoup d'analyser le code HTML
            soup = BeautifulSoup(reponse.text, 'html.parser')
            
            # --- ICI ON CHERCHE LE BOUT DE CODE ---
            # Météo France met souvent ces infos dans des balises spécifiques (classes CSS)
            # Par exemple, si la température est dans une zone qui contient "T° eau" :
            element_eau = soup.find(text=lambda t: t and "T° eau" in t)
            
            if element_eau:
                # On extrait juste le nombre (ex: de "T° eau :14°" on isole "14")
                sst_c = element_eau.replace("T° eau :", "").replace("°", "").strip()
    except Exception as e:
        print(f"Erreur pour {plage['nom_plage']} : {e}")
        
    results.append({
        "ID_PLAGE": plage["id_plage"],
        "NOM_PLAGE": plage["nom_plage"],
        "SST_CELSIUS": sst_c
    })

# Transformation en tableau
result_df = pd.DataFrame(results)

# ==========================================
# ENVOI VERS GOOGLE SHEETS
# ==========================================
wb = gc.open_by_key(SPREADSHEET_ID)
try:
    output_sheet = wb.worksheet(NOM_ONGLET)
except gspread.exceptions.WorksheetNotFound:
    output_sheet = wb.add_worksheet(title=NOM_ONGLET, rows="1000", cols="5")

output_sheet.clear()

# Préparation de la ligne de date
maintenant = datetime.now(timezone(timedelta(hours=2)))
date_formatee = maintenant.strftime("%d/%m/%Y à %H:%M:%S")
phrase_import = [f"Dernière mise à jour Météo France : le {date_formatee}"]

en_tetes = result_df.columns.values.tolist()
lignes_donnees = result_df.values.tolist()

# Envoi du bloc complet
output_sheet.update(values=[phrase_import] + [en_tetes] + lignes_donnees, range_name="A1")
print("✨ Google Sheet mis à jour avec les données de Météo France !")
