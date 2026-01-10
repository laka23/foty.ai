"""
Football Performance Analyzer - Performance Scoring Module
Calculate shot quality scores and provide detailed analysis
"""

import numpy as np
import config

class PerformanceScorer:
    """
    Score football shot performance based on multiple factors
    """
    
    def __init__(self):
        """Initialize performance scorer"""
        self.score_weights = config.SCORE_WEIGHTS
        self.quality_thresholds = config.QUALITY_THRESHOLDS
        self.power_categories = config.POWER_CATEGORIES
    
    def calculate_shot_score(self, shot_prediction, mechanics_analysis, power_estimation):
        """
        Calculate comprehensive shot score
        
        Args:
            shot_prediction: Shot type prediction from CNN
            mechanics_analysis: Mechanics analysis from YOLO
            power_estimation: Power estimation from trajectory
            
        Returns:
            Dictionary with detailed scoring
        """
        # Component scores
        scores = {}
        
        # 1. Shot Type Confidence Score (0-10)
        shot_confidence = shot_prediction.get('confidence', 0)
        scores['shot_type_confidence'] = shot_confidence * 10
        
        # 2. Technique Quality Score (0-10)
        mechanics_score = mechanics_analysis.get('mechanics_score', 0)
        scores['technique_quality'] = mechanics_score * 10
        
        # 3. Body Positioning Score (0-10)
        if mechanics_analysis.get('stance') == 'balanced':
            scores['body_positioning'] = 8.0
        elif mechanics_analysis.get('stance') == 'unbalanced':
            scores['body_positioning'] = 4.0
        else:
            scores['body_positioning'] = 6.0
        
        # Add bonus for close contact
        if mechanics_analysis.get('close_contact', False):
            scores['body_positioning'] += 2.0
        scores['body_positioning'] = min(scores['body_positioning'], 10.0)
        
        # 4. Follow Through Score (0-10)
        # Based on ball position relative to player
        ball_position = mechanics_analysis.get('ball_position', 'unknown')
        if ball_position == 'ground_level':
            scores['follow_through'] = 8.0
        elif ball_position == 'elevated':
            scores['follow_through'] = 6.0
        else:
            scores['follow_through'] = 5.0
        
        # 5. Ball Contact Score (0-10)
        # Based on detection confidence and player-ball proximity
        if mechanics_analysis.get('ball_detected', False):
            player_conf = mechanics_analysis.get('player', {}).get('confidence', 0)
            scores['ball_contact'] = player_conf * 10
        else:
            scores['ball_contact'] = 3.0
        
        # Calculate weighted total score
        weighted_score = sum(
            scores[component] * self.score_weights[component]
            for component in scores.keys()
        )
        
        # Get quality category
        quality_category = self._get_quality_category(weighted_score)
        
        # Power analysis
        power_category = power_estimation.get('power_category', 'unknown')
        power_score = power_estimation.get('power_score', 0) * 10
        
        # Determine if shot is weak
        is_weak = (
            weighted_score < 5.0 or
            power_category == 'weak' or
            mechanics_score < 0.4
        )
        
        return {
            'overall_score': round(weighted_score, 2),
            'quality_category': quality_category,
            'is_weak': is_weak,
            'component_scores': {
                'shot_type_confidence': round(scores['shot_type_confidence'], 2),
                'technique_quality': round(scores['technique_quality'], 2),
                'body_positioning': round(scores['body_positioning'], 2),
                'follow_through': round(scores['follow_through'], 2),
                'ball_contact': round(scores['ball_contact'], 2)
            },
            'power_analysis': {
                'category': power_category,
                'score': round(power_score, 2),
                'velocity': power_estimation.get('max_velocity', 0)
            },
            'mechanics_summary': {
                'stance': mechanics_analysis.get('stance', 'unknown'),
                'ball_position': mechanics_analysis.get('ball_position', 'unknown'),
                'close_contact': mechanics_analysis.get('close_contact', False),
                'issues': mechanics_analysis.get('issues', [])
            }
        }
    
    def _get_quality_category(self, score):
        """
        Get quality category based on score
        
        Args:
            score: Overall score (0-10)
            
        Returns:
            Quality category string
        """
        if score >= self.quality_thresholds['excellent']:
            return 'Excellent'
        elif score >= self.quality_thresholds['good']:
            return 'Good'
        elif score >= self.quality_thresholds['fair']:
            return 'Fair'
        else:
            return 'Weak'
    
    def compare_with_benchmark(self, score, shot_type):
        """
        Compare shot with benchmark scores
        
        Args:
            score: Current shot score
            shot_type: Type of shot
            
        Returns:
            Comparison analysis
        """
        # Benchmark scores for different shot types (out of 10)
        benchmarks = {
            'power': {'professional': 8.5, 'amateur': 6.0},
            'chip': {'professional': 8.0, 'amateur': 5.5},
            'curl': {'professional': 8.0, 'amateur': 5.5},
            'Header': {'professional': 7.5, 'amateur': 5.0},
            'volley': {'professional': 8.5, 'amateur': 6.0},
            'Drive': {'professional': 8.0, 'amateur': 6.0},
            'Bicycle_Kick': {'professional': 9.0, 'amateur': 4.0},
            'Rabona': {'professional': 8.5, 'amateur': 4.5},
            'Knuckleball': {'professional': 8.0, 'amateur': 5.0},
            'Chip_Shot': {'professional': 8.0, 'amateur': 5.5},
            'Curved_Shot': {'professional': 8.0, 'amateur': 5.5}
        }
        
        # Get benchmark for shot type
        benchmark = benchmarks.get(shot_type, {'professional': 8.0, 'amateur': 6.0})
        
        # Calculate percentiles
        pro_percentile = (score / benchmark['professional']) * 100
        amateur_percentile = (score / benchmark['amateur']) * 100
        
        # Determine level
        if score >= benchmark['professional'] * 0.9:
            level = 'Professional Level'
        elif score >= benchmark['amateur'] * 1.2:
            level = 'Advanced Amateur'
        elif score >= benchmark['amateur']:
            level = 'Amateur Level'
        else:
            level = 'Beginner Level'
        
        return {
            'level': level,
            'professional_benchmark': benchmark['professional'],
            'amateur_benchmark': benchmark['amateur'],
            'professional_percentile': round(min(pro_percentile, 100), 1),
            'amateur_percentile': round(min(amateur_percentile, 100), 1),
            'gap_to_professional': round(benchmark['professional'] - score, 2)
        }
    
    def identify_strengths_weaknesses(self, component_scores):
        """
        Identify strengths and weaknesses from component scores
        
        Args:
            component_scores: Dictionary of component scores
            
        Returns:
            Strengths and weaknesses analysis
        """
        strengths = []
        weaknesses = []
        
        for component, score in component_scores.items():
            component_name = component.replace('_', ' ').title()
            
            if score >= 8.0:
                strengths.append({
                    'component': component_name,
                    'score': score,
                    'comment': f'Excellent {component_name.lower()}'
                })
            elif score >= 6.0:
                strengths.append({
                    'component': component_name,
                    'score': score,
                    'comment': f'Good {component_name.lower()}'
                })
            elif score < 5.0:
                weaknesses.append({
                    'component': component_name,
                    'score': score,
                    'comment': f'Needs improvement in {component_name.lower()}'
                })
        
        # Sort by score
        strengths.sort(key=lambda x: x['score'], reverse=True)
        weaknesses.sort(key=lambda x: x['score'])
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'focus_area': weaknesses[0]['component'] if weaknesses else 'Overall consistency'
        }
    
    def generate_performance_summary(self, shot_analysis):
        """
        Generate comprehensive performance summary
        
        Args:
            shot_analysis: Complete shot analysis
            
        Returns:
            Performance summary
        """
        score_data = shot_analysis.get('performance_score', {})
        shot_type = shot_analysis.get('shot_prediction', {}).get('predicted_shot_type', 'Unknown')
        
        overall_score = score_data.get('overall_score', 0)
        quality = score_data.get('quality_category', 'Unknown')
        is_weak = score_data.get('is_weak', False)
        
        # Generate summary text
        if overall_score >= 8.0:
            summary_text = f"Outstanding {shot_type}! Your technique shows professional-level execution."
        elif overall_score >= 6.0:
            summary_text = f"Solid {shot_type} with good fundamentals. Minor refinements will elevate your game."
        elif overall_score >= 4.0:
            summary_text = f"Decent {shot_type} attempt. Focus on key improvements to enhance effectiveness."
        else:
            summary_text = f"Your {shot_type} needs significant work. Focus on mastering the basics first."
        
        # Weakness indicator
        if is_weak:
            power_warning = "⚠️ Shot lacks power - work on explosive leg drive and follow-through."
        else:
            power_warning = "✅ Shot power is adequate."
        
        return {
            'summary_text': summary_text,
            'quality_rating': quality,
            'score_out_of_10': overall_score,
            'power_warning': power_warning,
            'shot_type': shot_type,
            'primary_strength': self._get_primary_strength(score_data.get('component_scores', {})),
            'primary_weakness': self._get_primary_weakness(score_data.get('component_scores', {}))
        }
    
    def _get_primary_strength(self, component_scores):
        """Get the strongest component"""
        if not component_scores:
            return 'N/A'
        
        strongest = max(component_scores.items(), key=lambda x: x[1])
        return strongest[0].replace('_', ' ').title()
    
    def _get_primary_weakness(self, component_scores):
        """Get the weakest component"""
        if not component_scores:
            return 'N/A'
        
        weakest = min(component_scores.items(), key=lambda x: x[1])
        return weakest[0].replace('_', ' ').title()
    
    def calculate_improvement_potential(self, current_score, weaknesses):
        """
        Calculate potential score improvement
        
        Args:
            current_score: Current overall score
            weaknesses: List of weaknesses
            
        Returns:
            Improvement potential analysis
        """
        # Calculate potential improvement if weaknesses are addressed
        total_weakness_impact = sum(
            (8.0 - w['score']) * self.score_weights.get(
                w['component'].lower().replace(' ', '_'), 0.2
            )
            for w in weaknesses
        )
        
        potential_score = min(current_score + total_weakness_impact, 10.0)
        improvement_percentage = ((potential_score - current_score) / current_score) * 100 if current_score > 0 else 0
        
        return {
            'current_score': current_score,
            'potential_score': round(potential_score, 2),
            'improvement_points': round(potential_score - current_score, 2),
            'improvement_percentage': round(improvement_percentage, 1),
            'achievable_in_weeks': self._estimate_improvement_time(total_weakness_impact)
        }
    
    def _estimate_improvement_time(self, improvement_needed):
        """Estimate weeks needed for improvement"""
        if improvement_needed < 0.5:
            return '2-4 weeks'
        elif improvement_needed < 1.5:
            return '1-2 months'
        elif improvement_needed < 3.0:
            return '2-4 months'
        else:
            return '4-6 months'


