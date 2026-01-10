"""
Football Performance Analyzer - CNN Model Architecture
Hybrid Approach with Transfer Learning
Includes Overfitting & Underfitting Prevention
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, regularizers
from tensorflow.keras.applications import (
    ResNet50, MobileNetV2, EfficientNetB0, VGG16
)
import config

class ShotClassifierModel:
    """
    CNN Model for Football Shot Classification
    Uses Transfer Learning with pre-trained models
    """
    
    def __init__(self, base_model_name='mobilenetv2'):
        """
        Initialize model architecture
        
        Args:
            base_model_name: Name of pre-trained model to use
        """
        self.base_model_name = base_model_name
        self.num_classes = config.NUM_CLASSES
        self.input_shape = config.INPUT_SHAPE
        self.dropout_rate = config.DROPOUT_RATE
        self.l2_reg = config.L2_REGULARIZATION
        
    def get_base_model(self):
        """
        Get pre-trained base model
        
        Returns:
            Pre-trained model without top layers
        """
        base_models = {
            'resnet50': ResNet50,
            'mobilenetv2': MobileNetV2,
            'efficientnetb0': EfficientNetB0,
            'vgg16': VGG16
        }
        
        if self.base_model_name not in base_models:
            print(f"Warning: {self.base_model_name} not found, using MobileNetV2")
            self.base_model_name = 'mobilenetv2'
        
        base_model = base_models[self.base_model_name](
            weights='imagenet',
            include_top=False,
            input_shape=self.input_shape
        )
        
        # Freeze base model layers initially
        base_model.trainable = False
        
        return base_model
    
    def build_model(self, multi_output=True):
        """
        Build complete model architecture
        
        Args:
            multi_output: If True, creates both multi-class and binary outputs
            
        Returns:
            Compiled Keras model
        """
        # Input layer
        inputs = layers.Input(shape=self.input_shape, name='input_image')
        
        # Get pre-trained base model
        base_model = self.get_base_model()
        
        # Base model
        x = base_model(inputs, training=False)
        
        # Global Average Pooling (better than Flatten for overfitting)
        x = layers.GlobalAveragePooling2D(name='global_avg_pool')(x)
        
        # Dense layers with regularization
        x = layers.Dense(
            512,
            activation='relu',
            kernel_regularizer=regularizers.l2(self.l2_reg),
            name='dense_512'
        )(x)
        
        # Batch Normalization (helps with underfitting)
        x = layers.BatchNormalization(name='batch_norm_1')(x)
        
        # Dropout (overfitting prevention)
        x = layers.Dropout(self.dropout_rate, name='dropout_1')(x)
        
        # Second dense layer
        x = layers.Dense(
            256,
            activation='relu',
            kernel_regularizer=regularizers.l2(self.l2_reg),
            name='dense_256'
        )(x)
        
        x = layers.BatchNormalization(name='batch_norm_2')(x)
        x = layers.Dropout(self.dropout_rate / 2, name='dropout_2')(x)
        
        # Third dense layer
        x = layers.Dense(
            128,
            activation='relu',
            kernel_regularizer=regularizers.l2(self.l2_reg),
            name='dense_128'
        )(x)
        
        x = layers.BatchNormalization(name='batch_norm_3')(x)
        x = layers.Dropout(self.dropout_rate / 2, name='dropout_3')(x)
        
        # Output layers
        if multi_output:
            # Multi-class classification output (11 shot types)
            shot_type_output = layers.Dense(
                self.num_classes,
                activation='softmax',
                name='shot_type_output'
            )(x)
            
            # Binary classification output (powerful vs weak)
            shot_quality_output = layers.Dense(
                1,
                activation='sigmoid',
                name='shot_quality_output'
            )(x)
            
            # Create model with multiple outputs
            model = models.Model(
                inputs=inputs,
                outputs=[shot_type_output, shot_quality_output],
                name='shot_classifier_multi_output'
            )
            
            # Compile with multiple losses
            model.compile(
                optimizer=keras.optimizers.Adam(
                    learning_rate=config.INITIAL_LEARNING_RATE
                ),
                loss={
                    'shot_type_output': 'categorical_crossentropy',
                    'shot_quality_output': 'binary_crossentropy'
                },
                loss_weights={
                    'shot_type_output': 1.0,
                    'shot_quality_output': 0.5
                },
                metrics={
                    'shot_type_output': ['accuracy', 'top_k_categorical_accuracy'],
                    'shot_quality_output': ['accuracy', 'AUC']
                }
            )
        else:
            # Single output (multi-class only)
            outputs = layers.Dense(
                self.num_classes,
                activation='softmax',
                name='shot_type_output'
            )(x)
            
            model = models.Model(
                inputs=inputs,
                outputs=outputs,
                name='shot_classifier_single_output'
            )
            
            # Compile
            model.compile(
                optimizer=keras.optimizers.Adam(
                    learning_rate=config.INITIAL_LEARNING_RATE
                ),
                loss='categorical_crossentropy',
                metrics=['accuracy', 'top_k_categorical_accuracy']
            )
        
        return model
    
    def build_fine_tuning_model(self, base_model_layers_to_unfreeze=20):
        """
        Build model for fine-tuning (unfreeze some base layers)
        
        Args:
            base_model_layers_to_unfreeze: Number of top layers to unfreeze
            
        Returns:
            Model ready for fine-tuning
        """
        model = self.build_model(multi_output=True)
        
        # Unfreeze top layers of base model
        base_model = model.layers[1]  # Base model is second layer
        base_model.trainable = True
        
        # Freeze all layers except the top N
        for layer in base_model.layers[:-base_model_layers_to_unfreeze]:
            layer.trainable = False
        
        # Recompile with lower learning rate
        model.compile(
            optimizer=keras.optimizers.Adam(
                learning_rate=config.INITIAL_LEARNING_RATE / 10
            ),
            loss={
                'shot_type_output': 'categorical_crossentropy',
                'shot_quality_output': 'binary_crossentropy'
            },
            loss_weights={
                'shot_type_output': 1.0,
                'shot_quality_output': 0.5
            },
            metrics={
                'shot_type_output': ['accuracy', 'top_k_categorical_accuracy'],
                'shot_quality_output': ['accuracy', 'AUC']
            }
        )
        
        return model
    
    def get_callbacks(self):
        """
        Get training callbacks for overfitting/underfitting prevention
        
        Returns:
            List of Keras callbacks
        """
        callbacks = []
        
        # Early Stopping (prevent overfitting)
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=config.EARLY_STOPPING_PATIENCE,
            min_delta=config.EARLY_STOPPING_MIN_DELTA,
            restore_best_weights=True,
            verbose=1
        )
        callbacks.append(early_stopping)
        
        # Reduce Learning Rate on Plateau
        reduce_lr = keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=config.LR_REDUCTION_FACTOR,
            patience=config.LR_REDUCTION_PATIENCE,
            min_lr=config.MIN_LEARNING_RATE,
            verbose=1
        )
        callbacks.append(reduce_lr)
        
        # Model Checkpoint (save best model)
        checkpoint = keras.callbacks.ModelCheckpoint(
            str(config.MODEL_SAVE_PATH),
            monitor='val_loss',
            save_best_only=True,
            save_weights_only=False,
            verbose=1
        )
        callbacks.append(checkpoint)
        
        # TensorBoard (optional - for visualization)
        tensorboard = keras.callbacks.TensorBoard(
            log_dir=str(config.OUTPUTS_DIR / 'tensorboard_logs'),
            histogram_freq=1,
            write_graph=True,
            write_images=True
        )
        callbacks.append(tensorboard)
        
        return callbacks
    
    def print_model_summary(self):
        """Print model architecture summary"""
        model = self.build_model(multi_output=True)
        print("="*70)
        print("FOOTBALL SHOT CLASSIFIER - MODEL ARCHITECTURE")
        print("="*70)
        model.summary()
        print("="*70)
        print(f"Total Parameters: {model.count_params():,}")
        print(f"Base Model: {self.base_model_name.upper()}")
        print(f"Input Shape: {self.input_shape}")
        print(f"Output Classes: {self.num_classes}")
        print(f"Dropout Rate: {self.dropout_rate}")
        print(f"L2 Regularization: {self.l2_reg}")
        print("="*70)


def create_simple_cnn_model():
    """
    Create a simple CNN from scratch (without transfer learning)
    Useful if pre-trained models don't work well
    """
    model = models.Sequential([
        # Input
        layers.Input(shape=config.INPUT_SHAPE),
        
        # Conv Block 1
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Conv Block 2
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Conv Block 3
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Conv Block 4
        layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Dense layers
        layers.Flatten(),
        layers.Dense(512, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        
        # Output
        layers.Dense(config.NUM_CLASSES, activation='softmax')
    ], name='simple_cnn_classifier')
    
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model


# Test the model architecture
if __name__ == "__main__":
    print("Testing Model Architecture...")
    
    # Create model instance
    shot_classifier = ShotClassifierModel(
        base_model_name=config.SELECTED_BASE_MODEL
    )
    
    # Print model summary
    shot_classifier.print_model_summary()
    
    # Test callbacks
    print("\nCallbacks:")
    callbacks = shot_classifier.get_callbacks()
    for cb in callbacks:
        print(f"  - {cb.__class__.__name__}")
    
    print("\n✅ Model architecture test complete!")
