from rest_framework import serializers
from .models import Quest, Location, Challenge, QuestLog, ChallengeLog, TriviaQuestion

class ChallengeSerializer(serializers.ModelSerializer):
    quests_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Challenge
        fields = [
            'id', 'title', 'quests', 'quests_display', 'description', 
            'is_mandatory', 'experience_reward', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'quests': {'write_only': True}  # Hide raw quests in output
        }
    
    def get_quests_display(self, obj):
        # Only include quests display if requested via context
        if not self.context.get('include_quests', False):
            return None
            
        # Get the prefetched quests if available
        quests = getattr(obj, '_prefetched_objects_cache', {}).get('quests', None)
        if quests is None:
            # Fallback to querying if not prefetched
            quests = obj.quests.all()
        
        # Return a list of quest titles with their IDs
        return [
            {'id': q.id, 'title': q.title, 'is_active': q.is_active}
            for q in quests
        ]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'latitude', 'longitude', 'address', 'source', 'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class QuestSerializer(serializers.ModelSerializer):
    challenge = ChallengeSerializer(many=True, read_only=True)
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        write_only=True,
        source='location'
    )
    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'description', 'quest_type', 'difficulty', 'duration_minutes',
            'experience_reward', 'requirements', 'challenge', 'location', 'location_id', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
class QuestLogSerializer(serializers.ModelSerializer):
    quest = serializers.PrimaryKeyRelatedField(queryset=Quest.objects.all(), write_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = QuestLog
        fields = '__all__'
        read_only_fields = ('id', 'status_display')

    def validate(self, attrs):
        status = attrs.get('status') or getattr(self.instance, 'status', None)
        quest = attrs.get('quest') or getattr(self.instance, 'quest', None)
        if status == 'completed' and quest and not getattr(quest, 'is_active', True):
            raise serializers.ValidationError("Cannot complete an inactive quest")
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
            raise serializers.ValidationError("Authenticated user required.")
        validated_data['user'] = request.user
        return super().create(validated_data)

class ChallengeLogSerializer(serializers.ModelSerializer):
    challenge = serializers.PrimaryKeyRelatedField(queryset=Challenge.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = ChallengeLog
        fields = ['id', 'user', 'challenge', 'completed_at', 'experience_earned']
        read_only_fields = ['id', 'created_at', 'updated_at', 'experience_earned']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class TriviaQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriviaQuestion
        fields = [
            'id', 'question_text', 'choices', 'correct_answer', 'tags'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {'correct_answer': {'write_only': True}}


class LocationCheckpointSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = LocationCheckpoint
        fields = ['id', 'name', 'latitude', 'longitude', 'radius_meters', 'order', 'is_required']

    def get_latitude(self, obj):
        return obj.point.y if obj.point else None

    def get_longitude(self, obj):
        return obj.point.x if obj.point else None


class UserProgressCheckpointSerializer(serializers.ModelSerializer):
    checkpoint = LocationCheckpointSerializer(read_only=True)

    class Meta:
        model = UserProgressCheckpoint
        fields = ['checkpoint', 'visited_at', 'latitude', 'longitude']


class BadgeSerializer(serializers.ModelSerializer):
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'icon', 'tier', 'tier_display',
            'category', 'category_display', 'requirement_type',
            'requirement_value', 'quest_type_filter'
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserBadge
        fields = ['badge', 'progress', 'progress_percentage', 'is_complete', 'earned_at']

    def get_progress_percentage(self, obj):
        if obj.badge.requirement_value > 0:
            return min(100, int((obj.progress / obj.badge.requirement_value) * 100))
        return 0


class CarbonImpactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarbonImpact
        fields = [
            'activity_type', 'distance_km', 'carbon_saved_kg',
            'trees_equivalent', 'calculated_at'
        ]


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaderboardEntry
        fields = ['rank', 'username', 'display_name', 'score', 'updated_at']

    def get_display_name(self, obj):
        # Use user's profile display name or username
        return getattr(obj.user, 'profile', None) and obj.user.profile.display_name or obj.user.username


# Enhanced QuestSerializer with checkpoints
class EnhancedQuestSerializer(QuestSerializer):
    checkpoints = LocationCheckpointSerializer(many=True, read_only=True)
    user_progress = serializers.SerializerMethodField()

    class Meta(QuestSerializer.Meta):
        fields = QuestSerializer.Meta.fields + ['checkpoints', 'user_progress']

    def get_user_progress(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        try:
            quest_log = QuestLog.objects.get(user=request.user, quest=obj)
            return {
                'status': quest_log.status,
                'progress': quest_log.progress,
                'checkpoints_visited': UserProgressCheckpoint.objects.filter(
                    quest_log=quest_log
                ).count(),
                'total_checkpoints': obj.checkpoints.filter(is_required=True).count()
            }
        except QuestLog.DoesNotExist:
            return None