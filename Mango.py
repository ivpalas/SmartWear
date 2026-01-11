import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
import random

class MangoGlobalScraper:
    def __init__(self):
        self.base_url = "https://shop.mango.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9"
        }
        self.output_path = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result\Mango.json"

    def clean_product_name(self, raw_name, url):
        """Corrige les noms parasites en extrayant le nom réel depuis l'URL."""
        trash_labels = ["Disponible Plus", "Selection", "PERFORMANCE", "Exclusivité internet", "ESSENTIALS", "Vêtement", "Selectioned"]
        
        # Si le nom est un tag marketing ou bizarre, on déduit le nom de l'URL
        if raw_name in trash_labels or len(raw_name) < 3:
            # L'URL finit par .../nom-du-produit_ID. On capture ce qui est avant l'ID
            match = re.search(r'/([^/]+)_\d+', url)
            if match:
                return match.group(1).replace('-', ' ').capitalize()
        return raw_name

    def get_detailed_data(self, url):
        """Extraction approfondie sur la page produit."""
        try:
            time.sleep(random.uniform(0.5, 1.0))
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. Vrai Prix (Final Price)
            price = None
            p_tag = soup.find('span', class_=re.compile(r"finalPrice|SinglePrice_finalPrice", re.I))
            if not p_tag: p_tag = soup.find('span', class_=re.compile(r"SinglePrice_center", re.I))
            if p_tag:
                price = float(re.sub(r'[^\d,.]', '', p_tag.get_text()).replace(',', '.'))

            # 2. Couleur (Alt de l'image sélectionnée)
            color = None
            sel = soup.find('span', class_=re.compile(r"selected", re.I))
            if sel and sel.find('img'):
                color = sel.find('img').get('alt', '').replace('Couleur ', '').replace(' sélectionnée', '').strip()

            # 3. Tailles Disponibles (Exclut les notifyMe)
            sizes = []
            items = soup.find_all(['div', 'button'], class_=re.compile(r"sizeItem|sizePicker", re.I))
            for item in items:
                if not item.find(class_=re.compile(r"notifyMe|unavailable", re.I)):
                    s_tag = item.find(class_=re.compile(r"textActionM|size-label", re.I))
                    if s_tag:
                        val = s_tag.get_text(strip=True)
                        if val and val not in sizes: sizes.append(val)
            
            # 4. Description courte
            desc = ""
            desc_meta = soup.find('meta', {'property': 'og:description'})
            if desc_meta: desc = desc_meta['content']

            return color, sizes, price, desc
        except:
            return None, [], None, ""

    def scrape_category(self, url, genre, p_type):
        print(f"📡 Analyse : {genre} > {p_type}")
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = soup.find_all('a', href=re.compile(r'/p/'))
            cat_results = []
            seen_urls = set()

            for l in links:
                href = l.get('href')
                full_url = href if href.startswith('http') else self.base_url + href
                clean_url = full_url.split('?')[0]

                if clean_url in seen_urls: continue
                seen_urls.add(clean_url)

                # Extraction du nom brut
                name_tag = l.find(['p', 'span']) or l.find_next(['p', 'span'])
                raw_name = name_tag.get_text(strip=True) if name_tag else "Vêtement"
                
                # NETTOYAGE DU NOM IMMEDIAT
                name = self.clean_product_name(raw_name, clean_url)

                # Image
                img_tag = l.find('img')
                image_url = img_tag.get('src') if img_tag else None

                print(f"  ∟ {name}...")
                color, sizes, price, desc = self.get_detailed_data(clean_url)

                if price or sizes:
                    cat_results.append({
                        "name": name,
                        "price_value": price,
                        "currency": "EUR",
                        "description": desc,
                        "color": color,
                        "rating": None,
                        "sizes": sizes,
                        "fit_details": [],
                        "category_auto": "Vêtements",
                        "image": image_url,
                        "genre": genre,
                        "type": p_type,
                        "url": clean_url
                    })
            return cat_results
        except Exception as e:
            print(f"⚠️ Erreur catégorie: {e}")
            return []

    def run(self):
        catalog = [
            ("Femme", "Pulls", "https://shop.mango.com/fr/fr/c/femme/pulls-et-cardigans_f9a8c868"),
            ("Femme", "Manteaux", "https://shop.mango.com/fr/fr/c/femme/manteau_d1b967bc"),
            ("Femme", "Robes", "https://shop.mango.com/fr/fr/c/femme/robes-et-combinaisons_e6bb8705"),
            ("Femme", "Chaussures", "https://shop.mango.com/fr/fr/c/femme/chaussure_826dba0a"),
            ("Homme", "Manteaux", "https://shop.mango.com/fr/fr/c/homme/manteaux_3a5ade78"),
            ("Homme", "Pulls", "https://shop.mango.com/fr/fr/c/homme/gilets-et-pull-overs_89e09112"),
            ("Homme", "Pantalons", "https://shop.mango.com/fr/fr/c/homme/pantalons_b126cc9c"),
            ("Homme", "Vestes", "https://shop.mango.com/fr/fr/c/homme/vestes_b5a3a3f6"),
            ("Teen", "Manteaux", "https://shop.mango.com/fr/fr/c/teen/teena/manteaux-et-vestes_8573c85c"),
            ("Teen", "Pulls", "https://shop.mango.com/fr/fr/c/teen/teena/pulls-et-cardigans_48d543e1"),
            ("Teen", "Jeans", "https://shop.mango.com/fr/fr/c/teen/teena/jeans_98b73358"),
            ("Teen", "Robes", "https://shop.mango.com/fr/fr/c/teen/teena/robes-et-combinaisons_b05dc3e4"),
            ("Enfants Fille", "Manteaux", "https://shop.mango.com/fr/fr/c/enfants/fille/manteaux-et-vestes_39dace35"),
            ("Enfants Fille", "Jeans", "https://shop.mango.com/fr/fr/c/enfants/fille/jeans_a9530c83"),
            ("Enfants Garçon", "Manteaux", "https://shop.mango.com/fr/fr/c/enfants/garcon/manteaux-et-vestes_3311d26e"),
            ("Enfants Garçon", "T-shirts", "https://shop.mango.com/fr/fr/c/enfants/garcon/t-shirts_d4d4580c"),
        ]

        all_data = []
        for genre, p_type, url in catalog:
            category_data = self.scrape_category(url, genre, p_type)
            all_data.extend(category_data)
            print(f"✅ {len(category_data)} produits ajoutés.")

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
        
        print(f"\n✨ BASE DE DONNÉES COMPLÈTE & NETTOYÉE : {len(all_data)} produits.")

if __name__ == "__main__":
    MangoGlobalScraper().run()