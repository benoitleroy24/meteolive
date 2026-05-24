# ==========================================
# 1. IMPORTS
# ==========================================
import os
import json
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 2. CONFIGURATION GOOGLE SHEETS
# ==========================================
SPREADSHEET_ID = "1PJV98b4GkmHZsMF7uo9_eBUQG25JGaEdNJq0DvD9Z_4"
NOM_ONGLET = "Données Météo France"

google_secrets = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(google_secrets, scopes=scopes)
gc = gspread.authorize(creds)

# ==========================================
# 3. BASE DE DONNÉES DES PLAGES CIBLÉES
# ==========================================
# Le script va utiliser l'ordre exact de ce tableau pour travailler
DATA_PLAGES = [
    {"id_plage": 1, "nom_plage": "AGDE", "url": "https://meteofrance.com/meteo-plages/agde/3400351"},
    {"id_plage": 2, "nom_plage": "AJACCIO", "url": "https://meteofrance.com/meteo-plages/ajaccio/2000451"},
    {"id_plage": 3, "nom_plage": "ALÉRIA", "url": "https://meteofrance.com/meteo-plages/aleria/2000951"},
    {"id_plage": 4, "nom_plage": "ARCACHON", "url": "https://meteofrance.com/meteo-plages/arcachon/3300951"},
    {"id_plage": 5, "nom_plage": "ARGELÈS-SUR-MER", "url": "https://meteofrance.com/meteo-plages/argeles-sur-mer/6600851"},
    {"id_plage": 6, "nom_plage": "BANDOL", "url": "https://meteofrance.com/meteo-plages/bandol/8300951"},
    {"id_plage": 7, "nom_plage": "BANYULS-SUR-MER", "url": "https://meteofrance.com/meteo-plages/banyuls-sur-mer/6601651"},
    {"id_plage": 8, "nom_plage": "BASTIA", "url": "https://meteofrance.com/meteo-plages/bastia/2003351"},
    {"id_plage": 9, "nom_plage": "BELLE-ÎLE-EN-MER", "url": "https://meteofrance.com/meteo-plages/belle-ile-en-mer/5615251"},
    {"id_plage": 10, "nom_plage": "BERCK-SUR-MER", "url": "https://meteofrance.com/meteo-plages/berck-sur-mer/6210851"},
    {"id_plage": 11, "nom_plage": "BIARRITZ", "url": "https://meteofrance.com/meteo-plages/biarritz-anglet/6412251"},
    {"id_plage": 12, "nom_plage": "BOULOGNE-SUR-MER", "url": "https://meteofrance.com/meteo-plages/boulogne-sur-mer/6216051"},
    {"id_plage": 13, "nom_plage": "BRAY-DUNES", "url": "https://meteofrance.com/previsions-meteo-france/bray-dunes/59123"},
    {"id_plage": 14, "nom_plage": "BREST", "url": "https://meteofrance.com/meteo-plages/brest/2901951"},
    {"id_plage": 15, "nom_plage": "CABOURG", "url": "https://meteofrance.com/meteo-plages/cabourg/1411751"},
    {"id_plage": 16, "nom_plage": "CALVI", "url": "https://meteofrance.com/meteo-plages/calvi/2005051"},
    {"id_plage": 17, "nom_plage": "CANET-EN-ROUSSILLON", "url": "https://meteofrance.com/meteo-plages/canet-en-roussillon/6603751"},
    {"id_plage": 18, "nom_plage": "CANNES", "url": "https://meteofrance.com/meteo-plages/cannes/0602951"},
    {"id_plage": 19, "nom_plage": "CASSIS", "url": "https://meteofrance.com/meteo-plages/cassis/1302251"},
    {"id_plage": 20, "nom_plage": "CAYEUX-SUR-MER", "url": "https://meteofrance.com/meteo-plages/cayeux-sur-mer/8018251"},
    {"id_plage": 21, "nom_plage": "CHÂTELAILLON-PLAGE", "url": "https://meteofrance.com/meteo-plages/chatelaillon-plage/1709451"},
    {"id_plage": 22, "nom_plage": "CHERBOURG", "url": "https://meteofrance.com/meteo-plages/cherbourg/5012951"},
    {"id_plage": 23, "nom_plage": "COLLIOURE", "url": "https://meteofrance.com/meteo-plages/collioure/6605351"},
    {"id_plage": 24, "nom_plage": "CONCARNEAU", "url": "https://meteofrance.com/meteo-plages/concarneau/2903951"},
    {"id_plage": 25, "nom_plage": "CROZON", "url": "https://meteofrance.com/meteo-plages/crozon-morgat/2904251"},
    {"id_plage": 26, "nom_plage": "DEAUVILLE", "url": "https://meteofrance.com/meteo-plages/deauville/1422051"},
    {"id_plage": 27, "nom_plage": "DIEPPE", "url": "https://meteofrance.com/meteo-plages/dieppe/7621751"},
    {"id_plage": 28, "nom_plage": "DUNKERQUE", "url": "https://meteofrance.com/previsions-meteo-france/dunkerque/59140"},
    {"id_plage": 72, "nom_plage": "FÉCAMP", "url": "https://meteofrance.com/meteo-plages/fecamp/7625911"},
    {"id_plage": 29, "nom_plage": "FORT-MAHON PLAGE", "url": "https://meteofrance.com/meteo-plages/fort-mahon/8033351"},
    {"id_plage": 30, "nom_plage": "FRéJUS", "url": "https://meteofrance.com/meteo-plages/frejus/8306151"},
    {"id_plage": 31, "nom_plage": "GRANVILLE", "url": "https://meteofrance.com/meteo-plages/granville/5021851"},
    {"id_plage": 32, "nom_plage": "GRUISSAN", "url": "https://meteofrance.com/meteo-plages/gruissan/1117051"},
    {"id_plage": 33, "nom_plage": "HENDAYE", "url": "https://meteofrance.com/meteo-plages/hendaye/6426051"},
    {"id_plage": 34, "nom_plage": "HYÈRES", "url": "https://meteofrance.com/meteo-plages/hyeres-les-palmiers/8306951"},
    {"id_plage": 35, "nom_plage": "ILE D'OLÉRON", "url": "https://meteofrance.com/previsions-meteo-france/saint-pierre-d-oleron/17310"},
    {"id_plage": 36, "nom_plage": "L'ÎLE-ROUSSE", "url": "https://meteofrance.com/meteo-plages/l-ile-rousse/2013451"},
    {"id_plage": 37, "nom_plage": "LA BAULE", "url": "https://meteofrance.com/meteo-plages/la-baule-escoublac/4405551"},
    {"id_plage": 38, "nom_plage": "LA CIOTAT", "url": "https://meteofrance.com/meteo-plages/la-ciotat/1302851"},
    {"id_plage": 39, "nom_plage": "LA ROCHELLE", "url": "https://meteofrance.com/meteo-plages/la-rochelle/1730051"},
    {"id_plage": 40, "nom_plage": "LACANAU", "url": "https://meteofrance.com/meteo-plages/lacanau-spot-surf/3321451"},
    {"id_plage": 41, "nom_plage": "LE LAVANDOU", "url": "https://meteofrance.com/meteo-plages/le-lavandou/8307051"},
    {"id_plage": 42, "nom_plage": "LE MONT-SAINT-MICHEL", "url": "https://meteofrance.com/meteo-plages/le-mont-saint-michel/5035351"},
    {"id_plage": 43, "nom_plage": "LE TOUQUET", "url": "https://meteofrance.com/meteo-plages/le-touquet-paris/6282651"},
    {"id_plage": 44, "nom_plage": "LES SABLES-D'OLONNE", "url": "https://meteofrance.com/meteo-plages/les-sables-d-olonne/8519451"},
    {"id_plage": 45, "nom_plage": "LEUCATE", "url": "https://meteofrance.com/meteo-plages/leucate/1120251"},
    {"id_plage": 46, "nom_plage": "MARSEILLAN", "url": "https://meteofrance.com/meteo-plages/marseillan/3415051"},
    {"id_plage": 47, "nom_plage": "MARSEILLE", "url": "https://meteofrance.com/meteo-plages/marseille/1305551"},
    {"id_plage": 48, "nom_plage": "MARTIGUES", "url": "https://meteofrance.com/meteo-plages/martigues/1305651"},
    {"id_plage": 49, "nom_plage": "MENTON", "url": "https://meteofrance.com/meteo-plages/menton/0608351"},
    {"id_plage": 50, "nom_plage": "MERLIMONT", "url": "https://meteofrance.com/meteo-plages/merlimont/6257151"},
    {"id_plage": 51, "nom_plage": "MIMIZAN", "url": "https://meteofrance.com/meteo-plages/mimizan/4018451"},
    {"id_plage": 73, "nom_plage": "NAUJAC-SUR-MER", "url": "https://meteofrance.com/meteo-plages/naujac-sur-mer/3330011"},
    {"id_plage": 52, "nom_plage": "NICE", "url": "https://meteofrance.com/meteo-plages/nice/0608851"},
    {"id_plage": 53, "nom_plage": "NOIRMOUTIER", "url": "https://meteofrance.com/meteo-plages/noirmoutier-en-l-ile/8516351"},
    {"id_plage": 54, "nom_plage": "PALAVAS-LES-FLOTS", "url": "https://meteofrance.com/meteo-plages/palavas-les-flots/3419251"},
    {"id_plage": 55, "nom_plage": "PERROS-GUIREC", "url": "https://meteofrance.com/meteo-plages/perros-guirec/2216851"},
    {"id_plage": 56, "nom_plage": "PLOUDALMÉZEAU", "url": "https://meteofrance.com/previsions-meteo-france/ploudalmezeau/29830"},
    {"id_plage": 57, "nom_plage": "PORT-DE-BOUC", "url": "https://meteofrance.com/meteo-plages/port-de-bouc/1307751"},
    {"id_plage": 58, "nom_plage": "PORTO-VECCHIO", "url": "https://meteofrance.com/meteo-plages/porto-vecchio/2024751"},
    {"id_plage": 59, "nom_plage": "ROQUEBRUNE-CAP-MARTIN", "url": "https://meteofrance.com/meteo-plages/roquebrune-cap-martin/0610451"},
    {"id_plage": 60, "nom_plage": "ROYAN", "url": "https://meteofrance.com/meteo-plages/royan/1730651"},
    {"id_plage": 74, "nom_plage": "SAINT-BRIEUC", "url": "https://meteofrance.com/meteo-plages/saint-brieuc/2227811"},
    {"id_plage": 61, "nom_plage": "SAINT-JEAN-DE-LUZ", "url": "https://meteofrance.com/meteo-plages/saint-jean-de-luz/6448351"},
    {"id_plage": 62, "nom_plage": "SAINT-MALO", "url": "https://meteofrance.com/meteo-plages/saint-malo/3528851"},
    {"id_plage": 63, "nom_plage": "SAINT-TROPEZ", "url": "https://meteofrance.com/meteo-plages/saint-tropez/8311951"},
    {"id_plage": 64, "nom_plage": "SAINTE-MAXIME", "url": "https://meteofrance.com/meteo-plages/sainte-maxime/8311551"},
    {"id_plage": 65, "nom_plage": "SAINTES-MARIES-DE-LA-MER", "url": "https://meteofrance.com/meteo-plages/saintes-maries-de-la-mer/1309651"},
    {"id_plage": 66, "nom_plage": "SÈTE", "url": "https://meteofrance.com/meteo-plages/sete/3430151"},
    {"id_plage": 67, "nom_plage": "STELLA PLAGE", "url": "https://meteofrance.com/meteo-plages/stella/6226151"},
    {"id_plage": 68, "nom_plage": "TOULON", "url": "https://meteofrance.com/meteo-plages/toulon/8313751"},
    {"id_plage": 69, "nom_plage": "VILLEFRANCHE-SUR-MER", "url": "https://meteofrance.com/meteo-plages/villefranche-sur-mer/0615951"},
    {"id_plage": 70, "nom_plage": "WIMEREUX", "url": "https://meteofrance.com/meteo-plages/wimereux/6289351"},
    {"id_plage": 71, "nom_plage": "WISSANT", "url": "https://meteofrance.com/meteo-plages/wissant/6289951"}
]

