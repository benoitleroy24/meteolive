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

print("[INIT] Chargement des clés Google...")
google_secrets = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(google_secrets, scopes=scopes)
gc = gspread.authorize(creds)

# ==========================================
# 3. BASE DE DONNÉES DE TEST (1 SEULE PLAGE)
# ==========================================
DATA_PLAGES = [
    {"id_plage": 1, "nom_plage": "AGDE", "url": "https://meteofrance.com/meteo-plages/agde/3400351"}
]

en_tetes = ["ID_PLAGE", "NOM_PLAGE", "SST_CELSIUS", "UV_AUJOURDHUI", "UV_DEMAIN", "DATE_CONTRÔLE"]

# ==========================================
# 4. FONCTION DE SCRAPING D'UNE PLAGE UNIQUE
# ==========================================
async def scraper_une_plage(context, plage, date_str):
    print(f"[RUN] Début de l'analyse : {plage['nom_plage']}")
    sst_val = "N/A"
    uv_aujourdhui = "N/A"
    uv_demain = "N/A"
    page = None
    
    try:
        page = await context.new_page()
        # Timeout très court (15s) pour le test
        await page.goto(plage["url"], timeout=15000, wait_until="load")
        
        # --- 1. Bloc Température de l'eau ---
        sel_sst = "li.t_sea > strong"
        try:
            await page.wait_for_selector(sel_sst, timeout=3000)
            text_sst = await page.locator(sel_sst).inner_text()
            if text_sst:
                sst_val = text_sst.replace("°", "").strip()
        except Exception:
            sst_val = "N/A"

        # --- 2. Bloc UV Aujourd'hui ---
        sel_uv = "#atmogramme_slider > div > ul > li.weather_details > div > ul > li.indice_uv"
        try:
            await page.click('#msc_today', timeout=2000)
            await asyncio.sleep(0.3)
            await page.wait_for_selector(sel_uv, timeout=2000)
            text_uv_today = await page.locator(sel_uv).inner_text()
            if text_uv_today:
                uv_aujourdhui = text_uv_today.replace("Indice", "").replace("UV", "").strip().split()[-1]
        except Exception:
            uv_aujourdhui = "N/A"

        # --- 3. Bloc UV Demain ---
        try:
            await page.click('#msc_tomorrow', timeout=2000)
            await asyncio.sleep(0.3)
            await page.wait_for_selector(sel_uv, timeout=2000)
            text_uv_tomorrow = await page.locator(sel_uv).inner_text()
            if text_uv_tomorrow:
                uv_demain = text_uv_tomorrow.replace("Indice", "").replace("UV", "").strip().split()[-1]
        except Exception:
            uv_demain = "N/A"
            
    except Exception as e:
        print(f"[ERREUR] Échec pour {plage['nom_plage']}: {e}")
    finally:
        if page:
            await page.close()
        print(f"[OK] Terminé : {plage['nom_plage']} (Eau: {sst_val} | UV J: {uv_aujourdhui} | UV J+1: {uv_demain})")
        
    return [plage["id_plage"], plage["nom_plage"], sst_val, uv_aujourdhui, uv_demain, date_str]

# ==========================================
# 5. PILOTAGE ASYNC
# ==========================================
async def main():
    maintenant = datetime.now(timezone(timedelta(hours=2)))
    date_complete = maintenant.strftime("%d/%m/%Y à %H:%M:%S")
    
    print("[START] Initialisation du navigateur Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        print(f"[SCRAPE] Lancement du test sur {len(DATA_PLAGES)} plage...")
        lignes_finales = [await scraper_une_plage(context, DATA_PLAGES[0], date_complete)]
        
        await browser.close()
        
    print("[FILE] Écriture du fichier rapport.txt...")
    with open("rapport.txt", "w", encoding="utf-8") as f:
        f.write("\t".join(en_tetes) + "\n")
        for ligne in lignes_finales:
            f.write("\t".join(map(str, ligne)) + "\n")

    # ==========================================
    # 6. EXPÉDITION SUR GOOGLE SHEETS
    # ==========================================
    print("[SHEETS] Connexion à Google Sheets...")
    wb = gc.open_by_key(SPREADSHEET_ID)
    try:
        output_sheet = wb.worksheet(NOM_ONGLET)
    except gspread.exceptions.WorksheetNotFound:
        output_sheet = wb.add_worksheet(title=NOM_ONGLET, rows="10", cols="6")
        
    print("[SHEETS] Nettoyage et réécriture du tableau de test...")
    output_sheet.clear()
    
    phrase_titre = [f"TEST - Suivi Météo France - {date_complete}"]
    grille_a_pousser = [phrase_titre] + [en_tetes] + lignes_finales
    
    output_sheet.update("A1", grille_a_pousser)
    print("✨ [SUCCESS] Test complété avec succès pour 1 plage !")

if __name__ == "__main__":
    asyncio.run(main())
