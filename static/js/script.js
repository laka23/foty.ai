
let currentVideoFile = null;
let analysisInProgress = false;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Football analyzer initializing...');
    
    try {
        if (document.querySelector('.analyzer-section')) {
            setupAnalyzer();
        }
        
        if (document.getElementById('getstart')) {
            setupRegisterButton();
        }
        
        addEnhancedStyles();
        console.log('Initialization complete');
    } catch (error) {
        console.error('Initialization error:', error);
        showNotification('System initialization failed. Please refresh.', 'error');
    }
});

function addEnhancedStyles() {
    if (document.getElementById('enhanced-analyzer-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-analyzer-styles';
    style.textContent = `
        /* ADD THE NEW VALIDATION ERROR STYLES HERE */
        /* Copy from the CSS artifact above */
        
        /* ...existing styles... */
    `;
    
    document.head.appendChild(style);
}

function setupRegisterButton() {
    const btn = document.getElementById('getstart');
    if (btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = "/register";
        });
    }
}

function setupAnalyzer() {
    console.log('Setting up analyzer...');
    
    const uploadBox = document.getElementById('uploadBox');
    const videoInput = document.getElementById('videoInput');
    const videoPreview = document.getElementById('videoPreview');
    const previewVideo = document.getElementById('previewVideo');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (!uploadBox || !videoInput) {
        console.error('Upload elements missing');
        return;
    }
    
    // Click to upload
    uploadBox.addEventListener('click', () => videoInput.click());
    
    // File selection
    videoInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            handleVideoFile(this.files[0]);
        }
    });
    
    // Analyze button
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', function() {
            if (currentVideoFile && !analysisInProgress) {
                startVideoAnalysis();
            }
        });
    }
    
    // Drag and drop
    setupDragDrop(uploadBox);
}

function setupDragDrop(uploadBox) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
        uploadBox.addEventListener(event, e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });
    
    uploadBox.addEventListener('dragover', () => {
        uploadBox.classList.add('drag-over');
    });
    
    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('drag-over');
    });
    
    uploadBox.addEventListener('drop', function(e) {
        uploadBox.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            handleVideoFile(e.dataTransfer.files[0]);
        }
    });
}

function handleVideoFile(file) {
    console.log('File:', file.name, 'Size:', (file.size / 1024 / 1024).toFixed(2) + 'MB');
    
    // Validate
    const validTypes = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
    const ext = file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(ext)) {
        showNotification('Invalid file type. Use MP4, AVI, MOV, MKV, or WEBM', 'error');
        return;
    }
    
    if (file.size > 200 * 1024 * 1024) {
        showNotification('File too large. Maximum 200MB allowed', 'error');
        return;
    }
    
    currentVideoFile = file;
    showVideoPreview(file);
}

function showVideoPreview(file) {
    const uploadBox = document.getElementById('uploadBox');
    const videoPreview = document.getElementById('videoPreview');
    const previewVideo = document.getElementById('previewVideo');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    const videoURL = URL.createObjectURL(file);
    previewVideo.src = videoURL;
    
    uploadBox.style.display = 'none';
    videoPreview.style.display = 'block';
    analyzeBtn.disabled = false;
    
    showNotification('Video loaded successfully! Ready to analyze.', 'success');
}

function startVideoAnalysis() {
    console.log('Starting analysis...');
    
    analysisInProgress = true;
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
    }
    
    // FIXED: Show progress indicator properly
    showProgressIndicator();
    
    const formData = new FormData();
    formData.append('video', currentVideoFile);
    
    fetch('/api/upload_video', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('Analysis complete:', data);
        hideProgressIndicator();
        displayResults(data);
        showNotification('Analysis complete!', 'success');
    })
    .catch(error => {
        console.error('Analysis error:', error);
        hideProgressIndicator();
        showNotification('Analysis failed: ' + error.message, 'error');
    })
    .finally(() => {
        analysisInProgress = false;
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = '🤖 Analyze Performance';
        }
    });
}

