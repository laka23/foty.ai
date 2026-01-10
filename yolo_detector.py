"""
Football Performance Analyzer - YOLO Detection Module
Detect players and ball in football videos/frames
Uses YOLOv8 for real-time object detection
"""

import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import config

class FootballYOLODetector:
    """
    YOLO-based detector for football analysis
    Detects: Players, Ball, and relevant objects
    """
    
    def __init__(self, model_path=None, confidence=None):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model (None = use config)
            confidence: Detection confidence threshold (None = use config)
        """
        self.model_path = model_path or config.YOLO_MODEL_PATH
        self.confidence = confidence or config.YOLO_CONFIDENCE
        self.model = None
        self.class_names = []
        
        # Load YOLO model
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            print(f"🔄 Loading YOLO model from {self.model_path}...")
            self.model = YOLO(config.YOLO_MODEL)
            self.class_names = self.model.names
            print(f"✅ YOLO model loaded successfully!")
            print(f"   Classes available: {len(self.class_names)}")
            print(f"   Target classes: Person (0), Sports Ball (32)")
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
            raise
    
    def detect_objects(self, frame, return_annotated=True):
        """
        Detect objects in a frame
        
        Args:
            frame: Input frame (BGR format)
            return_annotated: Whether to return annotated frame
            
        Returns:
            Dictionary with detections and optional annotated frame
        """
        # Run detection
        results = self.model(frame, conf=self.confidence, verbose=False)
        
        # Extract detections
        detections = {
            'players': [],
            'balls': [],
            'other': []
        }
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.class_names[class_id]
                
                detection = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': confidence,
                    'class_id': class_id,
                    'class_name': class_name,
                    'center': [(x1 + x2) / 2, (y1 + y2) / 2],
                    'area': (x2 - x1) * (y2 - y1)
                }
                
                # Categorize detection
                if class_id == 0:  # Person
                    detections['players'].append(detection)
                elif class_id == 32:  # Sports ball
                    detections['balls'].append(detection)
                else:
                    detections['other'].append(detection)
        
        # Get annotated frame if requested
        annotated_frame = None
        if return_annotated:
            annotated_frame = results[0].plot()
        
        return {
            'detections': detections,
            'annotated_frame': annotated_frame,
            'total_objects': len(detections['players']) + len(detections['balls']) + len(detections['other'])
        }
    
    def detect_player_and_ball(self, frame):
        """
        Detect primary player and ball in frame
        
        Args:
            frame: Input frame
            
        Returns:
            Dictionary with player and ball info
        """
        result = self.detect_objects(frame, return_annotated=False)
        detections = result['detections']
        
        # Find primary player (largest person)
        primary_player = None
        if detections['players']:
            primary_player = max(detections['players'], key=lambda x: x['area'])
        
        # Find ball (highest confidence)
        ball = None
        if detections['balls']:
            ball = max(detections['balls'], key=lambda x: x['confidence'])
        
        return {
            'player': primary_player,
            'ball': ball,
            'player_count': len(detections['players']),
            'ball_count': len(detections['balls'])
        }
    
    def track_player_movement(self, frames):
        """
        Track player movement across frames
        
        Args:
            frames: List of frames
            
        Returns:
            List of player positions per frame
        """
        player_positions = []
        
        print("🏃 Tracking player movement...")
        
        for i, frame in enumerate(frames):
            result = self.detect_player_and_ball(frame)
            
            if result['player']:
                player_positions.append({
                    'frame_index': i,
                    'position': result['player']['center'],
                    'bbox': result['player']['bbox'],
                    'confidence': result['player']['confidence']
                })
        
        print(f"✅ Tracked player in {len(player_positions)}/{len(frames)} frames")
        return player_positions
    
    def analyze_shot_mechanics(self, frame):
        """
        Analyze shot mechanics from frame
        Detects player posture, ball position, etc.
        
        Args:
            frame: Input frame during shot
            
        Returns:
            Dictionary with mechanics analysis
        """
        result = self.detect_player_and_ball(frame)
        
        analysis = {
            'player_detected': result['player'] is not None,
            'ball_detected': result['ball'] is not None,
            'mechanics_score': 0.0,
            'issues': []
        }
        
        if not result['player']:
            analysis['issues'].append("Player not clearly visible")
            return analysis
        
        if not result['ball']:
            analysis['issues'].append("Ball not detected")
            analysis['mechanics_score'] = 0.5
            return analysis
        
        # Calculate relative positions
        player_center = result['player']['center']
        ball_center = result['ball']['center']
        
        # Distance between player and ball
        distance = np.sqrt(
            (player_center[0] - ball_center[0])**2 + 
            (player_center[1] - ball_center[1])**2
        )
        
        # Player and ball sizes
        player_bbox = result['player']['bbox']
        player_height = player_bbox[3] - player_bbox[1]
        
        # Analyze mechanics
        score = 0.0
        
        # 1. Ball-player proximity
        if distance < player_height * 0.5:
            score += 0.3
            analysis['close_contact'] = True
        else:
            analysis['issues'].append("Ball too far from player")
        
        # 2. Ball position relative to player
        ball_relative_y = ball_center[1] - player_center[1]
        if ball_relative_y > 0:  # Ball below player center (good for ground shots)
            score += 0.2
            analysis['ball_position'] = 'ground_level'
        else:
            analysis['ball_position'] = 'elevated'
        
        # 3. Player stance (based on bbox aspect ratio)
        player_width = player_bbox[2] - player_bbox[0]
        aspect_ratio = player_width / player_height if player_height > 0 else 0
        
        if 0.4 < aspect_ratio < 0.7:
            score += 0.3
            analysis['stance'] = 'balanced'
        else:
            analysis['stance'] = 'unbalanced'
            analysis['issues'].append("Player stance appears unbalanced")
        
        # 4. Detection confidence
        score += result['player']['confidence'] * 0.2
        
        analysis['mechanics_score'] = min(score, 1.0)
        analysis['distance_to_ball'] = distance
        
        return analysis
    
    def create_annotated_video(self, input_video_path, output_video_path):
        """
        Create annotated video with detections
        
        Args:
            input_video_path: Input video path
            output_video_path: Output video path
        """
        print(f"🎬 Creating annotated video...")
        
        cap = cv2.VideoCapture(str(input_video_path))
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))
        
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect and annotate
            result = self.detect_objects(frame, return_annotated=True)
            annotated_frame = result['annotated_frame']
            
            # Add frame info
            cv2.putText(
                annotated_frame,
                f"Frame: {frame_count}/{total_frames}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            out.write(annotated_frame)
            frame_count += 1
            
            if frame_count % 30 == 0:
                print(f"   Processed {frame_count}/{total_frames} frames")
        
        cap.release()
        out.release()
        
        print(f"✅ Annotated video saved to {output_video_path}")
    
    def detect_ball_trajectory(self, frames):
        """
        Detect ball trajectory across frames
        
        Args:
            frames: List of frames
            
        Returns:
            List of ball positions
        """
        trajectory = []
        
        print("⚽ Detecting ball trajectory...")
        
        for i, frame in enumerate(frames):
            result = self.detect_player_and_ball(frame)
            
            if result['ball']:
                trajectory.append({
                    'frame_index': i,
                    'position': result['ball']['center'],
                    'confidence': result['ball']['confidence']
                })
        
        # Calculate trajectory metrics
        if len(trajectory) > 1:
            # Calculate velocity
            velocities = []
            for i in range(1, len(trajectory)):
                pos1 = trajectory[i-1]['position']
                pos2 = trajectory[i]['position']
                
                distance = np.sqrt(
                    (pos2[0] - pos1[0])**2 + 
                    (pos2[1] - pos1[1])**2
                )
                velocities.append(distance)
            
            avg_velocity = np.mean(velocities) if velocities else 0
            max_velocity = max(velocities) if velocities else 0
            
            print(f"✅ Ball detected in {len(trajectory)}/{len(frames)} frames")
            print(f"   Average velocity: {avg_velocity:.2f} pixels/frame")
            print(f"   Max velocity: {max_velocity:.2f} pixels/frame")
            
            return {
                'trajectory': trajectory,
                'avg_velocity': avg_velocity,
                'max_velocity': max_velocity,
                'frames_detected': len(trajectory)
            }
        
        return {
            'trajectory': trajectory,
            'avg_velocity': 0,
            'max_velocity': 0,
            'frames_detected': len(trajectory)
        }
    
    def estimate_shot_power(self, frames):
        """
        Estimate shot power based on ball trajectory
        
        Args:
            frames: List of frames
            
        Returns:
            Shot power estimation
        """
        trajectory_data = self.detect_ball_trajectory(frames)
        
        if trajectory_data['frames_detected'] < 2:
            return {
                'power_score': 0.0,
                'power_category': 'unknown',
                'confidence': 0.0
            }
        
        # Calculate power based on velocity
        avg_velocity = trajectory_data['avg_velocity']
        max_velocity = trajectory_data['max_velocity']
        
        # Normalize velocity (assuming max pixel velocity ~100)
        normalized_velocity = min(max_velocity / 100.0, 1.0)
        
        # Determine power category
        if normalized_velocity > 0.7:
            power_category = 'powerful'
            power_score = 0.8 + (normalized_velocity - 0.7) * 0.67
        elif normalized_velocity > 0.4:
            power_category = 'medium'
            power_score = 0.4 + (normalized_velocity - 0.4) * 1.33
        else:
            power_category = 'weak'
            power_score = normalized_velocity * 1.0
        
        return {
            'power_score': power_score,
            'power_category': power_category,
            'avg_velocity': avg_velocity,
            'max_velocity': max_velocity,
            'confidence': min(trajectory_data['frames_detected'] / 10.0, 1.0)
        }


class FootballSceneAnalyzer:
    """
    High-level scene analysis for football videos
    Combines YOLO detection with heuristics
    """
    
    def __init__(self):
        """Initialize scene analyzer"""
        self.detector = FootballYOLODetector()
    
    def analyze_frame_quality(self, frame):
        """
        Analyze if frame is suitable for shot classification
        
        Args:
            frame: Input frame
            
        Returns:
            Quality score and recommendations
        """
        result = self.detector.detect_player_and_ball(frame)
        
        quality_score = 0.0
        issues = []
        
        # Check player detection
        if result['player']:
            quality_score += 0.5
            
            # Check player size (should be prominent)
            player_area = result['player']['area']
            frame_area = frame.shape[0] * frame.shape[1]
            player_ratio = player_area / frame_area
            
            if player_ratio > 0.1:
                quality_score += 0.2
            else:
                issues.append("Player too small in frame")
        else:
            issues.append("Player not detected")
        
        # Check ball detection
        if result['ball']:
            quality_score += 0.3
        else:
            issues.append("Ball not detected")
        
        return {
            'quality_score': quality_score,
            'is_suitable': quality_score >= 0.5,
            'issues': issues,
            'player_detected': result['player'] is not None,
            'ball_detected': result['ball'] is not None
        }
    
    def filter_best_frames(self, frames):
        """
        Filter frames to get best quality frames for classification
        
        Args:
            frames: List of frames
            
        Returns:
            Filtered list of best frames
        """
        print("🔍 Filtering best quality frames...")
        
        frame_scores = []
        
        for i, frame in enumerate(frames):
            quality = self.analyze_frame_quality(frame)
            frame_scores.append({
                'index': i,
                'frame': frame,
                'quality_score': quality['quality_score'],
                'is_suitable': quality['is_suitable']
            })
        
        # Sort by quality score
        frame_scores.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # Get top frames
        best_frames = [f for f in frame_scores if f['is_suitable']]
        
        if not best_frames:
            print("⚠️ No suitable frames found, using top 5 frames")
            best_frames = frame_scores[:5]
        
        print(f"✅ Selected {len(best_frames)} best quality frames")
        
        return [f['frame'] for f in best_frames]
    

    
    def analyze_complete_shot(self, frames):
        """
        Complete shot analysis combining all detections
        
        Args:
            frames: List of frames from video
            
        Returns:
            Complete analysis dictionary
        """
        print("="*70)
        print("⚽ COMPLETE SHOT ANALYSIS")
        print("="*70)
        
        # Filter best frames
        best_frames = self.filter_best_frames(frames)
        
        # Analyze mechanics on best frame
        mechanics = self.detector.analyze_shot_mechanics(best_frames[0])
        
        # Track player movement
        player_positions = self.detector.track_player_movement(frames)
        
        # Estimate shot power
        power = self.detector.estimate_shot_power(frames)
        
        # Overall quality assessment
        overall_score = (
            mechanics['mechanics_score'] * 0.4 +
            power['power_score'] * 0.3 +
            (len(player_positions) / len(frames)) * 0.3
        )
        
        analysis = {
            'mechanics': mechanics,
            'power': power,
            'player_tracking': {
                'frames_tracked': len(player_positions),
                'total_frames': len(frames),
                'tracking_ratio': len(player_positions) / len(frames)
            },
            'overall_score': overall_score,
            'best_frames_count': len(best_frames)
        }
        
        print("="*70)
        print("✅ SHOT ANALYSIS COMPLETE")
        print(f"   Mechanics Score: {mechanics['mechanics_score']:.2f}")
        print(f"   Power Score: {power['power_score']:.2f}")
        print(f"   Power Category: {power['power_category']}")
        print(f"   Overall Score: {overall_score:.2f}")
        print("="*70)
        
        return analysis
    

    
    
def validate_football_video(self, frames, min_detections=3):
    """
    Validate if video contains football content
    
    Args:
        frames: List of video frames
        min_detections: Minimum number of frames that must contain football elements
        
    Returns:
        Dictionary with validation result
    """
    football_frame_count = 0
    total_players = 0
    total_balls = 0
    
    # Sample frames for validation (check every 5th frame)
    sample_frames = frames[::5] if len(frames) > 5 else frames
    
    for frame in sample_frames:
        result = self.detect_player_and_ball(frame)
        
        if result['player'] or result['ball']:
            football_frame_count += 1
            total_players += result['player_count']
            total_balls += result['ball_count']
    
    # Calculate validation metrics
    detection_rate = football_frame_count / len(sample_frames) if sample_frames else 0
    is_valid = football_frame_count >= min_detections and detection_rate >= 0.3
    
    return {
        'is_valid_football_video': is_valid,
        'detection_rate': detection_rate,
        'frames_with_football': football_frame_count,
        'total_sampled_frames': len(sample_frames),
        'total_players_detected': total_players,
        'total_balls_detected': total_balls,
        'confidence_score': detection_rate * 100,
        'reason': 'Valid football video' if is_valid else 
                  'Not enough football elements detected. Please upload a video with clear football actions.'
    }

# Test the YOLO detector
if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("🎯 TESTING YOLO DETECTOR")
    print("="*70)
    
    # Test basic detection
    detector = FootballYOLODetector()
    
    print("\n✅ YOLO detector initialized successfully!")
    print(f"   Model: {config.YOLO_MODEL}")
    print(f"   Confidence threshold: {config.YOLO_CONFIDENCE}")
    print(f"   Target classes: Person (0), Sports Ball (32)")
    
    # If video path provided, test on video
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        
        print(f"\n🎬 Testing on video: {video_path}")
        
        # Load video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print("❌ Cannot open video")
            sys.exit(1)
        
        # Test on first few frames
        frames_to_test = 5
        frames = []
        
        for i in range(frames_to_test):
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        
        print(f"\n📊 Testing detection on {len(frames)} frames...")
        
        # Create scene analyzer
        analyzer = FootballSceneAnalyzer()
        
        # Analyze frames
        for i, frame in enumerate(frames):
            print(f"\n--- Frame {i+1} ---")
            result = detector.detect_player_and_ball(frame)
            print(f"Players detected: {result['player_count']}")
            print(f"Balls detected: {result['ball_count']}")
            
            if result['player']:
                print(f"Primary player confidence: {result['player']['confidence']:.2f}")
            if result['ball']:
                print(f"Ball confidence: {result['ball']['confidence']:.2f}")
        
        # Analyze shot
        shot_analysis = analyzer.analyze_complete_shot(frames)
        
        print("\n" + "="*70)
        print("📈 SHOT ANALYSIS RESULTS")
        print("="*70)
        print(f"Overall Score: {shot_analysis['overall_score']:.2f}/1.0")
        print(f"Mechanics Score: {shot_analysis['mechanics']['mechanics_score']:.2f}")
        print(f"Power Category: {shot_analysis['power']['power_category']}")
        print(f"Power Score: {shot_analysis['power']['power_score']:.2f}")
        print("="*70)
    
    print("\n✅ YOLO detector test complete!")