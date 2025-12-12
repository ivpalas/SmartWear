# Generation.py

import json
import os
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image 
from google import genai
from wordcloud import WordCloud
from Config import GOOGLE_GEMINI_API_KEY, PREDICT_IMAGE, json_Description, GEMINI_MODEL_NAME, OUTPUT_JSON_PATH, OUTPUT_GRAPH_DIR

# Initialisation du client Gemini
client = genai.Client(api_key=GOOGLE_GEMINI_API_KEY)

def analyze_image(image_path, json_Description):
    """
    Analyse une image et remplit un JSON selon le contenu visible en utilisant Gemini.
    """
    try:
        img = Image.open(image_path)
    except FileNotFoundError:
        print(f"Erreur : Image non trouvée à l'emplacement {image_path}")
        return json_Description
    prompt_text = f"""
Tu es un expert en analyse vestimentaire. Remplis ce JSON avec les informations visibles sur l'image.

Réponds **UNIQUEMENT** avec le JSON rempli, sans texte supplémentaire, ni introduction.
Tu vas fonctionner en deux étapes : Ce que tu peux voir, et ce que tu peux deviner.

Pour certaines informations, je vais te donner des catégories pour t'aiguiller :
age_tranches = ["0-9", "10-19", "20-29", "30-39", "40-49","50-59", "60-69", "70-79", "80-89", "90+"]

couleur_peau = ["Très clair", "Clair", "Moyen clair", "Moyen","Moyen foncé", "Foncé", "Très foncé", "Non déterminé"]

saison_vetement = ["Printemps", "Été", "Automne", "Hiver","Toute saison", "Non déterminé"]

Marques = ["Nike", "Adidas", "Puma", "Reebok", "Under Armour", "Zara", "H&M", "Uniqlo", "Levi’s", "Tommy Hilfiger", "Calvin Klein", "Lacoste", "Ralph Lauren", "The North Face",
"Columbia", "Superdry", "Carhartt", "Converse", "Vans", "Gucci", "Autre"]. Concernant la marque, j'aimerais beaucoup que tu essayes de deviner.

style_vetement = ["Décontracté", "Sportif", "Professionnel", "Élégant", "Streetwear", "Vintage", "Minimaliste", "Bohème", "Urbain", "Classique", "Avant-garde", "Autre/Inconnu"]

Couleur_vêtement = ["Blanc", "Noir", "Gris", "Rouge", "Bleu", "Vert", "Jaune", "Marron", "Beige", "Violet", "Rose", "Orange", "Doré", "Argenté", "Bordeaux", "Turquoise"]

Teinte = ["Pâle", "Claire", "Normal", "Foncé", "Très foncé", "Vive", "Pastel", "Métallique"]

Taille estimé = ["XS", "S", "M", "L", "XL", "XLL"]

Concernant les accesoires, tu devras mettre le nombre, le style générale ainsi que la couleur générale.
Attention, une écharpe sera catégorisé comme un accessoire et non pas dans "Haut".

Commence par compléter les informations physiques. Puis essaye de deviner le reste
**RESPECTE BIEN LE JSON, NE RENDS QUE LE JSON AVEC TOUTES LES INFORMATIONS**.
Je veux que tu gardes les mêmes noms de champs, que tu n'en rajoute pas, ni que t'en enleve.
Si c'est vide, cela doit être vide, donc si il faut lister tous les accesoires et mettre "0", fait le car je veux voir tous les champs du JSON.
Ne répète pas les mêmes informations inutilement. Chaque champ doit être renseigné **une seule fois** et correctement associé.


JSON template : {json.dumps(json_Description)}
"""
    # Appel à Gemini
    response = client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=[prompt_text, img],
        config={"response_mime_type": "application/json"}
    )

    # Récupérer le JSON généré
    filled_json_text = response.text

    # Nettoyer le JSON si Gemini ajoute des balises
    if filled_json_text.startswith("```json") and filled_json_text.endswith("```"):
        filled_json_text = filled_json_text.strip("`").lstrip("json\n")

    # Convertir en objet Python
    try:
        filled_json = json.loads(filled_json_text)
    except json.JSONDecodeError:
        print("Erreur : le texte retourné n'est pas un JSON valide.")
        print("Texte brut :", filled_json_text)
        filled_json = json_template

    return filled_json

if __name__ == "__main__":
    result = analyze_image(PREDICT_IMAGE, json_Description)

    # Afficher le résultat 
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Sauvegarder dans le fichier JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nRésultat sauvegardé dans : {OUTPUT_JSON_PATH}")


# ========================
# Visualisation radar du style vestimentaire
# ========================

