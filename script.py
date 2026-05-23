# ==========================================
# 1. IMPORTS
# ==========================================
import os
import json
from datetime import datetime, timedelta, timezone
import urllib.request
import numpy as np
import pandas as pd
import xarray as xr
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
# 3. CALCUL DYNAMIQUE DE LA DATE ET DE L'URL
# ==========================================
hier = datetime.now() - timedelta(days=1)
annee = hier.strftime("%Y")
jour_annee = hier.strftime("%j")
date_hms = hier.strftime("%Y%m%d")

base_url = f"https://data-cersat.ifremer.fr/data/sea-surface-temperature/odyssea/l4/glob/nrt/data/v2.1/{annee}/{jour_annee}/"
nom_fichier = f"{date_hms}000000-IFR-L4_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v02.1-fv01.0.nc"

URL_FICHIER = base_url + nom_fichier
LOCAL_NC = "sst_du_jour.nc"

# ==========================================
# 4. BASE DE DONNÉES DES 85 PLAGES
# ==========================================
DATA_PLAGES = [
    {"id_plage": 39, "nom_plage": "AGDE", "situation": "GOLFE DU LION", "lat": 43.30829, "lon": 3.476137},
    {"id_plage": 63, "nom_plage": "AJACCIO", "situation": "CÔTE D'AZUR ET CORSE", "lat": 41.917596, "lon": 8.737081},
    {"id_plage": 68, "nom_plage": "ALÉRIA", "situation": "CÔTE D'AZUR ET CORSE", "lat": 42.104742, "lon": 9.513496},
    {"id_plage": 80, "nom_plage": "AMBLETEUSE", "situation": "MANCHE", "lat": 50.811132, "lon": 1.597608},
    {"id_plage": 27, "nom_plage": "ARCACHON", "situation": "ATLANTIQUE", "lat": 44.651977, "lon": -1.178351},
    {"id_plage": 38, "nom_plage": "ARGELÈS-SUR-MER", "situation": "GOLFE DU LION", "lat": 42.545045, "lon": 3.030049},
    {"id_plage": 86, "nom_plage": "BANDOL", "situation": "CÔTE D'AZUR", "lat": 43.13457, "lon": 5.745524},
    {"id_plage": 7, "nom_plage": "BANYULS-SUR-MER", "situation": "GOLFE DU LION", "lat": 42.483013, "lon": 3.128801},
    {"id_plage": 64, "nom_plage": "BASTIA", "situation": "CÔTE D'AZUR ET CORSE", "lat": 42.696796, "lon": 9.449417},
    {"id_plage": 29, "nom_plage": "BELLE-ÎLE-EN-MER", "situation": "ATLANTIQUE", "lat": 47.339447, "lon": -3.181136},
    {"id_plage": 11, "nom_plage": "BERCK", "situation": "MANCHE", "lat": 50.410155, "lon": 1.567566},
    {"id_plage": 75, "nom_plage": "BERCK-SUR-MER", "situation": "MANCHE", "lat": 50.410079, "lon": 1.560336},
    {"id_plage": 23, "nom_plage": "BIARRITZ", "situation": "ATLANTIQUE", "lat": 43.482938, "lon": -1.558587},
    {"id_plage": 65, "nom_plage": "BORMES-LES-MIMOSAS", "situation": "CÔTE D'AZUR ET CORSE", "lat": 43.152188, "lon": 6.338519},
    {"id_plage": 6, "nom_plage": "BOULOGNE-SUR-MER", "situation": "MANCHE", "lat": 50.725415, "lon": 1.609996},
    {"id_plage": 71, "nom_plage": "BOULOGNE-SUR-MER", "situation": "MANCHE", "lat": 50.732054, "lon": 1.593741},
    {"id_plage": 79, "nom_plage": "BRAY-DUNES", "situation": "MANCHE", "lat": 51.080885, "lon": 2.518915},
    {"id_plage": 18, "nom_plage": "BREST", "situation": "MANCHE", "lat": 48.382171, "lon": -4.490333},
    {"id_plage": 3, "nom_plage": "CABOURG", "situation": "MANCHE", "lat": 49.288038, "lon": -0.117059},
    {"id_plage": 67, "nom_plage": "CALVI", "situation": "CÔTE D'AZUR ET CORSE", "lat": 42.567996, "lon": 8.756498},
    {"id_plage": 51, "nom_plage": "CANET-EN-ROUSSILLON", "situation": "GOLFE DU LION", "lat": 42.706366, "lon": 3.01445},
    {"id_plage": 56, "nom_plage": "CANNES", "situation": "CÔTE D'AZUR ET CORSE", "lat": 43.552383, "lon": 7.017526},
    {"id_plage": 54, "nom_plage": "CASSIS", "situation": "GOLFE DU LION", "lat": 43.215009, "lon": 5.536561},
    {"id_plage": 7, "nom_plage": "CAYEUX-SUR-MER", "situation": "MANCHE", "lat": 50.179206, "lon": 1.494718},
    {"id_plage": 30, "nom_plage": "CHÂTELAILLON-PLAGE", "situation": "ATLANTIQUE", "lat": 46.069529, "lon": -1.085762},
    {"id_plage": 13, "nom_plage": "CHERBOURG", "situation": "MANCHE", "lat": 49.642544, "lon": -1.620755},
    {"id_plage": 42, "nom_plage": "COLLIOURE", "situation": "GOLFE DU LION", "lat": 42.526835, "lon": 3.085593},
    {"id_plage": 24, "nom_plage": "CONCARNEAU", "situation": "ATLANTIQUE", "lat": 47.872428, "lon": -3.919914},
    {"id_plage": 19, "nom_plage": "CROZON", "situation": "ATLANTIQUE", "lat": 48.24635, "lon": -4.495029},
    {"id_plage": 16, "nom_plage": "DEAUVILLE", "situation": "MANCHE", "lat": 49.359921, "lon": 0.065822},
    {"id_plage": 2, "nom_plage": "DIEPPE", "situation": "MANCHE", "lat": 49.923088, "lon": 1.076194},
    {"id_plage": 1, "nom_plage": "DUNKERQUE", "situation": "MANCHE", "lat": 51.033935, "lon": 2.375012},
    {"id_plage": 12, "nom_plage": "FÉCAMP", "situation": "MANCHE", "lat": 49.760794, "lon": 0.364416},
    {"id_plage": 15, "nom_plage": "FORT-MAHON PLAGE", "situation": "MANCHE", "lat": 50.341175, "lon": 1.569026},
    {"id_plage": 84, "nom_plage": "FRéJUS", "situation": "CÔTE D'AZUR", "lat": 43.4228, "lon": 6.75607},
    {"id_plage": 9, "nom_plage": "GRANVILLE", "situation": "MANCHE", "lat": 48.837562, "lon": -1.599473},
    {"id_plage": 76, "nom_plage": "GRAVELINES", "situation": "MANCHE", "lat": 51.008737, "lon": 2.113196},
    {"id_plage": 33, "nom_plage": "GROIX", "situation": "ATLANTIQUE", "lat": 47.63829, "lon": -3.463913},
    {"id_plage": 48, "nom_plage": "GRUISSAN", "situation": "GOLFE DU LION", "lat": 43.106779, "lon": 3.087587},
    {"id_plage": 28, "nom_plage": "HENDAYE", "situation": "ATLANTIQUE", "lat": 43.35951, "lon": -1.765901},
    {"id_plage": 46, "nom_plage": "HYÈRES", "situation": "GOLFE DU LION", "lat": 43.097428, "lon": 6.150139},
    {"id_plage": 26, "nom_plage": "ILE D'OLÉRON", "situation": "ATLANTIQUE", "lat": 45.960464, "lon": -1.274991},
    {"id_plage": 58, "nom_plage": "L'ÎLE-ROUSSE", "situation": "CÔTE D'AZUR ET CORSE", "lat": 42.636248, "lon": 8.936835},
    {"id_plage": 25, "nom_plage": "LA BAULE", "situation": "ATLANTIQUE", "lat": 47.290808, "lon": -2.39219},
    {"id_plage": 35, "nom_plage": "LA CIOTAT", "situation": "GOLFE DU LION", "lat": 43.173493, "lon": 5.606893},
    {"id_plage": 5, "nom_plage": "LA ROCHELLE", "situation": "ATLANTIQUE", "lat": 46.160624, "lon": -1.155147},
    {"id_plage": 31, "nom_plage": "LACANAU", "situation": "ATLANTIQUE", "lat": 44.986024, "lon": -1.144186},
    {"id_plage": 8, "nom_plage": "LE HAVRE", "situation": "MANCHE", "lat": 49.494021, "lon": 0.106985},
    {"id_plage": 55, "nom_plage": "LE LAVANDOU", "situation": "CÔTE D'AZUR ET CORSE", "lat": 43.138063, "lon": 6.37039},
    {"id_plage": 64, "nom_plage": "LE MONT-SAINT-MICHEL", "situation": "MANCHE", "lat": 48.636031, "lon": -1.510954},
    {"id_plage": 78, "nom_plage": "LE TOUQUET", "situation": "MANCHE", "lat": 50.524697, "lon": 1.579117},
    {"id_plage": 21, "nom_plage": "LES SABLES-D'OLONNE", "situation": "ATLANTIQUE", "lat": 46.499463, "lon": -1.793856},
    {"id_plage": 43, "nom_plage": "LEUCATE", "situation": "GOLFE DU LION", "lat": 42.911149, "lon": 3.022312},
    {"id_plage": 73, "nom_plage": "MALO-LES-BAINS", "situation": "MANCHE", "lat": 51.050351, "lon": 2.385019},
    {"id_plage": 52, "nom_plage": "MARSEILLAN", "situation": "GOLFE DU LION", "lat": 43.357165, "lon": 3.529121},
    {"id_plage": 40, "nom_plage": "MARSEILLE", "situation": "GOLFE DU LION", "lat": 43.298798, "lon": 5.372173},
    {"id_plage": 85, "nom_plage": "MARTIGUES", "situation": "CÔTE D'AZUR", "lat": 43.33137, "lon": 5.063155},
    {"id_plage": 57, "nom_plage": "MENTON", "situation": "CÔTE D'AZUR ET CORSE", "lat": 43.774656, "lon": 7.496342},
    {"id_plage": 77, "nom_plage": "MERLIMONT", "situation": "MANCHE", "lat": 50.461574, "lon": 1.571547},
    {"id_plage": 32, "nom_plage": "MIMIZAN", "situation": "ATLANTIQUE", "lat": 44.199128, "lon": -1.228253},
    {"id_plage": 22, "nom_plage": "NAUJAC-SUR-MER", "situation": "ATLANTIQUE", "lat": 45.267514, "lon": -1.095543},
    {"id_plage": 61, "nom_plage": "NICE", "situation": "CÔTE D'AZUR ET CORSE", "lat": 43.709374, "lon": 7.260368},
    {"id_plage": 34, "nom_plage": "NOIRMOUTIER", "situation": "ATLANTIQUE", "lat": 46.988718, "lon": -2.26831},
    {"id_plage": 49, "nom_plage": "PALAVAS-LES-FLOTS", "situation": "GOLFE DU LION", "lat": 43.529247, "lon": 3.931246},
    {"id_plage": 5, "nom_plage": "PERROS-GUIREC", "situation": "MANCHE", "lat": 48.815141, "lon": -3.445935},
    {"id_plage": 81, "nom_plage": "PETIT-FORT-PHILIPPE", "situation": "MANCHE", "lat": 51.008737, "lon": 2.113196},
    {"id_plage": 10, "nom_plage": "PLOUDALMÉZEAU", "situation": "MANCHE", "lat": 48.567037, "lon": -4.690028},
    {"id_plage": 3, "nom_plage": "PORQUEROLLES", "situation": "CÔTE D'AZUR", "lat": 43.0026, "lon": 6.20445},
    {"id_plage": 59, "nom_plage": "PORT-DE-BOUC", "situation": "GOLFE DU LION", "lat": 43.405454, "lon": 4.985045},
    {"id_plage": 9, "nom_plage": "PORTO-VECCHIO", "situation": "CÔTE D'AZUR ET CORSE", "lat": 41.591248, "lon": 9.285675},
    {"id_plage": 62, "nom_plage": "ROQUEBRUNE-CAP-MARTIN", "situation": "CÔTE D'AZUR ET CORSE", "lat": 43.757827, "lon": 7.493574},
    {"id_plage": 36, "nom_plage": "ROYAN", "situation": "ATLANTIQUE", "lat": 45.622915, "lon": -1.042258},
    {"id_plage": 17, "nom_plage": "SAINT BRIEUC", "situation": "MANCHE", "lat": 48.522264, "lon": -2.727268},
    {"id_plage": 37, "nom_plage": "SAINT-JEAN-DE-LUZ", "situation": "ATLANTIQUE", "lat": 43.388269, "lon": -1.663906},
    {"id_plage": 14, "nom_plage": "SAINT-MALO", "situation": "MANCHE", "lat": 48.648885, "lon": -2.030514},
    {"id_plage": 60, "nom_plage": "SAINT-TROPEZ", "situation": "CÔTE D'AZUR ET CORSE", "lat": 43.267991, "lon": 6.640266},
    {"id_plage": 66, "nom_plage": "SAINTE-MAXIME", "situation": "CÔTE D'AZUR ET CORSE", "lat": 43.310667, "lon": 6.635901},
    {"id_plage": 53, "nom_plage": "SAINTES-MARIES-DE-LA-MER", "situation": "GOLFE DU LION", "lat": 43.492605, "lon": 4.481307},
    {"id_plage": 44, "nom_plage": "SÈTE", "situation": "GOLFE DU LION", "lat": 43.407088, "lon": 3.702138},
    {"id_plage": 72, "nom_plage": "STELLA PLAGE", "situation": "MANCHE", "lat": 50.480078, "lon": 1.575649},
    {"id_plage": 41, "nom_plage": "TOULON", "situation": "GOLFE DU LION", "lat": 43.12458, "lon": 5.925363},
    {"id_plage": 20, "nom_plage": "VANNES", "situation": "ATLANTIQUE", "lat": 47.633389, "lon": -2.766734},
    {"id_plage": 82, "nom_plage": "VILLEFRANCHE-SUR-MER", "situation": "CÔTE D'AZUR", "lat": 43.70115, "lon": 7.31145},
    {"id_plage": 74, "nom_plage": "WIMEREUX", "situation": "MANCHE", "lat": 50.768721, "lon": 1.606484},
    {"id_plage": 70, "nom_plage": "WISSANT", "situation": "MANCHE", "lat": 50.891108, "lon": 1.666095},
    {"id_plage": 69, "nom_plage": "ZUYDCOOTE", "situation": "MANCHE", "lat": 51.070792, "lon": 2.483572}
]
plages = pd.DataFrame(DATA_PLAGES)

