import os
import argparse
import shutil
import gdown

def copy_from_drive(source_path, target_path):
    """
    Copies a directory from a mounted Google Drive path to a target path.
    """
    if not os.path.exists(source_path):
        print(f"Error: Source path {source_path} does not exist.")
        print("Please ensure you have mounted your Google Drive and the shortcut is correctly placed.")
        return False
    
    if os.path.exists(target_path):
        print(f"Target path {target_path} already exists. Skipping copy.")
        return True
    
    print(f"Copying dataset from {source_path} to {target_path}...")
    shutil.copytree(source_path, target_path)
    print("Copy complete.")
    return True

def download_from_drive(url, output_path):
    """
    Downloads the dataset from a public Google Drive link using gdown.
    Note: Limited to 50 files for folders.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    folder_id = url.split('/')[-1].split('?')[0]
    print(f"Attempting to download dataset from Google Drive folder ID: {folder_id}...")
    try:
        gdown.download_folder(id=folder_id, output=output_path, quiet=False, use_cookies=False)
    except Exception as e:
        print(f"Error downloading folder: {e}")
        print("Recommendation: Use the Google Drive Shortcut method for folders with many files.")
        return False
    return True

def rename_and_index_images(dataset_path):
    """
    Renames images in each subfolder: disease_name_001.ext
    """
    if not os.path.exists(dataset_path):
        print(f"Error: Path {dataset_path} does not exist.")
        return

    classes = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]
    
    total_processed = 0
    for cls in classes:
        cls_path = os.path.join(dataset_path, cls)
        images = sorted([f for f in os.listdir(cls_path) if os.path.isfile(os.path.join(cls_path, f))])
        
        print(f"Processing class: {cls} ({len(images)} images)")
        
        for i, img_name in enumerate(images):
            ext = os.path.splitext(img_name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
                continue
                
            new_name = f"{cls}_{i+1:03d}{ext}"
            old_path = os.path.join(cls_path, img_name)
            new_path = os.path.join(cls_path, new_name)
            
            if old_path != new_path:
                os.rename(old_path, new_path)
                total_processed += 1
    
    print(f"Renaming complete. {total_processed} images indexed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and Prepare Dataset for Training")
    parser.add_argument("--url", type=str, default="https://drive.google.com/drive/folders/15HDXEEJoFNACdo1iURfiFQO4r_miKynq?usp=sharing", help="Public Google Drive folder URL")
    parser.add_argument("--source", type=str, help="Path to the dataset in your mounted Google Drive (shortcut)")
    parser.add_argument("--output", type=str, default="/content/datasets", help="Local directory to store dataset in Colab")
    parser.add_argument("--skip_download", action="store_true", help="Skip download/copy and only rename files")
    
    args = parser.parse_args()

    if not args.skip_download:
        if args.source:
            success = copy_from_drive(args.source, args.output)
        else:
            success = download_from_drive(args.url, args.output)
        
        if not success:
            exit(1)
    
    rename_and_index_images(args.output)
    print("Dataset preparation complete.")
