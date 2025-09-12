import logging
import time
from django.core.paginator import Paginator
from haversine import haversine
from django.db.models import F, Case, CharField, Value, When
from django.core.exceptions import FieldError
from django.db.utils import DatabaseError
from django.http import Http404
from rest_framework import viewsets, status, permissions
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quest, QuestLog, Challenge, ChallengeLog, TriviaQuestion
from .serializers import QuestSerializer, QuestLogSerializer, ChallengeSerializer, ChallengeLogSerializer


class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_mandatory']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']

    def get_queryset(self):
        return super().get_queryset().prefetch_related('quests')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['include_quests'] = self.request.query_params.get('include_quests', 'false').lower() == 'true'
        return context

logger = logging.getLogger(__name__)

# Create your views here.
class QuestViewSet(viewsets.ModelViewSet):
    queryset = Quest.objects.all()
    serializer_class = QuestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, filters.OrderingFilter]
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
                    # Find quests that the user has NOT started (no QuestLog entry)
                    started_quest_ids = QuestLog.objects.filter(
                        user=self.request.user
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

            from django.db.models import OuterRef, Subquery, CharField
            from django.db.models.functions import Coalesce

            # Get the latest quest log for each quest for the current user
            latest_quest_log = QuestLog.objects.filter(
                quest=OuterRef('pk'),
                user=self.request.user
            ).order_by('-created_at').values('status')[:1]

            # Annotate with the user's status using a subquery
            queryset = queryset.annotate(
                user_status=Coalesce(
                    Subquery(latest_quest_log, output_field=CharField()),
                    Value('not_started'),
                    output_field=CharField()
                )
            )

            logger.debug("Annotated queryset with user_status using Subquery")

        except (ValueError, FieldError, DatabaseError) as e:
            logger.error(f"Error in get_queryset: {e}", exc_info=True)
            return super().get_queryset()
        return queryset
    @action(detail=False, methods=['get'])
    def find_quest_nearby(self, request):
        try:
            latitude = float(request.query_params.get('latitude'))
            longitude = float(request.query_params.get('longitude'))
            radius = float(request.query_params.get('radius', 10))
            
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            if radius <= 0:
                raise ValueError("Radius must be positive")
        
        except (TypeError, ValueError):
            return Response({'error': 'Invalid parameters'}, status=status.HTTP_400_BAD_REQUEST)
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

        # Serialize the quests in the current page
        serialized_quests = page.object_list

        return Response({
            'quests': serialized_quests,
            'page': page.number,
            'total_pages': paginator.num_pages,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
            'total_count': paginator.count
        })

    @action(detail=True, methods=['post'])
    def start_quest(self, request, pk=None):
        """Start a quest for the current user"""
        try:
            quest = Quest.objects.get(pk=pk)
            user = request.user

            # Check if user already has progress for this quest
            progress, created = QuestLog.objects.get_or_create(
                user=user, 
                quest=quest, 
                defaults={'status': 'in_progress', 'progress': 0}
            )

            if not created and progress.status == 'abandoned':
                progress.status = 'in_progress'
                progress.save()

            serializer = QuestLogSerializer(progress)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
            
        except Quest.DoesNotExist:
            logger.warning(f'Attempted to start non-existent quest with id: {pk}')
            return Response(
                {'error': 'Quest not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
