# Étapes à exécuter dans Google Colab

Conformément à l'analyse du document `projet.txt` et au style de travail asynchrone défini (utilisation de Google Drive pour les datasets et exécution de scripts Python via Git), voici les cellules à intégrer et exécuter séquentiellement dans votre notebook Google Colab.

## Étape 1 : Préparation du Dataset
Le dossier public contient de nombreuses images, ce qui dépasse la limite de téléchargement direct de `gdown`. La méthode la plus fiable est d'utiliser un **raccourci Google Drive**.

### 1.1 Actions manuelles (une seule fois)
1. Ouvrez ce lien : [Dossier Public Datasets](https://drive.google.com/drive/folders/15HDXEEJoFNACdo1iURfiFQO4r_miKynq?usp=sharing)
2. Cliquez sur le titre **"datasets"** en haut de la page.
3. Choisissez **"Ajouter un raccourci dans Drive"** et sélectionnez **"Mon Drive"**.

### 1.2 Exécution dans Colab
Une fois le raccourci ajouté, exécutez ces cellules pour copier et préparer les données.

```python
# 1. Monter votre Google Drive
from google.colab import drive
drive.mount('/content/drive')

# 2. Cloner le projet Git (si nécessaire)
# !git clone <URL_DU_REPO> /content/projet_dermato_ia
# %cd /content/projet_dermato_ia

# 3. Préparer le dataset (Copie + Renommage + Indexation)
# On utilise le chemin vers le raccourci dans votre Drive
!python scripts/01_prepare_dataset.py \
    --source "/content/drive/MyDrive/datasets" \
    --output "/content/datasets"
```

> [!NOTE]
> Cette méthode est beaucoup plus rapide et stable car elle utilise l'infrastructure interne de Google pour copier les fichiers.

## Étape 2 : Cloner le projet Git (Code source)
Récupérer les scripts Python du projet qui vont orchestrer le pipeline de données et l'entraînement.

```bash
# Remplacer <URL_DU_REPO> par le lien GitHub ou GitLab de votre projet
!git clone <URL_DU_REPO> /content/projet_dermato_ia

# Se positionner dans le répertoire du projet
%cd /content/projet_dermato_ia

# Installer d'éventuelles dépendances manquantes (OpenCV, Tensorflow, etc.)
!pip install -r requirements.txt
```

---

## Étape 3 : Exécution des scripts - Phase 1 & 2 (Préparation des données)

### 3.1 Renommage et Indexation (selon point 1.2 du projet)
Ce script Python va lire les dossiers des maladies (`Leprosy`, `mpox`, `Scabies`, etc.) depuis le Drive, et renommer/indexer les images correctement.

```bash
# On suppose que le script s'appelle 01_prepare_dataset.py
!python scripts/01_prepare_dataset.py \
    --dataset_path "/content/drive/MyDrive/datasets"
```

### 3.2 Nettoyage et Data Augmentation (selon point 2.1 & 2.2)
Ce script gère le nettoyage automatisé via OpenCV (détection de flou, suppression de doublons, recadrage) et la configuration de l'augmentation de données.

```bash
!python scripts/02_data_pipeline.py \
    --input_dir "/content/drive/MyDrive/datasets" \
    --output_dir "/content/drive/MyDrive/datasets_processed"
```

---

## Étape 4 : Exécution du script - Phase 3 (Entraînement de l'IA)
Entraînement du modèle optimisé pour mobile (EfficientNet ou MobileNetV3) sur les données nettoyées, puis conversion automatique au format TensorFlow Lite (`.tflite`).

```bash
# Lancement de l'entraînement
!python scripts/03_train_model.py \
    --data_dir "/content/drive/MyDrive/datasets_processed" \
    --epochs 50 \
    --batch_size 32 \
    --model_type "MobileNetV3"
```

## Étape 5 : Sauvegarde des résultats
Une fois le modèle entraîné et converti (.tflite), on le sauvegarde sur Google Drive pour pouvoir l'intégrer facilement à l'application Flutter.

```bash
!cp /content/projet_dermato_ia/models/modele_cutanee.tflite "/content/drive/MyDrive/modele_cutanee.tflite"

# (Optionnel) Sauvegarder également les graphiques de performances (Loss/Accuracy)
!cp /content/projet_dermato_ia/logs/*.png "/content/drive/MyDrive/"
```
