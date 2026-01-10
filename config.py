"""
Football Performance Analyzer - Configuration File
Hybrid Approach: Train on Images, Inference on Videos
"""

import os
from pathlib import Path

# ==================== PROJECT PATHS ====================
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / 'dataset'
MODELS_DIR = BASE_DIR / 'models'
OUTPUTS_DIR = BASE_DIR / 'outputs'
UPLOADS_DIR = BASE_DIR / 'static' / 'uploads'
CHARTS_DIR = OUTPUTS_DIR / 'charts'
FRAMES_DIR = OUTPUTS_DIR / 'frames'

# Create directories if they don't exist
for directory in [MODELS_DIR, OUTPUTS_DIR, UPLOADS_DIR, CHARTS_DIR, FRAMES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== DATASET CONFIGURATION ====================
#SHOT_CLASSES = [
  #  'Backheel',
   # 'Bicycle_Kick',
   # 'Chip_Shot',
  #  'Curved_Shot',
   # 'Drive',
    #'Header',
   # 'Knuckleball',
   # 'Rabona',
   # 'Volley'
#]

SHOT_CLASSES = ['Bicycle_Kick', 'Chip_Shot', 'Curved_Shot', 'Drive', 'Header', 'Rabona', 'Volley']

NUM_CLASSES = 7  # This will be 9

# Dataset splits
TRAIN_SPLIT = 0.7
VALIDATION_SPLIT = 0.2
TEST_SPLIT = 0.1

# ==================== IMAGE CONFIGURATION ====================
IMG_HEIGHT = 224
IMG_WIDTH = 224
IMG_SIZE = (IMG_HEIGHT, IMG_WIDTH)
IMG_CHANNELS = 3
INPUT_SHAPE = (IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS)

# ==================== MODEL CONFIGURATION ====================
# Transfer Learning Base Models (choose one)
BASE_MODEL_OPTIONS = {
    'resnet50': 'ResNet50',
    'mobilenetv2': 'MobileNetV2',
    'efficientnetb0': 'EfficientNetB0',
    'vgg16': 'VGG16'
}
SELECTED_BASE_MODEL = 'mobilenetv2'  # Best for mobile deployment

# Training parameters
BATCH_SIZE = 32
EPOCHS = 50
INITIAL_LEARNING_RATE = 0.001
MIN_LEARNING_RATE = 1e-7

# Regularization (Overfitting Prevention)
DROPOUT_RATE = 0.5
L2_REGULARIZATION = 0.01

# Early Stopping (Overfitting Prevention)
EARLY_STOPPING_PATIENCE = 10
EARLY_STOPPING_MIN_DELTA = 0.001

# Learning Rate Reduction
LR_REDUCTION_FACTOR = 0.5
LR_REDUCTION_PATIENCE = 5

# ==================== DATA AUGMENTATION ====================
# Heavy augmentation to increase dataset size
AUGMENTATION_CONFIG = {
    'rotation_range': 20,
    'width_shift_range': 0.2,
    'height_shift_range': 0.2,
    'horizontal_flip': True,
    'zoom_range': 0.2,
    'shear_range': 0.15,
    'brightness_range': [0.7, 1.3],
    'fill_mode': 'nearest'
}

# ==================== VIDEO PROCESSING ====================
# Video upload settings
MAX_VIDEO_SIZE_MB = 200
ALLOWED_VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm']

# Frame extraction
FRAMES_PER_VIDEO = 15  # Extract 15 key frames from each video
MIN_FRAMES = 5
MAX_FRAMES = 30

# Video analysis
VIDEO_FPS = 30
FRAME_SKIP = 2  # Process every 2nd frame for speed

# ==================== YOLO CONFIGURATION ====================
YOLO_MODEL = 'yolov8n.pt'  # Nano model for speed
YOLO_CONFIDENCE = 0.5
YOLO_CLASSES = [0, 32]  # person=0, sports_ball=32

# ==================== PERFORMANCE SCORING ====================
# Score weights (total = 1.0)
SCORE_WEIGHTS = {
    'shot_type_confidence': 0.30,
    'technique_quality': 0.25,
    'body_positioning': 0.20,
    'follow_through': 0.15,
    'ball_contact': 0.10
}

# Quality thresholds
QUALITY_THRESHOLDS = {
    'excellent': 8.0,
    'good': 6.0,
    'fair': 4.0,
    'weak': 0.0
}

# Shot power categories
POWER_CATEGORIES = {
    'powerful': {'min_velocity': 25, 'min_confidence': 0.7},
    'medium': {'min_velocity': 15, 'min_confidence': 0.6},
    'weak': {'min_velocity': 0, 'min_confidence': 0.0}
}

# ==================== BINARY CLASSIFICATION ====================
# For power/quality binary classification
BINARY_THRESHOLD = 0.65  # Confidence threshold for good/weak classification

# Shot type groupings for binary analysis
POWER_SHOTS = ['power', 'Drive', 'volley', 'Knuckleball']
TECHNIQUE_SHOTS = ['chip', 'Chip_Shot', 'curl', 'Curved_Shot', 'Rabona']
AERIAL_SHOTS = ['Header', 'Bicycle_Kick']

# ==================== RECOMMENDATION ENGINE ====================
# Training advice templates
ADVICE_CATEGORIES = {
    'excellent': 'Maintain current technique and focus on consistency',
    'good': 'Solid fundamentals, work on power and precision',
    'fair': 'Practice technique, focus on body positioning',
    'weak': 'Master basics: stance, approach, and contact point'
}

# Drill recommendations per shot type
DRILLS_PER_SHOT_TYPE = {
    'power': [
        'Practice explosive leg movements',
        'Work on core strength',
        'Focus on proper run-up technique',
        'Strengthen quadriceps and hamstrings'
    ],
    'chip': [
        'Practice lofted passes with spin',
        'Work on precision over power',
        'Focus on follow-through height',
        'Improve ankle flexibility'
    ],
    'curl': [
        'Practice inside/outside foot techniques',
        'Work on ball spin control',
        'Focus on approach angle',
        'Strengthen hip flexors'
    ],
    'Header': [
        'Practice timing and jump height',
        'Work on neck strength',
        'Focus on forehead contact',
        'Improve aerial awareness'
    ],
    'volley': [
        'Practice body positioning for volleys',
        'Work on timing and balance',
        'Focus on knee-over-ball technique',
        'Improve coordination'
    ]
}

# ==================== VISUALIZATION ====================
# Chart settings
CHART_DPI = 100
CHART_FIGSIZE = (10, 6)
CHART_STYLE = 'seaborn-v0_8-darkgrid'

# Colors
PRIMARY_COLOR = '#1E90FF'
SECONDARY_COLOR = '#FF6B6B'
SUCCESS_COLOR = '#28a745'
WARNING_COLOR = '#ffc107'
DANGER_COLOR = '#dc3545'

# ==================== MODEL PATHS ====================
MODEL_SAVE_PATH = MODELS_DIR / 'cnn_shot_classifier.h5'
# Alternative model paths
SAVED_MODEL_PATH = MODELS_DIR / 'shot_classifier_saved_model'
MODEL_WEIGHTS_PATH = MODELS_DIR / 'model_weights.h5'
LABEL_ENCODER_PATH = MODELS_DIR / 'label_encoder.pkl'
TRAINING_HISTORY_PATH = MODELS_DIR / 'training_history.json'
YOLO_MODEL_PATH = MODELS_DIR / YOLO_MODEL

# ==================== LOGGING ====================
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = BASE_DIR / 'analyzer.log'

# ==================== FLASK CONFIGURATION ====================
FLASK_SECRET_KEY = 'your-secret-key-here-change-in-production'
FLASK_DEBUG = True
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000

# ==================== GPU CONFIGURATION ====================
# Set to False if you don't have GPU
USE_GPU = False
GPU_MEMORY_LIMIT = 4096  # MB

# ==================== MISC ====================
RANDOM_SEED = 42
VERBOSE = 1  # Training verbosity

# Print configuration summary
def print_config():
    """Print configuration summary"""
    print("="*60)
    print("FOOTBALL PERFORMANCE ANALYZER - CONFIGURATION")
    print("="*60)
    print(f"Number of Classes: {NUM_CLASSES}")
    print(f"Classes: {SHOT_CLASSES}")
    print(f"Image Size: {IMG_SIZE}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Epochs: {EPOCHS}")
    print(f"Base Model: {SELECTED_BASE_MODEL}")
    print(f"Dataset Directory: {DATASET_DIR}")
    print(f"Models Directory: {MODELS_DIR}")
    print(f"GPU Enabled: {USE_GPU}")
    print("="*60)

if __name__ == "__main__":
    print_config()
