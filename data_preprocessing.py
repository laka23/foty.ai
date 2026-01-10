"""
Football Performance Analyzer - Data Preprocessing Module
Load, augment, and prepare football shot images for training
FIXED: TensorFlow 2.12-2.18 + Keras 2/3 compatibility
"""

import os
# Force legacy Keras for compatibility with older saved models
os.environ.setdefault('TF_USE_LEGACY_KERAS', '1')

import numpy as np
from pathlib import Path
import tensorflow as tf

# Try importing ImageDataGenerator with fallback
try:
    from tensorflow.keras.preprocessing.image import ImageDataGenerator  # type: ignore
    USING_LEGACY = True
except (ImportError, AttributeError):
    try:
        from keras.preprocessing.image import ImageDataGenerator
        USING_LEGACY = True
    except ImportError:
        ImageDataGenerator = None
        USING_LEGACY = False
        print("Using modern tf.data pipeline (TF 2.16+)")

import config

class FootballDataPreprocessor:
    """
    Preprocess football shot images for CNN training
    Compatible with both legacy and modern TensorFlow
    """
    
    def __init__(self):
        """Initialize data preprocessor"""
        self.dataset_dir = config.DATASET_DIR
        self.img_size = config.IMG_SIZE
        self.batch_size = config.BATCH_SIZE
        self.num_classes = config.NUM_CLASSES
        self.using_legacy = USING_LEGACY
        
        # Check if dataset exists
        self._check_dataset()
    
    def _check_dataset(self):
        """Check if dataset directory exists"""
        if not self.dataset_dir.exists():
            print(f"Warning: Dataset directory not found at {self.dataset_dir}")
            print("Please organize your dataset in the following structure:")
            print(f"{self.dataset_dir}/")
            print("  train/")
            print("    Bicycle_Kick/")
            print("    chip/")
            print("    ...")
            print("  validation/")
            print("  test/")
    
    def create_data_generators(self):
        """
        Create data generators with augmentation
        Auto-detects whether to use legacy or modern pipeline
        
        Returns:
            Tuple of (train_gen, val_gen, test_gen)
        """
        if self.using_legacy and ImageDataGenerator is not None:
            return self._create_legacy_generators()
        else:
            return self._create_modern_generators()
    
    def _create_legacy_generators(self):
        """
        Create legacy ImageDataGenerator-based generators
        For TensorFlow < 2.16 or when legacy Keras is enabled
        """
        print("Using legacy ImageDataGenerator...")
        
        # Training data generator with heavy augmentation
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=config.AUGMENTATION_CONFIG['rotation_range'],
            width_shift_range=config.AUGMENTATION_CONFIG['width_shift_range'],
            height_shift_range=config.AUGMENTATION_CONFIG['height_shift_range'],
            horizontal_flip=config.AUGMENTATION_CONFIG['horizontal_flip'],
            zoom_range=config.AUGMENTATION_CONFIG['zoom_range'],
            shear_range=config.AUGMENTATION_CONFIG['shear_range'],
            brightness_range=config.AUGMENTATION_CONFIG['brightness_range'],
            fill_mode=config.AUGMENTATION_CONFIG['fill_mode']
        )
        
        # Validation and test generators (only rescaling)
        val_test_datagen = ImageDataGenerator(rescale=1./255)
        
        # Create training generator
        train_generator = train_datagen.flow_from_directory(
            self.dataset_dir / 'train',
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            shuffle=True,
            seed=config.RANDOM_SEED
        )
        
        # Create validation generator
        validation_generator = val_test_datagen.flow_from_directory(
            self.dataset_dir / 'validation',
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            shuffle=False
        )
        
        # Create test generator
        test_generator = val_test_datagen.flow_from_directory(
            self.dataset_dir / 'test',
            target_size=self.img_size,
            batch_size=self.batch_size,
            class_mode='categorical',
            shuffle=False
        )
        
        return train_generator, validation_generator, test_generator
    
    def _create_modern_generators(self):
        """
        Create modern tf.data-based generators
        For TensorFlow 2.16+
        """
        print("Using modern tf.data pipeline...")
        
        # Create datasets
        train_ds = tf.keras.utils.image_dataset_from_directory(
            self.dataset_dir / 'train',
            image_size=self.img_size,
            batch_size=self.batch_size,
            label_mode='categorical',
            shuffle=True,
            seed=config.RANDOM_SEED
        )
        
        val_ds = tf.keras.utils.image_dataset_from_directory(
            self.dataset_dir / 'validation',
            image_size=self.img_size,
            batch_size=self.batch_size,
            label_mode='categorical',
            shuffle=False
        )
        
        test_ds = tf.keras.utils.image_dataset_from_directory(
            self.dataset_dir / 'test',
            image_size=self.img_size,
            batch_size=self.batch_size,
            label_mode='categorical',
            shuffle=False
        )
        
        # Data augmentation layer
        data_augmentation = tf.keras.Sequential([
            tf.keras.layers.RandomFlip("horizontal_and_vertical"),
            tf.keras.layers.RandomRotation(
                config.AUGMENTATION_CONFIG['rotation_range'] / 360.0
            ),
            tf.keras.layers.RandomZoom(
                config.AUGMENTATION_CONFIG['zoom_range']
            ),
            tf.keras.layers.RandomTranslation(
                height_factor=config.AUGMENTATION_CONFIG['height_shift_range'],
                width_factor=config.AUGMENTATION_CONFIG['width_shift_range']
            ),
        ])
        
        # Normalization layer
        normalization = tf.keras.layers.Rescaling(1./255)
        
        # Apply augmentation to training data
        train_ds = train_ds.map(
            lambda x, y: (data_augmentation(x, training=True), y),
            num_parallel_calls=tf.data.AUTOTUNE
        )
        
        # Apply normalization to all datasets
        train_ds = train_ds.map(
            lambda x, y: (normalization(x), y),
            num_parallel_calls=tf.data.AUTOTUNE
        )
        val_ds = val_ds.map(
            lambda x, y: (normalization(x), y),
            num_parallel_calls=tf.data.AUTOTUNE
        )
        test_ds = test_ds.map(
            lambda x, y: (normalization(x), y),
            num_parallel_calls=tf.data.AUTOTUNE
        )
        
        # Optimize performance
        AUTOTUNE = tf.data.AUTOTUNE
        train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
        val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
        test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)
        
        return train_ds, val_ds, test_ds
    
    def create_multi_output_generators(self):
        """
        Create data generators for multi-output model
        (shot type + quality classification)
        
        Returns:
            Tuple of (train_gen, val_gen, test_gen)
        """
        # Get basic generators
        train_gen, val_gen, test_gen = self.create_data_generators()
        
        # Only wrap if using legacy generators
        if self.using_legacy:
            train_gen_wrapped = self._wrap_multi_output(train_gen)
            val_gen_wrapped = self._wrap_multi_output(val_gen)
            test_gen_wrapped = self._wrap_multi_output(test_gen)
            return train_gen_wrapped, val_gen_wrapped, test_gen_wrapped
        else:
            # For modern pipeline, wrap differently
            train_gen = self._wrap_multi_output_modern(train_gen)
            val_gen = self._wrap_multi_output_modern(val_gen)
            test_gen = self._wrap_multi_output_modern(test_gen)
            return train_gen, val_gen, test_gen
    
    def _wrap_multi_output(self, generator):
        """
        Wrap legacy generator to provide multiple outputs
        
        Args:
            generator: Original image generator
            
        Yields:
            (images, [shot_type_labels, quality_labels])
        """
        while True:
            images, labels = next(generator)
            
            # Shot type labels (categorical)
            shot_type_labels = labels
            
            # Quality labels (binary: powerful vs weak)
            quality_labels = np.zeros((len(labels), 1))
            
            for i, label in enumerate(labels):
                class_idx = np.argmax(label)
                class_name = list(generator.class_indices.keys())[
                    list(generator.class_indices.values()).index(class_idx)
                ]
                
                # Assign quality based on shot type
                if class_name in config.POWER_SHOTS:
                    quality_labels[i] = 1.0
                elif class_name in config.TECHNIQUE_SHOTS:
                    quality_labels[i] = 0.7
                elif class_name in config.AERIAL_SHOTS:
                    quality_labels[i] = 0.8
                else:
                    quality_labels[i] = 0.5
            
            yield images, {
                'shot_type_output': shot_type_labels,
                'shot_quality_output': quality_labels
            }
    
    def _wrap_multi_output_modern(self, dataset):
        """
        Wrap modern tf.data dataset for multi-output
        
        Args:
            dataset: tf.data.Dataset
            
        Returns:
            Modified dataset with multiple outputs
        """
        def process_batch(images, labels):
            shot_type_labels = labels
            
            # Create quality labels
            quality_labels = tf.zeros((tf.shape(labels)[0], 1))
            
            return images, {
                'shot_type_output': shot_type_labels,
                'shot_quality_output': quality_labels
            }
        
        return dataset.map(process_batch, num_parallel_calls=tf.data.AUTOTUNE)
    
    def prepare_datasets(self):
        """
        Prepare all datasets with augmentation
        
        Returns:
            Tuple of (train_gen, val_gen, test_gen)
        """
        print("="*70)
        print("PREPARING DATASETS")
        print("="*70)
        
        # Create generators
        train_gen, val_gen, test_gen = self.create_multi_output_generators()
        
        print(f"Dataset Directory: {self.dataset_dir}")
        print(f"Image Size: {self.img_size}")
        print(f"Batch Size: {self.batch_size}")
        print(f"Number of Classes: {self.num_classes}")
        print(f"Pipeline: {'Legacy ImageDataGenerator' if self.using_legacy else 'Modern tf.data'}")
        
        print("\nAugmentation Settings:")
        for key, value in config.AUGMENTATION_CONFIG.items():
            print(f"  {key}: {value}")
        
        print("="*70)
        
        return train_gen, val_gen, test_gen
    
    def get_class_weights(self, train_generator):
        """
        Calculate class weights for imbalanced dataset
        
        Args:
            train_generator: Training data generator
            
        Returns:
            Dictionary of class weights
        """
        from sklearn.utils.class_weight import compute_class_weight
        
        # Get classes differently based on generator type
        if self.using_legacy:
            classes = train_generator.classes
        else:
            # For modern pipeline, extract classes from dataset
            classes = []
            for _, labels in train_generator.unbatch():
                classes.append(np.argmax(labels['shot_type_output'].numpy()))
            classes = np.array(classes)
        
        # Compute class weights
        class_weights = compute_class_weight(
            'balanced',
            classes=np.unique(classes),
            y=classes
        )
        
        # Convert to dictionary
        class_weight_dict = {i: weight for i, weight in enumerate(class_weights)}
        
        print("\nClass Distribution:")
        class_counts = np.bincount(classes)
        for i, count in enumerate(class_counts):
            if self.using_legacy:
                class_name = list(train_generator.class_indices.keys())[
                    list(train_generator.class_indices.values()).index(i)
                ]
            else:
                class_name = config.SHOT_CLASSES[i]
            print(f"  {class_name}: {count} images (weight: {class_weight_dict[i]:.3f})")
        
        return class_weight_dict
    
    def visualize_augmentation(self, train_generator, num_images=5):
        """
        Visualize augmented images
        
        Args:
            train_generator: Training data generator
            num_images: Number of images to display
        """
        import matplotlib.pyplot as plt
        
        # Get a batch of images
        if self.using_legacy:
            images, labels = next(train_generator)
        else:
            for images, labels in train_generator.take(1):
                pass
        
        # Plot images
        fig, axes = plt.subplots(1, num_images, figsize=(15, 3))
        
        for i in range(min(num_images, len(images))):
            axes[i].imshow(images[i])
            
            # Get class name
            if isinstance(labels, dict):
                class_idx = np.argmax(labels['shot_type_output'][i])
            else:
                class_idx = np.argmax(labels[i])
            
            class_name = config.SHOT_CLASSES[class_idx]
            axes[i].set_title(f"{class_name}")
            axes[i].axis('off')
        
        plt.tight_layout()
        save_path = config.CHARTS_DIR / 'augmentation_samples.png'
        plt.savefig(save_path, dpi=config.CHART_DPI, bbox_inches='tight')
        print(f"Augmentation samples saved to {save_path}")
        plt.show()
    
    def split_dataset(self, source_dir=None):
        """
        Split dataset into train/validation/test sets
        
        Args:
            source_dir: Source directory with class folders
        """
        if source_dir is None:
            source_dir = self.dataset_dir
        else:
            source_dir = Path(source_dir)
        
        if not source_dir.exists():
            print(f"Error: Source directory {source_dir} not found")
            return
        
        from sklearn.model_selection import train_test_split
        import shutil
        
        print("Splitting dataset into train/validation/test...")
        
        # Create split directories
        train_dir = self.dataset_dir / 'train'
        val_dir = self.dataset_dir / 'validation'
        test_dir = self.dataset_dir / 'test'
        
        for directory in [train_dir, val_dir, test_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Process each class
        for class_name in config.SHOT_CLASSES:
            class_path = source_dir / class_name
            
            if not class_path.exists():
                print(f"Warning: Class directory {class_name} not found")
                continue
            
            # Get all images
            images = list(class_path.glob('*.jpg')) + list(class_path.glob('*.png'))
            
            if len(images) == 0:
                print(f"Warning: No images found in {class_name}")
                continue
            
            # Split data
            train_imgs, temp_imgs = train_test_split(
                images, 
                train_size=config.TRAIN_SPLIT,
                random_state=config.RANDOM_SEED
            )
            
            val_imgs, test_imgs = train_test_split(
                temp_imgs,
                train_size=config.VALIDATION_SPLIT / (config.VALIDATION_SPLIT + config.TEST_SPLIT),
                random_state=config.RANDOM_SEED
            )
            
            # Create class directories
            (train_dir / class_name).mkdir(exist_ok=True)
            (val_dir / class_name).mkdir(exist_ok=True)
            (test_dir / class_name).mkdir(exist_ok=True)
            
            # Copy images
            for img in train_imgs:
                shutil.copy(img, train_dir / class_name / img.name)
            
            for img in val_imgs:
                shutil.copy(img, val_dir / class_name / img.name)
            
            for img in test_imgs:
                shutil.copy(img, test_dir / class_name / img.name)
            
            print(f"{class_name}: {len(train_imgs)} train, {len(val_imgs)} val, {len(test_imgs)} test")
        
        print("Dataset split complete!")


class DatasetStatistics:
    """Calculate and display dataset statistics"""
    
    def __init__(self, dataset_dir=None):
        """Initialize statistics calculator"""
        self.dataset_dir = dataset_dir or config.DATASET_DIR
    
    def calculate_statistics(self):
        """Calculate dataset statistics"""
        stats = {
            'total_images': 0,
            'classes': {},
            'splits': {}
        }
        
        # Check each split
        for split in ['train', 'validation', 'test']:
            split_dir = self.dataset_dir / split
            
            if not split_dir.exists():
                continue
            
            split_stats = {'total': 0, 'classes': {}}
            
            # Count images per class
            for class_name in config.SHOT_CLASSES:
                class_dir = split_dir / class_name
                
                if class_dir.exists():
                    image_count = len(list(class_dir.glob('*.jpg'))) + len(list(class_dir.glob('*.png')))
                    split_stats['classes'][class_name] = image_count
                    split_stats['total'] += image_count
                    
                    # Update overall class count
                    if class_name not in stats['classes']:
                        stats['classes'][class_name] = 0
                    stats['classes'][class_name] += image_count
            
            stats['splits'][split] = split_stats
            stats['total_images'] += split_stats['total']
        
        return stats
    
    def print_statistics(self):
        """Print dataset statistics"""
        stats = self.calculate_statistics()
        
        print("="*70)
        print("DATASET STATISTICS")
        print("="*70)
        
        print(f"\nTotal Images: {stats['total_images']}")
        
        print("\nImages per Split:")
        for split, split_stats in stats['splits'].items():
            print(f"  {split.capitalize()}: {split_stats['total']}")
        
        print("\nImages per Class:")
        for class_name, count in stats['classes'].items():
            percentage = (count / stats['total_images']) * 100 if stats['total_images'] > 0 else 0
            print(f"  {class_name}: {count} ({percentage:.1f}%)")
        
        print("\nClass Distribution per Split:")
        for split, split_stats in stats['splits'].items():
            print(f"\n{split.capitalize()}:")
            for class_name, count in split_stats['classes'].items():
                print(f"  {class_name}: {count}")
        
        print("="*70)


# Test the preprocessor
if __name__ == "__main__":
    print("="*70)
    print("TESTING DATA PREPROCESSOR")
    print("="*70)
    
    # Create preprocessor
    preprocessor = FootballDataPreprocessor()
    
    print(f"\nUsing {'legacy' if preprocessor.using_legacy else 'modern'} pipeline")
    
    # Display statistics
    stats_calculator = DatasetStatistics()
    stats_calculator.print_statistics()
    
    # Try to create generators
    try:
        print("\nCreating data generators...")
        train_gen, val_gen, test_gen = preprocessor.prepare_datasets()
        
        print("\nData generators created successfully!")
        
        # Different stats for legacy vs modern
        if preprocessor.using_legacy:
            print(f"Training batches: {len(train_gen)}")
            print(f"Validation batches: {len(val_gen)}")
            print(f"Test batches: {len(test_gen)}")
        else:
            print("Using tf.data.Dataset (batch count not available)")
        
        print("\nData preprocessing test complete!")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease ensure your dataset is organized correctly:")
        print(f"{config.DATASET_DIR}/")
        print("  train/")
        print("    Bicycle_Kick/")
        print("    chip/")
        print("    ...")
        print("  validation/")
        print("  test/")
    
    print("\n" + "="*70)