# ==========================================
# 5. TÉLÉCHARGEMENT ET RECHERCHE DE LA TEMPÉRATURE
# ==========================================
print(f"Tentative de téléchargement : {URL_FICHIER}")
try:
    urllib.request.urlretrieve(URL_FICHIER, LOCAL_NC)
    print("Téléchargement réussi.")
except Exception as e:
    print(f"Erreur de téléchargement : {e}")
    exit(1)

ds = xr.open_dataset(LOCAL_NC)
rename_dict = {c: c.strip().lower() for c in list(ds.coords) + list(ds.data_vars)}
ds = ds.rename(rename_dict)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    return R * 2 * np.arcsin(np.sqrt(np.sin((lat2 - lat1)/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1)/2)**2))

results = []
for _, row in plages.iterrows():
    lat_plage, lon_plage = row["lat"], row["lon"]
    sst_k, distance_km = np.nan, np.nan
    
    # Tentative d'interpolation directe sur la plage
    try:
        interpolated_point = ds["analysed_sst"].interp(lat=lat_plage, lon=lon_plage, method="linear")
        val = interpolated_point.values.item()
        if not np.isnan(val):
            sst_k, distance_km = val, 0.0
    except:
        pass
        
    # Recherche élargie en mer si le point terrestre est vide
    if np.isnan(sst_k):
        try:
            lat_min, lat_max = sorted([lat_plage - 0.2, lat_plage + 0.2])
            lon_min, lon_max = sorted([lon_plage - 0.2, lon_plage + 0.2])
            
            subset = ds["analysed_sst"].sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
            local_df = subset.to_dataframe().reset_index().dropna()
            
            if not local_df.empty:
                local_df["dist"] = local_df.apply(lambda r: haversine_distance(lat_plage, lon_plage, r["lat"], r["lon"]), axis=1)
                closest_row = local_df.loc[local_df["dist"].idxmin()]
                sst_k = closest_row["analysed_sst"]
                distance_km = closest_row["dist"]
        except:
            pass
    
    sst_c = round(sst_k - 273.15, 1) if not np.isnan(sst_k) else "Non disponible"
    
    results.append({
        "ID_PLAGE": row["id_plage"],
        "NOM_PLAGE": row["nom_plage"],
        "SITUATION": row["situation"],
        "LAT": lat_plage,
        "LON": lon_plage,
        "DISTANCE_MER_KM": round(distance_km, 2) if not np.isnan(distance_km) else "",
        "SST_CELSIUS": sst_c
    })

