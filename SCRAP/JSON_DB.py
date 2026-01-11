import json
import os
import re

class SmartWearDataPipeline:
    def __init__(self):
        # Configuration des chemins
        self.paths = {
            "Mango": r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result\Mango.json",
            "Nike_Vets": r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result\Vêtements_Nike.json",
            "Nike_Shoes": r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result\Chaussures_Nike.json"
        }
        self.output_path = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result\SmartWear_DB.json"
        
        # Mots-clés pour la saisonnalité
        self.winter_keywords = ['laine', 'cachemire', 'manteau', 'anorak', 'polaire', 'doublure', 'chaud', 'froid', 'parka', 'velours', 'hiver', 'doudoune', 'bottines']
        self.summer_keywords = ['t-shirt', 'satin', 'lin', 'sandales', 'léger', 'fleurs', 'court', 'sans manches', 'fluide', 'été', 'débardeur']

    def determine_age_range(self, item):
        """Détermine la tranche d'âge basée sur le genre clean et les mots-clés."""
        genre = item.get('genre_clean')
        desc = (item.get('description', '') or '').lower()
        
        if genre == "Enfant": return "0-9"
        if genre == "Teen": return "10-19"
        
        # Logique pour adultes
        if any(x in desc for x in ["fêtes", "soirée", "mariage", "élégant", "sélection"]):
            return "20-49"
        
        return "20-29"

    def determine_style(self, item):
        """Détermine le style avec une logique de Fallback pour éliminer l'Inconnu."""
        name = item.get('name', '').lower()
        desc = (item.get('description', '') or '').lower()
        full_text = f"{name} {desc}".lower()
        source = item.get('brand_source', '')
        main_cat = item.get('main_category', '')

        # 1. LOGIQUE PAR MARQUE (Spécialisation Nike)
        if "Nike" in source:
            if any(x in full_text for x in ["jordan", "air max", "dunk", "shox", "force 1", "cargo", "oversize", "stranger things"]):
                return "Streetwear"
            return "Sportif"

        # 2. LOGIQUE PAR MOTS-CLÉS DÉTAILLÉS (Mango et autres)
        specific_styles = {
            "Élégant": ["satin", "cachemire", "bijou", "fêtes", "robe", "dentelle", "strass", "soie", "tailleur", "mariage", "noël", "talons"],
            "Urbain": ["manteau", "trench", "bottines", "chelsea", "laine", "pince", "cuir", "blazer", "ville", "gabardine"],
            "Streetwear": ["hoodie", "sweat", "jogging", "baggy", "mom-fit", "wideleg", "cargo", "denim", "jean", "skate", "jaspe"],
            "Minimaliste": ["uni", "coton", "basique", "essentiels", "simple", "droit", "noir", "blanc", "perkins"],
            "Vintage": ["rétro", "archive", "old school", "80s", "90s", "vintage", "pied-de-coq", "chevrons"],
            "Professionnel": ["chemise", "bureau", "travail", "veste basique", "pantalons regular fit", "viscose", "col polo"]
        }

        for style, keywords in specific_styles.items():
            if any(word in full_text for word in keywords):
                return style

        # 3. LOGIQUE DE SECOURS PAR CATÉGORIE (Élimine l'inconnu)
        fallback_map = {
            "Chaussures": "Urbain",
            "Robes/Ensembles": "Élégant",
            "Manteaux/Vestes": "Urbain",
            "Hauts": "Décontracté",
            "Bas": "Décontracté"
        }

        return fallback_map.get(main_cat, "Décontracté")

    def normalize_item(self, item, source):
        # A. Source
        item['brand_source'] = source

        # B. Genre Normalisé
        genre_raw = str(item.get('genre', 'Homme')).lower()
        if any(x in genre_raw for x in ['enfant', 'fille', 'garçon']):
            item['genre_clean'] = 'Enfant'
        elif any(x in genre_raw for x in ['teen', 'adolescent']):
            item['genre_clean'] = 'Teen'
        elif 'femme' in genre_raw:
            item['genre_clean'] = 'Femme'
        else:
            item['genre_clean'] = 'Homme'

        # C. Catégorie Unifiée
        full_type = (str(item.get('type', '')) + " " + str(item.get('category_auto', ''))).lower()
        if any(x in full_type for x in ['chaussure', 'bottine', 'sneaker', 'air max', 'jordan', 'sandale', 'claquette']):
            item['main_category'] = 'Chaussures'
        elif any(x in full_type for x in ['manteau', 'veste', 'anorak', 'parka', 'blouson', 'gabardine', 'trench']):
            item['main_category'] = 'Manteaux/Vestes'
        elif any(x in full_type for x in ['pull', 'sweat', 'hoodie', 't-shirt', 'haut', 'chemise', 'gilet', 'top']):
            item['main_category'] = 'Hauts'
        elif any(x in full_type for x in ['pantalon', 'jean', 'bas', 'jogging', 'short', 'trouser']):
            item['main_category'] = 'Bas'
        elif any(x in full_type for x in ['robe', 'combinaison', 'jupe']):
            item['main_category'] = 'Robes/Ensembles'
        else:
            item['main_category'] = 'Autre'

        # D. Saisonnalité
        text_to_scan = f"{item.get('name','')} {item.get('description','')} {full_type}".lower()
        if any(word in text_to_scan for word in self.winter_keywords):
            item['season'] = 'Hiver/Automne'
        elif any(word in text_to_scan for word in self.summer_keywords):
            item['season'] = 'Été/Printemps'
        else:
            item['season'] = 'Toutes saisons'

        # E. UPGRADE IA : Age & Style
        item['age_range'] = self.determine_age_range(item)
        item['style'] = self.determine_style(item)

        return item

    def run(self):
        print("🔄 Démarrage du Pipeline SmartWear (Fusion + Style Intelligence)...")
        final_db = []

        for source_name, path in self.paths.items():
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"📥 Traitement de {source_name}...")
                    for product in data:
                        final_db.append(self.normalize_item(product, source_name))
            else:
                print(f"⚠️ Fichier introuvable : {path}")

        if final_db:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(final_db, f, indent=4, ensure_ascii=False)
            
            print(f"\n✨ SUCCÈS : {len(final_db)} articles prêts pour SmartWear.")
            print(f"📄 Base de données finale : {self.output_path}")

if __name__ == "__main__":
    pipeline = SmartWearDataPipeline()
    pipeline.run()