// FIXED: Progress indicator that actually shows on screen
function showProgressIndicator() {
    // Remove any existing indicator
    hideProgressIndicator();
    
    const overlay = document.createElement('div');
    overlay.id = 'analysisProgress';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    overlay.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            max-width: 500px;
            border: 2px solid #1E90FF;
            box-shadow: 0 0 30px rgba(30, 144, 255, 0.5);
        ">
            <div class="loading-spinner" style="
                width: 60px;
                height: 60px;
                border: 4px solid #333;
                border-top: 4px solid #1E90FF;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            "></div>
            
            <h3 style="color: #1E90FF; margin-bottom: 15px;">🤖 AI Analysis in Progress</h3>
            <p style="color: #fff; margin-bottom: 20px;">Please wait while we analyze your football performance...</p>
            
            <div style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px;">
                <div class="analysis-steps">
                    <div class="step">📹 Processing Video</div>
                    <div class="step">⚽ Detecting Shots</div>
                    <div class="step">🎯 Analyzing Technique</div>
                    <div class="step">📊 Calculating Metrics</div>
                    <div class="step">💡 Generating Insights</div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .analysis-steps .step {
            color: #fff;
            padding: 8px;
            margin: 5px 0;
            font-size: 14px;
            opacity: 0.6;
            transition: opacity 0.3s;
        }
    `;
    document.head.appendChild(style);
    
    // Animate steps
    const steps = overlay.querySelectorAll('.step');
    let index = 0;
    const interval = setInterval(() => {
        if (index < steps.length) {
            steps[index].style.opacity = '1';
            steps[index].style.color = '#1E90FF';
            index++;
        } else {
            clearInterval(interval);
        }
    }, 800);
}

function hideProgressIndicator() {
    const indicator = document.getElementById('analysisProgress');
    if (indicator) {
        indicator.remove();
    }
}

// FIXED: Results display with proper accuracy calculation
function displayResults(data) {
    const resultsDiv = document.getElementById('analysisResults');
    if (!resultsDiv) return;
    
    const shots = data.shots_detected || [];
    const totalShots = shots.length;
    
    // FIXED: Calculate proper accuracy
    const validShots = shots.filter(s => (s.confidence || 0) > 0.6).length;
    const accuracy = totalShots > 0 ? (validShots / totalShots * 100) : 0;
    
    const metrics = data.metrics || {};
    const overallScore = parseFloat(metrics['Overall Score']) || 0;
    
    // FIXED: Calculate proper average velocity
    const velocities = shots.map(s => s.velocity || s.speed || 0).filter(v => v > 0);
    const avgVelocity = velocities.length > 0 ? 
        velocities.reduce((a, b) => a + b, 0) / velocities.length : 0;
    
    let html = `
        <h2>🏆 Performance Analysis Results</h2>
        
        <!-- Quick Summary -->
        <div class="quick-summary">
            <div class="stat-card">
                <div class="stat-value">${totalShots}</div>
                <div class="stat-label">Total Shots</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${validShots}</div>
                <div class="stat-label">Valid Shots</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${accuracy.toFixed(1)}%</div>
                <div class="stat-label">Accuracy</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${avgVelocity.toFixed(1)}</div>
                <div class="stat-label">Avg Velocity</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${overallScore.toFixed(1)}/10</div>
                <div class="stat-label">Overall Score</div>
            </div>
        </div>
        
        <!-- Individual Shots Analysis -->
        <div class="shots-analysis-section">
            <h3>⚽ Individual Shot Analysis</h3>
            <div class="shots-grid">
    `;
    
    // FIXED: Display each shot with CNN classification and specific advice
    shots.slice(0, 10).forEach((shot, index) => {
        const shotType = shot.cnn_shot_type || shot.shot_type || 'Normal Shot';
        const confidence = (shot.cnn_confidence || shot.confidence || 0) * 100;
        const velocity = shot.velocity || shot.speed || 0;
        const quality = shot.quality_score || (confidence / 10);
        
        // Determine quality level
        let qualityLabel, qualityClass, advice;
        if (quality >= 8) {
            qualityLabel = 'Excellent';
            qualityClass = 'excellent';
            advice = `Perfect ${shotType}! Maintain this technique. Focus on consistency.`;
        } else if (quality >= 6) {
            qualityLabel = 'Good';
            qualityClass = 'good';
            advice = `Good ${shotType}. Work on power and follow-through for better results.`;
        } else if (quality >= 4) {
            qualityLabel = 'Fair';
            qualityClass = 'fair';
            advice = `${shotType} needs improvement. Practice body positioning and timing.`;
        } else {
            qualityLabel = 'Weak';
            qualityClass = 'weak';
            advice = `Weak ${shotType}. Focus on fundamentals: stance, approach, and contact point.`;
        }
        
        html += `
            <div class="shot-card ${qualityClass}">
                <div class="shot-header">
                    <span class="shot-number">#${index + 1}</span>
                    <span class="shot-type">${shotType}</span>
                    <span class="shot-quality ${qualityClass}">${qualityLabel}</span>
                </div>
                <div class="shot-metrics">
                    <div class="metric">
                        <label>Confidence:</label>
                        <span>${confidence.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <label>Velocity:</label>
                        <span>${velocity.toFixed(1)} m/s</span>
                    </div>
                    <div class="metric">
                        <label>Quality:</label>
                        <span>${quality.toFixed(1)}/10</span>
                    </div>
                </div>
                <div class="shot-advice">
                    <strong>💡 Training Advice:</strong>
                    <p>${advice}</p>
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
        
        <!-- Overall Recommendations -->
        <div class="advice-section">
            <h3>🤖 AI Recommendations</h3>
            <div class="advice-content">
                ${generateOverallAdvice(shots, accuracy, avgVelocity, overallScore)}
            </div>
        </div>
        
        <div class="action-buttons">
            <button class="btn-secondary" onclick="window.print()">💾 Save Report</button>
            <button class="btn-primary" onclick="location.reload()">🔄 Analyze Another Video</button>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

function generateOverallAdvice(shots, accuracy, avgVelocity, overallScore) {
    let advice = [];
    
    // Overall performance
    if (overallScore >= 8) {
        advice.push('🌟 Excellent performance! You demonstrate advanced football shooting skills.');
    } else if (overallScore >= 6) {
        advice.push('✅ Good performance! You have solid fundamentals with room for improvement.');
    } else {
        advice.push('📚 Keep practicing! Focus on mastering the basics before advancing.');
    }
    
    // Accuracy feedback
    if (accuracy >= 80) {
        advice.push(`🎯 Outstanding accuracy (${accuracy.toFixed(1)}%)! Very consistent shooting.`);
    } else if (accuracy >= 60) {
        advice.push(`✓ Good accuracy (${accuracy.toFixed(1)}%). Work on consistency across all shot types.`);
    } else {
        advice.push(`⚠️ Accuracy needs work (${accuracy.toFixed(1)}%). Focus on shot selection and technique.`);
    }
    
    // Velocity feedback
    if (avgVelocity >= 25) {
        advice.push(`⚡ Strong shot power (avg ${avgVelocity.toFixed(1)} m/s). Maintain this strength.`);
    } else if (avgVelocity >= 15) {
        advice.push(`👍 Moderate power (avg ${avgVelocity.toFixed(1)} m/s). Leg strengthening exercises recommended.`);
    } else {
        advice.push(`💪 Shot power is low (avg ${avgVelocity.toFixed(1)} m/s). Focus on explosive movements and leg strength.`);
    }
    
    // Shot variety
    const shotTypes = new Set(shots.map(s => s.cnn_shot_type || s.shot_type));
    if (shotTypes.size >= 4) {
        advice.push('🎨 Excellent shot variety! You demonstrate versatility in your shooting.');
    } else if (shotTypes.size >= 2) {
        advice.push('📊 Good variety. Try practicing more shot types for greater versatility.');
    } else {
        advice.push('🔄 Limited shot variety detected. Practice different shooting techniques.');
    }
    
    // Training recommendations
    advice.push('');
    advice.push('🏋️ <strong>Training Recommendations:</strong>');
    advice.push('• Practice shooting drills 15-20 minutes daily');
    advice.push('• Focus on weaker shot types identified above');
    advice.push('• Work on both feet for better balance');
    advice.push('• Include strength training for more powerful shots');
    
    return advice.map(a => `<p>${a}</p>`).join('');
}

function showNotification(message, type = 'info') {
    const existing = document.querySelectorAll('.notification');
    existing.forEach(el => el.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    
    const icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <span>${icons[type]}</span>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" 
                style="background: none; border: none; color: white; 
                       font-size: 20px; cursor: pointer; margin-left: auto;">×</button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, type === 'error' ? 8000 : 5000);
}

function addEnhancedStyles() {
    if (document.getElementById('enhanced-analyzer-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-analyzer-styles';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #1E90FF;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        
        .upload-box.drag-over {
            border-color: #1E90FF;
            background: rgba(30, 144, 255, 0.1);
        }
        
        .quick-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin: 25px 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #1E1E1E 0%, #2A2A2A 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #444;
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #1E90FF;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
        }
        
        .shots-analysis-section {
            margin: 30px 0;
        }
        
        .shots-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .shot-card {
            background: #1E1E1E;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #666;
        }
        
        .shot-card.excellent { border-left-color: #28a745; }
        .shot-card.good { border-left-color: #17a2b8; }
        .shot-card.fair { border-left-color: #ffc107; }
        .shot-card.weak { border-left-color: #dc3545; }
        
        .shot-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .shot-number {
            background: #1E90FF;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .shot-type {
            font-weight: bold;
            color: #fff;
        }
        
        .shot-quality {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .shot-quality.excellent { background: #28a745; color: white; }
        .shot-quality.good { background: #17a2b8; color: white; }
        .shot-quality.fair { background: #ffc107; color: black; }
        .shot-quality.weak { background: #dc3545; color: white; }
        
        .shot-metrics {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .metric {
            text-align: center;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
        }
        
        .metric label {
            display: block;
            font-size: 11px;
            color: #999;
            margin-bottom: 3px;
        }
        
        .metric span {
            font-weight: bold;
            color: #1E90FF;
        }
        
        .shot-advice {
            background: rgba(30, 144, 255, 0.1);
            padding: 12px;
            border-radius: 5px;
            border-left: 3px solid #1E90FF;
        }
        
        .shot-advice strong {
            color: #1E90FF;
            display: block;
            margin-bottom: 5px;
        }
        
        .shot-advice p {
            margin: 0;
            font-size: 13px;
            line-height: 1.5;
            color: #ccc;
        }
        
        @media (max-width: 768px) {
            .quick-summary {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .shots-grid {
                grid-template-columns: 1fr;
            }
        }
    `;
    
    document.head.appendChild(style);
}

// Complete displayResults function with all requirements
function displayResults(data) {
    const resultsDiv = document.getElementById('analysisResults');
    if (!resultsDiv) return;
    
    const results = data.results || {};
    const shotPrediction = results.shot_prediction || {};
    const performanceScore = results.performance_score || {};
    const mechanics = results.mechanics || {};
    const recommendations = results.recommendations || {};
    const strengths = results.strengths_weaknesses || {};
    const benchmark = results.benchmark || {};
    const improvement = results.improvement || {};
    
    // Extract key metrics
    const overallScore = performanceScore.overall_score || 0;
    const quality = performanceScore.quality_category || 'Unknown';
    const shotType = shotPrediction.shot_type || 'Unknown';
    const confidence = (shotPrediction.confidence || 0) * 100;
    const isWeak = performanceScore.is_weak || false;
    const mechanicsScore = mechanics.mechanics_score || 0;
    const powerCategory = performanceScore.power_analysis?.category || 'Unknown';
    
    let html = `
        <h2>🏆 Performance Analysis Results</h2>
        
        <!-- Quick Summary Cards -->
        <div class="quick-summary">
            <div class="stat-card">
                <div class="stat-icon">⚽</div>
                <div class="stat-value">${shotType}</div>
                <div class="stat-label">Shot Type Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🎯</div>
                <div class="stat-value">${confidence.toFixed(1)}%</div>
                <div class="stat-label">AI Confidence</div>
            </div>
            <div class="stat-card ${overallScore >= 7 ? 'excellent' : overallScore >= 5 ? 'good' : 'weak'}">
                <div class="stat-icon">📊</div>
                <div class="stat-value">${overallScore.toFixed(1)}/10</div>
                <div class="stat-label">Overall Score</div>
            </div>
            <div class="stat-card ${quality === 'Excellent' ? 'excellent' : quality === 'Good' ? 'good' : 'weak'}">
                <div class="stat-icon">⭐</div>
                <div class="stat-value">${quality}</div>
                <div class="stat-label">Quality Rating</div>
            </div>
            <div class="stat-card ${isWeak ? 'weak' : 'good'}">
                <div class="stat-icon">💪</div>
                <div class="stat-value">${isWeak ? 'Weak' : powerCategory}</div>
                <div class="stat-label">Shot Power</div>
            </div>
        </div>
        
        <!-- Shot Quality Analysis -->
        <div class="analysis-section">
            <h3>📋 Shot Quality Analysis</h3>
            <div class="quality-details">
                <div class="quality-item ${isWeak ? 'warning' : 'success'}">
                    <strong>Shot Classification:</strong> 
                    <span>${isWeak ? '⚠️ Weak Shot - Needs Significant Improvement' : '✅ Strong Shot - Good Quality'}</span>
                </div>
                <div class="quality-item">
                    <strong>Technique Score:</strong> 
                    <span>${mechanicsScore.toFixed(1)}/10 ${mechanicsScore >= 7 ? '(Excellent)' : mechanicsScore >= 5 ? '(Good)' : '(Needs Work)'}</span>
                </div>
                <div class="quality-item">
                    <strong>Stance:</strong> 
                    <span>${mechanics.stance || 'Unknown'}</span>
                </div>
                <div class="quality-item">
                    <strong>Ball Contact:</strong> 
                    <span>${mechanics.close_contact ? '✅ Close & Proper' : '⚠️ Distance Issues'}</span>
                </div>
                <div class="quality-item">
                    <strong>Benchmark Level:</strong> 
                    <span>${benchmark.level || 'N/A'}</span>
                </div>
            </div>
        </div>
        
        <!-- Performance Component Breakdown -->
        <div class="analysis-section">
            <h3>📊 Performance Component Scores</h3>
            <div class="component-scores">
    `;
    
    // Component scores with visual bars
    const components = performanceScore.component_scores || {};
    for (const [key, value] of Object.entries(components)) {
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const percentage = (value / 10) * 100;
        const color = value >= 7 ? '#28a745' : value >= 5 ? '#ffc107' : '#dc3545';
        
        html += `
            <div class="component-item">
                <div class="component-header">
                    <span class="component-label">${label}</span>
                    <span class="component-value">${value.toFixed(1)}/10</span>
                </div>
                <div class="component-bar">
                    <div class="component-fill" style="width: ${percentage}%; background: ${color}"></div>
                </div>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
        
        <!-- Strengths & Weaknesses -->
        <div class="analysis-section">
            <div class="strengths-weaknesses-grid">
                <div class="strengths-box">
                    <h3>💪 Your Strengths</h3>
                    <ul>
    `;
    
    const strengthsList = strengths.strengths || [];
    if (strengthsList.length > 0) {
        strengthsList.forEach(strength => {
            html += `<li><strong>${strength.component}:</strong> ${strength.comment} (${strength.score.toFixed(1)}/10)</li>`;
        });
    } else {
        html += `<li>Focus on building foundational skills</li>`;
    }
    
    html += `
                    </ul>
                </div>
                <div class="weaknesses-box">
                    <h3>🎯 Areas to Improve</h3>
                    <ul>
    `;
    
    const weaknessesList = strengths.weaknesses || [];
    if (weaknessesList.length > 0) {
        weaknessesList.forEach(weakness => {
            html += `<li><strong>${weakness.component}:</strong> ${weakness.comment} (${weakness.score.toFixed(1)}/10)</li>`;
        });
    } else {
        html += `<li>Keep refining your excellent technique!</li>`;
    }
    
    html += `
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- AI RECOMMENDATIONS SECTION -->
        <div class="analysis-section recommendations-section">
            <h3>🤖 AI-Powered Training Recommendations</h3>
            
            <!-- Overall Advice -->
            <div class="recommendation-card highlight">
                <h4>📢 Overall Training Advice</h4>
                <div class="advice-content">
                    <p><strong>Level:</strong> ${recommendations.overall_advice?.level || 'Developing'}</p>
                    <p><strong>Focus Area:</strong> ${recommendations.overall_advice?.focus || 'Technical improvement'}</p>
                    <p><strong>Training Frequency:</strong> ${recommendations.overall_advice?.training_frequency || '3-4 times/week'}</p>
                    <p><strong>Priority:</strong> ${recommendations.overall_advice?.priority || 'Build strong foundation'}</p>
                    <p class="advice-message">${recommendations.overall_advice?.message || 'Keep practicing consistently'}</p>
                </div>
            </div>
            
            <!-- Shot-Specific Drills -->
            <div class="recommendation-card">
                <h4>⚽ Shot-Specific Training Drills</h4>
                <p class="drill-intro"><strong>Recommended for ${shotType}:</strong></p>
                <ul class="drill-list">
    `;
    
    const drills = recommendations.shot_specific_drills || [];
    if (Array.isArray(drills) && drills.length > 0) {
        drills.forEach((drill, index) => {
            html += `<li><span class="drill-number">${index + 1}</span> ${drill}</li>`;
        });
    } else {
        html += `
            <li><span class="drill-number">1</span> Practice proper stance and approach</li>
            <li><span class="drill-number">2</span> Focus on ball contact timing</li>
            <li><span class="drill-number">3</span> Work on follow-through technique</li>
            <li><span class="drill-number">4</span> Build leg strength with exercises</li>
        `;
    }
    
    html += `
                </ul>
            </div>
            
            <!-- Weakness-Targeted Training -->
            <div class="recommendation-card">
                <h4>🎯 Weakness-Targeted Training</h4>
    `;
    
    const weaknessTraining = recommendations.weakness_training || {};
    if (weaknessTraining.priority_order && weaknessTraining.priority_order.length > 0) {
        weaknessTraining.priority_order.forEach(training => {
            html += `
                <div class="weakness-training-item">
                    <h5>🔧 ${training.focus}</h5>
                    <p><strong>Current Score:</strong> ${training.current_score?.toFixed(1) || 'N/A'}/10 
                       <span class="severity ${training.severity?.toLowerCase()}">(${training.severity || 'Moderate'})</span></p>
                    <ul>
            `;
            (training.exercises || []).forEach(exercise => {
                html += `<li>${exercise}</li>`;
            });
            html += `
                    </ul>
                </div>
            `;
        });
    } else {
        html += `<p>No critical weaknesses detected. Focus on maintaining consistency.</p>`;
    }
    
    html += `
            </div>
            
            <!-- Technique Improvements -->
            <div class="recommendation-card">
                <h4>🔧 Specific Technique Improvements</h4>
                <ul class="improvement-list">
    `;
    
    const improvements = recommendations.technique_improvements || [];
    if (improvements.length > 0) {
        improvements.forEach(improvement => {
            html += `
                <li>
                    <strong>Issue:</strong> ${improvement.issue}<br>
                    <strong>Fix:</strong> ${improvement.fix}<br>
                    <strong>Drill:</strong> ${improvement.drill}
                </li>
            `;
        });
    } else {
        html += `<li>Your technique is solid. Keep practicing to maintain form.</li>`;
    }
    
    html += `
                </ul>
            </div>
            
            <!-- Power Training (if weak shot detected) -->
    `;
    
    if (isWeak || powerCategory === 'weak') {
        html += `
            <div class="recommendation-card warning-card">
                <h4>⚠️ CRITICAL: Power Training Required</h4>
                <p><strong>Status:</strong> ${recommendations.power_training?.status || 'Low power detected'}</p>
                ${recommendations.power_training?.urgency ? `<p class="urgency">Priority Level: ${recommendations.power_training.urgency}</p>` : ''}
                <ul class="power-training-list">
        `;
        
        const powerRecommendations = recommendations.power_training?.recommendations || [
            'Focus on leg strength development',
            'Practice explosive movements',
            'Work on hip flexor and core strength',
            'Include plyometric exercises'
        ];
        powerRecommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
        
        html += `
                </ul>
            </div>
        `;
    }
    
    html += `
            <!-- Pro Tips -->
            <div class="recommendation-card highlight">
                <h4>💡 Professional Tips for ${shotType}</h4>
                <ul class="pro-tips-list">
    `;
    
    const proTips = recommendations.pro_tips || [];
    if (proTips.length > 0) {
        proTips.forEach(tip => {
            html += `<li>${tip}</li>`;
        });
    } else {
        html += `
            <li>Practice with both feet for versatility</li>
            <li>Watch professional players for technique reference</li>
            <li>Record yourself to track improvements</li>
        `;
    }
    
    html += `
                </ul>
            </div>
            
            <!-- Weekly Practice Plan -->
            <div class="recommendation-card">
                <h4>📅 Weekly Training Schedule</h4>
    `;
    
    const practicePlan = recommendations.practice_plan?.weekly_plan || {};
    if (Object.keys(practicePlan).length > 0) {
        for (const [day, details] of Object.entries(practicePlan)) {
            html += `
                <div class="day-plan">
                    <h5>${day}</h5>
                    <p><strong>Focus:</strong> ${details.focus}</p>
                    <p><strong>Duration:</strong> ${details.duration}</p>
                    <ul>
            `;
            (details.exercises || []).forEach(exercise => {
                html += `<li>${exercise}</li>`;
            });
            html += `
                    </ul>
                </div>
            `;
        }
    } else {
        html += `
            <div class="day-plan">
                <h5>Recommended Weekly Structure</h5>
                <ul>
                    <li>Day 1-2: Technical drills (45 min)</li>
                    <li>Day 3-4: Power & strength training (60 min)</li>
                    <li>Day 5: Weakness-focused practice (45 min)</li>
                    <li>Day 6: Match simulation (60 min)</li>
                    <li>Day 7: Rest & recovery</li>
                </ul>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
        
        <!-- Improvement Potential -->
        <div class="analysis-section">
            <h3>🚀 Your Improvement Potential</h3>
            <div class="improvement-potential">
                <div class="potential-metric">
                    <span class="metric-label">Current Score:</span>
                    <span class="metric-value">${improvement.current_score?.toFixed(1) || overallScore.toFixed(1)}/10</span>
                </div>
                <div class="potential-arrow">➡️</div>
                <div class="potential-metric highlight">
                    <span class="metric-label">Potential Score:</span>
                    <span class="metric-value">${improvement.potential_score?.toFixed(1) || (overallScore + 2).toFixed(1)}/10</span>
                </div>
                <div class="potential-metric">
                    <span class="metric-label">Improvement:</span>
                    <span class="metric-value success">+${improvement.improvement_points?.toFixed(1) || '2.0'} points</span>
                </div>
                <div class="potential-metric">
                    <span class="metric-label">Timeline:</span>
                    <span class="metric-value">${improvement.achievable_in_weeks || '2-4 months'}</span>
                </div>
            </div>
        </div>
        
        <!-- Training Charts -->
        <div class="analysis-section charts-section">
            <h3>📈 Performance Charts</h3>
            
            <!-- Accuracy Chart -->
            <div class="chart-container">
                <h4>Shot Accuracy Analysis</h4>
                <canvas id="accuracyChart"></canvas>
            </div>
            
            <!-- Component Training Progress -->
            <div class="chart-container">
                <h4>Training Focus Areas</h4>
                <canvas id="trainingChart"></canvas>
            </div>
            
            <!-- Loss/Performance Over Time (if available) -->
            <div class="chart-container">
                <h4>Expected Progress Trajectory</h4>
                <canvas id="progressChart"></canvas>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="action-buttons">
            <button class="btn-primary" onclick="generatePDFReport()">📄 Download Full Report</button>
            <button class="btn-secondary" onclick="window.print()">🖨️ Print Analysis</button>
            <button class="btn-secondary" onclick="location.reload()">🔄 Analyze Another Video</button>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
    
    // Generate charts after DOM update
    setTimeout(() => {
        generateCharts(results);
    }, 100);
}

// Generate all charts
function generateCharts(results) {
    const performanceScore = results.performance_score || {};
    const components = performanceScore.component_scores || {};
    
    // 1. Accuracy Chart (Radar Chart)
    const accuracyCanvas = document.getElementById('accuracyChart');
    if (accuracyCanvas) {
        const ctx = accuracyCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: Object.keys(components).map(k => 
                    k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                ),
                datasets: [{
                    label: 'Your Performance',
                    data: Object.values(components),
                    backgroundColor: 'rgba(30, 144, 255, 0.2)',
                    borderColor: 'rgba(30, 144, 255, 1)',
                    pointBackgroundColor: 'rgba(30, 144, 255, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(30, 144, 255, 1)'
                }, {
                    label: 'Professional Level',
                    data: Object.keys(components).map(() => 8.5),
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    pointBackgroundColor: 'rgba(40, 167, 69, 1)',
                    pointBorderColor: '#fff',
                    borderDash: [5, 5]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    r: {
                        min: 0,
                        max: 10,
                        ticks: {
                            stepSize: 2,
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        pointLabels: {
                            color: '#fff',
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Performance Accuracy Across Components',
                        color: '#1E90FF',
                        font: {
                            size: 16
                        }
                    }
                }
            }
        });
    }
    
    // 2. Training Focus Chart (Bar Chart)
    const trainingCanvas = document.getElementById('trainingChart');
    if (trainingCanvas) {
        const ctx = trainingCanvas.getContext('2d');
        const sortedComponents = Object.entries(components)
            .sort((a, b) => a[1] - b[1]);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedComponents.map(([k, v]) => 
                    k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                ),
                datasets: [{
                    label: 'Current Score',
                    data: sortedComponents.map(([k, v]) => v),
                    backgroundColor: sortedComponents.map(([k, v]) => 
                        v >= 7 ? 'rgba(40, 167, 69, 0.8)' : 
                        v >= 5 ? 'rgba(255, 193, 7, 0.8)' : 
                        'rgba(220, 53, 69, 0.8)'
                    ),
                    borderColor: sortedComponents.map(([k, v]) => 
                        v >= 7 ? 'rgba(40, 167, 69, 1)' : 
                        v >= 5 ? 'rgba(255, 193, 7, 1)' : 
                        'rgba(220, 53, 69, 1)'
                    ),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Training Priority (Lowest to Highest)',
                        color: '#1E90FF',
                        font: {
                            size: 16
                        }
                    }
                }
            }
        });
    }
    
    // 3. Progress Trajectory Chart (Line Chart)
    const progressCanvas = document.getElementById('progressChart');
    if (progressCanvas) {
        const ctx = progressCanvas.getContext('2d');
        const currentScore = performanceScore.overall_score || 0;
        const targetScore = Math.min(currentScore + 3, 10);
        
        // Generate expected progress over 12 weeks
        const weeks = Array.from({length: 13}, (_, i) => `Week ${i}`);
        const progress = weeks.map((_, i) => {
            if (i === 0) return currentScore;
            const growth = (targetScore - currentScore) / 12;
            return Math.min(currentScore + (growth * i), targetScore);
        });
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: weeks,
                datasets: [{
                    label: 'Expected Progress',
                    data: progress,
                    borderColor: 'rgba(30, 144, 255, 1)',
                    backgroundColor: 'rgba(30, 144, 255, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }, {
                    label: 'Professional Level',
                    data: weeks.map(() => 8.5),
                    borderColor: 'rgba(40, 167, 69, 1)',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Expected Performance Improvement (12 Weeks)',
                        color: '#1E90FF',
                        font: {
                            size: 16
                        }
                    }
                }
            }
        });
    }
}

// PDF Report Generation
function generatePDFReport() {
    showNotification('Generating comprehensive PDF report...', 'info');
    
    // This would integrate with a PDF library like jsPDF
    // For now, show a placeholder
    setTimeout(() => {
        showNotification('PDF report feature coming soon! Use Print for now.', 'warning');
    }, 1000);
let currentVideoFile = null;
let analysisInProgress = false;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Football analyzer initializing...');
    
    try {
        if (document.querySelector('.analyzer-section')) {
            setupAnalyzer();
        }
        
        if (document.getElementById('getstart')) {
            setupRegisterButton();
        }
        
        addEnhancedStyles();
        console.log('Initialization complete');
    } catch (error) {
        console.error('Initialization error:', error);
        showNotification('System initialization failed. Please refresh.', 'error');
    }
});

function setupRegisterButton() {
    const btn = document.getElementById('getstart');
    if (btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = "/register";
        });
    }
}

function setupAnalyzer() {
    console.log('Setting up analyzer...');
    
    const uploadBox = document.getElementById('uploadBox');
    const videoInput = document.getElementById('videoInput');
    const videoPreview = document.getElementById('videoPreview');
    const previewVideo = document.getElementById('previewVideo');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (!uploadBox || !videoInput) {
        console.error('Upload elements missing');
        return;
    }
    
    // Click to upload
    uploadBox.addEventListener('click', () => videoInput.click());
    
    // File selection
    videoInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            handleVideoFile(this.files[0]);
        }
    });
    
    // Analyze button
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', function() {
            if (currentVideoFile && !analysisInProgress) {
                startVideoAnalysis();
            }
        });
    }
    
    // Drag and drop
    setupDragDrop(uploadBox);
}