total_plages = len(DATA_PLAGES)

# ==========================================
# 4. LECTURE DU COMPTEUR E1 DANS LE TABLEUR
# ==========================================
print("Connexion à Google Sheets...")
wb = gc.open_by_key(SPREADSHEET_ID)
output_sheet = wb.worksheet(NOM_ONGLET)

# On récupère TOUTES les valeurs de la feuille pour travailler en mémoire
valeurs_grille = output_sheet.get_all_values()

# Lecture de la case E1 (Index 0, Colonne 4). Si vide ou non numérique, on commence à l'index 0
try:
    prochain_index_a_traiter = int(valeurs_grille[0][4])
except Exception:
    prochain_index_a_traiter = 0

# Sécurité : Si le pointeur dépasse la taille de la liste, on boucle à 0
if prochain_index_a_traiter >= total_plages:
    print("Tour complet validé. Réinitialisation du pointeur à 0.")
    prochain_index_a_traiter = 0

# On détermine la tranche de plages à traiter (ex: 0 à 9, puis 10 à 19...)
indices_du_bloc = list(range(prochain_index_a_traiter, min(prochain_index_a_traiter + 10, total_plages)))
print(f"Pointeur E1 actuel : {prochain_index_a_traiter}. Plages analysées ce tour-ci : {indices_du_bloc}")

