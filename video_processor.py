"""
Football Performance Analyzer - Video Processing Module
Extract frames from videos, detect key moments, analyze shots
Hybrid Approach: Train on Images, Inference on Videos
"""

import cv2
import numpy as np
from pathlib import Path
import config
from tqdm import tqdm
import json

class VideoProcessor:
    """
    Process football videos for shot analysis
    Extracts key frames and prepares for CNN classification
    """
    
    def __init__(self, video_path):
        """
        Initialize video processor
        
        Args:
            video_path: Path to video file
        """
        self.video_path = Path(video_path)
        self.video_name = self.video_path.stem
        self.cap = None
        self.fps = 0
        self.total_frames = 0
        self.width = 0
        self.height = 0
        self.duration = 0
        
        # Initialize video capture
        self._initialize_video()
    
    def _initialize_video(self):
        """Initialize video capture and get properties"""
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {self.video_path}")
        
        self.cap = cv2.VideoCapture(str(self.video_path))
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")
        
        # Get video properties
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        print(f"✅ Video loaded: {self.video_name}")
        print(f"   Resolution: {self.width}x{self.height}")
        print(f"   FPS: {self.fps}")
        print(f"   Total Frames: {self.total_frames}")
        print(f"   Duration: {self.duration:.2f} seconds")
    
    def extract_key_frames(self, num_frames=None, method='uniform'):
        """
        Extract key frames from video
        
        Args:
            num_frames: Number of frames to extract (None = use config)
            method: Extraction method ('uniform', 'motion', 'smart')
            
        Returns:
            List of extracted frames
        """
        if num_frames is None:
            num_frames = config.FRAMES_PER_VIDEO
        
        print(f"\n🎬 Extracting {num_frames} key frames using '{method}' method...")
        
        if method == 'uniform':
            frames = self._extract_uniform_frames(num_frames)
        elif method == 'motion':
            frames = self._extract_motion_frames(num_frames)
        elif method == 'smart':
            frames = self._extract_smart_frames(num_frames)
        else:
            print(f"⚠️ Unknown method '{method}', using 'uniform'")
            frames = self._extract_uniform_frames(num_frames)
        
        print(f"✅ Extracted {len(frames)} frames")
        return frames
    
    def _extract_uniform_frames(self, num_frames):
        """
        Extract frames uniformly across video
        
        Args:
            num_frames: Number of frames to extract
            
        Returns:
            List of frames with metadata
        """
        frames = []
        
        # Calculate frame indices to extract
        frame_indices = np.linspace(0, self.total_frames - 1, num_frames, dtype=int)
        
        # Extract frames
        for idx in tqdm(frame_indices, desc="Extracting frames"):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = self.cap.read()
            
            if ret:
                # Preprocess frame
                processed_frame = self._preprocess_frame(frame)
                
                frames.append({
                    'frame': processed_frame,
                    'original_frame': frame,
                    'frame_number': idx,
                    'timestamp': idx / self.fps,
                    'method': 'uniform'
                })
        
        return frames
    
    def _extract_motion_frames(self, num_frames):
        """
        Extract frames based on motion detection
        High motion = likely shot moment
        
        Args:
            num_frames: Number of frames to extract
            
        Returns:
            List of frames with high motion
        """
        frames = []
        motion_scores = []
        
        print("🔍 Analyzing video motion...")
        
        # Calculate motion for all frames
        prev_frame = None
        for i in tqdm(range(0, self.total_frames, config.FRAME_SKIP), desc="Analyzing motion"):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, gray)
                motion_score = np.mean(diff)
                motion_scores.append({
                    'frame_number': i,
                    'score': motion_score,
                    'frame': frame
                })
            
            prev_frame = gray
        
        # Sort by motion score and get top frames
        motion_scores.sort(key=lambda x: x['score'], reverse=True)
        top_motion_frames = motion_scores[:num_frames]
        
        # Sort by frame number for chronological order
        top_motion_frames.sort(key=lambda x: x['frame_number'])
        
        # Process selected frames
        for item in top_motion_frames:
            processed_frame = self._preprocess_frame(item['frame'])
            frames.append({
                'frame': processed_frame,
                'original_frame': item['frame'],
                'frame_number': item['frame_number'],
                'timestamp': item['frame_number'] / self.fps,
                'motion_score': item['score'],
                'method': 'motion'
            })
        
        return frames
    
    def _extract_smart_frames(self, num_frames):
        """
        Smart frame extraction combining motion and uniform sampling
        
        Args:
            num_frames: Number of frames to extract
            
        Returns:
            List of smartly selected frames
        """
        # Use 60% motion-based, 40% uniform
        motion_frames_count = int(num_frames * 0.6)
        uniform_frames_count = num_frames - motion_frames_count
        
        print(f"📊 Smart extraction: {motion_frames_count} motion + {uniform_frames_count} uniform")
        
        # Get motion-based frames
        motion_frames = self._extract_motion_frames(motion_frames_count)
        
        # Get uniform frames
        uniform_frames = self._extract_uniform_frames(uniform_frames_count)
        
        # Combine and sort by timestamp
        all_frames = motion_frames + uniform_frames
        all_frames.sort(key=lambda x: x['timestamp'])
        
        # Update method
        for frame in all_frames:
            frame['method'] = 'smart'
        
        return all_frames
    
    def _preprocess_frame(self, frame):
        """
        Preprocess frame for CNN model
        
        Args:
            frame: Raw frame from video
            
        Returns:
            Preprocessed frame ready for model
        """
        # Resize to model input size
        resized = cv2.resize(frame, (config.IMG_WIDTH, config.IMG_HEIGHT))
        
        # Convert BGR to RGB (OpenCV uses BGR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        normalized = rgb.astype('float32') / 255.0
        
        return normalized
    
    def save_frames(self, frames, output_dir=None):
        """
        Save extracted frames to disk
        
        Args:
            frames: List of frame dictionaries
            output_dir: Output directory (None = use config)
            
        Returns:
            List of saved frame paths
        """
        if output_dir is None:
            output_dir = config.FRAMES_DIR / self.video_name
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        
        print(f"\n💾 Saving frames to {output_dir}...")
        
        for i, frame_data in enumerate(frames):
            # Save preprocessed frame (for model)
            preprocessed_path = output_dir / f"frame_{i:03d}_preprocessed.jpg"
            preprocessed_img = (frame_data['frame'] * 255).astype('uint8')
            preprocessed_img_bgr = cv2.cvtColor(preprocessed_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(preprocessed_path), preprocessed_img_bgr)
            
            # Save original frame (for visualization)
            original_path = output_dir / f"frame_{i:03d}_original.jpg"
            cv2.imwrite(str(original_path), frame_data['original_frame'])
            
            saved_paths.append({
                'preprocessed': preprocessed_path,
                'original': original_path,
                'timestamp': frame_data['timestamp'],
                'frame_number': frame_data['frame_number']
            })
        
        # Save metadata
        metadata = {
            'video_name': self.video_name,
            'total_frames_extracted': len(frames),
            'video_duration': self.duration,
            'extraction_method': frames[0]['method'] if frames else 'unknown',
            'frames': [
                {
                    'index': i,
                    'timestamp': f['timestamp'],
                    'frame_number': f['frame_number']
                }
                for i, f in enumerate(frames)
            ]
        }
        
        metadata_path = output_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        print(f"✅ Saved {len(saved_paths)} frames")
        print(f"✅ Metadata saved to {metadata_path}")
        
        return saved_paths
    
    def detect_shot_moments(self, frames, threshold=0.7):
        """
        Detect potential shot moments from frames
        Uses motion and ball detection heuristics
        
        Args:
            frames: List of frame dictionaries
            threshold: Confidence threshold for shot detection
            
        Returns:
            List of potential shot moments
        """
        shot_moments = []
        
        print("\n⚽ Detecting shot moments...")
        
        for i, frame_data in enumerate(frames):
            frame = frame_data['original_frame']
            
            # Convert to HSV for better ball detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Detect white/bright objects (likely ball)
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            mask = cv2.inRange(hsv, lower_white, upper_white)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Check for circular objects (potential ball)
            ball_detected = False
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 5000:  # Ball size range
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                    
                    if circularity > 0.7:  # Circular object
                        ball_detected = True
                        break
            
            # If ball detected or high motion, mark as potential shot
            confidence = 0.0
            if ball_detected:
                confidence += 0.5
            
            if 'motion_score' in frame_data and frame_data['motion_score'] > 30:
                confidence += 0.3
            
            if confidence >= threshold:
                shot_moments.append({
                    'frame_index': i,
                    'timestamp': frame_data['timestamp'],
                    'confidence': confidence,
                    'ball_detected': ball_detected
                })
        
        print(f"✅ Detected {len(shot_moments)} potential shot moments")
        return shot_moments
    
    def get_frame_batch(self, frames):
        """
        Prepare frames as batch for model prediction
        
        Args:
            frames: List of frame dictionaries
            
        Returns:
            Numpy array of frames ready for model
        """
        batch = np.array([f['frame'] for f in frames])
        return batch
    
    def release(self):
        """Release video capture"""
        if self.cap is not None:
            self.cap.release()
            print("✅ Video capture released")
    
    def __del__(self):
        """Destructor to ensure video is released"""
        self.release()