function setupDragDrop(uploadBox) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
        uploadBox.addEventListener(event, e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });
    
    uploadBox.addEventListener('dragover', () => {
        uploadBox.classList.add('drag-over');
    });
    
    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('drag-over');
    });
    
    uploadBox.addEventListener('drop', function(e) {
        uploadBox.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            handleVideoFile(e.dataTransfer.files[0]);
        }
    });
}

function handleVideoFile(file) {
    console.log('File:', file.name, 'Size:', (file.size / 1024 / 1024).toFixed(2) + 'MB');
    
    // Validate
    const validTypes = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
    const ext = file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(ext)) {
        showNotification('Invalid file type. Use MP4, AVI, MOV, MKV, or WEBM', 'error');
        return;
    }
    
    if (file.size > 200 * 1024 * 1024) {
        showNotification('File too large. Maximum 200MB allowed', 'error');
        return;
    }
    
    currentVideoFile = file;
    showVideoPreview(file);
}

function showVideoPreview(file) {
    const uploadBox = document.getElementById('uploadBox');
    const videoPreview = document.getElementById('videoPreview');
    const previewVideo = document.getElementById('previewVideo');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    const videoURL = URL.createObjectURL(file);
    previewVideo.src = videoURL;
    
    uploadBox.style.display = 'none';
    videoPreview.style.display = 'block';
    analyzeBtn.disabled = false;
    
    showNotification('Video loaded successfully! Ready to analyze.', 'success');
}