# ==========================================
# 5. SCRAPING PAR NAVIGATEUR POUR LE BLOC STRICT
# ==========================================
print("Ouverture du navigateur invisible...")
maintenant = datetime.now(timezone(timedelta(hours=2)))
date_complete = maintenant.strftime("%d/%m/%Y à %H:%M:%S")

donnees_mises_a_jour = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    for idx in indices_du_bloc:
        plage = DATA_PLAGES[idx]
        print(f"-> Extraction : {plage['nom_plage']}...")
        
        sst_val = "Indisponible"
        uv_val = "0"
        
        try:
            page.goto(plage["url"], timeout=25000)
            
            if "previsions-meteo-france" not in plage["url"]:
                # 1. Température de l'eau
                sel_sst = "li.t_sea > strong"
                if page.locator(sel_sst).count() > 0:
                    sst_val = page.locator(sel_sst).inner_text().replace("°", "").strip()
                
                # 2. Indice UV
                sel_uv = "#atmogramme_slider > div > ul > li.weather_details > div > ul > li.indice_uv > strong"
                if page.locator(sel_uv).count() > 0:
                    uv_val = page.locator(sel_uv).inner_text().strip()
            else:
                sst_val = "Page Classique"
                uv_val = "Page Classique"
                
        except Exception:
            date_complete += " (Échec)"
            
        # On mémorise les résultats associés au NOM de la plage
        donnees_mises_a_jour[plage["nom_plage"]] = {
            "sst": sst_val,
            "uv": uv_val,
            "date": date_complete
        }

    browser.close()

