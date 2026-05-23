# ==========================================
# 1. IMPORTS
# ==========================================
import os
import json
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
# 3. LISTE DES PLAGES AVEC LEURS COORDONNÉES ET ID
# ==========================================
# Pour vos 84 autres plages, il suffira de dupliquer la ligne en remplaçant 
# la lat, la lon et l'id par ceux trouvés dans les requêtes réseau correspondantes.
DATA_PLAGES = [
    {
        "id_plage": 5, 
        "nom_plage": "PERROS-GUIREC", 
        "url_api": "https://rwg.meteofrance.com/internet2018client/2.0/forecast/gp?lat=48.818429&lon=-3.454232&id=2216851&instants=morning%2Cafternoon%2Cevening%2Cnight"
    }
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

results = []

# ==========================================
# 4. LECTURE DIRECTE DES DONNÉES DE L'API
# ==========================================
print("Interrogation de la véritable API Météo France...")

for plage in DATA_PLAGES:
    print(f"Récupération des données pour : {plage['nom_plage']}...")
    sst_c = "Non disponible"
    
    try:
        reponse = requests.get(plage["url_api"], headers=headers, timeout=10)
        
        if reponse.status_code == 200:
            data = reponse.json()
            
            # Météo France organise les données par échéances ("properties" -> "forecast")
            # On va chercher la première prévision disponible dans la liste pour y trouver la température de la mer
            if "properties" in data and "forecast" in data["properties"]:
                forecasts = data["properties"]["forecast"]
                
                # On parcourt les prévisions (souvent matin, après-midi...) jusqu'à trouver la clé 'sea_water_temperature' ou 'sea_temperature'
                for period in forecasts:
                    if "sea_water_temperature" in period and period["sea_water_temperature"] is not None:
                        sst_c = period["sea_water_temperature"]
                        break
                    elif "sea_temperature" in period and period["sea_temperature"] is not None:
                        sst_c = period["sea_temperature"]
                        break
        else:
            print(f"Météo France a répondu avec une erreur {reponse.status_code}")
            
    except Exception as e:
        print(f"Erreur technique : {e}")
        
    results.append({
        "ID_PLAGE": plage["id_plage"],
        "NOM_PLAGE": plage["nom_plage"],
        "SST_CELSIUS": sst_c
    })

result_df = pd.DataFrame(results)

# ==========================================
# 5. ENVOI ET MISE EN FORME DANS GOOGLE SHEETS
# ==========================================
print("Connexion à Google Sheets...")
wb = gc.open_by_key(SPREADSHEET_ID)

try:
    output_sheet = wb.worksheet(NOM_ONGLET)
except gspread.exceptions.WorksheetNotFound:
    output_sheet = wb.add_worksheet(title=NOM_ONGLET, rows="1000", cols="5")

output_sheet.clear()

maintenant = datetime.now(timezone(timedelta(hours=2)))
date_formatee = maintenant.strftime("%d/%m/%Y à %H:%M:%S")
phrase_import = [f"Dernière mise à jour Météo France (Flux Direct) : le {date_formatee}"]

en_tetes = result_df.columns.values.tolist()
lignes_donnees = result_df.values.tolist()
toutes_les_lignes = [phrase_import] + [en_tetes] + lignes_donnees

output_sheet.update(values=toutes_les_lignes, range_name="A1")
print("✨ Google Sheet mis à jour avec succès !")