function startVideoAnalysis() {
    console.log('Starting analysis...');
    
    analysisInProgress = true;
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
    }
    
    showProgressIndicator();
    
    const formData = new FormData();
    formData.append('video', currentVideoFile);
    
    fetch('/api/upload_video', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('Analysis complete:', data);
        hideProgressIndicator();
        
        if (data.success && data.results) {
            displayCompleteResults(data.results);
            showNotification('Analysis complete!', 'success');
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
    })
    .catch(error => {
        console.error('Analysis error:', error);
        hideProgressIndicator();
        showNotification('Analysis failed: ' + error.message, 'error');
    })
    .finally(() => {
        analysisInProgress = false;
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = '🤖 Analyze Performance';
        }
    });
}

function showProgressIndicator() {
    hideProgressIndicator();
    
    const overlay = document.createElement('div');
    overlay.id = 'analysisProgress';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    overlay.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            max-width: 500px;
            border: 2px solid #1E90FF;
            box-shadow: 0 0 30px rgba(30, 144, 255, 0.5);
        ">
            <div class="loading-spinner" style="
                width: 60px;
                height: 60px;
                border: 4px solid #333;
                border-top: 4px solid #1E90FF;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            "></div>
            
            <h3 style="color: #1E90FF; margin-bottom: 15px;">🤖 AI Analysis in Progress</h3>
            <p style="color: #fff; margin-bottom: 20px;">    Analyzing your football Video....  </p>
            
            <div style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px;">
                <div class="analysis-steps">
                    <div class="step">🎬 Processing Video </div>
                    <div class="step">⚽ Shot Identify </div>
                    <div class="step">🎯 Object Detection</div>
                    <div class="step">📊 Performance Scoring</div>
                    <div class="step">💡 Generating AI Recommendations</div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .analysis-steps .step {
            color: #fff;
            padding: 8px;
            margin: 5px 0;
            font-size: 14px;
            opacity: 0.6;
            transition: opacity 0.3s;
        }
    `;
    document.head.appendChild(style);
    
    const steps = overlay.querySelectorAll('.step');
    let index = 0;
    const interval = setInterval(() => {
        if (index < steps.length) {
            steps[index].style.opacity = '1';
            steps[index].style.color = '#1E90FF';
            index++;
        } else {
            clearInterval(interval);
        }
    }, 800);
}

function hideProgressIndicator() {
    const indicator = document.getElementById('analysisProgress');
    if (indicator) {
        indicator.remove();
    }
}

// ==================== COMPLETE RESULTS DISPLAY ====================

function displayCompleteResults(results) {
    const resultsDiv = document.getElementById('analysisResults');
    if (!resultsDiv) return;
    
    console.log('Displaying results:', results);
    
    // Extract data from comprehensive results
    const shotPrediction = results.shot_prediction || {};
    const performanceScore = results.performance_score || {};
    const mechanics = results.mechanics || {};
    const recommendations = results.recommendations || {};
    const benchmark = results.benchmark || {};
    const strengths = results.strengths_weaknesses || {};
    const improvement = results.improvement || {};
    const summary = results.summary || {};
    
    // Key metrics
    const shotType = shotPrediction.shot_type || 'Unknown';
    const confidence = (shotPrediction.confidence * 100) || 0;
    const overallScore = performanceScore.overall_score || 0;
    const qualityCategory = performanceScore.quality_category || 'Unknown';
    const isWeak = performanceScore.is_weak || false;
    const componentScores = performanceScore.component_scores || {};
    
    let html = `
        <h2>🏆 Complete Performance Analysis Results</h2>
        
        <!-- Summary Cards -->
        <div class="quick-summary">
            <div class="stat-card ${confidence >= 80 ? 'excellent' : confidence >= 60 ? 'good' :'weak'}">
                <div class="stat-icon">⚽</div>
                <div class="stat-value">${shotType}</div>
                <div class="stat-label">Shot Type (CNN)</div>
                <div class="stat-sublabel">${confidence.toFixed(1)}% confidence</div>
            </div>
            <div class="stat-card ${overallScore >= 8 ? 'excellent' : overallScore >= 6 ? 'good' : 'weak'}">
                <div class="stat-icon">📊</div>
                <div class="stat-value">${overallScore.toFixed(1)}/10</div>
                <div class="stat-label">Overall Score</div>
                <div class="stat-sublabel">${qualityCategory}</div>
            </div>
            <div class="stat-card ${!isWeak ? 'excellent' : 'weak'}">
                <div class="stat-icon">💪</div>
                <div class="stat-value">${isWeak ? 'Weak' : 'Strong'}</div>
                <div class="stat-label">Shot Power</div>
                <div class="stat-sublabel">${performanceScore.power_analysis?.category || 'N/A'}</div>
            </div>
            <div class="stat-card ${benchmark.level === 'Professional Level' ? 'excellent' : 'good'}">
                <div class="stat-icon">⭐</div>
                <div class="stat-value">${benchmark.level || 'Beginner'}</div>
                <div class="stat-label">Skill Level</div>
                <div class="stat-sublabel">${benchmark.professional_percentile || 0}% of pro</div>
            </div>
        </div>

        <!-- Top 3 Shot Type Predictions -->
        <div class="analysis-section">
            <h3>🎯 CNN Model Predictions (Top 3)</h3>
            <div class="predictions-container">
    `;
    
    if (shotPrediction.top_3_predictions && shotPrediction.top_3_predictions.length > 0) {
        shotPrediction.top_3_predictions.forEach((pred, idx) => {
            const conf = (pred.confidence * 100);
            html += `
                <div class="prediction-bar">
                    <div class="prediction-rank">#${idx + 1}</div>
                    <div class="prediction-label">${pred.shot_type}</div>
                    <div class="prediction-progress">
                        <div class="prediction-fill" style="width: ${conf}%"></div>
                    </div>
                    <div class="prediction-value">${conf.toFixed(1)}%</div>
                </div>
            `;
        });
    }
    
    html += `
            </div>
        </div>

        <!-- Component Scores Breakdown -->
        <div class="analysis-section">
            <h3>📊 Performance Component Scores</h3>
            <div class="component-scores-grid">
    `;
    
    for (const [key, value] of Object.entries(componentScores)) {
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        const percentage = (value / 10) * 100;
        const color = value >= 7 ? '#28a745' : value >= 5 ? '#ffc107' : '#dc3545';
        
        html += `
            <div class="component-item">
                <div class="component-header">
                    <span class="component-label">${label}</span>
                    <span class="component-value">${value.toFixed(1)}/10</span>
                </div>
                <div class="component-bar">
                    <div class="component-fill" style="width: ${percentage}%; background: ${color}"></div>
                </div>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>

        <!-- Mechanics Analysis (YOLO) -->
        <div class="analysis-section">
            <h3>🔧 Shot Mechanics Analysis</h3>
            <div class="mechanics-grid">
                <div class="mechanic-item">
                    <strong>Stance:</strong> <span>${mechanics.stance || 'Unknown'}</span>
                </div>
                <div class="mechanic-item">
                    <strong>Ball Position:</strong> <span>${mechanics.ball_position || 'Unknown'}</span>
                </div>
                <div class="mechanic-item">
                    <strong>Close Contact:</strong> <span>${mechanics.close_contact ? '✅ Yes' : '❌ No'}</span>
                </div>
                <div class="mechanic-item">
                    <strong>Mechanics Score:</strong> <span>${mechanics.mechanics_score.toFixed(2)}/1.0</span>
                </div>
            </div>
            ${mechanics.issues && mechanics.issues.length > 0 ? `
                <div class="issues-box">
                    <h4>⚠️ Detected Issues:</h4>
                    <ul>
                        ${mechanics.issues.map(issue => `<li>${issue}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>

        <!-- Strengths & Weaknesses -->
        <div class="analysis-section">
            <div class="strengths-weaknesses-grid">
                <div class="strengths-box">
                    <h3>💪 Your Strengths</h3>
                    <ul>
    `;
    
    if (strengths.strengths && strengths.strengths.length > 0) {
        strengths.strengths.forEach(strength => {
            html += `<li><strong>${strength.component}:</strong> ${strength.comment} <span class="score-badge">${strength.score.toFixed(1)}/10</span></li>`;
        });
    } else {
        html += `<li>Focus on building foundational skills consistently</li>`;
    }
    
    html += `
                    </ul>
                </div>
                <div class="weaknesses-box">
                    <h3>🎯 Areas to Improve</h3>
                    <ul>
    `;
    
    if (strengths.weaknesses && strengths.weaknesses.length > 0) {
        strengths.weaknesses.forEach(weakness => {
            html += `<li><strong>${weakness.component}:</strong> ${weakness.comment} <span class="score-badge weak">${weakness.score.toFixed(1)}/10</span></li>`;
        });
    } else {
        html += `<li>Keep refining your excellent technique!</li>`;
    }
    
    html += `
                    </ul>
                </div>
            </div>
        </div>

        <!-- AI RECOMMENDATIONS SECTION -->
        <div class="analysis-section recommendations-section">
            <h3>🤖 AI-Powered Training Recommendations</h3>
            
            <!-- Overall Advice -->
            <div class="recommendation-card highlight">
                <h4>📢 Overall Training Advice</h4>
                <div class="advice-content">
    `;
    
    const overallAdvice = recommendations.overall_advice || {};
    if (typeof overallAdvice === 'string') {
        html += `<p>${overallAdvice}</p>`;
    } else {
        html += `
                    <p><strong>Level:</strong> ${overallAdvice.level || 'Developing'}</p>
                    <p><strong>Focus Area:</strong> ${overallAdvice.focus || 'Technical improvement'}</p>
                    <p><strong>Training Frequency:</strong> ${overallAdvice.training_frequency || '3-4 times/week'}</p>
                    <p class="advice-message">${overallAdvice.message || 'Keep practicing consistently'}</p>
        `;
    }
    
    html += `
                </div>
            </div>
            
            <!-- Shot-Specific Drills -->
            <div class="recommendation-card">
                <h4>⚽ Shot-Specific Training Drills</h4>
                <p class="drill-intro"><strong>Recommended for ${shotType}:</strong></p>
                <ul class="drill-list">
    `;
    
    const drills = recommendations.shot_specific_drills || [];
    if (Array.isArray(drills) && drills.length > 0) {
        drills.forEach((drill, index) => {
            html += `<li><span class="drill-number">${index + 1}</span> ${drill}</li>`;
        });
    } else {
        html += `
            <li><span class="drill-number">1</span> Practice proper stance and approach</li>
            <li><span class="drill-number">2</span> Focus on ball contact timing</li>
            <li><span class="drill-number">3</span> Work on follow-through technique</li>
        `;
    }
    
    html += `
                </ul>
            </div>

            <!-- Weakness Training -->
            <div class="recommendation-card">
                <h4>🎯 Weakness-Targeted Training</h4>
    `;
    
    const weaknessTraining = recommendations.weakness_training || {};
    if (weaknessTraining.priority_order && weaknessTraining.priority_order.length > 0) {
        weaknessTraining.priority_order.forEach(training => {
            html += `
                <div class="weakness-training-item">
                    <h5>🔧 ${training.focus}</h5>
                    <p><strong>Current Score:</strong> ${training.current_score?.toFixed(1) || 'N/A'}/10 
                       <span class="severity ${training.severity?.toLowerCase()}">(${training.severity || 'Moderate'})</span></p>
                    <ul>
            `;
            (training.exercises || []).forEach(exercise => {
                html += `<li>${exercise}</li>`;
            });
            html += `</ul></div>`;
        });
    } else {
        html += `<p>No critical weaknesses detected. Focus on maintaining consistency.</p>`;
    }
    
    html += `
            </div>

            <!-- Pro Tips -->
            <div class="recommendation-card highlight">
                <h4>💡 Professional Tips for ${shotType}</h4>
                <ul class="pro-tips-list">
    `;
    
    const proTips = recommendations.pro_tips || [];
    if (proTips.length > 0) {
        proTips.forEach(tip => {
            html += `<li>${tip}</li>`;
        });
    } else {
        html += `
            <li>Practice with both feet for versatility</li>
            <li>Watch professional players for technique reference</li>
        `;
    }
    
    html += `
                </ul>
            </div>
        </div>

        <!-- Improvement Potential -->
        <div class="analysis-section">
            <h3>🚀 Your Improvement Potential</h3>
            <div class="improvement-potential">
                <div class="potential-metric">
                    <span class="metric-label">Current Score:</span>
                    <span class="metric-value">${improvement.current_score?.toFixed(1) || overallScore.toFixed(1)}/10</span>
                </div>
                <div class="potential-arrow">➡️</div>
                <div class="potential-metric highlight">
                    <span class="metric-label">Potential Score:</span>
                    <span class="metric-value">${improvement.potential_score?.toFixed(1) || (overallScore + 2).toFixed(1)}/10</span>
                </div>
                <div class="potential-metric">
                    <span class="metric-label">Improvement:</span>
                    <span class="metric-value success">+${improvement.improvement_points?.toFixed(1) || '2.0'} points</span>
                </div>
                <div class="potential-metric">
                    <span class="metric-label">Timeline:</span>
                    <span class="metric-value">${improvement.achievable_in_weeks || '2-4 months'}</span>
                </div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="analysis-section charts-section">
            <h3>📈 Performance Visualization Charts</h3>
            
            <div class="chart-container">
                <h4>Shot Accuracy Radar Chart</h4>
                <canvas id="accuracyChart"></canvas>
            </div>
            
            <div class="chart-container">
                <h4>Training Focus Areas (Bar Chart)</h4>
                <canvas id="trainingChart"></canvas>
            </div>
            
            <div class="chart-container">
                <h4>Expected Progress Trajectory</h4>
                <canvas id="progressChart"></canvas>
            </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
            <button class="btn-primary" onclick="window.print()">🖨️ Print Analysis</button>
            <button class="btn-secondary" onclick="location.reload()">🔄 Analyze Another Video</button>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
    
    // Generate charts after DOM update
    setTimeout(() => {
        generateCharts(results);
    }, 100);
}

// ==================== CHART GENERATION ====================

function generateCharts(results) {
    const performanceScore = results.performance_score || {};
    const components = performanceScore.component_scores || {};
    
    // 1. Accuracy Radar Chart
    const accuracyCanvas = document.getElementById('accuracyChart');
    if (accuracyCanvas && typeof Chart !== 'undefined') {
        const ctx = accuracyCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: Object.keys(components).map(k => 
                    k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                ),
                datasets: [{
                    label: 'Your Performance',
                    data: Object.values(components),
                    backgroundColor: 'rgba(30, 144, 255, 0.2)',
                    borderColor: 'rgba(30, 144, 255, 1)',
                    pointBackgroundColor: 'rgba(30, 144, 255, 1)',
                    borderWidth: 2
                }, {
                    label: 'Professional Level',
                    data: Object.keys(components).map(() => 8.5),
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderDash: [5, 5]
                }]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        min: 0,
                        max: 10,
                        ticks: { stepSize: 2, color: '#fff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: '#fff' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#fff' } }
                }
            }
        });
    }
    
    // 2. Training Focus Bar Chart
    const trainingCanvas = document.getElementById('trainingChart');
    if (trainingCanvas && typeof Chart !== 'undefined') {
        const ctx = trainingCanvas.getContext('2d');
        const sortedComponents = Object.entries(components).sort((a, b) => a[1] - b[1]);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedComponents.map(([k]) => 
                    k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                ),
                datasets: [{
                    label: 'Current Score',
                    data: sortedComponents.map(([, v]) => v),
                    backgroundColor: sortedComponents.map(([, v]) => 
                        v >= 7 ? 'rgba(40, 167, 69, 0.8)' : 
                        v >= 5 ? 'rgba(255, 193, 7, 0.8)' : 
                        'rgba(220, 53, 69, 0.8)'
                    )
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, max: 10, ticks: { color: '#fff' } },
                    x: { ticks: { color: '#fff' } }
                },
                plugins: {
                    legend: { labels: { color: '#fff' } }
                }
            }
        });
    }
    
    // 3. Progress Trajectory Line Chart
    const progressCanvas = document.getElementById('progressChart');
    if (progressCanvas && typeof Chart !== 'undefined') {
        const ctx = progressCanvas.getContext('2d');
        const currentScore = performanceScore.overall_score || 0;
        const targetScore = Math.min(currentScore + 3, 10);
        
        const weeks = Array.from({length: 13}, (_, i) => `Week ${i}`);
        const progress = weeks.map((_, i) => {
            if (i === 0) return currentScore;
            const growth = (targetScore - currentScore) / 12;
            return Math.min(currentScore + (growth * i), targetScore);
        });
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: weeks,
                datasets: [{
                    label: 'Expected Progress',
                    data: progress,
                    borderColor: 'rgba(30, 144, 255, 1)',
                    backgroundColor: 'rgba(30, 144, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Professional Level',
                    data: weeks.map(() => 8.5),
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderDash: [5, 5],
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, max: 10, ticks: { color: '#fff' } },
                    x: { ticks: { color: '#fff' } }
                },
                plugins: {
                    legend: { labels: { color: '#fff' } }
                }
            }
        });
    }
}

