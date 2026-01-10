"""
Football Performance Analyzer - Model Training Script
Train CNN Model on Football Shot Images
Hybrid Approach with Overfitting/Underfitting Prevention
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
from datetime import datetime
import config
from model_architecture import ShotClassifierModel
from data_preprocessing import FootballDataPreprocessor

class ModelTrainer:
    """
    Handles complete model training pipeline
    Includes overfitting/underfitting prevention
    """
    
    def __init__(self, base_model_name='mobilenetv2'):
        """
        Initialize trainer
        
        Args:
            base_model_name: Pre-trained model to use
        """
        self.base_model_name = base_model_name
        self.model = None
        self.history = None
        self.data_preprocessor = FootballDataPreprocessor()
        
        # Setup GPU if available
        self._setup_gpu()
    
    def _setup_gpu(self):
        """Configure GPU settings"""
        if config.USE_GPU:
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                try:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    print(f" GPU Enabled: {len(gpus)} GPU(s) available")
                except RuntimeError as e:
                    print(f" GPU setup error: {e}")
            else:
                print(" No GPU found, using CPU")
        else:
            print(" Running on CPU (GPU disabled in config)")
    
    def prepare_data(self):
        """
        Prepare training, validation, and test datasets
        
        Returns:
            Tuple of (train_gen, val_gen, test_gen)
        """
        print("="*70)
        print(" PREPARING DATASETS")
        print("="*70)
        
        # Load and prepare data
        train_gen, val_gen, test_gen = self.data_preprocessor.prepare_datasets()
        
        try:
          print(f" Training samples: {train_gen.samples}")
          print(f" Validation samples: {val_gen.samples}")
          print(f" Test samples: {test_gen.samples}")
        except AttributeError:
          print(f" Data generators created successfully")
          print(f" Classes: {config.NUM_CLASSES}")  
        
        return train_gen, val_gen, test_gen
    
    def build_and_compile_model(self):
        """
        Build and compile the model
        
        Returns:
            Compiled Keras model
        """
        print("="*70)
        print(" BUILDING MODEL")
        print("="*70)
        
        # Create model
        model_builder = ShotClassifierModel(
            base_model_name=self.base_model_name
        )
        
        # Build model with multi-output
        self.model = model_builder.build_model(multi_output=True)
        
        # Print summary
        self.model.summary()
        
        print(f" Model built successfully!")
        print(f"   Base Model: {self.base_model_name.upper()}")
        print(f"   Total Parameters: {self.model.count_params():,}")
        
        return self.model
    
    def train_model(self, train_gen, val_gen, epochs=None):
        """
        Train the model
        
        Args:
            train_gen: Training data generator
            val_gen: Validation data generator
            epochs: Number of epochs (uses config if None)
            
        Returns:
            Training history
        """
        if epochs is None:
            epochs = config.EPOCHS
        
        print("="*70)
        print(" STARTING TRAINING")
        print("="*70)
        print(f"Epochs: {epochs}")
        print(f"Batch Size: {config.BATCH_SIZE}")
        print(f"Learning Rate: {config.INITIAL_LEARNING_RATE}")
        print(f"Dropout Rate: {config.DROPOUT_RATE}")
        print(f"L2 Regularization: {config.L2_REGULARIZATION}")
        print("="*70)
        
        # Get callbacks
        model_builder = ShotClassifierModel(self.base_model_name)
        callbacks = model_builder.get_callbacks()
        
        # Calculate steps
        try:
          steps_per_epoch = train_gen.samples // config.BATCH_SIZE
          validation_steps = val_gen.samples // config.BATCH_SIZE
        except AttributeError:
    # For wrapped generators, use default steps
           steps_per_epoch = len(train_gen) if hasattr(train_gen, '__len__') else 1
           validation_steps = len(val_gen) if hasattr(val_gen, '__len__') else 1
        
        # Train model
        start_time = datetime.now()
        
        self.history = self.model.fit(
            train_gen,
            steps_per_epoch=steps_per_epoch,
            epochs=epochs,
            validation_data=val_gen,
            validation_steps=validation_steps,
            callbacks=callbacks,
            verbose=config.VERBOSE
        )
        
        end_time = datetime.now()
        training_duration = (end_time - start_time).total_seconds()
        
        print("="*70)
        print(f" TRAINING COMPLETE!")
        print(f"   Duration: {training_duration/60:.2f} minutes")
        print(f"   Final Loss: {self.history.history['loss'][-1]:.4f}")
        print(f"   Final Val Loss: {self.history.history['val_loss'][-1]:.4f}")
        print(f"   Final Accuracy: {self.history.history['shot_type_output_accuracy'][-1]:.4f}")
        print(f"   Final Val Accuracy: {self.history.history['val_shot_type_output_accuracy'][-1]:.4f}")
        print("="*70)
        
        # Save training history
        self._save_training_history()
        
        return self.history
    
    def fine_tune_model(self, train_gen, val_gen, epochs=20):
        """
        Fine-tune the model by unfreezing base layers
        
        Args:
            train_gen: Training data generator
            val_gen: Validation data generator
            epochs: Number of fine-tuning epochs
            
        Returns:
            Fine-tuning history
        """
        print("="*70)
        print(" FINE-TUNING MODEL")
        print("="*70)
        
        # Build fine-tuning model
        model_builder = ShotClassifierModel(self.base_model_name)
        self.model = model_builder.build_fine_tuning_model(
            base_model_layers_to_unfreeze=20
        )
        
        # Get callbacks
        callbacks = model_builder.get_callbacks()
        
        # Calculate steps
        try:
           steps_per_epoch = train_gen.samples // config.BATCH_SIZE
           validation_steps = val_gen.samples // config.BATCH_SIZE
        except AttributeError:
            steps_per_epoch = None
            validation_steps = None
        
        # Fine-tune
        fine_tune_history = self.model.fit(
            train_gen,
            steps_per_epoch=steps_per_epoch,
            epochs=epochs,
            validation_data=val_gen,
            validation_steps=validation_steps,
            callbacks=callbacks,
            verbose=config.VERBOSE
        )
        
        print(" Fine-tuning complete!")
        
        return fine_tune_history
    
    def evaluate_model(self, test_gen):
        """
        Evaluate model on test set
        
        Args:
            test_gen: Test data generator
            
        Returns:
            Test metrics
        """
        print("="*70)
        print(" EVALUATING MODEL")
        print("="*70)
        
        # Evaluate
        test_loss = self.model.evaluate(
            test_gen,
            steps=test_gen.samples // config.BATCH_SIZE,
            verbose=1
        )
        
        print(f" Test Loss: {test_loss[0]:.4f}")
        print(f" Test Accuracy: {test_loss[1]:.4f}")
        
        # Generate predictions for confusion matrix
        print("\n Generating predictions for detailed metrics...")
        
        test_gen.reset()
        predictions = self.model.predict(
            test_gen,
            steps=test_gen.samples // config.BATCH_SIZE,
            verbose=1
        )
        
        # Get shot type predictions (first output)
        if isinstance(predictions, list):
            shot_type_predictions = predictions[0]
        else:
            shot_type_predictions = predictions
        
        # Get predicted classes
        predicted_classes = np.argmax(shot_type_predictions, axis=1)
        
        # Get true classes
        true_classes = test_gen.classes[:len(predicted_classes)]
        
        # Classification report
        print("\n Classification Report:")
        print(classification_report(
            true_classes,
            predicted_classes,
            target_names=config.SHOT_CLASSES,
            zero_division=0
        ))
        
        # Generate confusion matrix
        self._plot_confusion_matrix(true_classes, predicted_classes)
        
        return test_loss
    
    def _save_training_history(self):
        """Save training history to JSON"""
        if self.history is None:
            print(" No training history to save")
            return
        
        history_dict = {
            'loss': [float(x) for x in self.history.history['loss']],
            'val_loss': [float(x) for x in self.history.history['val_loss']],
            'shot_type_output_accuracy': [float(x) for x in self.history.history['shot_type_output_accuracy']],
            'val_shot_type_output_accuracy': [float(x) for x in self.history.history['val_shot_type_output_accuracy']],
        }
        
        # Save to JSON
        with open(config.TRAINING_HISTORY_PATH, 'w') as f:
            json.dump(history_dict, f, indent=4)
        
        print(f" Training history saved to {config.TRAINING_HISTORY_PATH}")
    
    def plot_training_history(self):
        """Plot training history curves"""
        if self.history is None:
            print(" No training history to plot")
            return
        
        print(" Generating training plots...")
        
        history = self.history.history
        
        # Create figure with 2 subplots
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot 1: Loss
        axes[0].plot(history['loss'], label='Training Loss', linewidth=2)
        axes[0].plot(history['val_loss'], label='Validation Loss', linewidth=2)
        axes[0].set_title('Model Loss', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Epoch', fontsize=12)
        axes[0].set_ylabel('Loss', fontsize=12)
        axes[0].legend(fontsize=10)
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Accuracy
        axes[1].plot(history['shot_type_output_accuracy'], label='Training Accuracy', linewidth=2)
        axes[1].plot(history['val_shot_type_output_accuracy'], label='Validation Accuracy', linewidth=2)
        axes[1].set_title('Model Accuracy', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Epoch', fontsize=12)
        axes[1].set_ylabel('Accuracy', fontsize=12)
        axes[1].legend(fontsize=10)
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        save_path = config.CHARTS_DIR / 'training_history.png'
        plt.savefig(save_path, dpi=config.CHART_DPI, bbox_inches='tight')
        print(f" Training history plot saved to {save_path}")
        
        plt.show()
    
    def _plot_confusion_matrix(self, true_labels, predicted_labels):
        """
        Plot confusion matrix
        
        Args:
            true_labels: True class labels
            predicted_labels: Predicted class labels
        """
        # Calculate confusion matrix
        cm = confusion_matrix(true_labels, predicted_labels)
        
        # Create figure
        plt.figure(figsize=(12, 10))
        
        # Plot heatmap
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=config.SHOT_CLASSES,
            yticklabels=config.SHOT_CLASSES,
            cbar_kws={'label': 'Count'}
        )
        
        plt.title('Confusion Matrix - Shot Type Classification', fontsize=14, fontweight='bold')
        plt.xlabel('Predicted Label', fontsize=12)
        plt.ylabel('True Label', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        
        # Save plot
        save_path = config.CHARTS_DIR / 'confusion_matrix.png'
        plt.savefig(save_path, dpi=config.CHART_DPI, bbox_inches='tight')
        print(f" Confusion matrix saved to {save_path}")
        
        plt.show()
    
    def save_model(self):
        """Save trained model"""
        if self.model is None:
            print(" No model to save")
            return
        
        # Save full model
        self.model.save(config.MODEL_SAVE_PATH)
        print(f" Model saved to {config.MODEL_SAVE_PATH}")
        
        # Save weights separately
        self.model.save_weights(config.MODEL_WEIGHTS_PATH)
        print(f" Model weights saved to {config.MODEL_WEIGHTS_PATH}")
    
    def load_model(self):
        """Load trained model"""
        if config.MODEL_SAVE_PATH.exists():
            self.model = keras.models.load_model(config.MODEL_SAVE_PATH)
            print(f" Model loaded from {config.MODEL_SAVE_PATH}")
            return self.model
        else:
            print(f" Model not found at {config.MODEL_SAVE_PATH}")
            return None


def train_complete_pipeline(base_model='mobilenetv2', epochs=50, fine_tune=True):
    """
    Complete training pipeline
    
    Args:
        base_model: Base model to use
        epochs: Number of training epochs
        fine_tune: Whether to fine-tune after initial training
    """
    print("="*70)
    print(" FOOTBALL SHOT CLASSIFIER - TRAINING PIPELINE")
    print("="*70)
    
    # Create trainer
    trainer = ModelTrainer(base_model_name=base_model)
    
    # Step 1: Prepare data
    train_gen, val_gen, test_gen = trainer.prepare_data()
    
    # Step 2: Build model
    trainer.build_and_compile_model()
    
    # Step 3: Train model
    trainer.train_model(train_gen, val_gen, epochs=epochs)
    
    # Step 4: Plot training history
    trainer.plot_training_history()
    
    # Step 5: Fine-tune (optional)
    if fine_tune:
        print("\n" + "="*70)
        print(" Starting Fine-Tuning Phase")
        print("="*70)
        trainer.fine_tune_model(train_gen, val_gen, epochs=20)
        trainer.plot_training_history()
    
    # Step 6: Evaluate on test set
    trainer.evaluate_model(test_gen)
    
    # Step 7: Save model
    trainer.save_model()
    
    print("\n" + "="*70)
    print(" TRAINING PIPELINE COMPLETE!")
    print("="*70)
    print(f"Model saved at: {config.MODEL_SAVE_PATH}")
    print(f"Training history: {config.TRAINING_HISTORY_PATH}")
    print(f"Charts saved in: {config.CHARTS_DIR}")
    print("="*70)


# Main execution
if __name__ == "__main__":
    # Train the model
    train_complete_pipeline(
        base_model=config.SELECTED_BASE_MODEL,
        epochs=config.EPOCHS,
        fine_tune=True
    )
