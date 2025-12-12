import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os

# --- Constantes Globales ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9"
}
BASE_URL = "https://www.nike.com"

# Chemins de sortie centralisés
OUTPUT_RESULT_DIR = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result"


# =====================================================================
# UTILITAIRES DE PARSING ET CLASSIFICATION
# =====================================================================

def parse_price_text(price_text):
    """Extrait un nombre et la monnaie depuis un texte de prix."""
    if not price_text: return None, None, ""

    txt = price_text.strip().replace('\xa0', ' ').replace('\u202f', ' ').strip()
    currency = 'EUR' if '€' in txt else 'USD' if '$' in txt else None
        
    m = re.search(r'(\d{1,3}(?:[ \u00A0]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)', txt)
    if not m: return None, currency, txt

    num = m.group(1).replace(' ', '').replace('\u00A0', '').replace(',', '.')
    try:
        val = float(num)
    except:
        val = None

    return val, currency, txt

def classify_clothing(name, description):
    """Classe le vêtement dans une catégorie simple (Haut, Bas, Veste, etc.)."""
    name = name.lower()
    description = description.lower()
    
    if any(term in name or term in description for term in ["pantalon", "legging", "short", "jogging", "jupe"]):
        return "Bas"
    if any(term in name or term in description for term in ["veste", "doudoune", "blouson", "parka", "manteau", "coupe-vent"]):
        return "Veste/Manteau"
    if any(term in name or term in description for term in ["sweat", "hoodie", "capuche", "pull", "gilet"]):
        return "Sweat/Hoodie"
    if any(term in name or term in description for term in ["t-shirt", "haut", "tee", "débardeur", "chemise", "maillot"]):
        return "Haut/T-shirt"
    if any(term in name or term in description for term in ["brassière", "soutien-gorge"]):
        return "Brassière/Sous-vêtement"
    
    return "Autre"


# =====================================================================
# 1. Scrape une page produit Nike 
# =====================================================================
def scrape_product(product_url, genre, product_type):
    """Scrape les détails d'un produit unique (avec genre et type d'article)."""
    
    try:
        r = requests.get(product_url, headers=HEADERS, timeout=15) 
    except requests.exceptions.RequestException:
        return None

    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # --- Initialisation ---
    name, price_value, currency, description, color, rating = "Inconnu", None, None, "Aucune description", "Couleur inconnue", None
    available_sizes, fit_details = [], []
    image_url = None
    price_raw = None 

    # ---- Extraction des données (simplifiée pour la concision) ----
    name_tag = soup.find("h1")
    name = name_tag.get_text(strip=True) if name_tag else "Inconnu"

    price_elem = soup.find(attrs={"data-testid": "currentPrice-container"}) or soup.find(id="price-container")
    if price_elem: price_raw = price_elem.get_text(" ", strip=True)
    if price_raw:
        val, curr, _ = parse_price_text(price_raw)
        price_value = val
        currency = currency or curr

    desc_container = soup.find("div", {"id": "product-description-container"})
    if desc_container:
        desc_elem = desc_container.find(attrs={"data-testid": "product-description"})
        description = desc_elem.get_text(" ", strip=True) if desc_elem else description
    
    color_elem = soup.find(attrs={"data-testid": "product-description-color-description"})
    if color_elem:
        raw_color_text = color_elem.get_text(" ", strip=True)
        color = raw_color_text.replace("Couleur affichée :", "").strip()
    
    rating_elem = soup.find(attrs={"data-testid": "reviews-summary-rating"})
    if rating_elem:
        rating_text = rating_elem.get_text(" ", strip=True).replace('\xa0', ' ').replace('\u202f', ' ').strip()
        rating_match = re.search(r'(\d+[.,]\d+)', rating_text)
        if rating_match: rating = float(rating_match.group(1).replace(',', '.'))
            
    # Tailles (commune aux chaussures et vêtements)
    size_items = soup.find_all(attrs={"data-testid": "pdp-grid-selector-item"})
    for item in size_items:
        is_disabled = 'disabled' in item.get('class', [])
        label_tag = item.find('label')
        size_text = label_tag.get_text(" ", strip=True) if label_tag else item.get_text(" ", strip=True)
        
        if size_text and not size_text.isspace():
            cleaned_size = size_text.strip()
            if cleaned_size: available_sizes.append({"size": cleaned_size, "available": not is_disabled})

    # Fit Details (Pour les vêtements)
    fit_accordion = soup.find(attrs={"data-testid": "pdp-info-accordions__size-fit-accordion"})
    if fit_accordion:
        ul_tag = fit_accordion.find('ul') 
        if ul_tag:
            for li in ul_tag.find_all('li'):
                text = li.get_text(" ", strip=True)
                if text and "Guide des tailles" not in text: fit_details.append(text)

    # Image (Fallback HTML)
    if not image_url:
        img_tag = soup.find("img", {"alt": True})
        image_url = img_tag["src"] if img_tag and img_tag.get("src") else None

    # Classification automatique pour les VÊTEMENTS
    category_auto = classify_clothing(name, description) if product_type == "Vêtements" else product_type
    

    return {
        "name": name,
        "price_value": price_value,
        "currency": currency,
        "description": description,
        "color": color,       
        "rating": rating,     
        "sizes": available_sizes, 
        "fit_details": fit_details, # Détaillée sur les vêtements
        "category_auto": category_auto, 
        "image": image_url,
        "url": product_url,
        "genre": genre,
        "type": product_type # Chaussures ou Vêtements
    }


