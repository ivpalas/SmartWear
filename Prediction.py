import os
import h5py
import numpy as np
from tqdm import tqdm
from tensorflow.keras.applications import resnet50
from tensorflow.keras.preprocessing import image
from sklearn.neighbors import KNeighborsClassifier

# --- Chemins ---
BASE_PATH = r"C:\Users\Ivin\Documents\SmartWear\BaseDeDonnee"
PREDICT_IMAGE = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Image1.png"
TRAIN_FILE = os.path.join(BASE_PATH, "fashiongen_256_256_train.h5")

# --- Informations sur le dataset ---
print("📂 Lecture du fichier HDF5...")
with h5py.File(TRAIN_FILE, "r") as f:
    keys = list(f.keys())
    print(f"Clés disponibles ({len(keys)}): {keys}")
    total_images = f["input_image"].shape[0]
    print(f"➡️ Nombre total d'images disponibles : {total_images}")

# --- Chargement du dataset ---
SAMPLE_SIZE = 10000  # tu peux monter à 20000 si ta RAM le permet
print(f"\nChargement des {SAMPLE_SIZE} premiers échantillons...")
with h5py.File(TRAIN_FILE, "r") as f:
    images = f["input_image"][:SAMPLE_SIZE]
    
    # Attributs textuels pertinents uniquement
    valid_keys = [
        "input_brand", "input_category", "input_department",
        "input_gender", "input_season", "input_subcategory"
    ]
    attributes = {}
    for key in valid_keys:
        dataset = f[key][:SAMPLE_SIZE]
        attributes[key] = np.array([
            d[0].decode('utf-8', errors='ignore') if isinstance(d[0], bytes) else str(d[0])
            for d in dataset
        ])

print("✅ Dataset chargé avec succès.")

# --- Extraction des features avec ResNet50 ---
print("\n🧠 Extraction des features avec ResNet50...")
model = resnet50.ResNet50(weights="imagenet", include_top=False, pooling='avg')

def extract_features(img_array):
    img_resized = image.array_to_img(img_array).resize((224, 224))
    x = np.expand_dims(np.array(img_resized), axis=0)
    x = resnet50.preprocess_input(x)
    return model.predict(x, verbose=0)

features = []
for img in tqdm(images, desc="Extraction des features", ncols=80):
    features.append(extract_features(img))
features = np.vstack(features)

# --- Entraînement des modèles ---
def train_knn(targets):
    knn = KNeighborsClassifier(n_neighbors=3)
    knn.fit(features, targets)
    return knn

print("\n🔧 Entraînement des modèles pour chaque attribut...")
classifiers = {}
for key, values in tqdm(attributes.items(), desc="Entraînement", ncols=80):
    classifiers[key] = train_knn(values)

# --- Prédiction sur ton image ---
print("\n🖼️ Prédiction sur ton image...")
img = image.load_img(PREDICT_IMAGE, target_size=(256, 256))
img_array = image.img_to_array(img)
img_features = extract_features(img_array)

# --- Résultats ---
predictions = {}
for key, clf in classifiers.items():
    predictions[key] = clf.predict(img_features)[0]

print("\n🎯 PRÉDICTIONS POUR TON IMAGE :")
for k, v in predictions.items():
    print(f"{k} : {v}")

print("\n✅ Exécution terminée.")