from rest_framework import serializers
from .models import Quest, Location, Challenge, QuestLog, ChallengeLog, TriviaQuestion

class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = [
            'id', 'title', 'quests', 'description', 'is_mandatory', 'experience_reward', 'order'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'latitude', 'longitude', 'address', 'source', 'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class QuestSerializer(serializers.ModelSerializer):
    challenge = ChallengeSerializer(many=True, read_only=True)
    location = LocationSerializer()
    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'description', 'quest_type', 'difficulty', 'duration_minutes', 'experience_reward', 'requirements', 'location', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class QuestLogSerializer(serializers.ModelSerializer):
    quest = serializers.PrimaryKeyRelatedField(queryset=Quest.objects.all(), write_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = QuestLog
        fields = ['id', 'user', 'quest', 'status', 'status_display', 'start_time', 'end_time', 'experience_earned', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'quest', 'status_display', 'experience_earned', 'start_time', 'end_time']

    def validate(self, attrs):
        if self.instance and attrs.get('status') == 'completed' and not self.quest.is_active:
            raise serializers.ValidationError("Cannot complete an inactive quest")
        return attrs

class ChallengeLogSerializer(serializers.ModelSerializer):
    challenge = serializers.PrimaryKeyRelatedField(queryset=Challenge.objects.all(), write_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    
    class Meta:
        model = ChallengeLog
        fields = ['id', 'user', 'challenge', 'completed_at', 'experience_earned']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'challenge', 'experience_earned']
    
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