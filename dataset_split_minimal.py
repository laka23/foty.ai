"""
Minimal Dataset Splitter - Works with small datasets
FOR TESTING PURPOSES ONLY - Not recommended for production
"""

import os
import shutil
from pathlib import Path
import random

random.seed(42)

def split_small_dataset(source_dir, output_dir):
    """
    Split dataset even with few images per class
    Minimum 3 images required per class
    """
    
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    if not source_path.exists():
        print(f"Error: Source directory '{source_dir}' not found!")
        return
    
    shot_types = [
        'Backheel', 'Bicycle_Kick', 'Chip_Shot', 'Curved_Shot',
        'Drive', 'Header', 'Knuckleball', 'Rabona', 'Volley'
    ]
    
    print("=" * 70)
    print("MINIMAL DATASET SPLITTING (FOR TESTING ONLY)")
    print("=" * 70)
    print(f"Source: {source_path.absolute()}")
    print(f"Output: {output_path.absolute()}")
    print("=" * 70)
    print("WARNING: This will create a very small dataset!")
    print("         Training accuracy will be LOW")
    print("         Use only for testing the pipeline")
    print("=" * 70)
    
    for split in ['train', 'validation', 'test']:
        (output_path / split).mkdir(parents=True, exist_ok=True)
    
    split_summary = []
    
    for shot_type in shot_types:
        source_folder = source_path / shot_type
        
        if not source_folder.exists():
            print(f"\n{shot_type}: Folder not found, skipping...")
            continue
        
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            images.extend(list(source_folder.glob(ext)))
        
        if len(images) == 0:
            print(f"\n{shot_type}: No images found, skipping...")
            continue
        
        print(f"\n{shot_type}: Found {len(images)} images")
        
        # Create folders
        for split in ['train', 'validation', 'test']:
            (output_path / split / shot_type).mkdir(parents=True, exist_ok=True)
        
        # Shuffle images
        random.shuffle(images)
        
        # Smart split based on available images
        if len(images) < 3:
            print(f"  ERROR: Need minimum 3 images, skipping...")
            continue
        elif len(images) <= 5:
            # Very few images: 60% train, 20% val, 20% test (minimum 1 each)
            train_count = max(1, int(len(images) * 0.6))
            val_count = max(1, int(len(images) * 0.2))
            test_count = len(images) - train_count - val_count
            
            if test_count < 1:
                train_count = len(images) - 2
                val_count = 1
                test_count = 1
        elif len(images) <= 10:
            # Few images: 60% train, 30% val, 10% test
            train_count = max(2, int(len(images) * 0.6))
            val_count = max(1, int(len(images) * 0.3))
            test_count = len(images) - train_count - val_count
        else:
            # Normal split: 70% train, 20% val, 10% test
            train_count = int(len(images) * 0.7)
            val_count = int(len(images) * 0.2)
            test_count = len(images) - train_count - val_count
        
        # Split images
        train_imgs = images[:train_count]
        val_imgs = images[train_count:train_count + val_count]
        test_imgs = images[train_count + val_count:]
        
        # Copy files
        for img in train_imgs:
            shutil.copy2(img, output_path / 'train' / shot_type / img.name)
        
        for img in val_imgs:
            shutil.copy2(img, output_path / 'validation' / shot_type / img.name)
        
        for img in test_imgs:
            shutil.copy2(img, output_path / 'test' / shot_type / img.name)
        
        print(f"  Split: {len(train_imgs)} train | {len(val_imgs)} val | {len(test_imgs)} test")
        
        split_summary.append({
            'shot_type': shot_type,
            'total': len(images),
            'train': len(train_imgs),
            'val': len(val_imgs),
            'test': len(test_imgs)
        })
    
    # Final summary
    print("\n" + "=" * 70)
    print("SPLIT SUMMARY")
    print("=" * 70)
    
    if split_summary:
        print(f"\n{'Shot Type':<20} {'Total':<10} {'Train':<10} {'Val':<10} {'Test':<10}")
        print("-" * 70)
        
        total_all = 0
        total_train = 0
        total_val = 0
        total_test = 0
        
        for item in split_summary:
            print(f"{item['shot_type']:<20} {item['total']:<10} {item['train']:<10} {item['val']:<10} {item['test']:<10}")
            total_all += item['total']
            total_train += item['train']
            total_val += item['val']
            total_test += item['test']
        
        print("-" * 70)
        print(f"{'TOTAL':<20} {total_all:<10} {total_train:<10} {total_val:<10} {total_test:<10}")
        print("=" * 70)
        
        print("\nDataset split complete!")
        print(f"Classes processed: {len(split_summary)}")
        
        if total_all < 100:
            print("\n" + "!" * 70)
            print("CRITICAL WARNING: Dataset is TOO SMALL!")
            print("!" * 70)
            print(f"Total images: {total_all}")
            print("Recommendations:")
            print("  1. This is only for TESTING the training pipeline")
            print("  2. Model accuracy will be VERY LOW (< 30%)")
            print("  3. Collect at least 50-100 images per class for real use")
            print("  4. Use data augmentation (already enabled in training)")
            print("!" * 70)
        
        # Save processed classes to config
        processed_classes = [item['shot_type'] for item in split_summary]
        config_note = f"""
# Update your config.py with these classes:
SHOT_CLASSES = {processed_classes}
NUM_CLASSES = {len(processed_classes)}
        """
        print(config_note)
        
    else:
        print("\nError: No valid classes found!")


if __name__ == "__main__":
    # CONFIGURE PATHS
    SOURCE_DIRECTORY = "Dataset/shot_types"
    OUTPUT_DIRECTORY = "dataset"
    
    print("\nMinimal Dataset Splitter")
    print("For testing purposes only - works with small datasets\n")
    
    if not Path(SOURCE_DIRECTORY).exists():
        print(f"Error: '{SOURCE_DIRECTORY}' not found!")
        print("Please update SOURCE_DIRECTORY path in the script")
    else:
        split_small_dataset(SOURCE_DIRECTORY, OUTPUT_DIRECTORY)