// ==================== NOTIFICATIONS ====================

function showNotification(message, type = 'info') {
    const existing = document.querySelectorAll('.notification');
    existing.forEach(el => el.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    
    const icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <span>${icons[type]}</span>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" 
                style="background: none; border: none; color: white; 
                       font-size: 20px; cursor: pointer; margin-left: auto;">×</button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, type === 'error' ? 8000 : 5000);
}

// ==================== ENHANCED STYLES ====================

function addEnhancedStyles() {
    if (document.getElementById('enhanced-analyzer-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'enhanced-analyzer-styles';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #1E90FF;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 8px;
        }
        
        .upload-box.drag-over {
            border-color: #1E90FF;
            background: rgba(30, 144, 255, 0.1);
        }
        
        /* Summary Cards */
        .quick-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #1E1E1E 0%, #2A2A2A 100%);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            border: 2px solid #444;
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card.excellent {
            border-color: #28a745;
            background: linear-gradient(135deg, #1a3a1a 0%, #2d5a2d 100%);
        }
        
        .stat-card.good {
            border-color: #17a2b8;
            background: linear-gradient(135deg, #1a3a3a 0%, #2d5a5a 100%);
        }
        
        .stat-card.weak {
            border-color: #dc3545;
            background: linear-gradient(135deg, #3a1a1a 0%, #5a2d2d 100%);
        }
        
        .stat-icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #1E90FF;
            margin-bottom: 8px;
        }
        
        .stat-label {
            font-size: 14px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-sublabel {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        /* Analysis Sections */
        .analysis-section {
            margin: 40px 0;
            padding: 30px;
            background: #1E1E1E;
            border-radius: 15px;
            border: 1px solid #333;
        }
        
        .analysis-section h3 {
            color: #1E90FF;
            margin-bottom: 25px;
            font-size: 24px;
            border-bottom: 2px solid #1E90FF;
            padding-bottom: 10px;
        }
        
        /* Predictions */
        .predictions-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .prediction-bar {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }
        
        .prediction-rank {
            background: #1E90FF;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .prediction-label {
            min-width: 150px;
            font-weight: bold;
            color: #fff;
        }
        
        .prediction-progress {
            flex: 1;
            height: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
        }
        
        .prediction-fill {
            height: 100%;
            background: linear-gradient(90deg, #1E90FF, #4CAF50);
            border-radius: 15px;
            transition: width 1s ease;
        }
        
        .prediction-value {
            min-width: 60px;
            text-align: right;
            font-weight: bold;
            color: #1E90FF;
            font-size: 18px;
        }
        
        /* Component Scores */
        .component-scores-grid {
            display: grid;
            gap: 20px;
        }
        
        .component-item {
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }
        
        .component-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        
        .component-label {
            font-weight: bold;
            color: #fff;
        }
        
        .component-value {
            color: #1E90FF;
            font-weight: bold;
        }
        
        .component-bar {
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .component-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 1s ease;
        }
        
        /* Mechanics */
        .mechanics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .mechanic-item {
            padding: 15px;
            background: rgba(30, 144, 255, 0.1);
            border-radius: 8px;
            border-left: 3px solid #1E90FF;
        }
        
        .mechanic-item strong {
            color: #1E90FF;
            display: block;
            margin-bottom: 5px;
        }
        
        .issues-box {
            padding: 20px;
            background: rgba(220, 53, 69, 0.1);
            border-radius: 8px;
            border-left: 4px solid #dc3545;
        }
        
        .issues-box h4 {
            color: #dc3545;
            margin-bottom: 10px;
        }
        
        /* Strengths & Weaknesses */
        .strengths-weaknesses-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        .strengths-box, .weaknesses-box {
            padding: 25px;
            border-radius: 10px;
        }
        
        .strengths-box {
            background: rgba(40, 167, 69, 0.1);
            border: 2px solid #28a745;
        }
        
        .strengths-box h3 {
            color: #28a745;
            border-color: #28a745;
        }
        
        .weaknesses-box {
            background: rgba(255, 193, 7, 0.1);
            border: 2px solid #ffc107;
        }
        
        .weaknesses-box h3 {
            color: #ffc107;
            border-color: #ffc107;
        }
        
        .score-badge {
            display: inline-block;
            padding: 4px 10px;
            background: #28a745;
            color: white;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 8px;
        }
        
        .score-badge.weak {
            background: #dc3545;
        }
        
        /* Recommendations */
        .recommendations-section {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        
        .recommendation-card {
            margin: 25px 0;
            padding: 25px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border-left: 4px solid #1E90FF;
        }
        
        .recommendation-card.highlight {
            background: rgba(30, 144, 255, 0.1);
            border-left-color: #1E90FF;
        }
        
        .recommendation-card h4 {
            color: #1E90FF;
            margin-bottom: 15px;
        }
        
        .drill-list, .pro-tips-list {
            list-style: none;
            padding: 0;
        }
        
        .drill-list li, .pro-tips-list li {
            padding: 12px;
            margin: 10px 0;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            border-left: 3px solid #1E90FF;
        }
        
        .drill-number {
            display: inline-block;
            width: 30px;
            height: 30px;
            background: #1E90FF;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            margin-right: 10px;
            font-weight: bold;
        }
        
        .weakness-training-item {
            margin: 20px 0;
            padding: 20px;
            background: rgba(220, 53, 69, 0.1);
            border-radius: 8px;
            border-left: 4px solid #dc3545;
        }
        
        .severity {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .severity.critical {
            background: #dc3545;
            color: white;
        }
        
        .severity.moderate {
            background: #ffc107;
            color: black;
        }
        
        /* Improvement Potential */
        .improvement-potential {
            display: flex;
            align-items: center;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
            padding: 30px;
            background: rgba(30, 144, 255, 0.1);
            border-radius: 15px;
        }
        
        .potential-metric {
            text-align: center;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            min-width: 150px;
        }
        
        .potential-metric.highlight {
            background: rgba(30, 144, 255, 0.2);
            border: 2px solid #1E90FF;
        }
        
        .metric-label {
            display: block;
            font-size: 14px;
            color: #999;
            margin-bottom: 10px;
        }
        
        .metric-value {
            display: block;
            font-size: 28px;
            font-weight: bold;
            color: #1E90FF;
        }
        
        .metric-value.success {
            color: #28a745;
        }
        
        .potential-arrow {
            font-size: 48px;
            color: #1E90FF;
        }
        
        /* Charts */
        .charts-section {
            background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
        }
        
        .chart-container {
            margin: 30px 0;
            padding: 25px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            border: 1px solid #333;
        }
        
        .chart-container h4 {
            color: #1E90FF;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .chart-container canvas {
            max-height: 400px;
        }
        
        /* Action Buttons */
        .action-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin: 40px 0;
            flex-wrap: wrap;
        }
        
        .btn-primary, .btn-secondary {
            padding: 15px 40px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #1E90FF, #4CAF50);
            color: white;
        }
        
        .btn-secondary {
            background: #444;
            color: white;
        }
        
        .btn-primary:hover, .btn-secondary:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .quick-summary {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .strengths-weaknesses-grid {
                grid-template-columns: 1fr;
            }
            
            .improvement-potential {
                flex-direction: column;
            }
            
            .potential-arrow {
                transform: rotate(90deg);
            }
        }
    `;
    
    document.head.appendChild(style);
}

function startVideoAnalysis() {
    console.log('Starting analysis...');
    
    analysisInProgress = true;
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
    }
    
    showProgressIndicator();
    
    const formData = new FormData();
    formData.append('video', currentVideoFile);
    
    fetch('/api/upload_video', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('Analysis response:', data);
        hideProgressIndicator();
        
        // Check if validation failed
        if (data.results && data.results.validation_failed) {
            showValidationError(data.results);
            return;
        }
        
        if (data.success && data.results) {
            displayCompleteResults(data.results);
            showNotification('Analysis complete!', 'success');
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
    })
    .catch(error => {
        console.error('Analysis error:', error);
        hideProgressIndicator();
        showNotification('Analysis failed: ' + error.message, 'error');
    })
    .finally(() => {
        analysisInProgress = false;
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = '🤖 Analyze Performance';
        }
    });
}

// Add this new function to show validation errors
function showValidationError(results) {
    const resultsDiv = document.getElementById('analysisResults');
    if (!resultsDiv) return;
    
    const details = results.details || {};
    
    const html = `
        <div class="validation-error-container">
            <div class="error-icon">⚠️</div>
            <h2>❌ Not a Football Video</h2>
            <p class="error-message">${results.message}</p>
            
            <div class="validation-details">
                <h3>Detection Summary</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">Confidence Score:</span>
                        <span class="detail-value">${details.confidence_score?.toFixed(1) || 0}%</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Detection Rate:</span>
                        <span class="detail-value">${(details.detection_rate * 100)?.toFixed(1) || 0}%</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Frames Analyzed:</span>
                        <span class="detail-value">${details.frames_analyzed || 0}</span>
                    </div>
                </div>
            </div>
            
            <div class="suggestion-box">
                <h3>💡 Suggestion</h3>
                <p>${details.suggestion}</p>
                <ul>
                    <li>✓ Video should show clear football/soccer actions</li>
                    <li>✓ Player(s) and ball should be visible</li>
                    <li>✓ Good lighting and camera angle</li>
                    <li>✓ Training or match footage works best</li>
                </ul>
            </div>
            
            <div class="action-buttons">
                <button class="btn-primary" onclick="location.reload()">
                    🔄 Upload Different Video
                </button>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
    
    showNotification('Please upload a valid football video', 'warning');
}