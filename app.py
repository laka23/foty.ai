from flask import Flask, render_template, request, jsonify, url_for, session, redirect, flash
from werkzeug.utils import secure_filename
from football_validator import FootballVideoValidator
import os
import cv2
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import traceback
import logging
from contextlib import contextmanager
import mysql.connector
from mysql.connector import pooling
import time

from email_service import (
    send_welcome_email, 
    send_password_reset_email, 
    send_contact_message_to_team,
    send_contact_auto_reply,
    send_account_deletion_notification
)
import secrets

# Import custom modules
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_VIDEO_SIZE_MB * 1024 * 1024
app.config['UPLOAD_FOLDER'] = config.UPLOADS_DIR
app.config['RESULTS_FOLDER'] = config.OUTPUTS_DIR

# Create directories
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'foty.ai',
    'pool_name': 'football_pool',
    'pool_size': 10,
    'pool_reset_session': True,
    'autocommit': False,
    'connect_timeout': 30
}

# Create connection pool
try:
    connection_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
    logger.info("✓ Database connection pool created")
except Exception as e:
    logger.error(f"✗ Database pool failed: {e}")
    connection_pool = None

# AI modules
shot_classifier = None
yolo_detector = None
scene_analyzer = None
performance_scorer = None
recommendation_engine = None

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def initialize_models():
    """Initialize AI models with error handling"""
    global shot_classifier, yolo_detector, scene_analyzer, performance_scorer, recommendation_engine
    
    try:
        print("="*70)
        print(" Initializing AI models...")
        print("="*70)
        
        # Optional CNN Model
        try:
            if config.MODEL_SAVE_PATH.exists():
                from shot_classifier import ShotClassifier
                shot_classifier = ShotClassifier()
                print("✓ Shot Classifier loaded")
            else:
                print("ℹ  CNN model not found - using YOLO only")
                shot_classifier = None
        except Exception as e:
            print(f"ℹ  Shot Classifier unavailable: {e}")
            shot_classifier = None
        
        # Required YOLO
        from yolo_detector import FootballYOLODetector, FootballSceneAnalyzer
        yolo_detector = FootballYOLODetector()
        scene_analyzer = FootballSceneAnalyzer()
        print("✓ YOLO Detector loaded")
        print("✓ Scene Analyzer loaded")
        
        # Performance modules
        from performance_scorer import PerformanceScorer
        from recommendation_engine import RecommendationEngine
        performance_scorer = PerformanceScorer()
        recommendation_engine = RecommendationEngine()
        print("✓ Performance Scorer loaded")
        print("✓ Recommendation Engine loaded")
        
        print("="*70)
        print("✓ AI modules initialized!")
        if not shot_classifier:
            print("ℹ  Running in YOLO-only mode")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"✗ Model initialization error: {e}")
        traceback.print_exc()
        return False

models_loaded = initialize_models()

# ==================== DATABASE ====================

def get_db_connection_with_retry(max_retries=3, retry_delay=1):
    """Get database connection with retry"""
    for attempt in range(max_retries):
        try:
            if connection_pool:
                connection = connection_pool.get_connection()
            else:
                connection = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='',
                    database='foty.ai',
                    connect_timeout=30
                )
            
            if connection.is_connected():
                return connection
            
        except Exception as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
    return None

