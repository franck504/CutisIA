# Étapes à exécuter dans Google Colab

Voici les cellules à intégrer et exécuter séquentiellement dans votre notebook Google Colab.

## Étape 0 : Environnement & Authentification
Cette étape permet d'accéder à vos ressources Google Drive et de récupérer votre code source depuis GitHub.

### 0.1 Connexion au Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
```

### 0.2 Récupération du Projet (GitHub)
```bash
# On se place dans /content/ et on récupère le code
%cd /content/
!rm -rf CutisIA
!git clone https://github.com/franck504/CutisIA.git

# Se positionner dans le répertoire du projet pour les scripts suivants
%cd CutisIA
```

---

## Étape 1 : Préparation du Dataset
Vous avez deux options pour préparer vos images. La méthode "Directe" est plus simple, la méthode "Copie Locale" est plus rapide pour l'entraînement.

### Option A : Travailler directement sur Google Drive (Plus simple)
Utilisez cette option si vous voulez renommer les fichiers directement dans votre Drive sans faire de copie.
*Note : Le renommage de milliers de fichiers sur Drive peut prendre quelques minutes.*

```python
# On lance le script directement sur le dossier du Drive
!python scripts/01_prepare_dataset.py \
    --output "/content/drive/MyDrive/datasets" \
    --skip_download
```

### Option B : Copie locale dans Colab (Plus rapide pour l'entraînement)
Utilisez cette option pour copier les images dans la mémoire de Colab. C'est recommandé pour accélérer l'entraînement de l'IA.

```python
# Ce script copie depuis votre Drive vers /content/datasets et prépare tout
!python scripts/01_prepare_dataset.py \
    --source "/content/drive/MyDrive/datasets" \
    --output "/content/datasets"
```

---

## Étape 2 : Nettoyage et Pipeline (OpenCV)
Cette étape filtre les images floues, supprime les doublons et redimensionne les images en **224x224**.

### Cas 1 : Si vous avez utilisé l'Option A (Direct Drive)
```python
!python scripts/02_data_pipeline.py \
    --input_dir "/content/drive/MyDrive/datasets" \
    --output_dir "/content/datasets_processed" \
    --blur_threshold 100.0
```

### Cas 2 : Si vous avez utilisé l'Option B (Copie Locale)
```python
!python scripts/02_data_pipeline.py \
    --input_dir "/content/datasets" \
    --output_dir "/content/datasets_processed" \
    --blur_threshold 100.0
```

> [!TIP]
> Les images traitées sont sauvegardées dans `/content/datasets_processed`.
> Les images floues rejetées sont dans `/content/datasets_processed/rejected/`.

---

## Étape 3 : Entraînement de l'IA
Entraînement du modèle optimisé pour mobile (MobileNetV3) et conversion automatique au format TensorFlow Lite (`.tflite`).

```python
!python scripts/03_train_model.py \
    --data_dir "/content/datasets_processed" \
    --epochs 50 \
    --batch_size 32 \
    --model_type "MobileNetV3"
```

---

## Étape 4 : Sauvegarde des Résultats
Sauvegarde du modèle final sur votre Google Drive pour une utilisation permanente.

```bash
# Créer un dossier sur le Drive s'il n'existe pas
!mkdir -p "/content/drive/MyDrive/CutisIA_Models"

# Copier le modèle converti
!cp /content/CutisIA/models/modele_cutanee.tflite "/content/drive/MyDrive/CutisIA_Models/modele_cutanee.tflite"

# (Optionnel) Sauvegarder les graphiques de performances
!cp /content/CutisIA/logs/*.png "/content/drive/MyDrive/CutisIA_Models/"
```
