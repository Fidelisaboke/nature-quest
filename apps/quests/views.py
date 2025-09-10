import logging
import time

from django.core import paginator
from django.views.generic.list import Paginator
from haversine import haversine
from django.db.models import F, Case, CharField, Value, When
from django.http import Http404
from rest_framework import viewsets, status, permissions, generics, filters
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quest, QuestLog, Challenge, ChallengeLog, TriviaQuestion
from .serializers import QuestSerializer, QuestLogSerializer, ChallengeSerializer, ChallengeLogSerializer

# Create your views here.
class QuestViewSet(viewsets.ModelViewSet):
    queryset = Quest.objects.all()
    serializer_class = QuestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'quest_type': ['exact', 'in'],
        'difficulty': ['exact', 'in'],
        'duration_minutes': ['exact', 'lt', 'gt'],
        'is_active': ['exact'],
    }
    search_fields = ['title', 'description']
    ordering_fields = ['difficulty', 'duration_minutes', 'experience_reward']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter quests based on user's progress with improved performance and error handling.
        """
        logger = logging.getLogger(__name__)
        queryset = super().get_queryset()

        # Early return if user not authenticated
        if not self.request.user.is_authenticated:
            logger.debug("User not authenticated, returning base queryset")
            return queryset

        # Get and validate status filter
        status_filter = self.request.query_params.get('user_status')
        if not status_filter:
            logger.debug("No status filter provided, returning base queryset")
            return queryset

        # Validate status_filter against allowed values
        allowed_statuses = ['in_progress', 'completed', 'not_started', 'all_active']
        if status_filter not in allowed_statuses:
            logger.warning(f"Invalid status_filter: {status_filter}. Allowed: {allowed_statuses}")
            raise ValidationError(f"Invalid status filter. Allowed values: {', '.join(allowed_statuses)}")

        try:
            # Build status mapping from model choices
            status_choices = dict(QuestLog.STATUS_CHOICES)
            status_mapping = {
                'in_progress': ['in_progress'],
                'completed': ['completed'],
                'not_started': ['not_started'],
                'all_active': ['in_progress', 'not_started']
            }

            statuses = status_mapping.get(status_filter, [])
            logger.debug(f"Filtering by statuses: {statuses}")

            if statuses:
                # Optimize query based on filter type
                if status_filter == 'not_started':
                    # Use subquery for better performance with large datasets
                    started_quest_ids = QuestLog.objects.filter(
                        user=self.request.user,
                        status__in=statuses
                    ).values('quest_id')

                    queryset = queryset.exclude(id__in=started_quest_ids)
                    logger.debug("Applied exclude filter for not_started quests")
                else:
                    # For other filters, use direct filtering
                    quest_ids = QuestLog.objects.filter(
                        user=self.request.user,
                        status__in=statuses
                    ).values_list('quest_id', flat=True)

                    queryset = queryset.filter(id__in=quest_ids)
                    logger.debug(f"Applied include filter for {len(quest_ids)} quests")

            # Add user status annotation with correct field reference
            queryset = queryset.annotate(
                user_status=Case(
                    When(quest_logs__user=self.request.user, then=F('quest_logs__status')),
                    default=Value('not_started'),
                    output_field=CharField()
                )
            ).prefetch_related('quest_logs')  # Prevent N+1 queries

            logger.debug(f"Annotated queryset with user_status and prefetch_related")

        except Exception as e:
            logger.error(f"Error in get_queryset: {e}", exc_info=True)
            # Return base queryset on error to prevent breaking the API
            return super().get_queryset()

        return queryset
    
    @action(detail=True, methods=['get'])
    def find_quest_nearby(self, request, pk=None):
        """Find quests within a radius of the user's location"""
        try:
            latitude = float(request.query_params.get('latitude'))
            longitude = float(request.query_params.get('longitude'))
            radius = float(request.query_params.get('radius', 10))
        
        except (TypeError, ValueError):
            return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)

        # Get all quests with locations
        quests = Quest.objects.filter(location__isnull=False).select_related('location').all()

        nearby_quests = []
        for quest in quests:
            try:
                # Calculate distance using haversine
                distance = haversine((latitude, longitude), (quest.location.latitude, quest.location.longitude))
                if distance <= radius:
                    serializer = QuestSerializer(quest)
                    nearby_quests.append({
                        **serializer.data,
                        'distance_km': round(distance, 2)
                    })
            except (AttributeError, TypeError) as e:
                logger.error(f"Error calculating distance for quest {quest.id}: {str(e)}", exc_info=True)
                continue

        # Sort quests by distance
        nearby_quests.sort(key=lambda x: x['distance_km'])

        # Add pagination
        paginator = Paginator(nearby_quests, 10)
        page_number = request.query_params.get('page', 1)
        page = paginator.get_page(page_number)

        return Response({
            'quests': page,
            'count': paginator.count,
            'pages': paginator.num_pages
        })

    @action(detail=True, methods=['post'])
    def start_quest(self, request, pk=None):
        """Start a quest for the current user"""
        quest = Quest.objects.get(pk=pk)
        user = request.user

        # Check if user already has progress for this quest
        progress, created = QuestLog.objects.get_or_create(user=user, quest=quest, defaults={'status': 'in_progress', 'progress': 0})

        if not created and progress.status == 'abandoned':
            progress.status = 'in_progress'
            progress.save()

        serializer = QuestLogSerializer(progress)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