class VideoAnalyzer:
    """
    High-level video analysis for shot classification
    Combines frame extraction with CNN inference
    """
    
    def __init__(self, video_path):
        """
        Initialize analyzer
        
        Args:
            video_path: Path to video file
        """
        self.video_processor = VideoProcessor(video_path)
        self.frames = []
        self.shot_moments = []
    
    def analyze_video(self, extraction_method='smart', save_frames=True):
        """
        Complete video analysis pipeline
        
        Args:
            extraction_method: Frame extraction method
            save_frames: Whether to save frames to disk
            
        Returns:
            Analysis results dictionary
        """
        print("="*70)
        print("🎬 VIDEO ANALYSIS PIPELINE")
        print("="*70)
        
        # Step 1: Extract frames
        self.frames = self.video_processor.extract_key_frames(
            method=extraction_method
        )
        
        # Step 2: Detect shot moments
        self.shot_moments = self.video_processor.detect_shot_moments(self.frames)
        
        # Step 3: Save frames (optional)
        saved_paths = None
        if save_frames:
            saved_paths = self.video_processor.save_frames(self.frames)
        
        # Step 4: Prepare results
        results = {
            'video_name': self.video_processor.video_name,
            'duration': self.video_processor.duration,
            'total_frames': self.video_processor.total_frames,
            'fps': self.video_processor.fps,
            'extracted_frames': len(self.frames),
            'shot_moments': self.shot_moments,
            'frames': self.frames,
            'saved_paths': saved_paths
        }
        
        print("="*70)
        print("✅ VIDEO ANALYSIS COMPLETE")
        print(f"   Extracted Frames: {len(self.frames)}")
        print(f"   Shot Moments: {len(self.shot_moments)}")
        print("="*70)
        
        return results
    
    def get_batch_for_inference(self):
        """
        Get frame batch ready for CNN inference
        
        Returns:
            Numpy array of frames
        """
        return self.video_processor.get_frame_batch(self.frames)
    
    def cleanup(self):
        """Cleanup resources"""
        self.video_processor.release()


# Test the video processor
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_processor.py <video_path>")
        print("Example: python video_processor.py sample_shot.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    print("="*70)
    print("🎬 TESTING VIDEO PROCESSOR")
    print("="*70)
    
    # Create analyzer
    analyzer = VideoAnalyzer(video_path)
    
    # Analyze video
    results = analyzer.analyze_video(extraction_method='smart')
    
    # Print results
    print("\n📊 Analysis Results:")
    print(f"Video: {results['video_name']}")
    print(f"Duration: {results['duration']:.2f}s")
    print(f"Extracted Frames: {results['extracted_frames']}")
    print(f"Shot Moments Detected: {len(results['shot_moments'])}")
    
    if results['shot_moments']:
        print("\n⚽ Shot Moments:")
        for moment in results['shot_moments']:
            print(f"  - Time: {moment['timestamp']:.2f}s, Confidence: {moment['confidence']:.2f}")
    
    # Cleanup
    analyzer.cleanup()
    
    print("\n✅ Test complete!")