def generate_style_scores(image_path, model_name):
    """    Score de 0 à 1 pour chaque style vestimentaire    """
    img = Image.open(image_path)

    prompt_radar = f"""
Tu es un expert en mode et style vestimentaire.
Pour l'image fournie, évalue **la probabilité pour chaque style**.
Les styles sont : Sportif, Décontracté, Streetwear, Urbain, Minimaliste, 
Élégant, Professionnel, Classique, Vintage, Bohème, Avant-garde.
Retourne un JSON où chaque style a une valeur entre 0 et 1 correspondant à sa probabilité.
Ne renvoie que le JSON, sans texte supplémentaire.
"""

    response = client.models.generate_content(
        model=model_name,
        contents=[prompt_radar, img],
        config={"response_mime_type": "application/json"}
    )

    radar_json_text = response.text
    if radar_json_text.startswith("```json") and radar_json_text.endswith("```"):
        radar_json_text = radar_json_text.strip("`").lstrip("json\n")

    try:
        style_scores = json.loads(radar_json_text)
    except json.JSONDecodeError:
        print("Erreur : le texte retourné n'est pas un JSON valide pour le radar.")
        style_scores = {style: 0 for style in all_styles}

    return style_scores

style_scores = generate_style_scores(PREDICT_IMAGE, GEMINI_MODEL_NAME)

labels = list(style_scores.keys())
values = list(style_scores.values())


values += values[:1]  # boucle pour fermer le radar
# Recalcul des angles avec la nouvelle longueur (11 catégories)
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
angles += angles[:1]

# Création du radar
# Augmentation de la taille de la figure (8, 8) et ajustement du padding pour les labels coupés.
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

ax.plot(angles, values, color='green', linewidth=2)
ax.fill(angles, values, color='green', alpha=0.25)

ax.set_xticks(angles[:-1])

# Eviter les chevauchements & éloignement des labels
ax.set_xticklabels(labels, ha='center', size=10) 
ax.tick_params(pad=15)

# Correction de l'alignement des étiquettes
for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
    # Si le label est sur la gauche (entre 90° et 270° / pi/2 et 3pi/2)
    if angle >= np.pi / 2 and angle <= 3 * np.pi / 2:
        label.set_horizontalalignment("right")
    # Si le label est sur la droite (entre 270° et 90°)
    else:
        label.set_horizontalalignment("left")


ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], color='gray', size=9) # Ajustement de la taille de police pour les pourcentages
ax.set_title("Radar des styles vestimentaires (scores)", va='bottom', size=14)

# ========================
# Export du RADAR
# ========================

GRAPH_FILENAME_PREFIX = "Radar_Predict" 
FULL_SAVE_PATH = os.path.join(OUTPUT_GRAPH_DIR, f"{GRAPH_FILENAME_PREFIX}.png")

try:
    fig.savefig(FULL_SAVE_PATH, bbox_inches='tight', dpi=300) 
    print(f"\n✅ Graphique radar sauvegardé : {FULL_SAVE_PATH}")
except Exception as e:
    print(f"\n❌ Erreur lors de la sauvegarde du graphique : {e}")


# ========================
# Couleurs général de l'accoutrement
# ========================

def generate_color_analysis(image_path, model_name):
    """
    Analyse des couleurs dominantes dans la tenue en utilisant Gemini.
    """

    img = Image.open(image_path)

    prompt_colors = """
Tu es un expert en mode et analyse visuelle.
Pour l'image fournie, donne les **couleurs dominantes** du haut, bas, chaussures et accessoires.
FORMAT STRICT (JSON PUR) :
{
  "haut": {
    "Blanc":0,
    "Noir":0,
    "Gris":0,
    "Rouge":0,
    "Bleu":0,
    "Vert":0,
    "Jaune":0,
    "Marron":0,
    "Beige":0,
    "Violet":0,
    "Rose":0,
    "Orange":0,
    "Doré":0,
    "Argenté":0,
    "Bordeaux":0,
    "Turquoise":0
  },
  "bas": { ... mêmes clés ... },
  "chaussures": { ... mêmes clés ... },
  "accessoires": { ... mêmes clés ... }
}

Règles :
- Les pourcentages doivent faire 100% pour chaque catégorie.
- Si une catégorie n’est pas visible : toutes les valeurs = 0%.
- Ne renvoie QUE le JSON, aucun texte autour.
"""
    
    response = client.models.generate_content(
        model=model_name,
        contents=[prompt_colors, img],
        config={"response_mime_type": "application/json"}
    )

    colors_json = response.text.strip()
    colors_json = colors_json.replace("```json", "").replace("```", "").strip()

    try:
        colors_data = json.loads(colors_json)
    except:
        # La gestion de l'erreur est conservée sans afficher d'information inutile
        colors_data = {
            "haut": {"Inconnu": 100},
            "bas": {"Inconnu": 100},
            "chaussures": {"Inconnu": 100},
            "accessoires": {"Inconnu": 100}
        }

    return colors_data



