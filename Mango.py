import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
from urllib.parse import urljoin

# --- Constantes Globales ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9"
}
BASE_URL = "https://shop.mango.com"

# URL du catalogue Femme : Pulls et Cardigans (une catégorie de vêtements)
MANGO_WOMEN_URL = "https://shop.mango.com/fr/fr/c/femme/pulls-et-cardigans_f9a8c868"
OUTPUT_RESULT_DIR = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result"


# =====================================================================
# UTILITAIRES DE PARSING ET CLASSIFICATION
# =====================================================================

def parse_price_text(price_text):
    """Extrait un nombre et la monnaie d'un texte de prix."""
    if not price_text: return None, None
    
    txt = price_text.strip().replace('\xa0', ' ').replace('\u202f', ' ').strip()
    currency = 'EUR' if '€' in txt else None
        
    m = re.search(r'(\d{1,3}(?:[ \u00A0]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)', txt)
    if not m: return None, currency

    num = m.group(1).replace(' ', '').replace('\u00A0', '').replace(',', '.')
    try:
        val = float(num)
    except:
        val = None

    return val, currency

def extract_from_json(r_text, catalogue_url):
    """
    Recherche les données produit dans le bloc JSON pré-chargé de Mango.
    """
    products_data = []
    
    # Mango utilise window.__PRELOADED_STATE__
    match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.+?\});', r_text, re.DOTALL)
    
    if not match:
        return products_data

    try:
        data = json.loads(match.group(1))
        
        # Le chemin vers les produits est dans 'entities.products' et les IDs sont dans 'catalog.products'
        products_entities = data.get("entities", {}).get("products", {})
        product_ids = data.get("catalog", {}).get("products", [])
        
        for p_id in product_ids:
             # Récupère les données complètes de l'entité produit
             product_data = products_entities.get(str(p_id))
             
             if product_data:
                 products_data.append(product_data)

    except json.JSONDecodeError:
        return products_data
    
    return products_data


# =====================================================================
# 2. Scrape la page catalogue Mango
# =====================================================================
def scrape_mango_catalogue(catalogue_url, genre):
    
    try:
        r = requests.get(catalogue_url, headers=HEADERS, timeout=20) 
        r.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    # --- TENTATIVE D'EXTRACTION JSON (Priorité absolue pour Mango) ---
    raw_products = extract_from_json(r.text, catalogue_url)
    
    if not raw_products:
        return []

    # --- PHASE 2: CONVERSION DES DONNÉES BRUTES EN FORMAT JSON DÉFINI ---
    products = []
    
    for item in raw_products:
        
        # Tente de récupérer le prix
        price_raw = item.get("price") or item.get("finalPrice") or ""
        price_value, currency = parse_price_text(price_raw)
        
        # Récupération des URLs
        product_url_slug = item.get("slug")
        product_url = urljoin(BASE_URL, product_url_slug) if product_url_slug else None
        
        # Image : Mango donne souvent l'URL complète de l'image principale
        image_url = item.get("images", [{}])[0].get("url")
        
        # Classification rapide (Pulls/Cardigans)
        category_name = item.get("families", [{}])[0].get("label") or "Vêtement"

        # Construction du dictionnaire final
        products.append({
            "name": item.get("name") or "Inconnu",
            "price_value": price_value,
            "currency": currency,
            "description": item.get("description") or "Aucune description",
            "color": item.get("colors", [{}])[0].get("label") or "Inconnu",
            "rating": None, # Non stocké dans le catalogue JSON principal
            "sizes": item.get("sizes", []), # Liste brute des tailles
            "fit_details": [], # Détails de coupe non disponibles dans le catalogue JSON
            "category_auto": category_name,
            "image": image_url,
            "url": product_url,
            "genre": genre
        })
        
    return products


# =====================================================================
# 3. Exécution et Sauvegarde Silencieuse
# =====================================================================
def main_scraper():
    
    CATEGORIES_TO_SCRAPE = {
        "Femme": "https://shop.mango.com/fr/fr/c/femme/pulls-et-cardigans_f9a8c868"
    }
    
    all_results = []
    
    for genre, url in CATEGORIES_TO_SCRAPE.items():
        
        # Le type de produit est "Vêtements"
        results_category = scrape_mango_catalogue(url, genre) 
        all_results.extend(results_category)
        
        # Pause après la catégorie
        time.sleep(random.uniform(10, 20))
        
    return all_results


# =====================================================================
# 4. Exécution et Sauvegarde Silencieuse
# =====================================================================
if __name__ == "__main__":
    
    # Créer le répertoire s'il n'existe pas
    if not os.path.exists(OUTPUT_RESULT_DIR):
        os.makedirs(OUTPUT_RESULT_DIR)
        
    results = [] 

    try:
        # --- EXÉCUTION ---
        results = main_scraper() 
        
    except KeyboardInterrupt:
        print("\n\n❌ INTERRUPTION UTILISATEUR. Sauvegarde des données collectées...")
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}. Sauvegarde des données partielles...")
    
    finally:
        # --- SAUVEGARDE SILENCIEUSE ---
        OUTPUT_FILENAME = "Mango_Femme_Vetements.json"
        FULL_OUTPUT_PATH = os.path.join(OUTPUT_RESULT_DIR, OUTPUT_FILENAME)

        with open(FULL_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        print("\n==========================")
        print("SCRAPING MANGO TERMINÉ")
        print("==========================")
        print(f"Total des produits extraits : {len(results)}")
        print(f"Fichier enregistré : {FULL_OUTPUT_PATH}")