import logging

from django.core.paginator import Paginator
from django.db import models
from django.db.models import CharField, Value
from django.core.exceptions import FieldError
from django.db.utils import DatabaseError
from rest_framework import viewsets, status, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.shortcuts import get_object_or_404
from haversine import haversine

from .models import (
    Quest, QuestLog, Challenge, ChallengeLog, Location,
    LocationCheckpoint, UserProgressCheckpoint, Badge, UserBadge,
    CarbonImpact, LeaderboardEntry
)
from .serializers import (
    QuestSerializer, QuestLogSerializer, ChallengeSerializer, ChallengeLogSerializer,
    BadgeSerializer, UserBadgeSerializer, LeaderboardEntrySerializer,
    EnhancedQuestSerializer
)

logger = logging.getLogger(__name__)


class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_mandatory']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']

    def get_queryset(self):
        return super().get_queryset().prefetch_related('quests')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['include_quests'] = self.request.query_params.get('include_quests', 'false').lower() == 'true'
        return context

    @action(detail=True, methods=['post'])
    def start_challenge(self, request, pk=None):
        """Start a challenge for the current user"""
        try:
            challenge = Challenge.objects.get(pk=pk)
            user = request.user

            # Get or create challenge log
            progress, created = ChallengeLog.objects.get_or_create(
                user=user,
                challenge=challenge,
                defaults={'experience_earned': 0}
            )

            serializer = ChallengeLogSerializer(progress)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )

        except Challenge.DoesNotExist:
            logger.warning(f'Attempted to start non-existent challenge with id: {pk}')
            return Response(
                {'error': 'Challenge not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def complete_challenge(self, request, pk=None):
        """Complete a challenge for the current user"""
        try:
            challenge = Challenge.objects.get(pk=pk)
            user = request.user

            # Get or create challenge log
            progress, created = ChallengeLog.objects.get_or_create(
                user=user,
                challenge=challenge,
                defaults={'experience_earned': challenge.experience_reward}
            )

            if not created:
                progress.experience_earned = challenge.experience_reward
                progress.save()

            serializer = ChallengeLogSerializer(progress)
            return Response(serializer.data)

        except Challenge.DoesNotExist:
            logger.warning(f'Attempted to complete non-existent challenge with id: {pk}')
            return Response(
                {'error': 'Challenge not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def abandon_challenge(self, request, pk=None):
        """Abandon a challenge for the current user"""
        try:
            challenge = Challenge.objects.get(pk=pk)
            user = request.user

            # Delete challenge log if exists (abandon = remove progress)
            ChallengeLog.objects.filter(user=user, challenge=challenge).delete()

            return Response({'message': 'Challenge abandoned successfully'})

        except Challenge.DoesNotExist:
            logger.warning(f'Attempted to abandon non-existent challenge with id: {pk}')
            return Response(
                {'error': 'Challenge not found'},
                status=status.HTTP_404_NOT_FOUND
            )

# Create your views here.
class QuestViewSet(viewsets.ModelViewSet):
    queryset = Quest.objects.all()
    serializer_class = QuestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'quest_type': ['exact', 'in'],
        'difficulty': ['exact', 'in'],
        'duration_minutes': ['exact', 'lt', 'gt'],
        'is_active': ['exact'],
    }
    search_fields = ['title', 'description']
    ordering_fields = ['difficulty', 'duration_minutes', 'experience_reward']
    ordering = ['-created_at']

    def _validate_status_filter(self, status_filter: str) -> None:
        """Validate the status filter parameter against allowed values."""
        allowed_statuses = ['in_progress', 'completed', 'not_started', 'all_active']
        if status_filter not in allowed_statuses:
            logger.warning(
                f"Invalid status_filter: {status_filter}. Allowed: {allowed_statuses}"
            )
            raise ValidationError(
                f"Invalid status filter. Allowed values: {', '.join(allowed_statuses)}"
            )

    def _get_status_mapping(self) -> dict:
        """Return mapping of filter keys to status values."""
        return {
            'in_progress': ['in_progress'],
            'completed': ['completed'],
            'not_started': ['not_started'],
            'all_active': ['in_progress', 'not_started']
        }

    def _filter_by_status(self, queryset, status_filter: str, statuses: list):
        """Apply status-based filtering to the queryset."""
        if status_filter == 'not_started':
            started_quest_ids = QuestLog.objects.filter(
                user=self.request.user
            ).values('quest_id')
            queryset = queryset.exclude(id__in=started_quest_ids)
            logger.debug("Applied exclude filter for not_started quests")
        else:
            quest_ids = QuestLog.objects.filter(
                user=self.request.user,
                status__in=statuses
            ).values_list('quest_id', flat=True)
            queryset = queryset.filter(id__in=quest_ids)
            logger.debug(f"Applied include filter for {len(list(quest_ids))} quests")
        return queryset

    def _annotate_user_status(self, queryset):
        """Annotate queryset with user's quest status using subquery."""
        from django.db.models import OuterRef, Subquery
        from django.db.models.functions import Coalesce

        latest_quest_log = QuestLog.objects.filter(
            quest=OuterRef('pk'),
            user=self.request.user
        ).order_by('-created_at').values('status')[:1]

        return queryset.annotate(
            user_status=Coalesce(
                Subquery(latest_quest_log, output_field=CharField()),
                Value('not_started'),
                output_field=CharField()
            )
        )

    def get_queryset(self):
        """
        Filter quests based on user's progress with improved performance and error handling.
        """
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            logger.debug("User not authenticated, returning base queryset")
            return queryset

        status_filter = self.request.query_params.get('user_status')
        if not status_filter:
            logger.debug("No status filter provided, returning base queryset")
            return queryset

        try:
            self._validate_status_filter(status_filter)
            status_mapping = self._get_status_mapping()
            statuses = status_mapping.get(status_filter, [])
            logger.debug(f"Filtering by statuses: {statuses}")

            if statuses:
                queryset = self._filter_by_status(queryset, status_filter, statuses)

            queryset = self._annotate_user_status(queryset)
            logger.debug("Annotated queryset with user_status using Subquery")

        except (ValueError, FieldError, DatabaseError) as e:
            logger.error(f"Error in get_queryset: {e}", exc_info=True)
            return super().get_queryset()

        return queryset
    def _validate_coordinates(self, latitude: float, longitude: float, radius: float) -> None:
        """Validate coordinate and radius parameters."""
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if radius <= 0:
            raise ValueError("Radius must be positive")

    def _calculate_quest_distance(self, quest, user_lat: float, user_lng: float, radius: float):
        """Calculate distance to a quest if within radius."""
        try:
            distance = haversine(
                (user_lat, user_lng),
                (quest.location.latitude, quest.location.longitude)
            )
            if distance <= radius:
                serializer = QuestSerializer(quest)
                return {
                    **serializer.data,
                    'distance_km': round(distance, 2)
                }
        except (AttributeError, TypeError) as e:
            logger.error(
                f"Error calculating distance for quest {quest.id}: {str(e)}",
                exc_info=True
            )
        return None

    def _get_nearby_quests(self, quests, latitude: float, longitude: float, radius: float):
        """Filter and calculate distances for nearby quests."""
        nearby_quests = []
        for quest in quests:
            quest_data = self._calculate_quest_distance(quest, latitude, longitude, radius)
            if quest_data:
                nearby_quests.append(quest_data)
        nearby_quests.sort(key=lambda x: x['distance_km'])
        return nearby_quests

    def _paginate_nearby_quests(self, nearby_quests, page_number: int):
        """Paginate the nearby quests list."""
        paginator = Paginator(nearby_quests, 10)
        page = paginator.get_page(page_number)
        return {
            'quests': page.object_list,
            'page': page.number,
            'total_pages': paginator.num_pages,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
            'total_count': paginator.count
        }

    @action(detail=False, methods=['get'])
    def find_quest_nearby(self, request):
        """Find quests near a given location with pagination."""
        try:
            latitude = float(request.query_params.get('latitude'))
            longitude = float(request.query_params.get('longitude'))
            radius = float(request.query_params.get('radius', 10))
            self._validate_coordinates(latitude, longitude, radius)
        except (TypeError, ValueError):
            return Response(
                {'error': 'Invalid parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )

        quests = Quest.objects.filter(
            location__isnull=False
        ).select_related('location').all()

        nearby_quests = self._get_nearby_quests(quests, latitude, longitude, radius)
        page_number = request.query_params.get('page', 1)
        result = self._paginate_nearby_quests(nearby_quests, page_number)

        return Response(result)

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

    @action(detail=True, methods=['post'])
    def complete_quest(self, request, pk=None):
        """Complete a quest for the current user"""
        try:
            quest = Quest.objects.get(pk=pk)
            user = request.user

            # Get or create quest log
            progress, created = QuestLog.objects.get_or_create(
                user=user, 
                quest=quest,
                defaults={'status': 'completed', 'progress': 100}
            )

            if not created:
                progress.status = 'completed'
                progress.progress = 100
                progress.save()

            serializer = QuestLogSerializer(progress)
            return Response(serializer.data)
            
        except Quest.DoesNotExist:
            logger.warning(f'Attempted to complete non-existent quest with id: {pk}')
            return Response(
                {'error': 'Quest not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def abandon_quest(self, request, pk=None):
        """Abandon a quest for the current user"""
        try:
            quest = Quest.objects.get(pk=pk)
            user = request.user

            # Get or create quest log
            progress, created = QuestLog.objects.get_or_create(
                user=user, 
                quest=quest,
                defaults={'status': 'abandoned', 'progress': 0}
            )

            if not created:
                progress.status = 'abandoned'
                progress.save()

            serializer = QuestLogSerializer(progress)
            return Response(serializer.data)
            
        except Quest.DoesNotExist:
            logger.warning(f'Attempted to abandon non-existent quest with id: {pk}')
            return Response(
                {'error': 'Quest not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def _parse_discovery_params(self, request) -> tuple:
        """Parse and validate discovery endpoint parameters."""
        try:
            lat = float(request.query_params.get('latitude'))
            lng = float(request.query_params.get('longitude'))
            min_radius = float(request.query_params.get('min_radius', 1))
            max_radius = float(request.query_params.get('max_radius', 50))
            target_count = int(request.query_params.get('target_count', 10))
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid parameters: {e}")

        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise ValueError("Invalid coordinates")

        return lat, lng, min_radius, max_radius, target_count

    def _search_nearby_quests(
        self, user_point, min_radius: float, max_radius: float, target_count: int
    ):
        """Execute smart radius search for nearby quests."""
        radius = min_radius
        quests = []

        while radius <= max_radius and len(quests) < target_count:
            nearby_locations = Location.objects.filter(
                point__dwithin=(user_point, D(km=radius))
            ).annotate(
                distance=Distance('point', user_point)
            )

            quests = Quest.objects.filter(
                location__in=nearby_locations,
                is_active=True
            ).select_related('location').prefetch_related('checkpoints').annotate(
                distance_km=Distance('location__point', user_point) / 1000
            ).order_by('distance_km')[:target_count]

            if len(quests) < target_count:
                radius *= 1.5

        return quests, radius

    @action(detail=False, methods=['get'])
    def discover(self, request):
        """
        Smart radius quest discovery based on user location.
        Adapts radius based on quest density.
        """
        try:
            lat, lng, min_radius, max_radius, target_count = self._parse_discovery_params(request)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_point = Point(lng, lat, srid=4326)
        quests, radius = self._search_nearby_quests(
            user_point, min_radius, max_radius, target_count
        )

        serializer = EnhancedQuestSerializer(
            quests, many=True, context={'request': request}
        )
        return Response({
            'quests': serializer.data,
            'search_radius_km': round(radius, 2),
            'total_found': len(quests)
        })

    def _parse_location_params(self, request) -> tuple:
        """Parse and validate location validation parameters."""
        try:
            user_lat = float(request.data.get('latitude'))
            user_lng = float(request.data.get('longitude'))
        except (TypeError, ValueError) as e:
            raise ValueError("Invalid coordinates. latitude and longitude are required.") from e
        return user_lat, user_lng

    def _calculate_validation_distance(
        self, user_point, quest, checkpoint_id: str = None
    ) -> tuple:
        """Calculate distance and validation status for location or checkpoint."""
        if checkpoint_id:
            checkpoint = get_object_or_404(
                LocationCheckpoint, id=checkpoint_id, quest=quest
            )
            distance = user_point.distance(checkpoint.point) * 100000
            is_valid = distance <= checkpoint.radius_meters
            required_radius = checkpoint.radius_meters
        else:
            distance = user_point.distance(quest.location.point) * 100000
            is_valid = distance <= 100
            required_radius = 100

        return distance, is_valid, required_radius

    def _record_checkpoint_visit(
        self, user, quest, checkpoint_id: str, user_lat: float, user_lng: float
    ) -> bool:
        """Record user visit to a checkpoint and check completion status."""
        quest_log, _ = QuestLog.objects.get_or_create(
            user=user,
            quest=quest,
            defaults={'status': 'in_progress'}
        )

        if checkpoint_id:
            checkpoint = get_object_or_404(
                LocationCheckpoint, id=checkpoint_id, quest=quest
            )
            UserProgressCheckpoint.objects.get_or_create(
                quest_log=quest_log,
                checkpoint=checkpoint,
                defaults={'latitude': user_lat, 'longitude': user_lng}
            )

        required_checkpoints = quest.checkpoints.filter(is_required=True)
        visited_checkpoints = UserProgressCheckpoint.objects.filter(
            quest_log=quest_log,
            checkpoint__in=required_checkpoints
        )

        return visited_checkpoints.count() >= required_checkpoints.count()

    @action(detail=True, methods=['post'])
    def validate_location(self, request, pk=None):
        """Validate user is at quest location or checkpoint."""
        try:
            user_lat, user_lng = self._parse_location_params(request)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        quest = self.get_object()
        checkpoint_id = request.data.get('checkpoint_id')
        user_point = Point(user_lng, user_lat, srid=4326)

        distance, is_valid, required_radius = self._calculate_validation_distance(
            user_point, quest, checkpoint_id
        )

        if not is_valid:
            return Response({
                'valid': False,
                'distance_meters': round(distance, 2),
                'required_radius_meters': required_radius
            }, status=status.HTTP_400_BAD_REQUEST)

        all_visited = self._record_checkpoint_visit(
            request.user, quest, checkpoint_id, user_lat, user_lng
        )

        return Response({
            'valid': True,
            'distance_meters': round(distance, 2),
            'checkpoint_completed': checkpoint_id is not None,
            'all_required_checkpoints_visited': all_visited
        })


class GamificationViewSet(viewsets.ViewSet):
    """ViewSet for gamification features including badges, leaderboards, and user stats."""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get user's complete gamification profile."""
        user = request.user
        profile = user.profile

        # Calculate category progress
        category_progress = QuestLog.objects.filter(
            user=user,
            status='completed'
        ).values('quest__quest_type').annotate(
            count=models.Count('id'),
            total_xp=models.Sum('quest__experience_reward')
        )

        # Get recent badges
        recent_badges = UserBadge.objects.filter(
            user=user,
            is_complete=True
        ).select_related('badge').order_by('-earned_at')[:5]

        # Calculate environmental impact totals
        environmental_totals = CarbonImpact.objects.filter(
            user=user
        ).aggregate(
            total_carbon_saved=models.Sum('carbon_saved_kg'),
            total_trees_equivalent=models.Sum('trees_equivalent'),
            total_distance=models.Sum('distance_km')
        )

        # Calculate next level XP (exponential curve)
        next_level_xp = int(100 * (profile.level ** 1.5))

        return Response({
            'level': profile.level,
            'total_xp': profile.points,
            'next_level_xp': next_level_xp,
            'xp_to_next_level': next_level_xp - profile.points,
            'category_progress': list(category_progress),
            'recent_badges': UserBadgeSerializer(recent_badges, many=True).data,
            'environmental_impact': environmental_totals,
            'quests_completed': QuestLog.objects.filter(user=user, status='completed').count(),
            'challenges_completed': ChallengeLog.objects.filter(user=user).count()
        })

    @action(detail=False, methods=['get'])
    def badges(self, request):
        """Get all badges with user's progress."""
        category = request.query_params.get('category')
        tier = request.query_params.get('tier')

        badges = Badge.objects.all()
        if category:
            badges = badges.filter(category=category)
        if tier:
            badges = badges.filter(tier=tier)

        # Annotate with user's progress
        user_badges = {
            ub.badge_id: ub for ub in UserBadge.objects.filter(user=request.user)
        }

        result = []
        for badge in badges:
            user_badge = user_badges.get(badge.id)
            result.append({
                'badge': BadgeSerializer(badge).data,
                'progress': user_badge.progress if user_badge else 0,
                'is_complete': user_badge.is_complete if user_badge else False,
                'earned_at': user_badge.earned_at if user_badge else None
            })

        return Response(result)

    @action(detail=False, methods=['get'])
    def leaderboards(self, request):
        """Get leaderboard data."""
        leaderboard_type = request.query_params.get('type', 'global_xp')
        region = request.query_params.get('region', '')
        quest_type = request.query_params.get('quest_type')
        period = request.query_params.get('period', 'all_time')

        entries = LeaderboardEntry.objects.filter(
            leaderboard_type=leaderboard_type,
            region=region,
            period=period
        ).select_related('user', 'user__profile').order_by('rank')[:100]

        if quest_type:
            entries = entries.filter(quest_type=quest_type)

        # Include user's own rank if not in top 100
        user_entry = LeaderboardEntry.objects.filter(
            user=request.user,
            leaderboard_type=leaderboard_type,
            region=region,
            period=period
        ).first()

        serializer = LeaderboardEntrySerializer(entries, many=True)

        return Response({
            'leaderboard': serializer.data,
            'user_rank': {
                'rank': user_entry.rank,
                'score': user_entry.score
            } if user_entry else None,
            'total_participants': LeaderboardEntry.objects.filter(
                leaderboard_type=leaderboard_type,
                region=region,
                period=period
            ).count()
        })

    @action(detail=False, methods=['get'])
    def environmental_impact(self, request):
        """Get detailed environmental impact data."""
        user = request.user

        # Get impact by quest type
        impact_by_type = CarbonImpact.objects.filter(
            user=user
        ).values('activity_type').annotate(
            total_carbon_saved=models.Sum('carbon_saved_kg'),
            total_trees=models.Sum('trees_equivalent'),
            total_distance=models.Sum('distance_km'),
            quest_count=models.Count('id')
        )

        # Get monthly trends (last 6 months)
        from django.utils import timezone
        from datetime import timedelta

        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_trends = CarbonImpact.objects.filter(
            user=user,
            calculated_at__gte=six_months_ago
        ).annotate(
            month=models.functions.TruncMonth('calculated_at')
        ).values('month').annotate(
            carbon_saved=models.Sum('carbon_saved_kg'),
            quest_count=models.Count('id')
        ).order_by('month')

        return Response({
            'impact_by_type': list(impact_by_type),
            'monthly_trends': list(monthly_trends),
            'total_impact': CarbonImpact.objects.filter(user=user).aggregate(
                carbon_saved_kg=models.Sum('carbon_saved_kg'),
                trees_equivalent=models.Sum('trees_equivalent'),
                distance_km=models.Sum('distance_km')
            )
        })