@contextmanager
def get_db_session():
    """Database session context manager"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection_with_retry()
        cursor = connection.cursor(dictionary=True)
        yield connection, cursor
    except Exception as e:
        if connection and connection.is_connected():
            connection.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def test_database_connection():
    """Test database"""
    try:
        with get_db_session() as (conn, cursor):
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            return {'success': True, 'message': 'Connected'} if result else {'success': False}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def save_analysis_to_database(file_path, original_filename, results):
    """Save analysis to database"""
    try:
        with get_db_session() as (conn, cursor):
            cursor.execute("SELECT user_id FROM systemuser WHERE email=%s", (session['user'],))
            user = cursor.fetchone()
            if not user:
                return {'success': False, 'error': 'User not found'}
            user_id = user['user_id']

            cursor.execute("SELECT player_id FROM player WHERE user_id=%s", (user_id,))
            player = cursor.fetchone()
            if not player:
                cursor.execute("INSERT INTO player (user_id, position, team_name) VALUES (%s, %s, %s)",
                             (user_id, 'Forward', 'Default Team'))
                conn.commit()
                player_id = cursor.lastrowid
            else:
                player_id = player['player_id']

            cursor.execute("INSERT INTO videoinput (player_id, upload_time, file_path, original_filename) VALUES (%s, %s, %s, %s)",
                         (player_id, datetime.now(), file_path, original_filename))
            conn.commit()
            video_id = cursor.lastrowid

            cursor.execute("INSERT INTO aiengine (video_id, process_date, status, model_version) VALUES (%s, %s, %s, %s)",
                         (video_id, datetime.now(), "Completed", "v4.5-YOLO"))
            conn.commit()
            engine_id = cursor.lastrowid

            overall_score = results['performance_score']['overall_score']
            shot_type = results['shot_prediction']['shot_type']
            
            cursor.execute("INSERT INTO motionanalysis (engine_id, technique_score, balance_score, movement_efficiency, kick_count, shots_detected, shot_accuracy) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                         (engine_id, overall_score, overall_score, 85.0, 1, 1, overall_score * 10))
            conn.commit()
            analysis_id = cursor.lastrowid

            power_score = results['performance_score']['component_scores'].get('technique_quality', 7.0)
            cursor.execute("INSERT INTO playermetrics (player_id, analysis_id, stamina, strength) VALUES (%s, %s, %s, %s)",
                         (player_id, analysis_id, 7.0, power_score))
            conn.commit()
            metric_id = cursor.lastrowid

            cursor.execute("INSERT INTO shotanalysis (metric_id, shot_frame, shot_speed, shot_direction, shot_type, shot_quality, technique_rating) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                         (metric_id, 0, results['performance_score']['power_analysis'].get('velocity', 0), 0, shot_type, overall_score, overall_score))
            conn.commit()

            return {'success': True, 'video_id': video_id, 'analysis_id': analysis_id}

    except Exception as e:
        logger.error(f"Database save error: {e}")
        return {'success': False, 'error': str(e)}

# ==================== HELPERS ====================

def allowed_file(filename):
    """Check file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_VIDEO_FORMATS

