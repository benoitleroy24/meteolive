import os
import asyncio
import json
from playwright.async_api import async_playwright
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

async def scraper_plage(page, url):
    try:
        await page.goto(url, timeout=60000)
        # Attendre que la page soit chargée
        await page.wait_for_load_state("networkidle")
        
        # 1. Extraction de la température de l'eau (SST)
        try:
            # Remplacer par votre sélecteur exact si nécessaire
            temp_element = await page.locator('.releve-temperature__valeur').first
            temp_eau = await temp_element.text_content(timeout=5000)
            temp_eau = temp_eau.strip().replace("°", "")
        except Exception:
            temp_eau = "N/A"

        # 2. Extraction de l'indice UV - AUJOURD'HUI
        try:
            await page.click('#msc_today')
            await page.wait_for_timeout(500) # Pause pour le chargement du slider
            uv_element = await page.locator('#atmogramme_slider > div > ul > li.weather_details > div > ul > li.indice_uv').first
            uv_aujourdhui = await uv_element.text_content(timeout=5000)
            uv_aujourdhui = uv_aujourdhui.strip().split()[-1] # On prend le dernier élément (souvent le chiffre)
        except Exception:
            uv_aujourdhui = "N/A"

        # 3. Extraction de l'indice UV - DEMAIN
        try:
            await page.click('#msc_tomorrow')
            await page.wait_for_timeout(500) # Pause pour le basculement du slider
            uv_element_demain = await page.locator('#atmogramme_slider > div > ul > li.weather_details > div > ul > li.indice_uv').first
            uv_demain = await uv_element_demain.text_content(timeout=5000)
            uv_demain = uv_demain.strip().split()[-1]
        except Exception:
            uv_demain = "N/A"

        return temp_eau, uv_aujourdhui, uv_demain
    except Exception as e:
        print(error:=f"Erreur sur l'URL {url}: {e}")
        return "N/A", "N/A", "N/A"

async def main():
    # Liste des 71 plages (Exemple à compléter avec vos vraies URLs et Noms)
    plages = [
        {"nom": "Agde", "url": "https://meteofrance.com/meteo-marine/agde/relais-plage/340031"},
        # ... Ajoutez les 70 autres plages ici ...
    ]

    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Utilisation d'un User-Agent standard pour éviter les blocages de sécurité
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        for plage in plages:
            print(f"Scraping de {plage['nom']}...")
            temp, uv_immediat, uv_lendemain = await scraper_plage(page, plage["url"])
            results.append({
                "Plage": plage["nom"],
                "Temp Eau (°C)": temp,
                "UV Aujourd'hui": uv_immediat,
                "UV Demain": uv_lendemain
            })
            
        await browser.close()

    # Création du DataFrame et du fichier texte pour le mail
    df = pd.DataFrame(results)
    df.to_csv("rapport.txt", sep="\t", index=False) # Génère le fichier lu par le mail de fin

    # Connexion à Google Sheets via le Secret GitHub
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS"])
        creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Ouvre votre feuille "meteolive" ou le nom exact de votre fichier Google Sheet
        sheet = client.open("meteolive").sheet1
        
        # Nettoyage et mise à jour complète
        sheet.clear()
        # En tête + données
        data_to_write = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(data_to_write)
        print("Google Sheet mis à jour avec succès !")
    except Exception as e:
        print(f"Erreur lors de la mise à jour Google Sheets : {e}")

if __name__ == "__main__":
    asyncio.run(main())
