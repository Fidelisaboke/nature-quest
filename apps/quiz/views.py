from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Quiz, QuizAttempt, QuestionBank, QuizMetrics
from .serializers import (
    QuizSerializer,
    QuizDetailSerializer,
    QuizResultSerializer,
    QuizAttemptSerializer,
    QuizSubmissionSerializer,
    QuestionBankSerializer,
    QuizGenerationRequestSerializer,
    QuizMetricsSerializer,
    QuizStatsSerializer,
)
from .services import QuizService
import logging
import requests

logger = logging.getLogger(__name__)


class QuizViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quizzes"""

    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == "retrieve":
            return QuizDetailSerializer
        return QuizSerializer

    @action(detail=False, methods=["get"])
    def my_active_quiz(self, request):
        """Get user's current active (incomplete) quiz"""
        active_quiz = Quiz.objects.filter(
            user=request.user, completed_at__isnull=True
        ).first()

        if active_quiz:
            serializer = self.get_serializer(active_quiz)
            return Response(serializer.data)
        else:
            return Response(
                {"message": "No active quiz found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit quiz answers"""
        quiz = self.get_object()

        if quiz.is_completed:
            return Response(
                {"error": "Quiz already completed"}, status=status.HTTP_400_BAD_REQUEST
            )

        submission_serializer = QuizSubmissionSerializer(data=request.data)
        if not submission_serializer.is_valid():
            return Response(
                submission_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        # Submit quiz
        quiz_service = QuizService()
        result = quiz_service.submit_quiz(
            quiz.id, submission_serializer.validated_data["responses"]
        )

        if result["success"]:
            # If passed (80%+), award points via progress app
            if result["passed"]:
                self._award_quiz_completion_points(request.user, quiz, result["score"])

            # Return detailed results
            quiz.refresh_from_db()
            result_serializer = QuizResultSerializer(quiz)

            return Response({"result": result, "quiz_details": result_serializer.data})
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    def _award_quiz_completion_points(self, user, quiz, score):
        """Award points to user for completing quiz (via progress app API)"""
        try:
            # Calculate points based on difficulty and score
            base_points = {"easy": 50, "medium": 75, "hard": 100}

            points = base_points.get(quiz.difficulty, 50)
            # Bonus points for high scores
            if score >= 95:
                points += 25
            elif score >= 90:
                points += 15
            elif score >= 85:
                points += 10

            # Call progress app API
            progress_data = {
                "user_id": user.id,
                "points_to_add": points,
                "transaction_type": "quiz_completion",
                "description": f"Completed {quiz.tech_stack} quiz ({quiz.difficulty}) - {score:.1f}%",
                "quiz_id": quiz.id,
                "increment_quizzes": True,
            }

            # Make internal API call to progress app
            response = requests.post(
                "http://localhost:8000/api/progress/update-progress/",
                json=progress_data,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info(
                    f"Awarded {points} points to {user.username} for quiz completion"
                )
            else:
                logger.error(f"Failed to award points: {response.text}")

        except Exception as e:
            logger.error(f"Error awarding quiz points: {str(e)}")

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        """Get detailed quiz results with correct answers"""
        quiz = self.get_object()

        if not quiz.is_completed:
            return Response(
                {"error": "Quiz not yet completed"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = QuizResultSerializer(quiz)
        return Response(serializer.data)


class QuizGenerationAPIView(APIView):
    """API endpoint for generating quizzes (called by challengeverification app)"""

    permission_classes = []  # Open endpoint for internal app communication

    def post(self, request):
        """Generate a new quiz for a user after challenge completion"""
        serializer = QuizGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        quiz_service = QuizService()

        quiz = quiz_service.create_quiz_for_user(
            user_id=data["user_id"],
            challenge_id=data["challenge_id"],
            tech_stack=data["tech_stack"],
            difficulty=data["difficulty"],
        )

        if quiz:
            quiz_serializer = QuizSerializer(quiz)
            return Response(
                {
                    "success": True,
                    "quiz": quiz_serializer.data,
                    "message": f"Quiz generated for {data['tech_stack']} ({data['difficulty']})",
                }
            )
        else:
            return Response(
                {"success": False, "error": "Failed to generate quiz"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuestionBankViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing question bank (admin only)"""

    queryset = QuestionBank.objects.all()
    serializer_class = QuestionBankSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show to staff users
        if self.request.user.is_staff:
            return QuestionBank.objects.all().order_by("-created_at")
        return QuestionBank.objects.none()

    @action(detail=False, methods=["get"])
    def by_tech_stack(self, request):
        """Get questions filtered by tech stack and difficulty"""
        if not request.user.is_staff:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        tech_stack = request.query_params.get("tech_stack")
        difficulty = request.query_params.get("difficulty")

        queryset = self.get_queryset()
        if tech_stack:
            queryset = queryset.filter(tech_stack__icontains=tech_stack)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class QuizStatsAPIView(APIView):
    """API endpoint for getting quiz statistics"""

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        """Get quiz statistics for user"""
        if user_id is None:
            user_id = request.user.id

        quiz_service = QuizService()
        stats = quiz_service.get_user_quiz_stats(user_id)

        if "error" in stats:
            return Response(stats, status=status.HTTP_404_NOT_FOUND)

        serializer = QuizStatsSerializer(stats)
        return Response(serializer.data)


class QuizMetricsAPIView(APIView):
    """API endpoint for getting quiz metrics (admin only)"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get quiz performance metrics"""
        if not request.user.is_staff:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        metrics = QuizMetrics.objects.all()

        # Filter by tech stack if provided
        tech_stack = request.query_params.get("tech_stack")
        if tech_stack:
            metrics = metrics.filter(tech_stack__icontains=tech_stack)

        serializer = QuizMetricsSerializer(metrics, many=True)
        return Response(serializer.data)


class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing quiz attempts"""

    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            QuizAttempt.objects.filter(quiz__user=self.request.user)
            .select_related("quiz")
            .order_by("-started_at")
        )

    @action(detail=True, methods=["get"])
    def responses(self, request, pk=None):
        """Get detailed responses for a quiz attempt"""
        attempt = self.get_object()
        responses = attempt.responses.select_related("question").order_by(
            "question__order"
        )

        response_data = []
        for response in responses:
            response_data.append(
                {
                    "question": {
                        "id": response.question.id,
                        "text": response.question.question_text,
                        "options": response.question.options,
                        "correct_answers": response.question.correct_answers,
                        "explanation": response.question.explanation,
                    },
                    "user_answers": response.selected_answers,
                    "is_correct": response.is_correct,
                    "points_earned": response.points_earned,
                }
            )

        return Response(
            {
                "attempt_id": attempt.id,
                "quiz_id": attempt.quiz.id,
                "total_score": attempt.total_score,
                "responses": response_data,
            }
        )
