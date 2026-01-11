# config.py

# ==========================
#  Clés API
# ==========================
GOOGLE_GEMINI_API_KEY = "AIzaSyCkyCH_2SjSWq9XVqeqZ29dAoG_80e896Q"

# ==========================
#  Chemins locaux
# ==========================
BASE_PATH = r"C:\Users\Ivin\Documents\SmartWear\BaseDeDonnee"
PREDICT_IMAGE = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Insert\Image4.png"
OUTPUT_JSON_PATH = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result\BDD.json"
OUTPUT_GRAPH_DIR = r"C:\Users\Ivin\Documents\SmartWear\Prediction\Result"

# ==========================
#  Paramètres image / IA
# ==========================
RESNET_FEATURE_SIZE = 2048
BLIP_MODEL_NAME = "Salesforce/blip-image-captioning-base"
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# ==========================
#  Template JSON pour chaque image
# ==========================
json_Description = {
    "Genre": None,
    "Couleur de peau": None,
    "Couleur des cheveux":None,
    "Age_estimé": None,
    "Saison_de_l'accoutrement": None,
    "Style de l'accoutrement":None,
    "Estimation_Prix":None,
    "Haut": {
        "Nombre_De_Pieces": None,
        "Type": None,
        "Couleur": None,
        "Teinte": None,
        "Taille estimée": None,
        "Marque": None,
        "Style": None
    },

    "Bas": {
        "Nombre_De_Pieces": None,
        "Type":None,
        "Couleur": None,
        "Teinte": None,
        "Taille estimée": None,
        "Marque": None,
        "Style": None
    },
    "Chaussures": {
        "Présent": None,
        "Couleur": None,
        "Teinte": None,
        "Taille estimée": None,
        "Marque": None,
        "Style": None
    },
    "Accessoires": {
    "Présent": None,
    "Animal": None,
    "NombreAccessoire":None,
    "Style_Général":None,
    "Couleur_Global":None,
    "Chapeau": None,
    "Casquette": None,
    "Lunettes de soleil": None,
    "Lunettes de vue": None,
    "Téléphone": None,
    "Écharpe": None,
    "Foulard": None,
    "Montre": None,
    "Bracelet": None,
    "Collier": None,
    "Boucles d’oreilles": None,
    "Ceinture": None,
    "Sac à main": None,
    "Sac à dos": None,
    "Gants": None,
    "Bague": None,
    "Broche": None,
    "Porte-clés": None,
    "Chaussettes fantaisie": None,
    "Cravate": None,
    "Noeud papillon": None,
    "Masque": None
    }
}

# ==========================
#  Packages pour le projet
# ==========================

import os                       # Gestion des chemins et fichiers
import h5py                     # Lecture des fichiers HDF5 (dataset)
import numpy as np              # Manipulation des tableaux / matrices
import matplotlib.pyplot as plt # Visualisation pour des graphiques
from PIL import Image           # Gestion / conversion d'images
from wordcloud import WordCloud # Nuage de Point

# ==========================
#  OPENAI
# ==========================

from google import genai        # IA Gemini

# ==========================
#  TensorFlow / Keras
# ==========================
import tensorflow as tf
from tensorflow.keras.applications import resnet50   # Modèle ResNet50 pour features
from tensorflow.keras.preprocessing import image     # Prétraitement des images

# ==========================
#  Scikit-learn
# ==========================
from sklearn.neighbors import KNeighborsClassifier  # KNN pour classification
from sklearn.ensemble import RandomForestClassifier # Random Forest

# ==========================
#  Transformers / BLIP / HF
# ==========================
import torch                     # PyTorch requis pour Hugging Face
from transformers import BlipProcessor, BlipForConditionalGeneration
from transformers import pipeline  # Pour génération de texte / JSON

# ==========================
#  Utilitaires
# ==========================

import json                      # Pour sauvegarder le JSON
import requests                  # Pour appeler une API externe (Gemini Pro)
from tqdm import tqdm            # Barres de progression

# ==========================
#  API & Scrapping
# ==========================

import base64
from bs4 import BeautifulSoup