from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
import logging
import json

from .models import (
    Challenge, ChallengeAttempt, PhotoAnalysis, 
    LocationVerification, VerificationMetrics, FraudDetection
)
from .serializers import (
    ChallengeSerializer, ChallengeAttemptSerializer, ChallengeSubmissionSerializer,
    PhotoAnalysisSerializer, LocationVerificationSerializer, 
    VerificationMetricsSerializer, FraudDetectionSerializer
)
from .services import PhotoVerificationService, LocationVerificationService, FraudDetectionService

logger = logging.getLogger(__name__)


class ChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for challenge management - read-only for users
    Provides endpoints for listing and retrieving challenges
    """
    queryset = Challenge.objects.filter(is_active=True)
    serializer_class = ChallengeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter challenges based on user level or other criteria"""
        queryset = super().get_queryset()
        
        # Optional: Filter by difficulty or user preferences
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        location_type = self.request.query_params.get('location_type', None)
        if location_type:
            queryset = queryset.filter(location_type=location_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def my_progress(self, request):
        """Get user's progress on all challenges"""
        try:
            user_attempts = ChallengeAttempt.objects.filter(user=request.user)
            
            # Group by challenge
            progress_data = {}
            for attempt in user_attempts:
                challenge_id = attempt.challenge.id
                if challenge_id not in progress_data:
                    progress_data[challenge_id] = {
                        'challenge': ChallengeSerializer(attempt.challenge).data,
                        'attempts': [],
                        'best_attempt': None,
                        'is_completed': False
                    }
                
                attempt_data = ChallengeAttemptSerializer(attempt).data
                progress_data[challenge_id]['attempts'].append(attempt_data)
                
                # Track best attempt and completion status
                if attempt.status == 'verified':
                    progress_data[challenge_id]['is_completed'] = True
                    if not progress_data[challenge_id]['best_attempt']:
                        progress_data[challenge_id]['best_attempt'] = attempt_data
            
            return Response({
                'progress': list(progress_data.values()),
                'total_challenges': Challenge.objects.filter(is_active=True).count(),
                'completed_challenges': len([p for p in progress_data.values() if p['is_completed']])
            })
            
        except Exception as e:
            logger.error(f"Error fetching user progress: {str(e)}")
            return Response(
                {'error': f'Failed to fetch progress: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChallengeAttemptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for challenge submissions and attempts
    Handles photo and location verification
    """
    serializer_class = ChallengeAttemptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only show user's own attempts"""
        return ChallengeAttempt.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return ChallengeSubmissionSerializer
        return ChallengeAttemptSerializer
    
    def create(self, request, *args, **kwargs):
        """Submit a new challenge attempt with photo and location verification"""
        try:
            with transaction.atomic():
                # Validate and create attempt
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                # Get challenge
                challenge = get_object_or_404(Challenge, id=serializer.validated_data['challenge_id'])
                
                # Create attempt instance
                attempt = ChallengeAttempt.objects.create(
                    user=request.user,
                    challenge=challenge,
                    submitted_photo=serializer.validated_data['submitted_photo'],
                    submitted_latitude=serializer.validated_data['submitted_latitude'],
                    submitted_longitude=serializer.validated_data['submitted_longitude'],
                    submitted_description=serializer.validated_data.get('submitted_description', ''),
                    verification_status='pending'
                )
                
                # Start verification process
                verification_result = self._process_verification(attempt)
                
                # Update attempt with verification results
                attempt.verification_status = verification_result['status']
                attempt.verification_notes = verification_result['notes']
                attempt.verified_at = timezone.now() if verification_result['status'] == 'verified' else None
                attempt.save()
                
                return Response(
                    ChallengeAttemptSerializer(attempt).data,
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            logger.error(f"Error creating challenge attempt: {str(e)}")
            return Response(
                {'error': 'Failed to submit challenge attempt'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_verification(self, attempt: ChallengeAttempt) -> dict:
        """Process photo and location verification for an attempt"""
        try:
            # Initialize services
            photo_service = PhotoVerificationService()
            location_service = LocationVerificationService()
            fraud_service = FraudDetectionService()
            
            # Analyze photo
            photo_analysis = photo_service.analyze_photo(
                attempt.submitted_photo, 
                attempt.challenge
            )
            
            # Create PhotoAnalysis record
            photo_analysis_obj = PhotoAnalysis.objects.create(
                attempt=attempt,
                quality_score=photo_analysis.get('quality_score', 0.0),
                authenticity_score=photo_analysis.get('authenticity_score', 0.0),
                detected_objects=photo_analysis.get('detected_objects', []),
                exif_data=photo_analysis.get('exif_data', {}),
                verification_passed=photo_analysis.get('verification_passed', False),
                analysis_notes=json.dumps({
                    'timestamp_valid': photo_analysis.get('timestamp_valid', False),
                    'has_required_elements': photo_analysis.get('has_required_elements', False),
                    'location_from_exif': photo_analysis.get('location_from_exif')
                })
            )
            
            # Verify location
            location_verification = location_service.verify_location(
                attempt.submitted_latitude,
                attempt.submitted_longitude,
                attempt.challenge
            )
            
            # Create LocationVerification record
            location_verification_obj = LocationVerification.objects.create(
                attempt=attempt,
                is_within_radius=location_verification.get('verification_passed', False),
                distance_to_target=location_verification.get('distance_to_target', 0.0),
                foursquare_data=location_verification.get('foursquare_verification', {}),
                verification_confidence=location_verification.get('confidence_score', 0.0),
                verification_passed=location_verification.get('verification_passed', False)
            )
            
            # Check for fraud
            fraud_analysis = fraud_service.analyze_submission(attempt)
            
            # Create FraudDetection record
            fraud_detection_obj = FraudDetection.objects.create(
                attempt=attempt,
                risk_level=fraud_analysis.get('risk_level', 'low'),
                risk_score=fraud_analysis.get('risk_score', 0.0),
                risk_factors=fraud_analysis.get('risk_factors', []),
                requires_manual_review=fraud_analysis.get('requires_manual_review', False)
            )
            
            # Determine overall verification status
            photo_passed = photo_analysis_obj.verification_passed
            location_passed = location_verification_obj.verification_passed
            fraud_ok = not fraud_detection_obj.requires_manual_review
            
            if photo_passed and location_passed and fraud_ok:
                verification_status = 'verified'
                notes = 'Challenge completed successfully!'
                
                # Award points/badges (call to userprogress API)
                self._award_completion_rewards(attempt)
                
            elif fraud_detection_obj.requires_manual_review:
                verification_status = 'flagged'
                notes = f'Flagged for manual review: {", ".join(fraud_analysis.get("risk_factors", []))}'
            else:
                verification_status = 'failed'
                failed_reasons = []
                if not photo_passed:
                    failed_reasons.append('Photo verification failed')
                if not location_passed:
                    failed_reasons.append('Location verification failed')
                notes = f'Verification failed: {", ".join(failed_reasons)}'
            
            # Create verification metrics
            VerificationMetrics.objects.create(
                attempt=attempt,
                photo_analysis_time=0.5,  # Placeholder - track actual time
                location_verification_time=0.3,
                fraud_detection_time=0.1,
                total_processing_time=0.9,
                api_calls_made=['foursquare'],
                processing_errors=[]
            )
            
            return {
                'status': verification_status,
                'notes': notes,
                'photo_passed': photo_passed,
                'location_passed': location_passed,
                'fraud_check_passed': fraud_ok
            }
            
        except Exception as e:
            logger.error(f"Error in verification process: {str(e)}")
            return {
                'status': 'failed',
                'notes': f'Verification error: {str(e)}',
                'photo_passed': False,
                'location_passed': False,
                'fraud_check_passed': False
            }
    
    def _award_completion_rewards(self, attempt: ChallengeAttempt):
        """Award points and badges for successful challenge completion"""
        try:
            # This would call the userprogress API to award points
            # For now, we'll just log it
            points_awarded = attempt.challenge.points_reward
            logger.info(f"Awarded {points_awarded} points to user {attempt.user.id} for challenge {attempt.challenge.id}")
            
            # In a real implementation, make API call to userprogress app:
            # requests.post(f"{settings.USERPROGRESS_API_URL}/award-points/", {
            #     'user_id': attempt.user.id,
            #     'points': points_awarded,
            #     'source': f'challenge_{attempt.challenge.id}'
            # })
            
        except Exception as e:
            logger.error(f"Error awarding completion rewards: {str(e)}")
    
    @action(detail=True, methods=['post'])
    def resubmit(self, request, pk=None):
        """Allow resubmission of a failed challenge"""
        try:
            original_attempt = self.get_object()
            
            if original_attempt.verification_status == 'verified':
                return Response(
                    {'error': 'Challenge already completed successfully'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create new attempt with updated data
            new_data = request.data.copy()
            new_data['challenge_id'] = original_attempt.challenge.id
            
            return self.create(request)
            
        except Exception as e:
            logger.error(f"Error resubmitting challenge: {str(e)}")
            return Response(
                {'error': 'Failed to resubmit challenge'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for accessing verification details
    Provides detailed information about verification processes
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only show verification details for user's own attempts"""
        return None  # Will be overridden by specific actions
    
    @action(detail=False, methods=['get'])
    def photo_analysis(self, request):
        """Get photo analysis details for user's attempts"""
        try:
            attempt_id = request.query_params.get('attempt_id')
            if not attempt_id:
                return Response(
                    {'error': 'attempt_id parameter required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify user owns this attempt
            attempt = get_object_or_404(
                ChallengeAttempt, 
                id=attempt_id, 
                user=request.user
            )
            
            photo_analysis = PhotoAnalysis.objects.filter(attempt=attempt).first()
            if not photo_analysis:
                return Response(
                    {'error': 'Photo analysis not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(PhotoAnalysisSerializer(photo_analysis).data)
            
        except Exception as e:
            logger.error(f"Error fetching photo analysis: {str(e)}")
            return Response(
                {'error': 'Failed to fetch photo analysis'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def location_verification(self, request):
        """Get location verification details for user's attempts"""
        try:
            attempt_id = request.query_params.get('attempt_id')
            if not attempt_id:
                return Response(
                    {'error': 'attempt_id parameter required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify user owns this attempt
            attempt = get_object_or_404(
                ChallengeAttempt, 
                id=attempt_id, 
                user=request.user
            )
            
            location_verification = LocationVerification.objects.filter(attempt=attempt).first()
            if not location_verification:
                return Response(
                    {'error': 'Location verification not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(LocationVerificationSerializer(location_verification).data)
            
        except Exception as e:
            logger.error(f"Error fetching location verification: {str(e)}")
            return Response(
                {'error': 'Failed to fetch location verification'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get verification metrics and statistics"""
        try:
            from django.db import models
            
            user_attempts = ChallengeAttempt.objects.filter(user=request.user)
            
            total_attempts = user_attempts.count()
            verified_attempts = user_attempts.filter(status='verified').count()
            failed_attempts = user_attempts.filter(status='failed').count()
            flagged_attempts = user_attempts.filter(status='flagged').count()
            
            success_rate = (verified_attempts / total_attempts * 100) if total_attempts > 0 else 0
            
            # Get average verification metrics - handle case where VerificationMetrics may not exist
            try:
                metrics = VerificationMetrics.objects.filter(
                    attempt__user=request.user
                ).aggregate(
                    avg_processing_time=models.Avg('total_processing_time'),
                    avg_photo_time=models.Avg('photo_analysis_time'),
                    avg_location_time=models.Avg('location_verification_time')
                )
            except Exception as metrics_error:
                logger.warning(f"VerificationMetrics query failed: {str(metrics_error)}")
                metrics = {
                    'avg_processing_time': None,
                    'avg_photo_time': None,
                    'avg_location_time': None
                }
            
            return Response({
                'user_stats': {
                    'total_attempts': total_attempts,
                    'verified_attempts': verified_attempts,
                    'failed_attempts': failed_attempts,
                    'flagged_attempts': flagged_attempts,
                    'success_rate': round(success_rate, 2)
                },
                'performance_metrics': {
                    'avg_processing_time': metrics.get('avg_processing_time') or 0,
                    'avg_photo_analysis_time': metrics.get('avg_photo_time') or 0,
                    'avg_location_verification_time': metrics.get('avg_location_time') or 0
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching verification metrics: {str(e)}")
            return Response(
                {'error': f'Failed to fetch metrics: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Admin views for staff/admin users
from rest_framework.permissions import IsAdminUser

class AdminChallengeViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for challenge management
    Allows CRUD operations on challenges
    """
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get challenge statistics for admin dashboard"""
        try:
            challenges = Challenge.objects.all()
            
            stats = {
                'total_challenges': challenges.count(),
                'active_challenges': challenges.filter(is_active=True).count(),
                'challenge_difficulty': {},
                'challenge_types': {},
                'completion_rates': {}
            }
            
            # Group by difficulty
            for challenge in challenges:
                difficulty = challenge.difficulty_level
                if difficulty not in stats['challenge_difficulty']:
                    stats['challenge_difficulty'][difficulty] = 0
                stats['challenge_difficulty'][difficulty] += 1
                
                # Group by location type
                location_type = challenge.location_type
                if location_type not in stats['challenge_types']:
                    stats['challenge_types'][location_type] = 0
                stats['challenge_types'][location_type] += 1
                
                # Calculate completion rate
                total_attempts = ChallengeAttempt.objects.filter(challenge=challenge).count()
                successful_attempts = ChallengeAttempt.objects.filter(
                    challenge=challenge, 
                    verification_status='verified'
                ).count()
                
                completion_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0
                stats['completion_rates'][challenge.id] = {
                    'challenge_name': challenge.title,
                    'total_attempts': total_attempts,
                    'successful_attempts': successful_attempts,
                    'completion_rate': round(completion_rate, 2)
                }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error fetching challenge statistics: {str(e)}")
            return Response(
                {'error': 'Failed to fetch statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminFraudDetectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin ViewSet for fraud detection management
    Allows viewing and managing flagged submissions
    """
    queryset = FraudDetection.objects.all()
    serializer_class = FraudDetectionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter fraud detection records"""
        queryset = super().get_queryset()
        
        risk_level = self.request.query_params.get('risk_level', None)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        requires_review = self.request.query_params.get('requires_review', None)
        if requires_review is not None:
            queryset = queryset.filter(requires_manual_review=requires_review.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def review_submission(self, request, pk=None):
        """Manual review of flagged submission"""
        try:
            fraud_detection = self.get_object()
            action = request.data.get('action')  # 'approve' or 'reject'
            notes = request.data.get('notes', '')
            
            if action not in ['approve', 'reject']:
                return Response(
                    {'error': 'Action must be "approve" or "reject"'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update the associated attempt
            attempt = fraud_detection.attempt
            if action == 'approve':
                attempt.verification_status = 'verified'
                attempt.verification_notes = f'Manually approved: {notes}'
                attempt.verified_at = timezone.now()
                
                # Award completion rewards
                self._award_completion_rewards(attempt)
            else:
                attempt.verification_status = 'failed'
                attempt.verification_notes = f'Manually rejected: {notes}'
            
            attempt.save()
            
            # Update fraud detection record
            fraud_detection.requires_manual_review = False
            fraud_detection.manual_review_notes = notes
            fraud_detection.reviewed_by = request.user
            fraud_detection.reviewed_at = timezone.now()
            fraud_detection.save()
            
            return Response({
                'status': 'success',
                'action': action,
                'attempt_status': attempt.verification_status
            })
            
        except Exception as e:
            logger.error(f"Error reviewing submission: {str(e)}")
            return Response(
                {'error': 'Failed to review submission'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _award_completion_rewards(self, attempt):
        """Award completion rewards for manually approved submissions"""
        try:
            points_awarded = attempt.challenge.points_reward
            logger.info(f"Awarded {points_awarded} points to user {attempt.user.id} for manually approved challenge {attempt.challenge.id}")
        except Exception as e:
            logger.error(f"Error awarding completion rewards: {str(e)}")
