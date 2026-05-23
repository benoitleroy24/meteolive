import os
import json
import time
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# CONFIGURATION GOOGLE SHEETS
# ==========================================
SPREADSHEET_ID = "1PJV98b4GkmHZsMF7uo9_eBUQG25JGaEdNJq0DvD9Z_4"
NOM_ONGLET = "Tempé plages"

google_secrets = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(google_secrets, scopes=scopes)
gc = gspread.authorize(creds)

# ==========================================
# LISTE DES PLAGES
# ==========================================
DATA_PLAGES = [
    {"id_plage": 5, "nom_plage": "PERROS-GUIREC", "url": "https://meteofrance.com/meteo-plages/perros-guirec/2216851"}
]

results = []

# ==========================================
# CHARGEMENT AVEC UN VRAI NAVIGATEUR (PLAYWRIGHT)
# ==========================================
print("Lancement du navigateur invisible...")
with sync_playwright() as p:
    # On lance un Chrome invisible
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    for plage in DATA_PLAGES:
        print(f"Navigation vers la page de : {plage['nom_plage']}...")
        sst_c = "Non disponible"
        
        try:
            # Ouverture de la page Météo-France
            page.goto(plage["url"], timeout=30000)
            
            # On attend que l'élément généré par le JavaScript soit présent à l'écran
            selecteur = "li.t_sea > strong"
            page.wait_for_selector(selecteur, timeout=10000)
            
            # Extraction du texte de la balise
            texte_temperature = page.locator(selecteur).inner_text()
            if texte_temperature:
                sst_c = texte_temperature.replace("°", "").strip()
                print(f"✓ Température trouvée : {sst_c}°C")
                
        except Exception as e:
            print(f"⚠️ Impossible de charger la température pour {plage['nom_plage']} : {e}")
            
        results.append({
            "ID_PLAGE": plage["id_plage"],
            "NOM_PLAGE": plage["nom_plage"],
            "SST_CELSIUS": sst_c
        })
        
    browser.close()

result_df = pd.DataFrame(results)

# ==========================================
# ENVOI VERS GOOGLE SHEETS
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
phrase_import = [f"Dernière mise à jour Météo France (Navigateur Réel) : le {date_formatee}"]

en_tetes = result_df.columns.values.tolist()
lignes_donnees = result_df.values.tolist()
toutes_les_lignes = [phrase_import] + [en_tetes] + lignes_donnees

output_sheet.update(values=toutes_les_lignes, range_name="A1")
print("✨ Google Sheet synchronisé avec succès !")
