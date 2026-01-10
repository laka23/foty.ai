"""
Football Performance Analyzer - Shot Classifier
Classify football shots using trained CNN model
Hybrid Approach: Trained on Images, Inference on Video Frames
FIXED: Compatible with all TensorFlow versions
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
import cv2
from pathlib import Path
import config
import sys

class ShotClassifier:
    """
    Classify football shot types using trained CNN model
    """
    
    def __init__(self, model_path=None):
        """
        Initialize shot classifier
        
        Args:
            model_path: Path to trained model (None = use config)
        """
        self.model_path = model_path or config.MODEL_SAVE_PATH
        self.model = None
        self.shot_classes = config.SHOT_CLASSES
        self.num_classes = config.NUM_CLASSES
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load trained model with compatibility fixes"""
        if not Path(self.model_path).exists():
            raise FileNotFoundError(
                f"Model not found at {self.model_path}. "
                "Please train the model first using model_training.py"
            )
        
        try:
            print(f"Loading trained model from {self.model_path}...")
            
            # Method 1: Try loading with compile=False
            try:
                self.model = tf.keras.models.load_model(
                    self.model_path, 
                    compile=False
                )
                print("Model loaded successfully!")
                
            except Exception as e1:
                print(f"First loading attempt failed: {str(e1)[:100]}")
                
                # Method 2: Try rebuilding architecture and loading weights
                try:
                    print("Attempting to rebuild model and load weights...")
                    from model_architecture import ShotClassifierModel
                    
                    # Rebuild model architecture
                    model_builder = ShotClassifierModel(
                        base_model_name=config.SELECTED_BASE_MODEL
                    )
                    self.model = model_builder.build_model(multi_output=True)
                    
                    # Try loading weights from separate weights file
                    weights_path = str(self.model_path).replace('.h5', '_weights.h5')
                    if Path(weights_path).exists():
                        self.model.load_weights(weights_path)
                        print("Weights loaded from separate file!")
                    else:
                        # Try extracting weights from full model
                        print("Extracting weights from saved model...")
                        temp_model = tf.keras.models.load_model(
                            self.model_path,
                            compile=False
                        )
                        self.model.set_weights(temp_model.get_weights())
                        print("Weights transferred successfully!")
                        
                except Exception as e2:
                    print(f"Second loading attempt failed: {str(e2)[:100]}")
                    
                    # Method 3: Try using SavedModel format
                    try:
                        saved_model_dir = config.MODELS_DIR / 'shot_classifier_saved_model'
                        if saved_model_dir.exists():
                            print("Attempting to load SavedModel format...")
                            self.model = tf.keras.models.load_model(saved_model_dir)
                            print("SavedModel loaded successfully!")
                        else:
                            raise Exception("No alternative model formats found")
                            
                    except Exception as e3:
                        print(f"All loading attempts failed!")
                        print(f"Error 1: {str(e1)[:100]}")
                        print(f"Error 2: {str(e2)[:100]}")
                        print(f"Error 3: {str(e3)[:100]}")
                        
                        # Final fallback: rebuild untrained model
                        print("\nWARNING: Creating untrained model structure.")
                        print("Please retrain the model using model_training.py")
                        from model_architecture import ShotClassifierModel
                        model_builder = ShotClassifierModel(
                            base_model_name=config.SELECTED_BASE_MODEL
                        )
                        self.model = model_builder.build_model(multi_output=True)
                        print("Untrained model structure created.")
            
            print(f"Model ready!")
            print(f"   Classes: {self.num_classes}")
            print(f"   Input shape: {config.INPUT_SHAPE}")
            
        except Exception as e:
            print(f"Critical error loading model: {e}")
            raise
    
    def preprocess_frame(self, frame):
        """
        Preprocess frame for model inference
        
        Args:
            frame: Input frame (BGR or RGB)
            
        Returns:
            Preprocessed frame ready for model
        """
        # Resize to model input size
        resized = cv2.resize(frame, (config.IMG_WIDTH, config.IMG_HEIGHT))
        
        # Convert BGR to RGB if needed
        if len(resized.shape) == 3 and resized.shape[2] == 3:
            # Check if it's BGR (OpenCV default)
            if np.mean(resized[:,:,0]) > np.mean(resized[:,:,2]):
                resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        normalized = resized.astype('float32') / 255.0
        
        return normalized
    
    def predict_single_frame(self, frame):
        """
        Predict shot type from single frame
        
        Args:
            frame: Input frame
            
        Returns:
            Prediction dictionary
        """
        if self.model is None:
            raise RuntimeError("Model not loaded!")
        
        # Preprocess
        preprocessed = self.preprocess_frame(frame)
        
        # Add batch dimension
        batch = np.expand_dims(preprocessed, axis=0)
        
        # Predict
        predictions = self.model.predict(batch, verbose=0)
        
        # Handle multi-output model
        if isinstance(predictions, list):
            shot_type_probs = predictions[0][0]  # First output (shot type)
            shot_quality_prob = predictions[1][0][0] if len(predictions) > 1 else None
        else:
            shot_type_probs = predictions[0]
            shot_quality_prob = None
        
        # Get predicted class
        predicted_class_idx = np.argmax(shot_type_probs)
        predicted_class = self.shot_classes[predicted_class_idx]
        confidence = float(shot_type_probs[predicted_class_idx])
        
        # Get top 3 predictions
        top_3_indices = np.argsort(shot_type_probs)[-3:][::-1]
        top_3_predictions = [
            {
                'shot_type': self.shot_classes[idx],
                'confidence': float(shot_type_probs[idx])
            }
            for idx in top_3_indices
        ]
        
        result = {
            'predicted_shot_type': predicted_class,
            'confidence': confidence,
            'top_3_predictions': top_3_predictions,
            'all_probabilities': {
                self.shot_classes[i]: float(shot_type_probs[i])
                for i in range(len(self.shot_classes))
            }
        }
        
        # Add quality prediction if available
        if shot_quality_prob is not None:
            result['shot_quality'] = {
                'is_powerful': shot_quality_prob > config.BINARY_THRESHOLD,
                'quality_score': float(shot_quality_prob),
                'category': 'Powerful' if shot_quality_prob > config.BINARY_THRESHOLD else 'Weak'
            }
        
        return result
    
    def predict_multiple_frames(self, frames):
        """
        Predict shot types for multiple frames
        
        Args:
            frames: List of frames
            
        Returns:
            List of predictions for each frame
        """
        print(f"Predicting shot types for {len(frames)} frames...")
        
        predictions = []
        
        for i, frame in enumerate(frames):
            pred = self.predict_single_frame(frame)
            pred['frame_index'] = i
            predictions.append(pred)
        
        print(f"Predictions complete!")
        return predictions
    
    def predict_video_consensus(self, frames, method='voting'):
        """
        Predict shot type from video using consensus of multiple frames
        
        Args:
            frames: List of frames from video
            method: Consensus method ('voting', 'confidence', 'weighted')
            
        Returns:
            Final prediction with consensus
        """
        print(f"Analyzing video with {len(frames)} frames...")
        print(f"   Consensus method: {method}")
        
        # Get predictions for all frames
        frame_predictions = self.predict_multiple_frames(frames)
        
        if method == 'voting':
            result = self._voting_consensus(frame_predictions)
        elif method == 'confidence':
            result = self._confidence_consensus(frame_predictions)
        elif method == 'weighted':
            result = self._weighted_consensus(frame_predictions)
        else:
            print(f"Unknown method '{method}', using 'voting'")
            result = self._voting_consensus(frame_predictions)
        
        # Add frame predictions
        result['frame_predictions'] = frame_predictions
        result['total_frames_analyzed'] = len(frames)
        
        return result
    
    def _voting_consensus(self, predictions):
        """
        Simple majority voting consensus
        
        Args:
            predictions: List of frame predictions
            
        Returns:
            Consensus prediction
        """
        # Count votes for each shot type
        votes = {}
        for pred in predictions:
            shot_type = pred['predicted_shot_type']
            votes[shot_type] = votes.get(shot_type, 0) + 1
        
        # Get winner
        winner = max(votes.items(), key=lambda x: x[1])
        predicted_shot_type = winner[0]
        vote_count = winner[1]
        
        # Calculate consensus confidence
        consensus_confidence = vote_count / len(predictions)
        
        # Get average confidence for the winning class
        avg_confidence = np.mean([
            pred['confidence'] 
            for pred in predictions 
            if pred['predicted_shot_type'] == predicted_shot_type
        ])
        
        return {
            'predicted_shot_type': predicted_shot_type,
            'confidence': float(avg_confidence),
            'consensus_confidence': float(consensus_confidence),
            'vote_distribution': votes,
            'method': 'voting'
        }
    
    def _confidence_consensus(self, predictions):
        """
        Select prediction with highest confidence
        
        Args:
            predictions: List of frame predictions
            
        Returns:
            Highest confidence prediction
        """
        # Find prediction with highest confidence
        best_pred = max(predictions, key=lambda x: x['confidence'])
        
        # Calculate how many frames agree
        agreement_count = sum(
            1 for pred in predictions 
            if pred['predicted_shot_type'] == best_pred['predicted_shot_type']
        )
        
        consensus_confidence = agreement_count / len(predictions)
        
        return {
            'predicted_shot_type': best_pred['predicted_shot_type'],
            'confidence': best_pred['confidence'],
            'consensus_confidence': float(consensus_confidence),
            'agreeing_frames': agreement_count,
            'method': 'confidence'
        }
    
    def _weighted_consensus(self, predictions):
        """
        Weighted average of all predictions
        
        Args:
            predictions: List of frame predictions
            
        Returns:
            Weighted consensus prediction
        """
        # Calculate weighted probabilities
        weighted_probs = np.zeros(self.num_classes)
        total_weight = 0
        
        for pred in predictions:
            weight = pred['confidence']  # Use confidence as weight
            for i, shot_type in enumerate(self.shot_classes):
                weighted_probs[i] += pred['all_probabilities'][shot_type] * weight
            total_weight += weight
        
        # Normalize
        weighted_probs /= total_weight
        
        # Get predicted class
        predicted_class_idx = np.argmax(weighted_probs)
        predicted_shot_type = self.shot_classes[predicted_class_idx]
        confidence = float(weighted_probs[predicted_class_idx])
        
        # Calculate consensus
        agreement_count = sum(
            1 for pred in predictions 
            if pred['predicted_shot_type'] == predicted_shot_type
        )
        consensus_confidence = agreement_count / len(predictions)
        
        return {
            'predicted_shot_type': predicted_shot_type,
            'confidence': confidence,
            'consensus_confidence': float(consensus_confidence),
            'weighted_probabilities': {
                self.shot_classes[i]: float(weighted_probs[i])
                for i in range(self.num_classes)
            },
            'method': 'weighted'
        }
    
    def get_shot_category(self, shot_type):
        """
        Get shot category (power/technique/aerial)
        
        Args:
            shot_type: Predicted shot type
            
        Returns:
            Shot category
        """
        if shot_type in config.POWER_SHOTS:
            return 'power'
        elif shot_type in config.TECHNIQUE_SHOTS:
            return 'technique'
        elif shot_type in config.AERIAL_SHOTS:
            return 'aerial'
        else:
            return 'other'
    
    def analyze_shot_distribution(self, predictions):
        """
        Analyze distribution of shot types in video
        
        Args:
            predictions: List of frame predictions
            
        Returns:
            Distribution analysis
        """
        # Count shot types
        distribution = {}
        for pred in predictions:
            shot_type = pred['predicted_shot_type']
            distribution[shot_type] = distribution.get(shot_type, 0) + 1
        
        # Calculate percentages
        total = len(predictions)
        distribution_pct = {
            shot_type: (count / total) * 100
            for shot_type, count in distribution.items()
        }
        
        # Categorize
        categories = {'power': 0, 'technique': 0, 'aerial': 0, 'other': 0}
        for shot_type, count in distribution.items():
            category = self.get_shot_category(shot_type)
            categories[category] += count
        
        return {
            'distribution': distribution,
            'distribution_percentage': distribution_pct,
            'categories': categories,
            'total_frames': total
        }


