"""
Dataset Splitter for Football Shot Classification
Splits images into train/validation/test folders
"""

import os
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split
import random

# Set random seed for reproducibility
random.seed(42)

def split_dataset(source_dir, output_dir, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    """
    Split dataset into train/validation/test
    
    Args:
        source_dir: Directory with shot type folders (e.g., 'shot_types')
        output_dir: Output directory name (e.g., 'dataset')
        train_ratio: Percentage for training (default 70%)
        val_ratio: Percentage for validation (default 20%)
        test_ratio: Percentage for testing (default 10%)
    """
    
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    # Check if source exists
    if not source_path.exists():
        print(f"Error: Source directory '{source_dir}' not found!")
        print(f"Please provide the correct path to your shot_types folder")
        return
    
    # Shot types to process
    shot_types = [
        'Backheel',
        'Bicycle_Kick',
        'Chip_Shot',
        'Curved_Shot',
        'Drive',
        'Header',
        'Knuckleball',
        'Rabona',
        'Volley'
    ]
    
    # Create output directories
    print("=" * 70)
    print("DATASET SPLITTING")
    print("=" * 70)
    print(f"Source: {source_path.absolute()}")
    print(f"Output: {output_path.absolute()}")
    print(f"Split: {train_ratio*100}% train, {val_ratio*100}% val, {test_ratio*100}% test")
    print("=" * 70)
    
    for split in ['train', 'validation', 'test']:
        (output_path / split).mkdir(parents=True, exist_ok=True)
    
    total_images = 0
    split_summary = []
    
    # Process each shot type
    for shot_type in shot_types:
        source_folder = source_path / shot_type
        
        # Check if folder exists
        if not source_folder.exists():
            print(f"\nWarning: '{shot_type}' folder not found, skipping...")
            continue
        
        # Get all images (jpg, png, jpeg)
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            images.extend(list(source_folder.glob(ext)))
        
        if len(images) == 0:
            print(f"\nWarning: No images found in '{shot_type}', skipping...")
            continue
        
        print(f"\n{shot_type}:")
        print(f"  Found: {len(images)} images")
        
        # Check minimum images
        if len(images) < 10:
            print(f"  WARNING: Only {len(images)} images - need at least 10 for good training!")
        
        # Split dataset
        # First split: separate test set
        train_val_imgs, test_imgs = train_test_split(
            images, 
            test_size=test_ratio,
            random_state=42
        )
        
        # Second split: separate train and validation
        val_size = val_ratio / (train_ratio + val_ratio)
        train_imgs, val_imgs = train_test_split(
            train_val_imgs,
            test_size=val_size,
            random_state=42
        )
        
        # Create class folders in each split
        for split in ['train', 'validation', 'test']:
            (output_path / split / shot_type).mkdir(parents=True, exist_ok=True)
        
        # Copy images to respective folders
        for img in train_imgs:
            dest = output_path / 'train' / shot_type / img.name
            shutil.copy2(img, dest)
        
        for img in val_imgs:
            dest = output_path / 'validation' / shot_type / img.name
            shutil.copy2(img, dest)
        
        for img in test_imgs:
            dest = output_path / 'test' / shot_type / img.name
            shutil.copy2(img, dest)
        
        # Summary
        print(f"  Split: {len(train_imgs)} train | {len(val_imgs)} val | {len(test_imgs)} test")
        
        split_summary.append({
            'shot_type': shot_type,
            'total': len(images),
            'train': len(train_imgs),
            'val': len(val_imgs),
            'test': len(test_imgs)
        })
        
        total_images += len(images)
    
    # Print final summary
    print("\n" + "=" * 70)
    print("SPLIT SUMMARY")
    print("=" * 70)
    
    if split_summary:
        print(f"\n{'Shot Type':<20} {'Total':<10} {'Train':<10} {'Val':<10} {'Test':<10}")
        print("-" * 70)
        
        total_train = 0
        total_val = 0
        total_test = 0
        
        for item in split_summary:
            print(f"{item['shot_type']:<20} {item['total']:<10} {item['train']:<10} {item['val']:<10} {item['test']:<10}")
            total_train += item['train']
            total_val += item['val']
            total_test += item['test']
        
        print("-" * 70)
        print(f"{'TOTAL':<20} {total_images:<10} {total_train:<10} {total_val:<10} {total_test:<10}")
        
        print("\n" + "=" * 70)
        print("Dataset split complete!")
        print(f"Output directory: {output_path.absolute()}")
        print("=" * 70)
        
        # Check if dataset is sufficient
        if total_images < 500:
            print("\nWARNING: Small dataset detected!")
            print(f"  Total images: {total_images}")
            print("  Recommendation: At least 500-1000 images for good results")
            print("  Consider data augmentation during training")
    else:
        print("\nError: No images were processed!")
        print("Please check:")
        print("  1. Source directory path is correct")
        print("  2. Shot type folder names match expected names")
        print("  3. Images are in JPG/PNG format")


if __name__ == "__main__":
    # CONFIGURE THESE PATHS
    # =====================
    
    # Path to your current shot_types folder
    # Example: "Downloads/shot_types-20250104T150800Z-1-001/shot_types"
    SOURCE_DIRECTORY = "Dataset/shot_types"  # Change this to your actual path
    
    # Output dataset directory
    OUTPUT_DIRECTORY = "dataset"
    
    # Split ratios (must sum to 1.0)
    TRAIN_RATIO = 0.7   # 70% for training
    VAL_RATIO = 0.2     # 20% for validation
    TEST_RATIO = 0.1    # 10% for testing
    
    # =====================
    
    print("\nDataset Splitter for Football Shot Classification")
    print("=" * 70)
    
    # Check if source exists
    if not Path(SOURCE_DIRECTORY).exists():
        print(f"\nError: Source directory '{SOURCE_DIRECTORY}' not found!")
        print("\nPlease update SOURCE_DIRECTORY in the script to point to your shot_types folder")
        print("Example: SOURCE_DIRECTORY = 'Downloads/shot_types-20250104T150800Z-1-001/shot_types'")
    else:
        # Run the split
        split_dataset(
            source_dir=SOURCE_DIRECTORY,
            output_dir=OUTPUT_DIRECTORY,
            train_ratio=TRAIN_RATIO,
            val_ratio=VAL_RATIO,
            test_ratio=TEST_RATIO
        )
