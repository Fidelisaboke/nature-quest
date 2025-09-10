from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from progress.models import Badge, UserBadge, PointsTransaction
from quiz.models import Quiz, Question, QuizAttempt, QuestionResponse
from quests.models import (
    Challenge,
    ChallengeAttempt,
    PhotoAnalysis,
    LocationVerification,
)


class Command(BaseCommand):
    help = "Initialize test data for Nature Quest API testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing test data before creating new data",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.clear_test_data()

        self.create_test_data()

    def clear_test_data(self):
        """Clear existing test data"""
        self.stdout.write("🧹 Clearing existing test data...")

        # Clear in reverse dependency order
        QuestionResponse.objects.all().delete()
        QuizAttempt.objects.all().delete()
        Question.objects.all().delete()
        Quiz.objects.all().delete()

        LocationVerification.objects.all().delete()
        PhotoAnalysis.objects.all().delete()
        ChallengeAttempt.objects.all().delete()
        Challenge.objects.all().delete()

        PointsTransaction.objects.all().delete()
        UserBadge.objects.all().delete()

        self.stdout.write(self.style.WARNING("Cleared all test data"))

    def create_test_data(self):
        """Create comprehensive test data"""
        self.stdout.write("🚀 Creating test data for Nature Quest API...\n")

        # Get users
        users = list(User.objects.filter(is_superuser=False))
        if not users:
            self.stdout.write(
                self.style.ERROR("❌ No users found. Run create_sample_users first")
            )
            return

        self.stdout.write(f"👥 Found {len(users)} users for testing")

        # Create data
        challenges = self.create_challenges()
        quizzes = self.create_quizzes()
        self.create_quiz_attempts(users, quizzes)
        self.create_challenge_attempts(users, challenges)
        self.create_points_transactions(users)
        self.award_badges(users)

        # Summary
        self.stdout.write("\n✅ Test data creation completed!")
        self.stdout.write("📊 Summary:")
        self.stdout.write(f"   - Challenges: {Challenge.objects.count()}")
        self.stdout.write(f"   - Quizzes: {Quiz.objects.count()}")
        self.stdout.write(f"   - Questions: {Question.objects.count()}")
        self.stdout.write(f"   - Quiz Attempts: {QuizAttempt.objects.count()}")
        self.stdout.write(
            f"   - Challenge Attempts: {ChallengeAttempt.objects.count()}"
        )
        self.stdout.write(
            f"   - Points Transactions: {PointsTransaction.objects.count()}"
        )
        self.stdout.write(f"   - User Badges: {UserBadge.objects.count()}")

        self.stdout.write("\n🧪 API ready for testing with Postman!")

    def create_challenges(self):
        """Create sample challenges"""
        self.stdout.write("📸 Creating sample challenges...")

        challenges_data = [
            {
                "title": "Alpine Lake Photography",
                "description": "Capture a stunning photo of an alpine lake surrounded by mountains at elevation above 8,000 feet",
                "difficulty_level": "intermediate",
                "location_type": "lake",
                "location_name": "Maroon Lake, Colorado",
                "target_latitude": 39.0708,
                "target_longitude": -106.9890,
                "verification_radius": 50,
                "points_reward": 150,
                "required_elements": ["lake", "mountains", "alpine"],
                "is_active": True,
            },
            {
                "title": "Wildlife Spotting Challenge",
                "description": "Photograph a wild animal in its natural habitat without disturbing it",
                "difficulty_level": "advanced",
                "location_type": "wildlife_area",
                "location_name": "Yellowstone National Park",
                "target_latitude": 44.4280,
                "target_longitude": -110.5885,
                "verification_radius": 200,
                "points_reward": 250,
                "required_elements": ["wildlife", "natural_habitat"],
                "is_active": True,
            },
            {
                "title": "Sunset Point Hike",
                "description": "Reach the designated sunset viewpoint and verify your location at golden hour",
                "difficulty_level": "beginner",
                "location_type": "mountain",
                "location_name": "Sunset Point, Bryce Canyon",
                "target_latitude": 37.6261,
                "target_longitude": -112.1660,
                "verification_radius": 25,
                "points_reward": 100,
                "required_elements": ["sunset", "viewpoint"],
                "is_active": True,
            },
            {
                "title": "Waterfall Discovery",
                "description": "Find and photograph a hidden waterfall using provided GPS coordinates",
                "difficulty_level": "advanced",
                "location_type": "waterfall",
                "location_name": "Hidden Falls, Grand Teton",
                "target_latitude": 43.7904,
                "target_longitude": -110.7264,
                "verification_radius": 30,
                "points_reward": 300,
                "required_elements": ["waterfall", "discovery"],
                "is_active": True,
            },
            {
                "title": "Forest Canopy Study",
                "description": "Document different tree species in an old-growth forest area",
                "difficulty_level": "intermediate",
                "location_type": "forest",
                "location_name": "Hoh Rainforest, Olympic NP",
                "target_latitude": 47.8606,
                "target_longitude": -123.9348,
                "verification_radius": 100,
                "points_reward": 175,
                "required_elements": ["trees", "forest", "canopy"],
                "is_active": True,
            },
        ]

        challenges = []
        for data in challenges_data:
            challenge, created = Challenge.objects.get_or_create(
                title=data["title"], defaults=data
            )
            challenges.append(challenge)
            if created:
                self.stdout.write(f"  ✅ Created: {challenge.title}")

        return challenges

    def create_quizzes(self):
        """Create sample quizzes with questions"""
        self.stdout.write("🧠 Creating sample quizzes...")

        # Get the first user and first challenge for creating sample quizzes
        users = User.objects.filter(is_superuser=False)
        if not users.exists():
            self.stdout.write("  ⚠️ No users found for quiz creation")
            return []

        user = users.first()

        quiz_data = {
            "user": user,
            "challenge_id": 1,  # Reference to first challenge
            "difficulty": "medium",
            "tech_stack": "Nature Knowledge",
        }

        quiz, created = Quiz.objects.get_or_create(
            user=user, challenge_id=1, defaults=quiz_data
        )

        if created:
            self.stdout.write(
                f"  ✅ Created quiz: Nature Knowledge Quiz for {quiz.user.username}"
            )

            questions_data = [
                {
                    "question_text": "Which of the following is the largest species of bear found in North America?",
                    "question_type": "multiple_choice",
                    "tech_stack": "Nature Knowledge",
                    "difficulty": "medium",
                    "options": [
                        "Black Bear",
                        "Grizzly Bear",
                        "Polar Bear",
                        "Kodiak Bear",
                    ],
                    "correct_answers": [3],  # Kodiak Bear is at index 3
                    "explanation": "Kodiak bears are the largest subspecies of brown bear and can weigh up to 1,500 pounds.",
                    "points": 15,
                    "order": 1,
                },
                {
                    "question_text": "What is the primary method trees use to transport water from roots to leaves?",
                    "question_type": "multiple_choice",
                    "tech_stack": "Nature Knowledge",
                    "difficulty": "medium",
                    "options": [
                        "Osmosis",
                        "Transpiration",
                        "Xylem transport",
                        "Photosynthesis",
                    ],
                    "correct_answers": [2],  # Xylem transport is at index 2
                    "explanation": "Xylem vessels transport water and nutrients from the roots to all parts of the tree.",
                    "points": 10,
                    "order": 2,
                },
                {
                    "question_text": "Which biome is characterized by permafrost and very short growing seasons?",
                    "question_type": "multiple_choice",
                    "tech_stack": "Nature Knowledge",
                    "difficulty": "medium",
                    "options": ["Taiga", "Tundra", "Temperate Forest", "Grassland"],
                    "correct_answers": [1],  # Tundra is at index 1
                    "explanation": "Tundra biomes have permanently frozen subsoil (permafrost) and extremely short growing seasons.",
                    "points": 12,
                    "order": 3,
                },
                {
                    "question_text": "Mycorrhizal fungi form beneficial relationships with plant roots.",
                    "question_type": "multiple_choice",
                    "tech_stack": "Nature Knowledge",
                    "difficulty": "medium",
                    "options": ["True", "False"],
                    "correct_answers": [0],  # True is at index 0
                    "explanation": "Mycorrhizal fungi help plants absorb nutrients and water in exchange for carbohydrates.",
                    "points": 8,
                    "order": 4,
                },
                {
                    "question_text": "What percentage of Earth's surface is covered by forests?",
                    "question_type": "multiple_choice",
                    "tech_stack": "Nature Knowledge",
                    "difficulty": "medium",
                    "options": ["15%", "31%", "45%", "52%"],
                    "correct_answers": [1],  # 31% is at index 1
                    "explanation": "Approximately 31% of Earth's land surface is covered by forests.",
                    "points": 10,
                    "order": 5,
                },
            ]

            for q_data in questions_data:
                Question.objects.create(quiz=quiz, **q_data)

            self.stdout.write(f"    ➕ Added {len(questions_data)} questions")

        return [quiz]

    def create_quiz_attempts(self, users, quizzes):
        """Create sample quiz attempts"""
        self.stdout.write("🎯 Creating quiz attempts...")

        for quiz in quizzes:
            # Quiz already has a user, so create attempt for that user's quiz
            attempt, created = QuizAttempt.objects.get_or_create(
                quiz=quiz,
                defaults={
                    "submitted_at": timezone.now() - timedelta(hours=1),
                    "total_score": 85.0,
                },
            )

            if created:
                # Update the quiz with completion status
                quiz.completed_at = timezone.now() - timedelta(hours=1)
                quiz.score = 85.0
                quiz.passed = True
                quiz.save()

                # Create responses for each question
                for question in quiz.questions.all():
                    QuestionResponse.objects.get_or_create(
                        attempt=attempt,
                        question=question,
                        defaults={
                            "selected_answers": question.correct_answers,  # Use correct answers
                            "is_correct": True,
                            "points_earned": question.points,
                        },
                    )

                self.stdout.write(
                    f"  ✅ {quiz.user.username} completed quiz for challenge {quiz.challenge_id}"
                )
            else:
                self.stdout.write(
                    f"  ⚠️ Quiz attempt already exists for {quiz.user.username}"
                )

    def create_challenge_attempts(self, users, challenges):
        """Create sample challenge attempts"""
        self.stdout.write("🏔️ Creating challenge attempts...")

        for i, user in enumerate(users[:3]):
            for challenge in challenges[:2]:  # Use first 2 challenges
                # Create a simple test image path (you can create actual test images later)
                from django.core.files.base import ContentFile
                import io
                from PIL import Image

                # Create a simple test image
                img = Image.new("RGB", (100, 100), color="green")
                img_file = io.BytesIO()
                img.save(img_file, "JPEG")
                img_file.seek(0)

                attempt, created = ChallengeAttempt.objects.get_or_create(
                    user=user,
                    challenge=challenge,
                    defaults={
                        "status": "verified",
                        "submitted_photo": ContentFile(
                            img_file.read(),
                            name=f"test_photo_{user.id}_{challenge.id}.jpg",
                        ),
                        "submitted_latitude": challenge.target_latitude + (i * 0.001),
                        "submitted_longitude": challenge.target_longitude + (i * 0.001),
                        "submission_notes": f"Test challenge attempt by {user.username}",
                        "photo_verified": True,
                        "location_verified": True,
                        "verification_details": {
                            "camera": "test",
                            "location": "verified",
                        },
                        "points_earned": challenge.points_reward,
                        "bonus_points": 10,
                        "verified_at": timezone.now() - timedelta(hours=i + 1),
                    },
                )

                if created:
                    self.stdout.write(f"  ✅ {user.username} -> {challenge.title}")
                else:
                    self.stdout.write(
                        f"  ⚠️ Attempt already exists: {user.username} -> {challenge.title}"
                    )

    def create_points_transactions(self, users):
        """Create sample points transactions"""
        self.stdout.write("💰 Creating points transactions...")

        transactions = [
            {
                "points": 100,
                "transaction_type": "earned",
                "description": "Completed Forest Wildlife Quiz with 90% score",
            },
            {
                "points": 75,
                "transaction_type": "earned",
                "description": "Successfully verified location at Yellowstone",
            },
            {
                "points": 200,
                "transaction_type": "earned",
                "description": "Won weekly nature photography contest",
            },
            {
                "points": 150,
                "transaction_type": "earned",
                "description": "Completed Mountain Peak Photography Challenge",
            },
        ]

        for user in users[:4]:
            for i, transaction in enumerate(transactions):
                PointsTransaction.objects.get_or_create(
                    user=user,
                    description=transaction["description"],
                    defaults={
                        "points": transaction["points"],
                        "transaction_type": transaction["transaction_type"],
                        "created_at": timezone.now() - timedelta(days=i + 1),
                    },
                )
            self.stdout.write(f"  ✅ Added transactions for {user.username}")

    def award_badges(self, users):
        """Award sample badges"""
        self.stdout.write("🏆 Awarding badges...")

        badges = Badge.objects.all()[:5]

        for i, user in enumerate(users[:3]):
            for j, badge in enumerate(badges[: i + 2]):
                user_badge, created = UserBadge.objects.get_or_create(
                    user=user,
                    badge=badge,
                    defaults={
                        "earned_at": timezone.now() - timedelta(days=j + 1),
                        "points_when_earned": badge.points_required,
                    },
                )
                if created:
                    self.stdout.write(f"  🏆 {badge.name} -> {user.username}")
