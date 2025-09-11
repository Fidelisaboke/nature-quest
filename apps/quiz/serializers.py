from rest_framework import serializers
from .models import (
    Quiz,
    Question,
    QuizAttempt,
    QuestionResponse,
    QuestionBank,
    QuizMetrics,
)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "question_type", "question_text", "options", "points", "order"]
        # Don't expose correct answers or explanation until after submission


class QuestionWithAnswersSerializer(serializers.ModelSerializer):
    """Serializer that includes answers and explanations (for results)"""

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "question_text",
            "options",
            "correct_answers",
            "explanation",
            "points",
            "order",
        ]


class QuizSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "username",
            "challenge_id",
            "difficulty",
            "tech_stack",
            "total_questions",
            "created_at",
            "completed_at",
            "score",
            "passed",
            "is_completed",
        ]
        read_only_fields = ["score", "passed", "completed_at"]


class QuizDetailSerializer(serializers.ModelSerializer):
    """Detailed quiz serializer with questions (for single quiz view)"""

    questions = QuestionSerializer(many=True, read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "username",
            "challenge_id",
            "difficulty",
            "tech_stack",
            "total_questions",
            "created_at",
            "completed_at",
            "score",
            "passed",
            "is_completed",
            "questions",
        ]
        read_only_fields = ["score", "passed", "completed_at"]


class QuizResultSerializer(serializers.ModelSerializer):
    """Detailed quiz results with correct answers"""

    questions = QuestionWithAnswersSerializer(many=True, read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "username",
            "challenge_id",
            "difficulty",
            "tech_stack",
            "total_questions",
            "created_at",
            "completed_at",
            "score",
            "passed",
            "questions",
        ]


class QuestionResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(
        source="question.question_text", read_only=True
    )

    class Meta:
        model = QuestionResponse
        fields = [
            "question",
            "question_text",
            "selected_answers",
            "is_correct",
            "points_earned",
            "answered_at",
        ]
        read_only_fields = ["is_correct", "points_earned"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    responses = QuestionResponseSerializer(many=True, read_only=True)
    quiz_details = QuizSerializer(source="quiz", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "quiz_details",
            "started_at",
            "submitted_at",
            "total_score",
            "is_submitted",
            "responses",
        ]
        read_only_fields = ["total_score", "submitted_at"]


class QuizSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting quiz answers"""

    responses = serializers.ListField(
        child=serializers.DictField(child=serializers.JSONField()),
        help_text="List of {question_id: [selected_indices]} pairs",
    )

    def validate_responses(self, value):
        """Validate that all required questions are answered"""
        if not value:
            raise serializers.ValidationError("At least one response is required")

        for response in value:
            if "question_id" not in response or "selected_answers" not in response:
                raise serializers.ValidationError(
                    "Each response must have 'question_id' and 'selected_answers'"
                )

        return value


class QuestionBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionBank
        fields = [
            "id",
            "tech_stack",
            "difficulty",
            "question_type",
            "question_text",
            "options",
            "correct_answers",
            "explanation",
            "times_used",
            "quality_score",
            "created_at",
        ]


class QuizGenerationRequestSerializer(serializers.Serializer):
    """Serializer for requesting quiz generation"""

    user_id = serializers.IntegerField()
    challenge_id = serializers.IntegerField()
    tech_stack = serializers.CharField(max_length=100)
    difficulty = serializers.ChoiceField(choices=Quiz.DIFFICULTY_CHOICES)

    def validate_tech_stack(self, value):
        """Clean and validate tech stack"""
        return value.strip().lower()


class QuizMetricsSerializer(serializers.ModelSerializer):
    pass_rate = serializers.ReadOnlyField()

    class Meta:
        model = QuizMetrics
        fields = [
            "tech_stack",
            "difficulty",
            "total_quizzes",
            "total_passes",
            "average_score",
            "pass_rate",
            "average_completion_time",
            "last_updated",
        ]


class QuizStatsSerializer(serializers.Serializer):
    """Summary statistics for quiz performance"""

    total_quizzes_taken = serializers.IntegerField()
    quizzes_passed = serializers.IntegerField()
    overall_pass_rate = serializers.FloatField()
    average_score = serializers.FloatField()
    favorite_tech_stack = serializers.CharField()
    recent_quizzes = QuizSerializer(many=True)
