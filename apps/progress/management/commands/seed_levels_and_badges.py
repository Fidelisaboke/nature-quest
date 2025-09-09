from django.core.management.base import BaseCommand
from progress.models import Level, Badge


class Command(BaseCommand):
    help = "Initialize levels and badges with default data"

    def handle(self, *args, **options):
        self.stdout.write("Creating levels and badges...")

        # Create 12 gemstone levels
        levels_data = [
            (
                1,
                "Quartz",
                500,
                "A common but beautiful crystal - the foundation of your journey",
            ),
            (2, "Amethyst", 1200, "Purple beauty that brings clarity and calm"),
            (3, "Citrine", 2000, "Golden sunshine stone of abundance and joy"),
            (4, "Turquoise", 3000, "Sacred blue stone of protection and wisdom"),
            (5, "Garnet", 4200, "Deep red gem of passion and energy"),
            (6, "Peridot", 5600, "Bright green olivine from the depths of the earth"),
            (7, "Topaz", 7200, "Imperial golden crystal of strength and intellect"),
            (8, "Sapphire", 9000, "Royal blue gem of nobility and divine favor"),
            (9, "Ruby", 11000, "King of gems - crimson stone of love and courage"),
            (10, "Emerald", 13500, "Verdant jewel of rebirth and eternal spring"),
            (11, "Diamond", 16500, "Unbreakable brilliance and ultimate achievement"),
            (
                12,
                "Tanzanite",
                20000,
                "Rare violet-blue treasure found only in one place on Earth",
            ),
        ]

        for level_number, name, points, description in levels_data:
            level, created = Level.objects.get_or_create(
                level_number=level_number,
                defaults={
                    "name": name,
                    "points_required": points,
                    "description": description,
                },
            )
            if created:
                self.stdout.write(f"Created level: {name}")
            else:
                self.stdout.write(f"Level already exists: {name}")

        # Create 13 animal badges (12 zodiac + Cat)
        badges_data = [
            (
                "rat",
                "Curious Explorer",
                "Quick and resourceful, you find wonder in every corner",
                250,
                False,
            ),
            (
                "ox",
                "Steady Wanderer",
                "Patient and determined, you take nature at your own pace",
                500,
                False,
            ),
            (
                "tiger",
                "Bold Adventurer",
                "Fearless and strong, you tackle any outdoor challenge",
                750,
                False,
            ),
            (
                "rabbit",
                "Gentle Naturalist",
                "Soft and observant, you notice the subtle beauty around you",
                1000,
                False,
            ),
            (
                "dragon",
                "Legendary Seeker",
                "Powerful and wise, you inspire others on their nature journey",
                1250,
                False,
            ),
            (
                "snake",
                "Mysterious Tracker",
                "Intuitive and perceptive, you sense the hidden secrets of nature",
                1500,
                False,
            ),
            (
                "horse",
                "Free Spirit",
                "Independent and energetic, you gallop through wilderness with joy",
                1750,
                False,
            ),
            (
                "goat",
                "Mountain Climber",
                "Sure-footed and creative, you find beauty in the highest places",
                2000,
                False,
            ),
            (
                "monkey",
                "Playful Discoverer",
                "Clever and curious, you swing through adventures with enthusiasm",
                2250,
                False,
            ),
            (
                "rooster",
                "Dawn Herald",
                "Confident and observant, you rise early to greet nature's awakening",
                2500,
                False,
            ),
            (
                "dog",
                "Loyal Companion",
                "Faithful and honest, you share the joy of nature with friends",
                2750,
                False,
            ),
            (
                "pig",
                "Earth Guardian",
                "Generous and grounded, you understand the interconnection of all life",
                3000,
                False,
            ),
            (
                "cat",
                "Nature's Mystery",
                "The ultimate achievement - independent, graceful, and in perfect harmony with the wild",
                5000,
                True,
            ),
        ]

        for animal, name, description, points, is_special in badges_data:
            badge, created = Badge.objects.get_or_create(
                animal=animal,
                defaults={
                    "name": name,
                    "description": description,
                    "points_required": points,
                    "is_special": is_special,
                },
            )
            if created:
                self.stdout.write(f"Created badge: {name}")
            else:
                self.stdout.write(f"Badge already exists: {name}")

        self.stdout.write(
            self.style.SUCCESS("Successfully initialized levels and badges!")
        )