# ========================
# Analyse des couleurs
# ========================

colors_data = generate_color_analysis(PREDICT_IMAGE, GEMINI_MODEL_NAME)

# ========================
# Construction du graphique
# ========================

labels = []
values = []
bar_colors = []

# Palette élargie
palette = {
    "Noir": "#000000",
    "Blanc": "#FFFFFF",
    "Bleu": "#1f77b4",
    "Rouge": "#d62728",
    "Vert": "#2ca02c",
    "Gris": "#7f7f7f",
    "Jaune": "#ffdd00",
    "Orange": "#ff7f0e",
    "Marron": "#8b4513",
    "Violet": "#9467bd",
    "Rose": "#ff69b4",
    "Beige": "#f5f5dc",
    "Doré": "#d4af37",
    "Argenté": "#c0c0c0",
    "Bordeaux": "#800020",
    "Turquoise": "#40e0d0"
}
category_order = ["haut", "bas", "chaussures", "accessoires"]
category_labels_display = [c.capitalize() for c in category_order] # Pour l'affichage sur l'axe Y

# Les données pour les barres empilées doivent être sous forme de dictionnaires pour Matplotlib
# { couleur: [pct_haut, pct_bas, pct_chaussures, pct_accessoires] }
plot_data = {} 

# Initialisation pour toutes les couleurs possibles avec des zéros
all_colors_list = list(palette.keys())

for color_name in all_colors_list:
    plot_data[color_name] = [0] * len(category_order)

# Remplir plot_data avec les pourcentages réels
for i, category in enumerate(category_order):
    color_dict = colors_data.get(category, {})
    sorted_colors = sorted(color_dict.items(), key=lambda item: item[1], reverse=True)
    
    for color, pct in sorted_colors:
        if pct > 0 and color != "Inconnu" and color in plot_data: # S'assurer que la couleur est dans notre palette
            plot_data[color][i] = pct

# Retirer les couleurs qui sont à 0% partout pour ne pas encombrer la légende
plot_data = {color: pcts for color, pcts in plot_data.items() if any(p > 0 for p in pcts)}


# ========================
# Affichage (Graphique en barres empilées)
# ========================

fig, ax = plt.subplots(figsize=(10, 8))

# Créer les barres empilées
bottom = np.zeros(len(category_order)) # Piste pour empiler les barres

for color_name, percentages in plot_data.items():
    if any(p > 0 for p in percentages): # N'afficher que les couleurs qui ont une contribution
        ax.barh(
            category_labels_display,
            percentages,
            left=bottom, # Position de départ de la barre
            height=0.6, # Épaisseur des barres
            label=color_name, # Pour la légende
            color=palette.get(color_name, "#999999") # Couleur de la palette
        )
        bottom += np.array(percentages) # Mise à jour de la base pour la prochaine couleur

# Ajout des étiquettes de pourcentage sur les barres
# Ce n'est pas trivial pour les barres empilées, nous allons simplifier pour les totaux si besoin
# Ou itérer sur chaque segment :
for i, category_label in enumerate(category_labels_display):
    current_offset = 0
    for color_name, percentages in plot_data.items():
        pct = percentages[i]
        if pct > 0:
            # Positionnement du texte au centre du segment
            text_x_position = current_offset + pct / 2
            ax.text(text_x_position, i, f'{pct:.0f}%', va='center', ha='center',
                    color='black', fontsize=9, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
            current_offset += pct


ax.set_xlabel("Pourcentage (%)")
ax.set_title("Couleurs dominantes de la tenue par catégorie")
ax.set_xlim(0, 100) # Les pourcentages vont de 0 à 100
ax.invert_yaxis() # Pour avoir "Haut" en haut

ax.legend(title="Couleurs", bbox_to_anchor=(1.05, 1), loc='upper left') # Légende à droite
plt.tight_layout()

# ========================
# Sauvegarde du graphique
# ========================

GRAPH_FILENAME_PREFIX = "Couleurs_Predict"
FULL_SAVE_PATH = os.path.join(OUTPUT_GRAPH_DIR, f"{GRAPH_FILENAME_PREFIX}.png")

try:
    fig.savefig(FULL_SAVE_PATH, bbox_inches='tight', dpi=300)
    print(f"\n✅ Graphique couleurs sauvegardé : {FULL_SAVE_PATH}")
except Exception as e:
    print(f"\n❌ Erreur lors de la sauvegarde : {e}")