# Test the scorer
if __name__ == "__main__":
    print("="*70)
    print("🎯 TESTING PERFORMANCE SCORER")
    print("="*70)
    
    # Create scorer
    scorer = PerformanceScorer()
    
    # Sample data
    shot_prediction = {
        'predicted_shot_type': 'power',
        'confidence': 0.85
    }
    
    mechanics_analysis = {
        'mechanics_score': 0.75,
        'stance': 'balanced',
        'ball_position': 'ground_level',
        'close_contact': True,
        'ball_detected': True,
        'player': {'confidence': 0.90},
        'issues': []
    }
    
    power_estimation = {
        'power_category': 'powerful',
        'power_score': 0.82,
        'max_velocity': 35.5
    }
    
    # Calculate score
    print("\n📊 Calculating Shot Score...")
    score_result = scorer.calculate_shot_score(
        shot_prediction,
        mechanics_analysis,
        power_estimation
    )
    
    print(f"\n⭐ Overall Score: {score_result['overall_score']}/10")
    print(f"📈 Quality Category: {score_result['quality_category']}")
    print(f"💪 Power Category: {score_result['power_analysis']['category']}")
    print(f"⚠️ Is Weak: {'Yes' if score_result['is_weak'] else 'No'}")
    
    print("\n📊 Component Scores:")
    for component, score in score_result['component_scores'].items():
        print(f"   {component.replace('_', ' ').title()}: {score}/10")
    
    # Benchmark comparison
    print("\n🏆 Benchmark Comparison:")
    benchmark = scorer.compare_with_benchmark(
        score_result['overall_score'],
        shot_prediction['predicted_shot_type']
    )
    print(f"   Level: {benchmark['level']}")
    print(f"   Professional Percentile: {benchmark['professional_percentile']}%")
    print(f"   Gap to Pro: {benchmark['gap_to_professional']} points")
    
    # Strengths & Weaknesses
    print("\n💪 Strengths & Weaknesses:")
    analysis = scorer.identify_strengths_weaknesses(score_result['component_scores'])
    
    print("   Strengths:")
    for strength in analysis['strengths'][:2]:
        print(f"      ✅ {strength['component']}: {strength['score']}/10")
    
    print("   Weaknesses:")
    for weakness in analysis['weaknesses']:
        print(f"      ⚠️ {weakness['component']}: {weakness['score']}/10")
    
    # Improvement potential
    print("\n🚀 Improvement Potential:")
    improvement = scorer.calculate_improvement_potential(
        score_result['overall_score'],
        analysis['weaknesses']
    )
    print(f"   Current: {improvement['current_score']}/10")
    print(f"   Potential: {improvement['potential_score']}/10")
    print(f"   Gain: +{improvement['improvement_points']} points ({improvement['improvement_percentage']}%)")
    print(f"   Timeline: {improvement['achievable_in_weeks']}")
    
    print("\n" + "="*70)
    print("✅ Performance Scorer Test Complete!")
    print("="*70)
