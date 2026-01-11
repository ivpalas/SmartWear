import json
import random
import os
import requests
from PIL import Image
from io import BytesIO

# Import de ta config personnalisée (Clé API et Chemins)
import Config 

class SmartWearVisualizer:
    def __init__(self):
        # On garde l'accès Gemini pour des évolutions futures, 
        # mais on utilise un moteur d'image robuste pour éviter l'erreur 404
        self.db_path = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result\SmartWear_DB.json"
        self.products = self._load_db()

    def _load_db(self):
        """Chargement de la base de données normalisée."""
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        print(f"❌ Erreur : Base de données introuvable à {self.db_path}")
        return []

    def get_user_inputs(self):
        """Interface utilisateur dans le terminal."""
        print("\n" + "="*40)
        print(" 📸 STUDIO PHOTO SMARTWEAR IA ")
        print("="*40)
        print("Styles: Décontracté, Sportif, Professionnel, Élégant, Streetwear, Vintage, Minimaliste, Urbain")
        
        mode = input("\nVisualiser : (1: Tenue complète, 2: Haut, 3: Bas, 4: Chaussures) : ").strip()
        genre = input("Genre (Homme/Femme/Teen/Enfant) : ").strip()
        age = input("Âge du mannequin (ex: 25) : ").strip()
        style = input("Style souhaité : ").strip()
        saison = input("Saison (Hiver, Été, Automne, Printemps) : ").strip()
        lieu = input("Lieu de la scène (ex: Rue de Paris, Nature, Futuriste) : ").strip()
        
        return {
            "mode": mode, 
            "genre": genre, 
            "age": age, 
            "style": style, 
            "season": saison, 
            "location": lieu
        }

    def select_items(self, prefs):
        """Sélection intelligente basée sur tes tags IA."""
        # Filtrage flexible (Saison demandée OU Toutes saisons)
        pool = [
            p for p in self.products 
            if p['genre_clean'].lower() == prefs['genre'].lower() 
            and p['style'].lower() == prefs['style'].lower()
            and (prefs['season'].lower() in p['season'].lower() or "toutes" in p['season'].lower())
        ]

        # Sécurité : Si aucun article avec ce style précis, on élargit un peu
        if not pool:
            print(f"⚠️ Aucun article '{prefs['style']}' trouvé pour cette saison. Recherche élargie...")
            pool = [p for p in self.products if p['genre_clean'].lower() == prefs['genre'].lower()]

        hauts = [p for p in pool if p['main_category'] in ['Hauts', 'Manteaux/Vestes']]
        bas = [p for p in pool if p['main_category'] in ['Bas', 'Robes/Ensembles']]
        shoes = [p for p in pool if p['main_category'] == 'Chaussures']

        selection = {"top": None, "bottom": None, "shoes": None}

        if prefs['mode'] == "1":
            selection["top"] = random.choice(hauts) if hauts else None
            selection["bottom"] = random.choice(bas) if bas else None
            selection["shoes"] = random.choice(shoes) if shoes else None
        elif prefs['mode'] == "2": selection["top"] = random.choice(hauts) if hauts else None
        elif prefs['mode'] == "3": selection["bottom"] = random.choice(bas) if bas else None
        elif prefs['mode'] == "4": selection["shoes"] = random.choice(shoes) if shoes else None

        return selection

    def generate_and_show(self):
        """Génère l'image et affiche les liens réels du catalogue."""
        prefs = self.get_user_inputs()
        outfit = self.select_items(prefs)

        desc_parts = []
        links = []

        # Construction de la description en ANGLAIS pour une meilleure qualité IA
        if outfit['top']: 
            desc_parts.append(f"a {outfit['top']['name']} in {outfit['top']['color']} color")
            links.append(f"🧥 HAUT ({outfit['top']['brand_source']}): {outfit['top']['url']}")
        if outfit['bottom']: 
            desc_parts.append(f"a {outfit['bottom']['name']}")
            links.append(f"👖 BAS ({outfit['bottom']['brand_source']}): {outfit['bottom']['url']}")
        if outfit['shoes']: 
            desc_parts.append(f"sneakers model {outfit['shoes']['name']}")
            links.append(f"👟 CHAUSSURES ({outfit['shoes']['brand_source']}): {outfit['shoes']['url']}")

        if not desc_parts:
            print("❌ Désolé, aucun article correspondant n'a été trouvé.")
            return

        # Construction du Prompt pour Stable Diffusion XL
        clothing_desc = " and ".join(desc_parts)
        raw_prompt = (
            f"Professional full body fashion photography, high-end editorial style. "
            f"A {prefs['age']} year old {prefs['genre']} model, {prefs['style']} style, "
            f"wearing {clothing_desc}. Standing in {prefs['location']}. "
            f"Cinematic lighting, 8k, highly detailed face and fabric, photorealistic."
        )

        print("\n🚀 Génération de l'image SmartWear...")
        
        # Encodage de l'URL pour la génération
        encoded_prompt = requests.utils.quote(raw_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"

        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img.show() # Ouvre l'image avec la visionneuse Windows
                
                # Sauvegarde automatique
                save_path = os.path.join(Config.OUTPUT_GRAPH_DIR, "Last_Look_Generated.png")
                img.save(save_path)
                print(f"✅ Image enregistrée : {save_path}")
            else:
                print(f"❌ Erreur serveur image (Code: {response.status_code})")
        except Exception as e:
            print(f"❌ Erreur technique : {e}")

        # Affichage des liens réels
        print("\n" + "-"*50)
        print(" 🛒 ARTICLES RÉELS TROUVÉS DANS VOTRE CATALOGUE ")
        print("-"*50)
        for link in links:
            print(link)
        print("-"*50 + "\n")

if __name__ == "__main__":
    app = SmartWearVisualizer()
    app.generate_and_show()