# =====================================================================
# 2. Scrape une page catalogue Nike
# =====================================================================
def scrape_catalogue(catalogue_url, genre, product_type):
    
    try:
        r = requests.get(catalogue_url, headers=HEADERS, timeout=20) 
    except requests.exceptions.RequestException:
        return []

    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    unique_product_urls = set()

    # --- Stratégie HTML & JSON pour les URLs ---
    product_cards = soup.find_all("a", {"class": "product-card__link-overlay"})
    for card in product_cards:
        href = card.get("href")
        if href:
            unique_product_urls.add(BASE_URL + href if href.startswith('/') else href)

    hrefs_from_regex = re.findall(r'"productUrl":"(https?://www\.nike\.com[^"]+)"', r.text)
    unique_product_urls.update(hrefs_from_regex)
    
    # --- PHASE 2: SCRAPING DES DÉTAILS ---
    products = []
    urls_to_scrape = list(unique_product_urls)
    
    for product_url in urls_to_scrape:
        # Passage du genre et du type d'article
        details = scrape_product(product_url, genre, product_type)
        if details:
            products.append(details)

        time.sleep(random.uniform(5, 10)) 
        
    return products


# =====================================================================
# 3. FONCTION D'EXÉCUTION PRINCIPALE (COMBINÉE)
# =====================================================================
def main_scraper():
    
    ALL_CATEGORIES_TO_SCRAPE = {
        "Chaussures": {
            "Homme": "https://www.nike.com/fr/w/hommes-chaussures-nik1zy7ok",
            "Femme": "https://www.nike.com/fr/w/femmes-chaussures-5e1x6zy7ok"
        },
        "Vêtements": {
            "Homme": "https://www.nike.com/fr/w/hommes-vetements-6ymx6znik1",
            "Femme": "https://www.nike.com/fr/w/femmes-vetements-5e1x6z6ymx6"
        }
    }
    
    all_combined_results = {}

    for product_type, gender_urls in ALL_CATEGORIES_TO_SCRAPE.items():
        type_results = []
        
        for genre, url in gender_urls.items():
            print(f"--- Démarrage du scraping : {product_type} ({genre}) ---")
            
            # Scrape_catalogue reçoit le genre et le type d'article
            results_category = scrape_catalogue(url, genre, product_type) 
            type_results.extend(results_category)
            
            print(f"--- {len(results_category)} articles trouvés pour {genre} ({product_type}). ---")
            
            # Pause après chaque sous-catégorie
            time.sleep(random.uniform(10, 20))
            
        all_combined_results[product_type] = type_results
        
    return all_combined_results


# =====================================================================
# 4. Exécution et Sauvegarde Silencieuse
# =====================================================================
if __name__ == "__main__":
    
    # --- EXÉCUTION ---
    combined_results = main_scraper() 
    
    # Créer le répertoire s'il n'existe pas
    if not os.path.exists(OUTPUT_RESULT_DIR):
        os.makedirs(OUTPUT_RESULT_DIR)
        
    total_products = 0

    # --- SAUVEGARDE DES FICHIERS DISTINCTS ---
    for product_type, results_list in combined_results.items():
        
        # Définir le nom du fichier (ex: Chaussures_Nike.json ou Vêtements_Nike.json)
        OUTPUT_FILENAME = f"{product_type}_Nike.json"
        FULL_OUTPUT_PATH = os.path.join(OUTPUT_RESULT_DIR, OUTPUT_FILENAME)
        
        with open(FULL_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results_list, f, indent=4, ensure_ascii=False)
            
        total_products += len(results_list)
        print(f"\n📁 {len(results_list)} résultats pour {product_type} enregistrés dans {FULL_OUTPUT_PATH}")

    print("\n==========================")
    print("SCRAPING TERMINÉ")
    print("==========================")
    print(f"Total général des produits extraits : {total_products}")