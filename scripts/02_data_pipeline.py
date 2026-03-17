import os
import cv2
import hashlib
import numpy as np
import argparse
import shutil
from tqdm import tqdm

def get_image_hash(image_path):
    """Generates a dHash for the image to detect duplicates."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            return None
        # Resize to 9x8 and grayscale
        resized = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (9, 8), interpolation=cv2.INTER_AREA)
        # Compute horizontal gradients
        diff = resized[:, 1:] > resized[:, :-1]
        return hashlib.md5(diff).hexdigest()
    except Exception as e:
        print(f"Error hashing {image_path}: {e}")
        return None

def is_blurry(image_path, threshold=100.0):
    """Detects if an image is blurry using the Laplacian variance."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            return True, 0
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        return fm < threshold, fm
    except Exception as e:
        return True, 0

def process_dataset(input_dir, output_dir, blur_threshold=100.0, target_size=(224, 224)):
    """Main pipeline to clean and prepare images."""
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        print("Please check your --input_dir path (e.g., '/content/datasets' or '/content/drive/MyDrive/datasets')")
        return

    # Subdirectories (classes)
    classes = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d)) and not d.startswith('.')]
    
    hashes = set()
    stats = {"total": 0, "blurry": 0, "duplicate": 0, "saved": 0}

    for cls in classes:
        print(f"\nProcessing class: {cls}")
        cls_input = os.path.join(input_dir, cls)
        cls_output = os.path.join(output_dir, cls)
        os.makedirs(cls_output, exist_ok=True)
        
        # Folder for rejected images (optional check)
        cls_rejected = os.path.join(output_dir, "rejected", cls)
        os.makedirs(cls_rejected, exist_ok=True)

        images = [f for f in os.listdir(cls_input) if os.path.isfile(os.path.join(cls_input, f))]
        
        for img_name in tqdm(images):
            stats["total"] += 1
            img_path = os.path.join(cls_input, img_name)
            
            # 1. Blur Detection
            blurry, score = is_blurry(img_path, blur_threshold)
            if blurry:
                stats["blurry"] += 1
                shutil.copy(img_path, os.path.join(cls_rejected, f"blurry_{img_name}"))
                continue

            # 2. Duplicate Detection
            h = get_image_hash(img_path)
            if h in hashes:
                stats["duplicate"] += 1
                continue
            hashes.add(h)

            # 3. Preprocessing (Resize/Crop)
            try:
                img = cv2.imread(img_path)
                # Simple Resize (center crop logic could be added here)
                # For medical images, often a simple resize to square is used first
                final_img = cv2.resize(img, target_size, interpolation=cv2.INTER_LANCZOS4)
                
                output_path = os.path.join(cls_output, img_name)
                cv2.imwrite(output_path, final_img)
                stats["saved"] += 1
            except Exception as e:
                print(f"Error processing {img_name}: {e}")

    print("\n--- Pipeline Results ---")
    print(f"Total processed: {stats['total']}")
    print(f"Blurry removed : {stats['blurry']}")
    print(f"Duplicates     : {stats['duplicate']}")
    print(f"Final images   : {stats['saved']}")
    print(f"Results saved in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and Pipeline Dataset")
    parser.add_argument("--input_dir", type=str, required=True, help="Input dataset directory")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for cleaned data")
    parser.add_argument("--blur_threshold", type=float, default=100.0, help="Threshold for blur detection (lower = more permissive)")
    parser.add_argument("--size", type=int, default=224, help="Target image size (e.g. 224 for MobileNet)")

    args = parser.parse_args()
    process_dataset(args.input_dir, args.output_dir, args.blur_threshold, (args.size, args.size))
