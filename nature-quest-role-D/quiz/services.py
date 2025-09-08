import requests
import json
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from .models import Quiz, Question, QuizAttempt, QuestionResponse, QuestionBank, QuizMetrics

logger = logging.getLogger(__name__)


class HuggingFaceQuizGenerator:
    """Service for generating quiz questions using Hugging Face API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'HUGGINGFACE_API_KEY', '')
        self.base_url = "https://api-inference.huggingface.co/models"
        self.model = "microsoft/DialoGPT-large"  # Can be customized
        
    def generate_questions(self, tech_stack: str, difficulty: str, count: int = 5) -> List[Dict]:
        """
        Generate quiz questions for specific tech stack and difficulty
        Returns list of question dictionaries
        """
        questions = []
        
        try:
            for i in range(count):
                # Generate mix of multiple choice and checkbox questions
                question_type = 'multiple_choice' if i < 3 else 'checkbox'
                
                question_data = self._generate_single_question(
                    tech_stack, difficulty, question_type
                )
                
                if question_data:
                    questions.append(question_data)
                
                # Fallback to question bank if generation fails
                if len(questions) < i + 1:
                    fallback = self._get_fallback_question(tech_stack, difficulty, question_type)
                    if fallback:
                        questions.append(fallback)
            
            logger.info(f"Generated {len(questions)} questions for {tech_stack} ({difficulty})")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            # Return fallback questions from question bank
            return self._get_fallback_questions(tech_stack, difficulty, count)
    
    def _generate_single_question(self, tech_stack: str, difficulty: str, 
                                 question_type: str) -> Optional[Dict]:
        """Generate a single question using Hugging Face"""
        
        # Create context-appropriate prompt
        prompt = self._create_prompt(tech_stack, difficulty, question_type)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 500,
                    "temperature": 0.7,
                    "do_sample": True,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_generated_text(result, tech_stack, difficulty, question_type)
            else:
                logger.warning(f"HF API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Hugging Face API: {str(e)}")
            return None
    
    def _create_prompt(self, tech_stack: str, difficulty: str, question_type: str) -> str:
        """Create appropriate prompt for question generation"""
        
        difficulty_modifiers = {
            'easy': 'basic concepts and syntax',
            'medium': 'intermediate concepts and best practices', 
            'hard': 'advanced concepts and complex scenarios'
        }
        
        type_instructions = {
            'multiple_choice': 'Create a multiple choice question with 4 options where only ONE is correct',
            'checkbox': 'Create a checkbox question with 4-5 options where MULTIPLE answers can be correct'
        }
        
        prompt = f"""
Generate a {difficulty} level {tech_stack} programming question about {difficulty_modifiers.get(difficulty, 'concepts')}.

{type_instructions.get(question_type, '')}

Format the response as JSON:
{{
    "question": "Your question text here",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answers": [0, 2],
    "explanation": "Explanation of the correct answer(s)"
}}

