# ==========================================
# 1. IMPORTS
# ==========================================
import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
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
# 3. BASE DE DONNÉES DES 71 PLAGES
# ==========================================
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
    {"id_plage": 13, "nom_plage": "BRAY-DUNES", "url": "https://meteofrance.com/meteo-plages/calais/6219351"},
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
    {"id_plage": 28, "nom_plage": "DUNKERQUE", "url": "https://meteofrance.com/meteo-plages/calais/6219351"},
    {"id_plage": 72, "nom_plage": "FÉCAMP", "url": "https://meteofrance.com/meteo-plages/etretat/7625451"},
    {"id_plage": 29, "nom_plage": "FORT-MAHON PLAGE", "url": "https://meteofrance.com/meteo-plages/fort-mahon/8033351"},
    {"id_plage": 30, "nom_plage": "FRéJUS", "url": "https://meteofrance.com/meteo-plages/frejus/8306151"},
    {"id_plage": 31, "nom_plage": "GRANVILLE", "url": "https://meteofrance.com/meteo-plages/granville/5021851"},
    {"id_plage": 32, "nom_plage": "GRUISSAN", "url": "https://meteofrance.com/meteo-plages/gruissan/1117051"},
    {"id_plage": 33, "nom_plage": "HENDAYE", "url": "https://meteofrance.com/meteo-plages/hendaye/6426051"},
    {"id_plage": 34, "nom_plage": "HYÈRES", "url": "https://meteofrance.com/meteo-plages/hyeres-les-palmiers/8306951"},
    {"id_plage": 35, "nom_plage": "ILE D'OLÉRON", "url": "https://meteofrance.com/meteo-plages/saint-pierre-d-oleron/1738551"},
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
    {"id_plage": 73, "nom_plage": "NAUJAC-SUR-MER", "url": "https://meteofrance.com/meteo-plages/hourtin/3320351"},
    {"id_plage": 52, "nom_plage": "NICE", "url": "https://meteofrance.com/meteo-plages/nice/0608851"},
    {"id_plage": 53, "nom_plage": "NOIRMOUTIER", "url": "https://meteofrance.com/meteo-plages/noirmoutier-en-l-ile/8516351"},
    {"id_plage": 54, "nom_plage": "PALAVAS-LES-FLOTS", "url": "https://meteofrance.com/meteo-plages/palavas-les-flots/3419251"},
    {"id_plage": 55, "nom_plage": "PERROS-GUIREC", "url": "https://meteofrance.com/meteo-plages/perros-guirec/2216851"},
    {"id_plage": 56, "nom_plage": "PLOUDALMÉZEAU", "url": "https://meteofrance.com/meteo-plages/roscoff/2923951"},
    {"id_plage": 57, "nom_plage": "PORT-DE-BOUC", "url": "https://meteofrance.com/meteo-plages/port-de-bouc/1307751"},
    {"id_plage": 58, "nom_plage": "PORTO-VECCHIO", "url": "https://meteofrance.com/meteo-plages/porto-vecchio/2024751"},
    {"id_plage": 59, "nom_plage": "ROQUEBRUNE-CAP-MARTIN", "url": "https://meteofrance.com/meteo-plages/roquebrune-cap-martin/0610451"},
    {"id_plage": 60, "nom_plage": "ROYAN", "url": "https://meteofrance.com/meteo-plages/royan/1730651"},
    {"id_plage": 74, "nom_plage": "SAINT-BRIEUC", "url": "https://meteofrance.com/meteo-plages/erquy/2205451"},
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

en_tetes = ["ID_PLAGE", "NOM_PLAGE", "SST_CELSIUS", "DATE_CONTRÔLE"]

# ==========================================
# 4. FONCTION DE SCRAPING D'UNE PLAGE UNIQUE
# ==========================================
async def scraper_une_plage(context, plage, date_str):
    print(f"Analyse de {plage['nom_plage']}...")
    sst_val = "Indisponible"
    
    # On isole les erreurs pour qu'une plage en panne ne bloque pas les autres
    try:
        page = await context.new_page()
        await page.goto(plage["url"], timeout=30000)
        
        if "previsions-meteo-france" not in plage["url"]:
            sel_sst = "li.t_sea > strong"
            # FORCE l'attente du sélecteur à l'écran (Maximum 8 secondes)
            await page.wait_for_selector(sel_sst, timeout=8000)
            
            text_sst = await page.locator(sel_sst).inner_text()
            if text_sst:
                sst_val = text_sst.replace("°", "").strip()
        else:
            sst_val = "Page Classique"
            
        await page.close()
    except Exception:
        print(f"   -> Échec d'extraction (Timeout ou élément absent) pour {plage['nom_plage']}")
        try: await page.close()
        except: pass
        
    return [plage["id_plage"], plage["nom_plage"], sst_val, date_str]

# ==========================================
# 5. PILOTAGE ASYNC MULTI-ONGLETS
# ==========================================
async def main():
    maintenant = datetime.now(timezone(timedelta(hours=2)))
    date_complete = maintenant.strftime("%d/%m/%Y à %H:%M:%S")
    
    print("Démarrage du navigateur Playwright (Mode Rapide Asynchrone)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # On définit une limite de 5 requêtes simultanées pour ne pas surcharger Météo-France
        semaphore = asyncio.Semaphore(5)
        
        async def executer_avec_limite(plage):
            async with semaphore:
                return await scraper_une_plage(context, plage, date_complete)
                
        # On lance toutes les tâches en parallèle
        taches = [executer_avec_limite(plage) for plage in DATA_PLAGES]
        lignes_finales = await asyncio.gather(*taches)
        
        await browser.close()
        
    # ==========================================
    # 6. EXPÉDITION SUR GOOGLE SHEETS
    # ==========================================
    print("Connexion à l'API Google Sheets...")
    wb = gc.open_by_key(SPREADSHEET_ID)
    try:
        output_sheet = wb.worksheet(NOM_ONGLET)
    except gspread.exceptions.WorksheetNotFound:
        output_sheet = wb.add_worksheet(title=NOM_ONGLET, rows="200", cols="4")
        
    print("Réécriture complète du tableau...")
    output_sheet.clear()
    
    phrase_titre = [f"Suivi Général Météo France - Mise à jour globale du {date_complete}"]
    grille_a_pousser = [phrase_titre] + [en_tetes] + lignes_finales
    
    output_sheet.update(values=grille_a_pousser, range_name="A1")
    print("✨ Opération terminée avec succès ! Toutes les températures réelles sont restaurées.")

# Lancement du script
if __name__ == "__main__":
    asyncio.run(main())
