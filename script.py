# ==========================================
# 1. IMPORTS
# ==========================================
import os
import json
import re
import requests
from datetime import datetime, timedelta, timezone
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 2. CONFIGURATION
# ==========================================
SPREADSHEET_ID = "1PJV98b4GkmHZsMF7uo9_eBUQG25JGaEdNJq0DvD9Z_4"
NOM_ONGLET = "Tempé plages"

google_secrets = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(google_secrets, scopes=scopes)
gc = gspread.authorize(creds)

# ==========================================
# 3. LISTE DES PLAGES
# ==========================================
DATA_PLAGES = [
    {
        "id_plage": 5, 
        "nom_plage": "PERROS-GUIREC", 
        "url_api": "https://rwg.meteofrance.com/internet2018client/2.0/forecast/gp?lat=48.818429&lon=-3.454232&id=2216851&instants=morning%2Cafternoon%2Cevening%2Cnight"
    }
]

headers_base = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ==========================================
# 4. RÉCUPÉRATION AUTOMATIQUE DU TOKEN
# ==========================================
print("Récupération d'un jeton d'accès Météo-France valide...")
token = None

try:
    # On visite la page de garde pour récupérer les cookies et le token de session
    session = requests.Session()
    page_accueil = session.get("https://meteofrance.com/", headers=headers_base, timeout=10)
    
    # Le token est généralement stocké dans le code source de la page ou généré dans un script d'init
    # On utilise une expression régulière pour chercher une chaîne qui ressemble à votre token (eyJhbGci...)
    match = re.search(r'ey[a-zA-Z0-9_-]+\.ey[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', page_accueil.text)
    
    if match:
        token = match.group(0)
        print("✓ Jeton d'accès intercepté avec succès.")
    else:
        # Solution de secours si le token n'est pas dans le HTML pur : on utilise le vôtre temporairement
        print("⚠️ Impossible d'intercepter le jeton dynamiquement, utilisation du jeton de secours...")
        token = "eyJhbGciOiJIUzI1NiIsImNsYXNzIjoiaW50ZXJuZXQiLCJ0eXAiOiJKV1QifQ.eyJpYXQiOjE3Nzk1NDIzNTMsImp0aSI6IjhjZmM3NzkxMmZkMzRmNmY0YTQxMTU0Nzktext.koME0ryxmBcgwwd4W-cpdhJTg5DXjNQiVc9p32zMWfk"

except Exception as e:
    print(f"Erreur lors de la recherche du token : {e}")
    token = "eyJhbGciOiJIUzI1NiIsImNsYXNzIjoiaW50ZXJuZXQiLCJ0eXAiOiJKV1QifQ.eyJpYXQiOjE3Nzk1NDIzNTMsImp0aSI6IjhjZmM3NzkxMmZkMzRmNmY0YTQxMTU0Nzktext.koME0ryxmBcgwwd4W-cpdhJTg5DXjNQiVc9p32zMWfk"

# ==========================================
# 5. INTERROGATION DE L'API AVEC LE TOKEN
# ==========================================
# On ajoute le badge d'autorisation dans nos requêtes de données
headers_api = headers_base.copy()
headers_api['Authorization'] = f"Bearer {token}"

results = []

for plage in DATA_PLAGES:
    print(f"Appel de l'API pour : {plage['nom_plage']}...")
    sst_c = "Non disponible"
    
    try:
        reponse = requests.get(plage["url_api"], headers=headers_api, timeout=10)
        
        if reponse.status_code == 200:
            data = reponse.json()
            if "properties" in data and "forecast" in data["properties"]:
                forecasts = data["properties"]["forecast"]
                for period in forecasts:
                    if "sea_water_temperature" in period and period["sea_water_temperature"] is not None:
                        sst_c = period["sea_water_temperature"]
                        break
                    elif "sea_temperature" in period and period["sea_temperature"] is not None:
                        sst_c = period["sea_temperature"]
                        break
        else:
            print(f"Erreur API {reponse.status_code} (Token potentiellement expiré ou refusé)")
            
    except Exception as e:
        print(f"Erreur technique : {e}")
        
    results.append({
        "ID_PLAGE": plage["id_plage"],
        "NOM_PLAGE": plage["nom_plage"],
        "SST_CELSIUS": sst_c
    })

result_df = pd.DataFrame(results)

# ==========================================
# 6. MISE À JOUR GOOGLE SHEETS
# ==========================================
print("Mise à jour du fichier Google Sheets...")
wb = gc.open_by_key(SPREADSHEET_ID)
try:
    output_sheet = wb.worksheet(NOM_ONGLET)
except gspread.exceptions.WorksheetNotFound:
    output_sheet = wb.add_worksheet(title=NOM_ONGLET, rows="1000", cols="5")

output_sheet.clear()

maintenant = datetime.now(timezone(timedelta(hours=2)))
date_formatee = maintenant.strftime("%d/%m/%Y à %H:%M:%S")
phrase_import = [f"Dernière mise à jour Météo France (Flux API Sécurisé) : le {date_formatee}"]

en_tetes = result_df.columns.values.tolist()
lignes_donnees = result_df.values.tolist()
toutes_les_lignes = [phrase_import] + [en_tetes] + lignes_donnees

output_sheet.update(values=toutes_les_lignes, range_name="A1")
print("✨ Google Sheet synchronisé avec succès !")
