from django.core.management.base import BaseCommand
from quests.models import Challenge
import random


class Command(BaseCommand):
    help = "Create sample challenges for testing and development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of challenges to create (default: 10)",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing challenges before creating new ones",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Challenge.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared all existing challenges"))

        count = options["count"]

        # Sample challenge data
        challenge_templates = [
            {
                "title": "Forest Photography Challenge",
                "description": "Take a photo in a dense forest area showing at least 3 different tree species.",
                "location_type": "forest",
                "location_name": "Redwood National Forest",
                "target_latitude": 41.2132,
                "target_longitude": -124.0046,
                "verification_radius": 5000,  # 5km
                "difficulty_level": "beginner",
                "points_reward": 100,
                "required_elements": ["trees", "forest canopy", "natural lighting"],
                "special_instructions": "Include multiple tree species in your photo. Natural lighting preferred.",
            },
            {
                "title": "Mountain Peak Sunrise",
                "description": "Capture a sunrise or sunset from a mountain peak above 1000m elevation.",
                "location_type": "mountain",
                "location_name": "Mount Whitney Trail",
                "target_latitude": 36.5786,
                "target_longitude": -118.2923,
                "verification_radius": 2000,  # 2km
                "difficulty_level": "advanced",
                "points_reward": 300,
                "required_elements": [
                    "mountain peak",
                    "sunrise or sunset",
                    "clear sky",
                ],
                "special_instructions": "Photo must be taken during golden hour (sunrise/sunset).",
            },
            {
                "title": "Urban Park Wildlife",
                "description": "Photograph wildlife in an urban park setting.",
                "location_type": "park",
                "location_name": "Central Park NYC",
                "target_latitude": 40.7829,
                "target_longitude": -73.9654,
                "verification_radius": 1000,  # 1km
                "difficulty_level": "intermediate",
                "points_reward": 150,
                "required_elements": ["wildlife", "urban background"],
                "special_instructions": "Wildlife should be the main subject. Urban elements should be visible.",
            },
            {
                "title": "Desert Landscape Challenge",
                "description": "Capture the unique beauty of desert landscapes with cacti or desert plants.",
                "location_type": "desert",
                "location_name": "Joshua Tree National Park",
                "target_latitude": 33.8734,
                "target_longitude": -115.9010,
                "verification_radius": 10000,  # 10km
                "difficulty_level": "intermediate",
                "points_reward": 200,
                "required_elements": ["desert plants", "arid landscape"],
                "special_instructions": "Show the diversity of desert plant life.",
            },
            {
                "title": "Coastal Marine Life",
                "description": "Document marine life or coastal ecosystems at low tide.",
                "location_type": "beach",
                "location_name": "Monterey Bay",
                "target_latitude": 36.6002,
                "target_longitude": -121.8947,
                "verification_radius": 3000,  # 3km
                "difficulty_level": "intermediate",
                "points_reward": 175,
                "required_elements": ["marine life", "tidal pools", "coastal features"],
                "special_instructions": "Best captured during low tide. Respect marine life.",
            },
            {
                "title": "Botanical Garden Diversity",
                "description": "Showcase plant diversity in a botanical garden setting.",
                "location_type": "garden",
                "location_name": "San Francisco Botanical Garden",
                "target_latitude": 37.7694,
                "target_longitude": -122.4862,
                "verification_radius": 500,  # 500m
                "difficulty_level": "beginner",
                "points_reward": 75,
                "required_elements": ["flowering plants", "diverse species"],
                "special_instructions": "Include at least 3 different plant families in composition.",
            },
            {
                "title": "Waterfall Photography",
                "description": "Capture the power and beauty of a natural waterfall.",
                "location_type": "waterfall",
                "location_name": "Yosemite Falls",
                "target_latitude": 37.7456,
                "target_longitude": -119.5964,
                "verification_radius": 1500,  # 1.5km
                "difficulty_level": "advanced",
                "points_reward": 250,
                "required_elements": ["flowing water", "rock formations"],
                "special_instructions": "Use longer exposure for silky water effect if possible.",
            },
            {
                "title": "River Ecosystem Documentation",
                "description": "Document the ecosystem around a natural river or stream.",
                "location_type": "river",
                "location_name": "Colorado River",
                "target_latitude": 36.1069,
                "target_longitude": -112.1129,
                "verification_radius": 2500,  # 2.5km
                "difficulty_level": "intermediate",
                "points_reward": 125,
                "required_elements": ["flowing river", "riparian vegetation"],
                "special_instructions": "Show the interaction between water and surrounding vegetation.",
            },
            {
                "title": "Lake Reflection Challenge",
                "description": "Capture perfect reflections in a calm lake during golden hour.",
                "location_type": "lake",
                "location_name": "Lake Tahoe",
                "target_latitude": 39.0968,
                "target_longitude": -120.0324,
                "verification_radius": 5000,  # 5km
                "difficulty_level": "intermediate",
                "points_reward": 150,
                "required_elements": [
                    "lake reflection",
                    "mountain or tree reflections",
                ],
                "special_instructions": "Best captured during calm weather for clear reflections.",
            },
            {
                "title": "Wildlife Reserve Expedition",
                "description": "Document wildlife in their natural habitat within a protected reserve.",
                "location_type": "wildlife_area",
                "location_name": "Yellowstone National Park",
                "target_latitude": 44.4280,
                "target_longitude": -110.5885,
                "verification_radius": 15000,  # 15km
                "difficulty_level": "advanced",
                "points_reward": 350,
                "required_elements": ["wild animals", "natural habitat"],
                "special_instructions": "Maintain safe distance from wildlife. Use telephoto lens.",
            },
            {
                "title": "Urban Nature Trail",
                "description": "Find nature within urban environments - green spaces, urban wildlife.",
                "location_type": "trail",
                "location_name": "Golden Gate Park Trail",
                "target_latitude": 37.7694,
                "target_longitude": -122.4862,
                "verification_radius": 800,  # 800m
                "difficulty_level": "beginner",
                "points_reward": 50,
                "required_elements": ["urban nature", "walking path"],
                "special_instructions": "Show how nature thrives in urban settings.",
            },
            {
                "title": "Conservation Area Survey",
                "description": "Document conservation efforts and protected ecosystems.",
                "location_type": "nature_reserve",
                "location_name": "Point Reyes National Seashore",
                "target_latitude": 38.0466,
                "target_longitude": -122.9042,
                "verification_radius": 8000,  # 8km
                "difficulty_level": "intermediate",
                "points_reward": 200,
                "required_elements": ["protected landscape", "conservation signage"],
                "special_instructions": "Include evidence of conservation efforts where possible.",
            },
        ]

        created_count = 0

        for i in range(count):
            # Cycle through templates if we need more challenges than templates
            template = challenge_templates[i % len(challenge_templates)]

            # Add variation to titles if we're repeating templates
            if i >= len(challenge_templates):
                template["title"] = f"{template['title']} #{i + 1}"
                # Slightly vary coordinates for repeated challenges
                template["target_latitude"] += random.uniform(-0.01, 0.01)
                template["target_longitude"] += random.uniform(-0.01, 0.01)

            try:
                challenge = Challenge.objects.create(**template)
                created_count += 1

                self.stdout.write(
                    f"Created challenge: {challenge.title} "
                    f"({challenge.location_type}, {challenge.difficulty_level})"
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error creating challenge {template['title']}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} challenges!")
        )

        # Display summary
        self.stdout.write("\n--- Challenge Summary ---")
        for difficulty in ["beginner", "intermediate", "advanced"]:
            count = Challenge.objects.filter(difficulty_level=difficulty).count()
            self.stdout.write(f"{difficulty.title()}: {count} challenges")

        self.stdout.write(
            f"Total active challenges: {Challenge.objects.filter(is_active=True).count()}"
        )

        # Display API endpoints info
        self.stdout.write("\n--- API Endpoints ---")
        self.stdout.write("Challenges: GET /api/challenge-verification/challenges/")
        self.stdout.write("Submit attempt: POST /api/challenge-verification/attempts/")
        self.stdout.write(
            "User progress: GET /api/challenge-verification/challenges/my-progress/"
        )
        self.stdout.write(
            "Admin stats: GET /api/challenge-verification/admin/challenges/statistics/"
        )
