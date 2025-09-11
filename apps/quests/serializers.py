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