# Test the classifier
if __name__ == "__main__":
    print("="*70)
    print("TESTING SHOT CLASSIFIER")
    print("="*70)
    
    # Check if model exists
    if not config.MODEL_SAVE_PATH.exists():
        print("Trained model not found!")
        print(f"   Expected path: {config.MODEL_SAVE_PATH}")
        print("\nPlease train the model first:")
        print("   python model_training.py")
        sys.exit(1)
    
    # Initialize classifier
    try:
        classifier = ShotClassifier()
        print("\nClassifier initialized!")
        print(f"   Shot types: {classifier.num_classes}")
    except Exception as e:
        print(f"Failed to initialize classifier: {e}")
        sys.exit(1)
    
    # Test with sample image if provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        
        print(f"\nTesting on image: {image_path}")
        
        # Load image
        frame = cv2.imread(image_path)
        
        if frame is None:
            print("Cannot load image")
            sys.exit(1)
        
        # Predict
        result = classifier.predict_single_frame(frame)
        
        print("\n" + "="*70)
        print("PREDICTION RESULTS")
        print("="*70)
        print(f"Predicted Shot Type: {result['predicted_shot_type']}")
        print(f"Confidence: {result['confidence']:.2%}")
        
        print("\nTop 3 Predictions:")
        for i, pred in enumerate(result['top_3_predictions'], 1):
            print(f"   {i}. {pred['shot_type']}: {pred['confidence']:.2%}")
        
        if 'shot_quality' in result:
            quality = result['shot_quality']
            print(f"\nShot Quality:")
            print(f"   Category: {quality['category']}")
            print(f"   Score: {quality['quality_score']:.2%}")
        
        print("="*70)
    
    print("\nClassifier test complete!")