def process_video_analysis(video_path):
    """Video analysis pipeline"""
    try:
        print("\n" + "="*70)
        print(" STARTING ANALYSIS")
        print("="*70)
        
        from video_processor import VideoAnalyzer
        
        video_analyzer = VideoAnalyzer(video_path)
        video_results = video_analyzer.analyze_video(extraction_method='smart', save_frames=False)
        frames = [f['original_frame'] for f in video_results['frames']]
        print(f"✓ Extracted {len(frames)} frames")
        
        best_frames = scene_analyzer.filter_best_frames(frames) if scene_analyzer else frames[:10]
        print(f"✓ Selected {len(best_frames)} frames")
        
        if shot_classifier:
            shot_prediction = shot_classifier.predict_video_consensus(best_frames, method='weighted')
        else:
            shot_prediction = {
                'predicted_shot_type': 'power',
                'confidence': 0.6,
                'consensus_confidence': 0.6,
                'top_3_predictions': [
                    {'shot_type': 'power', 'confidence': 0.6},
                    {'shot_type': 'Drive', 'confidence': 0.3},
                    {'shot_type': 'volley', 'confidence': 0.1}
                ]
            }
        print(f"✓ Shot: {shot_prediction['predicted_shot_type']}")
        
        mechanics_analysis = yolo_detector.analyze_shot_mechanics(best_frames[0])
        power_estimation = yolo_detector.estimate_shot_power(frames)
        print(f"✓ Mechanics: {mechanics_analysis['mechanics_score']:.2f}")
        print(f"✓ Power: {power_estimation['power_category']}")
        
        performance_score = performance_scorer.calculate_shot_score(
            shot_prediction, mechanics_analysis, power_estimation
        )
        print(f"✓ Score: {performance_score['overall_score']}/10")
        
        shot_analysis = {
            'shot_prediction': shot_prediction,
            'mechanics': mechanics_analysis,
            'performance_score': performance_score
        }
        
        recommendations = recommendation_engine.generate_recommendations(shot_analysis, performance_score)
        benchmark = performance_scorer.compare_with_benchmark(
            performance_score['overall_score'], shot_prediction['predicted_shot_type']
        )
        analysis = performance_scorer.identify_strengths_weaknesses(
            performance_score['component_scores']
        )
        summary = performance_scorer.generate_performance_summary(shot_analysis)
        improvement = performance_scorer.calculate_improvement_potential(
            performance_score['overall_score'], analysis['weaknesses']
        )
        
        results = {
            'shot_prediction': {
                'shot_type': shot_prediction['predicted_shot_type'],
                'confidence': round(shot_prediction['confidence'], 4),
                'consensus_confidence': round(shot_prediction.get('consensus_confidence', 0), 4),
                'top_3_predictions': shot_prediction.get('top_3_predictions', [])
            },
            'performance_score': performance_score,
            'mechanics': {
                'mechanics_score': round(mechanics_analysis['mechanics_score'], 2),
                'stance': mechanics_analysis.get('stance', 'unknown'),
                'ball_position': mechanics_analysis.get('ball_position', 'unknown'),
                'close_contact': mechanics_analysis.get('close_contact', False),
                'issues': mechanics_analysis.get('issues', [])
            },
            'benchmark': benchmark,
            'strengths_weaknesses': analysis,
            'improvement': improvement,
            'summary': summary,
            'recommendations': {
                'overall_advice': recommendations.get('overall_advice', 'Keep practicing'),
                'shot_specific_drills': recommendations.get('shot_specific_drills', {}).get('primary_drills', []) if isinstance(recommendations.get('shot_specific_drills'), dict) else recommendations.get('shot_specific_drills', []),
                'weakness_training': recommendations.get('weakness_training', {}),
                'technique_improvements': recommendations.get('technique_improvements', []),
                'power_training': recommendations.get('power_training', {}),
                'practice_plan': recommendations.get('practice_plan', {}),
                'pro_tips': recommendations.get('pro_tips', [])
            },
            'video_info': {
                'duration': video_results['duration'],
                'total_frames': video_results['total_frames'],
                'analyzed_frames': len(best_frames),
                'fps': video_results['fps']
            },
            'timestamp': datetime.now().isoformat()
        }
        
        video_analyzer.cleanup()
        print("="*70)
        print("✓ ANALYSIS COMPLETE")
        print("="*70)
        
        return results
        
    except Exception as e:
        print(f"✗ Analysis error: {e}")
        traceback.print_exc()
        raise

# ==================== ROUTES ====================

@app.route('/')
def home():
    user = session.get('user')
    if user:
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute("SELECT * FROM systemuser WHERE email=%s", (user,))
                user_data = cursor.fetchone()
                
                # Redirect admin to user management
                if user_data and user_data['role'] == 'Admin':
                    return redirect(url_for('admin_users'))
                    
                return render_template('index.html', user=user_data)
        except:
            return render_template('index.html')
    return render_template('index.html')

@app.route('/backhome')
def backhome():
    return redirect(url_for('home'))

@app.route('/about')
def about():
    user = session.get('user')
    if user:
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute("SELECT * FROM systemuser WHERE email=%s", (user,))
                user_data = cursor.fetchone()
                return render_template('about.html', user=user_data)
        except:
            pass
    return render_template('about.html')

@app.route('/analyzer')
def analyzer():
    if 'user' not in session:
        return redirect(url_for('login'))
    try:
        with get_db_session() as (conn, cursor):
            cursor.execute("SELECT * FROM systemuser WHERE email=%s", (session['user'],))
            user = cursor.fetchone()
            
            if not user:
                return redirect(url_for('login'))
            
            # Redirect admin to user management
            if user['role'] == 'Admin':
                return redirect(url_for('admin_users'))
                
            return render_template('analyzer.html', user=user)
    except:
        return redirect(url_for('login'))

@app.route('/contact')
def contact():
    user = session.get('user')
    if user:
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute("SELECT * FROM systemuser WHERE email=%s", (user,))
                user_data = cursor.fetchone()
                return render_template('contact.html', user=user_data)
        except:
            pass
    return render_template('contact.html')

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    try:
        with get_db_session() as (conn, cursor):
            cursor.execute("SELECT * FROM systemuser WHERE email=%s", (session['user'],))
            user = cursor.fetchone()
            return render_template('profile.html', user=user) if user else redirect(url_for('login'))
    except:
        return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute("SELECT * FROM systemuser WHERE email=%s AND password=%s", 
                             (request.form['email'], request.form['password']))
                user = cursor.fetchone()
                if user:
                    session['user'] = user['email']
                    session['user_id'] = user['user_id']
                    session['user_role'] = user['role']
                    flash('Login successful!')
                    
                    # Redirect based on role
                    if user['role'] == 'Admin':
                        return redirect(url_for('admin_users'))
                    else:
                        return redirect(url_for('analyzer'))
                        
                flash('Invalid credentials!')
        except Exception as e:
            flash('Login failed!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out!')
    return redirect(url_for('login'))