# ==========================================
# 6. MISE À JOUR CIBLÉE DES CELLULES DANS GOOGLE SHEETS
# ==========================================
print("Application des nouvelles valeurs dans la grille globale...")

# On parcourt les lignes physiques de la feuille (la ligne 1=Titre, ligne 2=En-têtes, les données commencent ligne 3)
for row_idx, row_data in enumerate(valeurs_grille[2:], start=3):
    if len(row_data) > 1:
        nom_plage_sheet = row_data[1].strip() # Colonne B (Nom de la plage)
        
        # Si cette plage fait partie de celles qu'on vient de scrapper, on injecte les valeurs
        if nom_plage_sheet in donnees_mises_a_jour:
            infos = donnees_mises_a_jour[nom_plage_sheet]
            
            # Mise à jour des cellules spécifiques de la ligne
            output_sheet.update_cell(row_idx, 3, infos["sst"])   # Colonne C : Température
            output_sheet.update_cell(row_idx, 4, infos["uv"])    # Colonne D : Indice UV
            output_sheet.update_cell(row_idx, 5, infos["date"])  # Colonne E : Date contrôle

# Calcul du prochain pointeur pour la session de dans 5 minutes
prochain_pointeur = prochain_index_a_traiter + 10
if prochain_pointeur >= total_plages:
    prochain_pointeur = 0

# Sauvegarde finale du bandeau supérieur et du précieux pointeur en cellule E1
output_sheet.update_cell(1, 1, f"Suivi glissant Météo France - Dernier passage bloc : le {date_complete}")
output_sheet.update_cell(1, 5, str(prochain_pointeur))

print(f"✨ Bloc synchronisé. Prochain départ enregistré en E1 : Ligne {prochain_pointeur}")