Question about {tech_stack}:
"""
        return prompt
    
    def _parse_generated_text(self, result: Dict, tech_stack: str, 
                            difficulty: str, question_type: str) -> Optional[Dict]:
        """Parse the generated text and extract question data"""
        try:
            # Extract generated text
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
            else:
                generated_text = result.get('generated_text', '')
            
            # Try to extract JSON from the response
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = generated_text[json_start:json_end]
                question_data = json.loads(json_text)
                
                # Validate and clean the data
                return self._validate_question_data(
                    question_data, tech_stack, difficulty, question_type
                )
            
        except Exception as e:
            logger.error(f"Error parsing generated question: {str(e)}")
        
        return None
    
    def _validate_question_data(self, data: Dict, tech_stack: str, 
                              difficulty: str, question_type: str) -> Optional[Dict]:
        """Validate and clean generated question data"""
        try:
            required_fields = ['question', 'options', 'correct_answers']
            if not all(field in data for field in required_fields):
                return None
            
            # Clean and validate
            question = data['question'].strip()
            options = [opt.strip() for opt in data['options'][:5]]  # Max 5 options
            correct_answers = data['correct_answers']
            explanation = data.get('explanation', '').strip()
            
            # Validate correct answers
            if not isinstance(correct_answers, list):
                correct_answers = [correct_answers]
            
            correct_answers = [idx for idx in correct_answers if 0 <= idx < len(options)]
            
            if not correct_answers:
                return None
            
            # For multiple choice, ensure only one correct answer
            if question_type == 'multiple_choice' and len(correct_answers) > 1:
                correct_answers = [correct_answers[0]]
            
            # For checkbox, ensure at least one but not all answers are correct
            if question_type == 'checkbox':
                if len(correct_answers) == len(options):
                    correct_answers = correct_answers[:-1]  # Remove one
            
            return {
                'tech_stack': tech_stack,
                'difficulty': difficulty,
                'question_type': question_type,
                'question_text': question,
                'options': options,
                'correct_answers': correct_answers,
                'explanation': explanation,
                'generated_by_hf': True,
                'source_prompt': f"{tech_stack} {difficulty} {question_type}"
            }
            
        except Exception as e:
            logger.error(f"Error validating question data: {str(e)}")
            return None
    
    def _get_fallback_question(self, tech_stack: str, difficulty: str, 
                             question_type: str) -> Optional[Dict]:
        """Get a fallback question from the question bank"""
        try:
            # Try to find unused or least used questions
            questions = QuestionBank.objects.filter(
                tech_stack__icontains=tech_stack,
                difficulty=difficulty,
                question_type=question_type,
                is_active=True
            ).order_by('times_used', '?')[:1]
            
            if questions:
                q = questions[0]
                q.increment_usage()
                
                return {
                    'tech_stack': tech_stack,
                    'difficulty': difficulty,
                    'question_type': question_type,
                    'question_text': q.question_text,
                    'options': q.options,
                    'correct_answers': q.correct_answers,
                    'explanation': q.explanation,
                    'generated_by_hf': False,
                    'source_prompt': ''
                }
        
        except Exception as e:
            logger.error(f"Error getting fallback question: {str(e)}")
        
        return None
    
    def _get_fallback_questions(self, tech_stack: str, difficulty: str, 
                              count: int) -> List[Dict]:
        """Get multiple fallback questions when generation completely fails"""
        questions = []
        
        # Get mix of question types
        for i in range(count):
            question_type = 'multiple_choice' if i < count // 2 else 'checkbox'
            fallback = self._get_fallback_question(tech_stack, difficulty, question_type)
            if fallback:
                questions.append(fallback)
        
        # If still not enough, create basic template questions
        while len(questions) < count:
            questions.append(self._create_template_question(tech_stack, difficulty, len(questions)))
        
        return questions[:count]
    
    def _create_template_question(self, tech_stack: str, difficulty: str, index: int) -> Dict:
        """Create a basic template question as last resort"""
        templates = {
            'easy': {
                'question': f"What is a fundamental concept in {tech_stack}?",
                'options': ["Variables", "Loops", "Functions", "All of the above"],
                'correct_answers': [3]
            },
            'medium': {
                'question': f"Which best practices apply to {tech_stack} development?",
                'options': ["Code reusability", "Error handling", "Documentation", "All of the above"],
                'correct_answers': [3]
            },
            'hard': {
                'question': f"What advanced {tech_stack} concepts require careful consideration?",
                'options': ["Memory management", "Concurrency", "Security", "All of the above"],
                'correct_answers': [3]
            }
        }
        
        template = templates.get(difficulty, templates['easy'])
        
        return {
            'tech_stack': tech_stack,
            'difficulty': difficulty,
            'question_type': 'multiple_choice',
            'question_text': template['question'],
            'options': template['options'],
            'correct_answers': template['correct_answers'],
            'explanation': f"This covers important {difficulty} level concepts in {tech_stack}.",
            'generated_by_hf': False,
            'source_prompt': 'template'
        }


class QuizService:
    """Service for managing quiz creation, scoring, and completion"""
    
    def __init__(self):
        self.generator = HuggingFaceQuizGenerator()
    
    def create_quiz_for_user(self, user_id: int, challenge_id: int, 
                           tech_stack: str, difficulty: str) -> Optional[Quiz]:
        """Create a new quiz for a user after challenge completion"""
        try:
            with transaction.atomic():
                user = User.objects.get(id=user_id)
                
                # Check if quiz already exists for this challenge
                existing_quiz = Quiz.objects.filter(
                    user=user, challenge_id=challenge_id
                ).first()
                
                if existing_quiz:
                    logger.info(f"Quiz already exists for user {user_id}, challenge {challenge_id}")
                    return existing_quiz
                
                # Generate questions
                question_data_list = self.generator.generate_questions(
                    tech_stack, difficulty, count=5
                )
                
                if not question_data_list:
                    logger.error(f"Failed to generate questions for {tech_stack} ({difficulty})")
                    return None
                
                # Create quiz
                quiz = Quiz.objects.create(
                    user=user,
                    challenge_id=challenge_id,
                    difficulty=difficulty,
                    tech_stack=tech_stack,
                    total_questions=len(question_data_list)
                )
                
                # Create questions
                for i, question_data in enumerate(question_data_list):
                    Question.objects.create(
                        quiz=quiz,
                        question_type=question_data['question_type'],
                        question_text=question_data['question_text'],
                        tech_stack=question_data['tech_stack'],
                        difficulty=question_data['difficulty'],
                        options=question_data['options'],
                        correct_answers=question_data['correct_answers'],
                        explanation=question_data.get('explanation', ''),
                        order=i + 1
                    )
                    
                    # Store in question bank for reuse
                    self._store_in_question_bank(question_data)
                
                # Create quiz attempt
                QuizAttempt.objects.create(quiz=quiz)
                
                logger.info(f"Created quiz {quiz.id} for user {user.username}")
                return quiz
                
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error creating quiz: {str(e)}")
        
        return None
    
    def _store_in_question_bank(self, question_data: Dict):
        """Store generated question in question bank for reuse"""
        try:
            if question_data.get('generated_by_hf'):
                QuestionBank.objects.create(**question_data)
        except Exception as e:
            logger.error(f"Error storing question in bank: {str(e)}")
    
    def submit_quiz(self, quiz_id: int, responses: List[Dict]) -> Dict[str, Any]:
        """Submit quiz answers and calculate score"""
        try:
            with transaction.atomic():
                quiz = Quiz.objects.select_related('user').get(id=quiz_id)
                attempt = quiz.attempt
                
                if attempt.is_submitted:
                    return {'success': False, 'error': 'Quiz already submitted'}
                
                questions = quiz.questions.all().order_by('order')
                total_points = 0
                earned_points = 0
                
                # Process each response
                for response_data in responses:
                    question_id = response_data['question_id']
                    selected_answers = response_data['selected_answers']
                    
                    try:
                        question = questions.get(id=question_id)
                        is_correct = self._check_answer(question, selected_answers)
                        points = question.points if is_correct else 0
                        
                        QuestionResponse.objects.create(
                            attempt=attempt,
                            question=question,
                            selected_answers=selected_answers,
                            is_correct=is_correct,
                            points_earned=points
                        )
                        
                        total_points += question.points
                        earned_points += points
                        
                    except Question.DoesNotExist:
                        logger.warning(f"Question {question_id} not found in quiz {quiz_id}")
                
                # Calculate final score
                score = (earned_points / total_points * 100) if total_points > 0 else 0
                passed = score >= quiz.pass_threshold
                
                # Update quiz and attempt
                quiz.score = score
                quiz.passed = passed
                quiz.completed_at = timezone.now()
                quiz.save()
                
                attempt.total_score = score
                attempt.submitted_at = timezone.now()
                attempt.save()
                
                # Update metrics
                self._update_metrics(quiz)
                
                logger.info(f"Quiz {quiz_id} submitted: {score:.1f}% ({'PASSED' if passed else 'FAILED'})")
                
                return {
                    'success': True,
                    'score': score,
                    'passed': passed,
                    'earned_points': earned_points,
                    'total_points': total_points
                }
                
        except Quiz.DoesNotExist:
            return {'success': False, 'error': 'Quiz not found'}
        except Exception as e:
            logger.error(f"Error submitting quiz {quiz_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _check_answer(self, question: Question, selected_answers: List[int]) -> bool:
        """Check if the selected answers are correct"""
        correct_set = set(question.correct_answers)
        selected_set = set(selected_answers)
        return correct_set == selected_set
    
    def _update_metrics(self, quiz: Quiz):
        """Update quiz metrics for analytics"""
        try:
            metrics, created = QuizMetrics.objects.get_or_create(
                tech_stack=quiz.tech_stack,
                difficulty=quiz.difficulty,
                defaults={
                    'total_quizzes': 0,
                    'total_passes': 0,
                    'average_score': 0.0
                }
            )
            
            # Update metrics
            old_total = metrics.total_quizzes
            old_score_sum = metrics.average_score * old_total
            
            metrics.total_quizzes += 1
            if quiz.passed:
                metrics.total_passes += 1
            
            # Update average score
            new_score_sum = old_score_sum + quiz.score
            metrics.average_score = new_score_sum / metrics.total_quizzes
            
            metrics.save()
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
    
    def get_user_quiz_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive quiz statistics for a user"""
        try:
            user = User.objects.get(id=user_id)
            quizzes = Quiz.objects.filter(user=user)
            
            total_quizzes = quizzes.count()
            completed_quizzes = quizzes.filter(completed_at__isnull=False)
            passed_quizzes = completed_quizzes.filter(passed=True)
            
            stats = {
                'total_quizzes_taken': total_quizzes,
                'quizzes_passed': passed_quizzes.count(),
                'overall_pass_rate': 0.0,
                'average_score': 0.0,
                'favorite_tech_stack': '',
                'recent_quizzes': []
            }
            
            if completed_quizzes.exists():
                scores = completed_quizzes.values_list('score', flat=True)
                stats['average_score'] = sum(scores) / len(scores)
                stats['overall_pass_rate'] = (passed_quizzes.count() / completed_quizzes.count()) * 100
                
                # Find favorite tech stack
                tech_stacks = completed_quizzes.values_list('tech_stack', flat=True)
                if tech_stacks:
                    stats['favorite_tech_stack'] = max(set(tech_stacks), key=list(tech_stacks).count)
                
                # Recent quizzes
                stats['recent_quizzes'] = quizzes.order_by('-created_at')[:5]
            
            return stats
            
        except User.DoesNotExist:
            return {'error': 'User not found'}
        except Exception as e:
            logger.error(f"Error getting user quiz stats: {str(e)}")
            return {'error': str(e)}
