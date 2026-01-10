

import os
import sys
import shutil
import random
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================
print("="*70)
print("FOOTBALL SHOT CLASSIFIER - COMPLETE TRAINING SCRIPT")
print("="*70)

# Paths - UPDATE THESE
WORKING_DIR = '/content/drive/MyDrive/football_ai'
SOURCE_DATA_DIR = '/content/drive/MyDrive/football_ai/shot_types'

# Training parameters
IMG_HEIGHT = 224
IMG_WIDTH = 224
BATCH_SIZE = 8
EPOCHS = 30
LEARNING_RATE = 0.0001

# Dataset splits
TRAIN_SPLIT = 0.7
VAL_SPLIT = 0.2
TEST_SPLIT = 0.1

# ============================================================================
# STEP 1: SETUP DIRECTORIES
# ============================================================================
print("\nStep 1: Setting up directories...")

os.chdir(WORKING_DIR)
DATASET_DIR = Path(WORKING_DIR) / 'dataset'
MODELS_DIR = Path(WORKING_DIR) / 'models'
OUTPUTS_DIR = Path(WORKING_DIR) / 'outputs'
CHARTS_DIR = OUTPUTS_DIR / 'charts'

for dir_path in [MODELS_DIR, OUTPUTS_DIR, CHARTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

print(f"Working directory: {WORKING_DIR}")

# ============================================================================
# STEP 2: SCAN DATASET
# ============================================================================
print("\nStep 2: Scanning dataset...")

SOURCE_DIR = Path(SOURCE_DATA_DIR)
valid_classes = []
class_image_counts = {}

if not SOURCE_DIR.exists():
    print(f"ERROR: {SOURCE_DIR} not found!")
    sys.exit(1)

for folder in sorted(os.listdir(SOURCE_DIR)):
    folder_path = SOURCE_DIR / folder
    if os.path.isdir(folder_path):
        images = (list(folder_path.glob('*.jpg')) + 
                 list(folder_path.glob('*.png')) + 
                 list(folder_path.glob('*.jpeg')))
        
        if len(images) > 0:
            valid_classes.append(folder)
            class_image_counts[folder] = len(images)
            print(f"  {folder}: {len(images)} images")

NUM_CLASSES = len(valid_classes)
TOTAL_IMAGES = sum(class_image_counts.values())

print(f"\nFound {NUM_CLASSES} valid classes with {TOTAL_IMAGES} total images")
print(f"Classes: {valid_classes}")

if TOTAL_IMAGES < 20:
    print("\nWARNING: Very small dataset! Results will be poor.")
    print("Recommended: At least 50 images per class (500+ total)")

# ============================================================================
# STEP 3: ORGANIZE DATASET
# ============================================================================
print("\nStep 3: Organizing dataset into train/val/test...")

random.seed(42)

# Clear existing dataset
if DATASET_DIR.exists():
    shutil.rmtree(DATASET_DIR)

# Create folder structure
for split in ['train', 'validation', 'test']:
    for cls in valid_classes:
        (DATASET_DIR / split / cls).mkdir(parents=True, exist_ok=True)

# Copy images with smart splitting
total_train = 0
total_val = 0
total_test = 0

for cls in valid_classes:
    src = SOURCE_DIR / cls
    images = (list(src.glob('*.jpg')) + 
             list(src.glob('*.png')) + 
             list(src.glob('*.jpeg')))
    
    random.shuffle(images)
    total = len(images)
    
    # Adaptive split based on class size
    if total <= 2:
        train_imgs = images
        val_imgs = images[:1] if images else []
        test_imgs = []
    elif total <= 5:
        train_size = max(2, int(total * 0.6))
        train_imgs = images[:train_size]
        val_imgs = images[train_size:]
        test_imgs = []
    else:
        train_size = int(total * TRAIN_SPLIT)
        val_size = max(1, int(total * VAL_SPLIT))
        train_imgs = images[:train_size]
        val_imgs = images[train_size:train_size + val_size]
        test_imgs = images[train_size + val_size:]
    
    # Copy files
    for img in train_imgs:
        shutil.copy2(img, DATASET_DIR / 'train' / cls / img.name)
    for img in val_imgs:
        shutil.copy2(img, DATASET_DIR / 'validation' / cls / img.name)
    for img in test_imgs:
        shutil.copy2(img, DATASET_DIR / 'test' / cls / img.name)
    
    total_train += len(train_imgs)
    total_val += len(val_imgs)
    total_test += len(test_imgs)
    
    print(f"  {cls}: {len(train_imgs)} train, {len(val_imgs)} val, {len(test_imgs)} test")

print(f"\nTotal: {total_train} train, {total_val} val, {total_test} test")

# ============================================================================
# STEP 4: CREATE DATA GENERATORS
# ============================================================================
print("\nStep 4: Creating data generators with heavy augmentation...")

# Heavy augmentation for small datasets
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=40,
    width_shift_range=0.3,
    height_shift_range=0.3,
    horizontal_flip=True,
    vertical_flip=True,
    zoom_range=0.3,
    shear_range=0.2,
    brightness_range=[0.5, 1.5],
    fill_mode='nearest'
)

val_datagen = ImageDataGenerator(rescale=1./255)

train_gen = train_datagen.flow_from_directory(
    str(DATASET_DIR / 'train'),
    target_size=(IMG_HEIGHT, IMG_WIDTH),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=True
)

val_gen = val_datagen.flow_from_directory(
    str(DATASET_DIR / 'validation'),
    target_size=(IMG_HEIGHT, IMG_WIDTH),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False
)

print(f"Training samples: {train_gen.samples}")
print(f"Validation samples: {val_gen.samples}")
print(f"Detected classes: {train_gen.class_indices}")

