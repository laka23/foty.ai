"""
Football Performance Analyzer - Recommendation Engine
Generate personalized training advice and improvement suggestions
"""

import numpy as np
import config

class RecommendationEngine:
    """
    Generate personalized training recommendations based on shot analysis
    """
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.advice_categories = config.ADVICE_CATEGORIES
        self.drills_per_shot = config.DRILLS_PER_SHOT_TYPE
    
    def generate_recommendations(self, shot_analysis, performance_score):
        """
        Generate comprehensive training recommendations
        
        Args:
            shot_analysis: Complete shot analysis
            performance_score: Performance scoring results
            
        Returns:
            Dictionary with recommendations
        """
        shot_type = shot_analysis.get('shot_prediction', {}).get('predicted_shot_type', 'power')
        overall_score = performance_score.get('overall_score', 0)
        quality_category = performance_score.get('quality_category', 'Fair')
        component_scores = performance_score.get('component_scores', {})
        weaknesses = self._identify_weaknesses(component_scores)
        
        recommendations = {
            'overall_advice': self._get_overall_advice(quality_category, overall_score),
            'shot_specific_drills': self._get_shot_drills(shot_type),
            'weakness_targeted_training': self._get_weakness_training(weaknesses),
            'technique_improvements': self._get_technique_improvements(shot_analysis, component_scores),
            'power_training': self._get_power_training(performance_score.get('power_analysis', {})),
            'practice_plan': self._generate_practice_plan(shot_type, weaknesses),
            'progression_roadmap': self._create_progression_roadmap(overall_score, shot_type),
            'pro_tips': self._get_pro_tips(shot_type, quality_category)
        }
        
        return recommendations
    
    def _get_overall_advice(self, quality_category, score):
        """Get overall advice based on quality category"""
        base_advice = self.advice_categories.get(quality_category.lower(), 
                                                  self.advice_categories['fair'])
        
        if score >= 8.0:
            return {
                'level': 'Advanced',
                'message': base_advice,
                'focus': 'Consistency and match simulation',
                'training_frequency': '4-5 times per week',
                'priority': 'Maintain excellence, refine minor details'
            }
        elif score >= 6.0:
            return {
                'level': 'Intermediate',
                'message': base_advice,
                'focus': 'Power development and precision',
                'training_frequency': '3-4 times per week',
                'priority': 'Elevate good technique to excellent execution'
            }
        elif score >= 4.0:
            return {
                'level': 'Developing',
                'message': base_advice,
                'focus': 'Fundamental technique and body mechanics',
                'training_frequency': '3-4 times per week',
                'priority': 'Build strong technical foundation'
            }
        else:
            return {
                'level': 'Beginner',
                'message': base_advice,
                'focus': 'Basic stance, approach, and contact',
                'training_frequency': '2-3 times per week',
                'priority': 'Master the basics before progression'
            }
    
    def _get_shot_drills(self, shot_type):
        """Get specific drills for shot type"""
        # Map shot types to drill categories
        drill_mapping = {
            'Bicycle_Kick': 'Header',
            'chip': 'chip',
            'Chip_Shot': 'chip',
            'curl': 'curl',
            'Curved_Shot': 'curl',
            'Drive': 'power',
            'Header': 'Header',
            'Knuckleball': 'power',
            'power': 'power',
            'Rabona': 'curl',
            'volley': 'volley'
        }
        
        drill_category = drill_mapping.get(shot_type, 'power')
        drills = self.drills_per_shot.get(drill_category, self.drills_per_shot['power'])
        
        return {
            'shot_type': shot_type,
            'primary_drills': drills,
            'duration': '15-20 minutes per drill',
            'frequency': 'Daily practice recommended'
        }
    
    def _identify_weaknesses(self, component_scores):
        """Identify weaknesses from component scores"""
        weaknesses = []
        for component, score in component_scores.items():
            if score < 6.0:
                weaknesses.append({
                    'component': component,
                    'score': score,
                    'severity': 'Critical' if score < 4.0 else 'Moderate'
                })
        return weaknesses
    
    def _get_weakness_training(self, weaknesses):
        """Get targeted training for weaknesses"""
        if not weaknesses:
            return {
                'message': 'No major weaknesses detected! Focus on consistency.',
                'exercises': []
            }
        
        training_plans = {
            'shot_type_confidence': {
                'focus': 'Shot Recognition and Technique',
                'exercises': [
                    'Practice 50 shots daily with proper form',
                    'Record and review your technique',
                    'Work with a coach on shot mechanics',
                    'Study professional players performing similar shots'
                ]
            },
            'technique_quality': {
                'focus': 'Technical Execution',
                'exercises': [
                    'Slow-motion practice to perfect form',
                    'Mirror drills to check body positioning',
                    'Use training aids for proper technique',
                    'Focus on one technical aspect per session'
                ]
            },
            'body_positioning': {
                'focus': 'Stance and Balance',
                'exercises': [
                    'Balance drills on one leg',
                    'Core strengthening exercises',
                    'Yoga or pilates for flexibility',
                    'Practice approach angles'
                ]
            },
            'follow_through': {
                'focus': 'Follow-Through Mechanics',
                'exercises': [
                    'Exaggerate follow-through in practice',
                    'Film and analyze landing position',
                    'Practice with lighter balls first',
                    'Focus on full extension'
                ]
            },
            'ball_contact': {
                'focus': 'Ball Striking',
                'exercises': [
                    'Wall passing drills for accuracy',
                    'Target practice at different distances',
                    'Barefoot training for better feel',
                    'Practice with various ball pressures'
                ]
            }
        }
        
        targeted_training = []
        for weakness in weaknesses:
            component = weakness['component']
            if component in training_plans:
                plan = training_plans[component].copy()
                plan['severity'] = weakness['severity']
                plan['current_score'] = weakness['score']
                targeted_training.append(plan)
        
        return {
            'message': f'Focus on {len(weaknesses)} key area(s) for improvement',
            'priority_order': targeted_training
        }
    
    def _get_technique_improvements(self, shot_analysis, component_scores):
        """Get specific technique improvement suggestions"""
        improvements = []
        
        mechanics = shot_analysis.get('mechanics', {})
        issues = mechanics.get('issues', [])
        
        # Add issue-based improvements
        for issue in issues:
            if 'ball too far' in issue.lower():
                improvements.append({
                    'issue': 'Ball Distance',
                    'fix': 'Improve timing to strike ball at optimal distance',
                    'drill': 'Practice approach timing with stationary ball'
                })
            elif 'unbalanced' in issue.lower():
                improvements.append({
                    'issue': 'Balance',
                    'fix': 'Work on core stability and planted foot position',
                    'drill': 'Single-leg balance exercises and core work'
                })
            elif 'not detected' in issue.lower():
                improvements.append({
                    'issue': 'Visibility',
                    'fix': 'Ensure clear view of action, better camera angle',
                    'drill': 'Record from multiple angles for better analysis'
                })
        
        # Add score-based improvements
        if component_scores.get('shot_type_confidence', 10) < 7.0:
            improvements.append({
                'issue': 'Shot Consistency',
                'fix': 'Develop muscle memory through repetition',
                'drill': '100 shots daily with identical technique'
            })
        
        if component_scores.get('follow_through', 10) < 6.0:
            improvements.append({
                'issue': 'Incomplete Follow-Through',
                'fix': 'Extend kicking motion fully, maintain balance',
                'drill': 'Slow-motion practice focusing on complete extension'
            })
        
        return improvements
    
    def _get_power_training(self, power_analysis):
        """Get power-specific training recommendations"""
        power_category = power_analysis.get('category', 'weak')
        power_score = power_analysis.get('score', 0)
        
        if power_category == 'powerful':
            return {
                'status': 'Excellent power generation',
                'recommendations': [
                    'Maintain current strength training',
                    'Focus on power endurance',
                    'Practice power shots under fatigue',
                    'Work on controlled power for accuracy'
                ]
            }
        elif power_category == 'medium':
            return {
                'status': 'Moderate power, needs improvement',
                'recommendations': [
                    'Plyometric exercises: Box jumps, squat jumps',
                    'Leg strength training: Squats, lunges, leg press',
                    'Explosive movement drills',
                    'Practice striking with maximum effort'
                ]
            }
        else:
            return {
                'status': 'Low power - priority improvement area',
                'recommendations': [
                    'CRITICAL: Focus on leg strength development',
                    'Start with bodyweight exercises: Squats, lunges',
                    'Progress to weighted training',
                    'Work on hip flexor and core strength',
                    'Practice proper weight transfer technique',
                    'Build explosive power with sprints and jumps'
                ],
                'urgency': 'High Priority'
            }
    
    def _generate_practice_plan(self, shot_type, weaknesses):
        """Generate weekly practice plan"""
        return {
            'weekly_plan': {
                'Day 1 - Technique': {
                    'focus': 'Shot-specific technique',
                    'duration': '45 minutes',
                    'exercises': [
                        f'Warm-up: 10 minutes dynamic stretching',
                        f'{shot_type} technique drills: 20 minutes',
                        'Accuracy practice: 15 minutes'
                    ]
                },
                'Day 2 - Power': {
                    'focus': 'Strength and power',
                    'duration': '60 minutes',
                    'exercises': [
                        'Gym: Leg strength training - 30 minutes',
                        'Plyometrics: 15 minutes',
                        'Power shots: 15 minutes'
                    ]
                },
                'Day 3 - Weakness Focus': {
                    'focus': 'Target weaknesses',
                    'duration': '45 minutes',
                    'exercises': [
                        f'Primary weakness drill: {weaknesses[0]["component"] if weaknesses else "Balance"} - 25 minutes',
                        'Technical corrections: 20 minutes'
                    ]
                },
                'Day 4 - Match Simulation': {
                    'focus': 'Game-like scenarios',
                    'duration': '60 minutes',
                    'exercises': [
                        'Small-sided games: 30 minutes',
                        'Shot situations under pressure: 30 minutes'
                    ]
                },
                'Day 5 - Recovery & Review': {
                    'focus': 'Active recovery',
                    'duration': '30 minutes',
                    'exercises': [
                        'Light technique work',
                        'Video analysis of shots',
                        'Stretching and mobility'
                    ]
                }
            },
            'notes': [
                'Always warm up for 10 minutes before practice',
                'Cool down and stretch after each session',
                'Record your shots weekly to track progress',
                'Rest 2 days per week for recovery'
            ]
        }
    
    def _create_progression_roadmap(self, current_score, shot_type):
        """Create progression roadmap with milestones"""
        milestones = []
        
        if current_score < 4.0:
            milestones = [
                {
                    'level': 'Foundation',
                    'target_score': '4.0-5.0',
                    'timeline': '4-6 weeks',
                    'goals': [
                        'Master basic technique',
                        'Achieve consistent ball contact',
                        'Develop proper stance'
                    ]
                },
                {
                    'level': 'Development',
                    'target_score': '6.0-7.0',
                    'timeline': '2-3 months',
                    'goals': [
                        'Build shot power',
                        'Improve accuracy',
                        'Refine body mechanics'
                    ]
                },
                {
                    'level': 'Advanced',
                    'target_score': '8.0+',
                    'timeline': '6-12 months',
                    'goals': [
                        'Match-ready performance',
                        'Consistency under pressure',
                        'Professional-level execution'
                    ]
                }
            ]
        elif current_score < 6.0:
            milestones = [
                {
                    'level': 'Intermediate',
                    'target_score': '6.0-7.0',
                    'timeline': '6-8 weeks',
                    'goals': [
                        'Increase shot power',
                        'Improve consistency',
                        'Better follow-through'
                    ]
                },
                {
                    'level': 'Advanced',
                    'target_score': '8.0+',
                    'timeline': '3-6 months',
                    'goals': [
                        'Professional technique',
                        'Game-ready execution',
                        'Adaptability to match situations'
                    ]
                }
            ]
        else:
            milestones = [
                {
                    'level': 'Mastery',
                    'target_score': '9.0+',
                    'timeline': '2-4 months',
                    'goals': [
                        'Elite-level consistency',
                        'Advanced shot variations',
                        'Performance under pressure'
                    ]
                }
            ]
        
        return {
            'current_level': self._get_skill_level(current_score),
            'milestones': milestones,
            'long_term_goal': f'Master {shot_type} at professional level'
        }
    
    def _get_skill_level(self, score):
        """Determine skill level from score"""
        if score >= 8.0:
            return 'Advanced/Professional'
        elif score >= 6.0:
            return 'Intermediate'
        elif score >= 4.0:
            return 'Developing'
        else:
            return 'Beginner'
    
    def _get_pro_tips(self, shot_type, quality_category):
        """Get professional tips for shot type"""
        pro_tips = {
            'power': [
                'Plant foot 6-8 inches beside ball for maximum power',
                'Strike through the center of the ball',
                'Follow through with full leg extension',
                'Keep ankle locked for solid contact'
            ],
            'chip': [
                'Use side of foot for better control',
                'Lean back slightly on contact',
                'Follow through with toe pointed up',
                'Keep knee over ball for accuracy'
            ],
            'curl': [
                'Strike across the ball for spin',
                'Plant foot aimed at target',
                'Use inside/outside of foot depending on curl direction',
                'Follow through across body'
            ],
            'Header': [
                'Eyes on ball until contact',
                'Use forehead, not top of head',
                'Attack the ball, don\'t wait',
                'Neck muscles must be tensed'
            ],
            'volley': [
                'Keep eye on ball throughout',
                'Knee over ball for controlled shot',
                'Strike with laces for power',
                'Time your jump for optimal contact'
            ]
        }
        
        # Map shot types to categories
        tip_category = 'power'
        if shot_type in ['chip', 'Chip_Shot']:
            tip_category = 'chip'
        elif shot_type in ['curl', 'Curved_Shot', 'Rabona']:
            tip_category = 'curl'
        elif shot_type == 'Header':
            tip_category = 'Header'
        elif shot_type == 'volley':
            tip_category = 'volley'
        
        tips = pro_tips.get(tip_category, pro_tips['power'])
        
        # Add quality-specific tip
        if quality_category.lower() == 'weak':
            tips.append('Focus on mastering one aspect at a time')
        elif quality_category.lower() == 'excellent':
            tips.append('Work on performing under match pressure')
        
        return tips


