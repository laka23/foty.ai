"""
Football Video Validator Module
Validates if uploaded video contains actual football content
Uses YOLO detection to identify football-related objects
"""

import cv2
import numpy as np
from pathlib import Path
import config
from yolo_detector import FootballYOLODetector

class FootballVideoValidator:
    """
    Validates if a video contains football content before processing
    Prevents wasting resources on non-football videos
    """
    
    def __init__(self, min_football_frames=3, min_detection_rate=0.25):
        """
        Initialize validator
        
        Args:
            min_football_frames: Minimum frames that must contain football elements
            min_detection_rate: Minimum percentage of frames with football content
        """
        self.detector = FootballYOLODetector()
        self.min_football_frames = min_football_frames
        self.min_detection_rate = min_detection_rate
    
    def validate_video(self, video_path, sample_rate=5):
        """
        Validate if video contains football content
        
        Args:
            video_path: Path to video file
            sample_rate: Check every Nth frame (5 = check every 5th frame)
            
        Returns:
            Dictionary with validation results
        """
        print("\n" + "="*70)
        print("🔍 VALIDATING FOOTBALL CONTENT")
        print("="*70)
        
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return {
                'is_valid': False,
                'reason': 'Cannot open video file',
                'confidence_score': 0,
                'details': {}
            }
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Counters for detection
        frames_checked = 0
        frames_with_player = 0
        frames_with_ball = 0
        frames_with_football = 0
        total_players = 0
        total_balls = 0
        
        print(f"📹 Video: {total_frames} frames @ {fps} FPS")
        print(f"🔎 Checking every {sample_rate} frames...")
        
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Sample frames
            if frame_idx % sample_rate == 0:
                frames_checked += 1
                
                # Detect players and ball
                result = self.detector.detect_player_and_ball(frame)
                
                has_player = result['player'] is not None
                has_ball = result['ball'] is not None
                
                if has_player:
                    frames_with_player += 1
                    total_players += result['player_count']
                
                if has_ball:
                    frames_with_ball += 1
                    total_balls += result['ball_count']
                
                # Frame is "football" if it has player OR ball
                if has_player or has_ball:
                    frames_with_football += 1
                
                # Print progress every 20 frames checked
                if frames_checked % 20 == 0:
                    print(f"   Checked {frames_checked} frames... Football: {frames_with_football}")
            
            frame_idx += 1
        
        cap.release()
        
        # Calculate metrics
        detection_rate = frames_with_football / frames_checked if frames_checked > 0 else 0
        player_rate = frames_with_player / frames_checked if frames_checked > 0 else 0
        ball_rate = frames_with_ball / frames_checked if frames_checked > 0 else 0
        
        # Confidence score (0-100)
        confidence_score = detection_rate * 100
        
        # Validation decision
        is_valid = (
            frames_with_football >= self.min_football_frames and 
            detection_rate >= self.min_detection_rate
        )
        
        # Detailed reason
        if is_valid:
            reason = "✅ Valid football video detected"
            suggestion = "Video contains sufficient football content for analysis"
        else:
            if frames_with_football < self.min_football_frames:
                reason = f"❌ Too few football elements detected ({frames_with_football}/{self.min_football_frames} required frames)"
            else:
                reason = f"❌ Detection rate too low ({detection_rate:.1%} vs {self.min_detection_rate:.1%} required)"
            
            suggestion = "Please upload a video with clear football actions:\n"
            suggestion += "  • Players and ball should be clearly visible\n"
            suggestion += "  • Good lighting and camera angle\n"
            suggestion += "  • Training or match footage works best\n"
            suggestion += "  • Avoid videos with only spectators or celebrations"
        
        result = {
            'is_valid': is_valid,
            'reason': reason,
            'confidence_score': confidence_score,
            'details': {
                'frames_analyzed': frames_checked,
                'frames_with_football': frames_with_football,
                'frames_with_player': frames_with_player,
                'frames_with_ball': frames_with_ball,
                'total_players_detected': total_players,
                'total_balls_detected': total_balls,
                'detection_rate': detection_rate,
                'player_detection_rate': player_rate,
                'ball_detection_rate': ball_rate,
                'suggestion': suggestion
            }
        }
        
        # Print results
        print("="*70)
        print(f"{'✅ VALID' if is_valid else '❌ INVALID'} - {reason}")
        print(f"   Confidence: {confidence_score:.1f}%")
        print(f"   Detection Rate: {detection_rate:.1%}")
        print(f"   Frames Analyzed: {frames_checked}")
        print(f"   Football Frames: {frames_with_football}")
        print(f"   Player Detections: {total_players}")
        print(f"   Ball Detections: {total_balls}")
        print("="*70 + "\n")
        
        return result
    
    def validate_frames(self, frames):
        """
        Validate a list of frames (alternative method)
        
        Args:
            frames: List of video frames
            
        Returns:
            Dictionary with validation results
        """
        frames_with_football = 0
        total_players = 0
        total_balls = 0
        
        for frame in frames:
            result = self.detector.detect_player_and_ball(frame)
            
            if result['player'] or result['ball']:
                frames_with_football += 1
                total_players += result['player_count']
                total_balls += result['ball_count']
        
        detection_rate = frames_with_football / len(frames) if frames else 0
        confidence_score = detection_rate * 100
        
        is_valid = (
            frames_with_football >= self.min_football_frames and 
            detection_rate >= self.min_detection_rate
        )
        
        return {
            'is_valid': is_valid,
            'confidence_score': confidence_score,
            'detection_rate': detection_rate,
            'frames_with_football': frames_with_football,
            'total_frames': len(frames),
            'total_players': total_players,
            'total_balls': total_balls
        }


# Quick validation function
def quick_validate_football_video(video_path):
    """
    Quick validation function - can be called from anywhere
    
    Args:
        video_path: Path to video file
        
    Returns:
        True if valid football video, False otherwise
    """
    validator = FootballVideoValidator()
    result = validator.validate_video(video_path)
    return result['is_valid']


# Test the validator
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python football_validator.py <video_path>")
        print("Example: python football_validator.py sample_video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    print("="*70)
    print("🔍 TESTING FOOTBALL VIDEO VALIDATOR")
    print("="*70)
    
    # Create validator
    validator = FootballVideoValidator(
        min_football_frames=3,
        min_detection_rate=0.25
    )
    
    # Validate video
    result = validator.validate_video(video_path)
    
    # Print detailed results
    print("\n📊 VALIDATION RESULTS:")
    print(f"   Valid: {'✅ YES' if result['is_valid'] else '❌ NO'}")
    print(f"   Reason: {result['reason']}")
    print(f"   Confidence: {result['confidence_score']:.1f}%")
    
    if not result['is_valid']:
        print(f"\n💡 Suggestion:")
        print(f"   {result['details']['suggestion']}")
    
    print("\n✅ Test complete!")