result_df = pd.DataFrame(results)

# ==========================================
# 6. ENVOI ET MISE EN FORME DANS GOOGLE SHEETS
# ==========================================
print(f"Connexion à Google Sheets (Classeur ID: {SPREADSHEET_ID})...")
wb = gc.open_by_key(SPREADSHEET_ID)

try:
    output_sheet = wb.worksheet(NOM_ONGLET)
except gspread.exceptions.WorksheetNotFound:
    print(f"L'onglet '{NOM_ONGLET}' n'existe pas. Création automatique...")
    output_sheet = wb.add_worksheet(title=NOM_ONGLET, rows="1000", cols="10")

# 1. Nettoyage complet de l'onglet avant l'écriture
output_sheet.clear()

# 2. Préparation de la phrase de date pour la cellule A1
maintenant = datetime.now(timezone(timedelta(hours=2))) # Paris GMT+2
date_formatee = maintenant.strftime("%d/%m/%Y à %H:%M:%S")
phrase_import = [f"Dernière mise à jour des données : le {date_formatee}"]

# 3. Préparation du tableau (En-têtes + Lignes de données)
en_tetes = result_df.columns.values.tolist()
lignes_donnees = result_df.values.tolist()

# 4. Assemblage final : Ligne 1 (Date), Ligne 2 (En-têtes), Lignes suivantes (Plages)
toutes_les_lignes = [phrase_import] + [en_tetes] + lignes_donnees

# 5. Envoi propre et unifié en une seule fois (Zéro risque d'erreur 500)
output_sheet.update(values=toutes_les_lignes, range_name="A1")

print(f"✨ L'onglet '{NOM_ONGLET}' a été mis à jour avec brio et l'heure est gravée en A1 !")