# Test the recommendation engine
if __name__ == "__main__":
    print("="*70)
    print("TESTING RECOMMENDATION ENGINE")
    print("="*70)
    
    # Create engine
    engine = RecommendationEngine()
    
    # Sample data
    shot_analysis = {
        'shot_prediction': {
            'predicted_shot_type': 'power',
            'confidence': 0.75
        },
        'mechanics': {
            'mechanics_score': 0.65,
            'stance': 'balanced',
            'issues': ['Ball contact could be improved']
        }
    }
    
    performance_score = {
        'overall_score': 6.5,
        'quality_category': 'Good',
        'component_scores': {
            'shot_type_confidence': 7.5,
            'technique_quality': 6.5,
            'body_positioning': 8.0,
            'follow_through': 5.5,
            'ball_contact': 6.0
        },
        'power_analysis': {
            'category': 'medium',
            'score': 6.0
        }
    }
    
    # Generate recommendations
    print("\nGenerating Recommendations...")
    recommendations = engine.generate_recommendations(shot_analysis, performance_score)
    
    # Display results
    print("\nOVERALL ADVICE:")
    advice = recommendations['overall_advice']
    print(f"Level: {advice['level']}")
    print(f"Message: {advice['message']}")
    print(f"Training Frequency: {advice['training_frequency']}")
    
    print("\nSHOT-SPECIFIC DRILLS:")
    drills = recommendations['shot_specific_drills']
    for i, drill in enumerate(drills['primary_drills'], 1):
        print(f"{i}. {drill}")
    
    print("\nWEAKNESS-TARGETED TRAINING:")
    weakness_training = recommendations['weakness_targeted_training']
    print(weakness_training['message'])
    
    print("\nPRO TIPS:")
    for i, tip in enumerate(recommendations['pro_tips'], 1):
        print(f"{i}. {tip}")
    
    print("\n" + "="*70)
    print("Recommendation Engine Test Complete!")
    print("="*70)