# Save class indices
class_indices_path = MODELS_DIR / 'class_indices.txt'
with open(class_indices_path, 'w') as f:
    for cls, idx in train_gen.class_indices.items():
        f.write(f"{idx}: {cls}\n")

# ============================================================================
# STEP 5: BUILD MODEL
# ============================================================================
print("\nStep 5: Building model...")

# Check GPU
gpus = tf.config.list_physical_devices('GPU')
print(f"GPU Available: {len(gpus) > 0}")

# Build model
base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)
)
base_model.trainable = False

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(256, activation='relu'),
    layers.BatchNormalization(),
    layers.Dropout(0.3),
    layers.Dense(NUM_CLASSES, activation='softmax')
], name='football_shot_classifier')

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print("\nModel Architecture:")
model.summary()

# ============================================================================
# STEP 6: TRAIN MODEL
# ============================================================================
print("\nStep 6: Training model...")
print(f"Epochs: {EPOCHS}")
print(f"Batch size: {BATCH_SIZE}")
print(f"Learning rate: {LEARNING_RATE}")

if TOTAL_IMAGES < 50:
    print("\nWARNING: Small dataset detected!")
    print("Expected accuracy: 30-60% (due to limited data)")
    print("For production use, collect more images!")

MODEL_PATH = MODELS_DIR / 'cnn_shot_classifier.h5'

callbacks = [
    keras.callbacks.ModelCheckpoint(
        str(MODEL_PATH),
        save_best_only=True,
        monitor='val_accuracy',
        verbose=1
    ),
    keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True,
        verbose=1
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        verbose=1,
        min_lr=1e-7
    )
]

print("\nStarting training...\n")

history = model.fit(
    train_gen,
    epochs=EPOCHS,
    validation_data=val_gen,
    callbacks=callbacks,
    verbose=1
)

print("\nTraining complete!")

# ============================================================================
# STEP 7: PLOT RESULTS
# ============================================================================
print("\nStep 7: Plotting training results...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Loss plot
ax1.plot(history.history['loss'], label='Training Loss', linewidth=2, color='#1E90FF')
ax1.plot(history.history['val_loss'], label='Validation Loss', linewidth=2, color='#FF6B6B')
ax1.set_title('Model Loss', fontsize=16, fontweight='bold')
ax1.set_xlabel('Epoch', fontsize=12)
ax1.set_ylabel('Loss', fontsize=12)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Accuracy plot
ax2.plot(history.history['accuracy'], label='Training Accuracy', linewidth=2, color='#28a745')
ax2.plot(history.history['val_accuracy'], label='Validation Accuracy', linewidth=2, color='#ffc107')
ax2.set_title('Model Accuracy', fontsize=16, fontweight='bold')
ax2.set_xlabel('Epoch', fontsize=12)
ax2.set_ylabel('Accuracy', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
chart_path = CHARTS_DIR / 'training_history.png'
plt.savefig(str(chart_path), dpi=150, bbox_inches='tight')
plt.show()

print(f"Chart saved to: {chart_path}")

# ============================================================================
# STEP 8: SAVE TRAINING HISTORY
# ============================================================================
print("\nStep 8: Saving training history...")

import json

history_dict = {
    'loss': [float(x) for x in history.history['loss']],
    'val_loss': [float(x) for x in history.history['val_loss']],
    'accuracy': [float(x) for x in history.history['accuracy']],
    'val_accuracy': [float(x) for x in history.history['val_accuracy']],
    'epochs': len(history.history['loss']),
    'classes': valid_classes,
    'num_classes': NUM_CLASSES,
    'total_images': TOTAL_IMAGES
}

history_path = MODELS_DIR / 'training_history.json'
with open(history_path, 'w') as f:
    json.dump(history_dict, f, indent=4)

# ============================================================================
# STEP 9: FINAL SUMMARY
# ============================================================================
print("\n" + "="*70)
print("TRAINING COMPLETE - SUMMARY")
print("="*70)

final_train_acc = history.history['accuracy'][-1]
final_val_acc = history.history['val_accuracy'][-1]
final_train_loss = history.history['loss'][-1]
final_val_loss = history.history['val_loss'][-1]

print(f"\nFinal Results:")
print(f"  Training Accuracy:   {final_train_acc:.4f}")
print(f"  Validation Accuracy: {final_val_acc:.4f}")
print(f"  Training Loss:       {final_train_loss:.4f}")
print(f"  Validation Loss:     {final_val_loss:.4f}")

print(f"\nModel Information:")
print(f"  Classes: {NUM_CLASSES}")
print(f"  Total Images: {TOTAL_IMAGES}")
print(f"  Training Images: {total_train}")
print(f"  Validation Images: {total_val}")

print(f"\nSaved Files:")
print(f"  Model: {MODEL_PATH}")
print(f"  History: {history_path}")
print(f"  Chart: {chart_path}")
print(f"  Class Indices: {class_indices_path}")

# Performance evaluation
if final_val_acc > 0.8:
    print("\nPerformance: EXCELLENT")
elif final_val_acc > 0.6:
    print("\nPerformance: GOOD")
elif final_val_acc > 0.4:
    print("\nPerformance: FAIR (Need more data)")
else:
    print("\nPerformance: POOR (Insufficient data)")

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("1. Download the model file: MODEL_PATH")
print("2. Use it in your Flask application")
print("3. To improve accuracy, add more images to your dataset")
print("4. Recommended: 50-100 images per class minimum")
print("="*70)

# ============================================================================
# STEP 10: DOWNLOAD MODEL (Optional)
# ============================================================================
print("\nTo download the model, run this in a new cell:")
print(f"from google.colab import files")
print(f"files.download('{MODEL_PATH}')")