@app.route('/updatechange', methods=['POST'])
def update():
    if 'user' not in session:
        return redirect(url_for('login'))
    try:
        image_path = None
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
            file.save(file_path)
            image_path = f"uploads/profiles/{filename}"
        
        with get_db_session() as (conn, cursor):
            if image_path:
                cursor.execute("UPDATE systemuser SET name=%s, age=%s, TeamName=%s, email=%s, image=%s WHERE email=%s",
                             (request.form['name'], request.form['age'], request.form['team'], request.form['email'], image_path, session['user']))
            else:
                cursor.execute("UPDATE systemuser SET name=%s, age=%s, TeamName=%s, email=%s WHERE email=%s",
                             (request.form['name'], request.form['age'], request.form['team'], request.form['email'], session['user']))
            conn.commit()
        
        session['user'] = request.form['email']
        flash('Profile updated!')
        return redirect(url_for('profile'))
    except:
        flash('Update failed!')
        return redirect(url_for('profile'))


# ==================== USER MANAGEMENT ROUTES ====================

@app.route('/admin/users')
def admin_users():
    """User management dashboard - Admin only"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    try:
        with get_db_session() as (conn, cursor):
            # Check if current user is admin
            cursor.execute("SELECT role FROM systemuser WHERE email=%s", (session['user'],))
            current_user = cursor.fetchone()
            
            if not current_user or current_user['role'] != 'Admin':
                flash('Access denied. Admin only.')
                return redirect(url_for('home'))
            
            # Get current admin info
            cursor.execute("SELECT * FROM systemuser WHERE email=%s", (session['user'],))
            admin_data = cursor.fetchone()
            
            # Get all users
            cursor.execute("""
                SELECT u.user_id, u.name, u.email, u.role, u.TeamName, u.age, u.created_at,
                       CASE 
                           WHEN EXISTS (
                               SELECT 1 FROM videoinput v 
                               JOIN player p ON v.player_id = p.player_id 
                               WHERE p.user_id = u.user_id
                           ) THEN 'Active'
                           WHEN u.created_at > DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Pending'
                           ELSE 'Inactive'
                       END as status
                FROM systemuser u
                ORDER BY u.user_id
            """)
            users = cursor.fetchall()
            
            return render_template('admin_users.html', user=admin_data, users=users)
            
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        flash('Error loading users')
        return redirect(url_for('home'))


@app.route('/admin/users/add', methods=['POST'])
def admin_add_user():
    """Add new user - Admin only"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 403
    
    try:
        with get_db_session() as (conn, cursor):
            # Verify admin
            cursor.execute("SELECT role FROM systemuser WHERE email=%s", (session['user'],))
            current_user = cursor.fetchone()
            
            if not current_user or current_user['role'] != 'Admin':
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            
            # Check if email exists
            cursor.execute("SELECT user_id FROM systemuser WHERE email=%s", (request.form['email'],))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': 'Email already exists'}), 400
            
            # Insert new user
            cursor.execute("""
                INSERT INTO systemuser (name, email, password, role, TeamName, age, image) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form['name'],
                request.form['email'],
                request.form['password'],
                request.form['role'],
                request.form.get('team', ''),
                request.form.get('age', 0),
                'default.jpg'
            ))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'User added successfully'})
            
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
def admin_edit_user(user_id):
    """Edit user - Admin only"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 403
    
    try:
        with get_db_session() as (conn, cursor):
            # Verify admin
            cursor.execute("SELECT role FROM systemuser WHERE email=%s", (session['user'],))
            current_user = cursor.fetchone()
            
            if not current_user or current_user['role'] != 'Admin':
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            
            # Update user
            cursor.execute("""
                UPDATE systemuser 
                SET name=%s, email=%s, role=%s, TeamName=%s, age=%s
                WHERE user_id=%s
            """, (
                request.form['name'],
                request.form['email'],
                request.form['role'],
                request.form.get('team', ''),
                request.form.get('age', 0),
                user_id
            ))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'User updated successfully'})
            
    except Exception as e:
        logger.error(f"Error editing user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/admin/users/get/<int:user_id>')
def admin_get_user(user_id):
    """Get user details for editing - Admin only"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 403
    
    try:
        with get_db_session() as (conn, cursor):
            # Verify admin
            cursor.execute("SELECT role FROM systemuser WHERE email=%s", (session['user'],))
            current_user = cursor.fetchone()
            
            if not current_user or current_user['role'] != 'Admin':
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            
            # Get user details
            cursor.execute("""
                SELECT user_id, name, email, role, TeamName, age 
                FROM systemuser 
                WHERE user_id=%s
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            return jsonify({'success': True, 'user': user})
            
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API ROUTES ====================

@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    try:
        if not yolo_detector:
            return jsonify({'success': False, 'error': 'AI models not loaded'}), 500
        
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Please login'}), 403
        
        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'No video'}), 400
        
        file = request.files['video']
        if not file.filename or not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file'}), 400
        
        filename = secure_filename(file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        print("\n" + "="*70)
        print("🎬 NEW VIDEO UPLOAD")
        print("="*70)
        print(f"📁 File: {filename}")
        print(f"👤 User: {session['user']}")
        
        # ============================================================
        # STEP 1: VALIDATE IF VIDEO CONTAINS FOOTBALL CONTENT
        # ============================================================
        print("\n🔍 STEP 1: Validating football content...")
        
        validator = FootballVideoValidator(
            min_football_frames=3,      # At least 3 frames must have football
            min_detection_rate=0.25     # At least 25% of sampled frames
        )
        
        validation_result = validator.validate_video(filepath, sample_rate=5)
        
        # If validation fails, return error immediately
        if not validation_result['is_valid']:
            print("❌ VALIDATION FAILED - Not a football video")
            print(f"   Reason: {validation_result['reason']}")
            print("="*70)
            
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': False,
                'error': 'Not a valid football video',
                'results': {
                    'validation_failed': True,
                    'message': validation_result['reason'],
                    'details': {
                        'confidence_score': validation_result['confidence_score'],
                        'detection_rate': validation_result['details']['detection_rate'],
                        'frames_analyzed': validation_result['details']['frames_analyzed'],
                        'frames_with_football': validation_result['details']['frames_with_football'],
                        'suggestion': validation_result['details']['suggestion']
                    }
                }
            }), 400
        
        print(" VALIDATION PASSED - Football video confirmed!")
        print(f"   Confidence: {validation_result['confidence_score']:.1f}%")
        print(f"   Detection Rate: {validation_result['details']['detection_rate']:.1%}")
        
        # ============================================================
        # STEP 2: PROCEED WITH FULL ANALYSIS
        # ============================================================
        print("\n🤖 STEP 2: Starting detailed AI analysis...")
        
        results = process_video_analysis(filepath)
        results = convert_numpy_types(results)
        
        # Add validation info to results
        results['validation'] = {
            'passed': True,
            'confidence': validation_result['confidence_score'],
            'detection_rate': validation_result['details']['detection_rate'],
            'players_detected': validation_result['details']['total_players_detected'],
            'balls_detected': validation_result['details']['total_balls_detected']
        }
        
        # Save to database
        db_result = save_analysis_to_database(filepath, file.filename, results)
        
        results['database_saved'] = db_result['success']
        if db_result['success']:
            results['video_id'] = db_result['video_id']
            results['analysis_id'] = db_result['analysis_id']
        
        session['last_analysis'] = results
        
        print("="*70)
        print(" ANALYSIS COMPLETE")
        print("="*70)
        
        return jsonify({
            'success': True, 
            'message': 'Analysis complete', 
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        traceback.print_exc()
        
        # Clean up file on error
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({'success': False, 'error': str(e)}), 500
    try:
        if not yolo_detector:
            return jsonify({'success': False, 'error': 'AI models not loaded'}), 500
        
        if 'user' not in session:
            return jsonify({'success': False, 'error': 'Please login'}), 403
        
        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'No video'}), 400
        
        file = request.files['video']
        if not file.filename or not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file'}), 400
        
        filename = secure_filename(file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        results = process_video_analysis(filepath)

        results = convert_numpy_types(results)

        db_result = save_analysis_to_database(filepath, file.filename, results)
        
        results['database_saved'] = db_result['success']
        if db_result['success']:
            results['video_id'] = db_result['video_id']
            results['analysis_id'] = db_result['analysis_id']
        
        session['last_analysis'] = results
        
        return jsonify({'success': True, 'message': 'Analysis complete', 'results': results})
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/get_analysis/<task_id>')
def get_analysis(task_id):
    results = session.get('last_analysis')
    return jsonify({'success': True, 'results': results}) if results else jsonify({'success': False}), 404

@app.route('/api/system_status')
def system_status():
    return jsonify({
        'success': True,
        'models_loaded': models_loaded,
        'shot_classifier': shot_classifier is not None,
        'yolo_detector': yolo_detector is not None,
        'database_connected': connection_pool is not None
    })

@app.route('/test_db')
def test_db():
    return jsonify(test_database_connection())

# ==================== ERROR HANDLERS ====================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': f'File too large. Max: {config.MAX_VIDEO_SIZE_MB}MB'}), 413

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500





@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            with get_db_session() as (conn, cursor):
                name = request.form['name']
                email = request.form['email']
                
                cursor.execute("INSERT INTO systemuser (name, email, password, role, TeamName, age, image) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                             (name, email, request.form['password'], 'Player', request.form.get('team', ''), request.form['age'], 'default.jpg'))
                conn.commit()
                
                # Send welcome email
                try:
                    send_welcome_email(name, email)
                    logger.info(f"Welcome email sent to {email}")
                except Exception as e:
                    logger.error(f"Failed to send welcome email: {e}")
                
            flash('Registration successful!')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed!')
            logger.error(f"Registration error: {e}")
    return render_template('register.html')


@app.route('/send_contact', methods=['POST'])
def send_contact():
    try:
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Send message to team
        team_email_sent = send_contact_message_to_team(name, email, message)
        
        # Send auto-reply to customer
        customer_email_sent = send_contact_auto_reply(name, email)
        
        if team_email_sent and customer_email_sent:
            flash('Message sent successfully! Check your email for confirmation.')
        elif team_email_sent:
            flash('Message sent to our team!')
        else:
            flash('Message recorded. We will respond soon.')
        
        logger.info(f"Contact message from {name} ({email})")
        
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        flash('Failed to send message. Please try again.')
    
    return redirect(url_for('contact'))


@app.route('/passwordupdate', methods=['GET', 'POST'])
def password_update():
    if request.method == 'POST':
        email = request.form['email']
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute("SELECT name FROM systemuser WHERE email=%s", (email,))
                user = cursor.fetchone()
                
                if user:
                    # Generate reset token
                    reset_token = secrets.token_urlsafe(32)
                    
                    # Store token in session (in production, use database with expiry)
                    session[f'reset_token_{email}'] = reset_token
                    session[f'reset_token_time_{email}'] = datetime.now().timestamp()
                    
                    # Send reset email
                    if send_password_reset_email(user['name'], email, reset_token):
                        flash('Password reset link sent to your email!')
                    else:
                        flash('Failed to send email. Please try again.')
                else:
                    flash('Email not found!')
                    
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            flash('An error occurred. Please try again.')
        
        return redirect(url_for('password_update'))
    
    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Handle password reset with token"""
    if request.method == 'GET':
        token = request.args.get('token')
        if not token:
            flash('Invalid reset link!')
            return redirect(url_for('login'))
        
        # Find email for this token
        email = None
        for key in session.keys():
            if key.startswith('reset_token_') and session[key] == token:
                email = key.replace('reset_token_', '')
                
                # Check if token is expired (1 hour)
                token_time_key = f'reset_token_time_{email}'
                if token_time_key in session:
                    token_time = session[token_time_key]
                    if (datetime.now().timestamp() - token_time) > 3600:  # 1 hour
                        flash('Reset link expired! Please request a new one.')
                        return redirect(url_for('password_update'))
                break
        
        if not email:
            flash('Invalid or expired reset link!')
            return redirect(url_for('password_update'))
        
        return render_template('reset_password.html', email=email, token=token)
    
    else:  # POST
        email = request.form['email']
        new_password = request.form['password']
        
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute("UPDATE systemuser SET password=%s WHERE email=%s", (new_password, email))
                conn.commit()
                
                # Clear reset token
                session.pop(f'reset_token_{email}', None)
                session.pop(f'reset_token_time_{email}', None)
                
                flash('Password reset successful! Please login.')
                return redirect(url_for('login'))
                
        except Exception as e:
            logger.error(f"Password update error: {e}")
            flash('Failed to update password!')
            return redirect(url_for('password_update'))


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    """Delete user - Admin only WITH EMAIL NOTIFICATION"""
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 403
    
    try:
        with get_db_session() as (conn, cursor):
            # Verify admin
            cursor.execute("SELECT role, user_id FROM systemuser WHERE email=%s", (session['user'],))
            current_user = cursor.fetchone()
            
            if not current_user or current_user['role'] != 'Admin':
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            
            # Prevent self-deletion
            if current_user['user_id'] == user_id:
                return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
            
            # Get user details before deletion
            cursor.execute("SELECT name, email FROM systemuser WHERE user_id=%s", (user_id,))
            user_to_delete = cursor.fetchone()
            
            if not user_to_delete:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Delete related records first
            cursor.execute("SELECT player_id FROM player WHERE user_id=%s", (user_id,))
            player = cursor.fetchone()
            
            if player:
                player_id = player['player_id']
                
                # Delete in correct order
                cursor.execute("DELETE FROM trainingadvice WHERE player_id=%s", (player_id,))
                cursor.execute("DELETE FROM performancelog WHERE player_id=%s", (player_id,))
                
                cursor.execute("SELECT metric_id FROM playermetrics WHERE player_id=%s", (player_id,))
                metrics = cursor.fetchall()
                for metric in metrics:
                    cursor.execute("DELETE FROM shotanalysis WHERE metric_id=%s", (metric['metric_id'],))
                    cursor.execute("DELETE FROM recommendationengine WHERE metric_id=%s", (metric['metric_id'],))
                
                cursor.execute("DELETE FROM playermetrics WHERE player_id=%s", (player_id,))
                
                cursor.execute("SELECT video_id FROM videoinput WHERE player_id=%s", (player_id,))
                videos = cursor.fetchall()
                for video in videos:
                    cursor.execute("SELECT engine_id FROM aiengine WHERE video_id=%s", (video['video_id'],))
                    engines = cursor.fetchall()
                    for engine in engines:
                        cursor.execute("DELETE FROM motionanalysis WHERE engine_id=%s", (engine['engine_id'],))
                        cursor.execute("DELETE FROM trainingadvice WHERE engine_id=%s", (engine['engine_id'],))
                    cursor.execute("DELETE FROM aiengine WHERE video_id=%s", (video['video_id'],))
                
                cursor.execute("DELETE FROM videoinput WHERE player_id=%s", (player_id,))
                cursor.execute("DELETE FROM player WHERE player_id=%s", (player_id,))
            
            cursor.execute("DELETE FROM custommodels WHERE user_id=%s", (user_id,))
            cursor.execute("DELETE FROM systemuser WHERE user_id=%s", (user_id,))
            conn.commit()
            
            # Send deletion notification email
            try:
                send_account_deletion_notification(
                    user_to_delete['name'], 
                    user_to_delete['email'],
                    "Your account was deleted by an administrator"
                )
                logger.info(f"Deletion notification sent to {user_to_delete['email']}")
            except Exception as e:
                logger.error(f"Failed to send deletion email: {e}")
            
            return jsonify({'success': True, 'message': 'User deleted successfully'})
            
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    


# ==================== MAIN ====================

if __name__ == '__main__':
    print("="*70)
    print("⚽ FOOTBALL PERFORMANCE ANALYZER")
    print("="*70)
    print(f"Host: {config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"Upload: {app.config['UPLOAD_FOLDER']}")
    print(f"Max Size: {config.MAX_VIDEO_SIZE_MB}MB")
    
    db_status = test_database_connection()
    print(f"Database: {'✓ Connected' if db_status['success'] else '✗ Failed'}")
    
    print("="*70)
    
    if not yolo_detector:
        print("⚠ WARNING: Core models not loaded!")
    
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)