from django.core.management.base import BaseCommand
from quiz.models import QuestionBank


class Command(BaseCommand):
    help = "Populate question bank with sample questions for different tech stacks"

    def handle(self, *args, **options):
        self.stdout.write("Creating sample questions for question bank...")

        # Sample questions for popular tech stacks
        sample_questions = [
            # Python Easy Questions
            {
                "tech_stack": "python",
                "difficulty": "easy",
                "question_type": "multiple_choice",
                "question_text": "What is the correct way to create a list in Python?",
                "options": [
                    "list = [1, 2, 3]",
                    "list = (1, 2, 3)",
                    "list = {1, 2, 3}",
                    "list = <1, 2, 3>",
                ],
                "correct_answers": [0],
                "explanation": "Lists in Python are created using square brackets []",
                "quality_score": 4.5,
            },
            {
                "tech_stack": "python",
                "difficulty": "easy",
                "question_type": "checkbox",
                "question_text": "Which of the following are valid Python data types?",
                "options": ["int", "string", "list", "array", "dict"],
                "correct_answers": [0, 2, 4],
                "explanation": 'int, list, and dict are built-in Python data types. "string" should be "str", and "array" is not a built-in type.',
                "quality_score": 4.0,
            },
            # JavaScript Easy Questions
            {
                "tech_stack": "javascript",
                "difficulty": "easy",
                "question_type": "multiple_choice",
                "question_text": "How do you declare a variable in JavaScript?",
                "options": ["var x;", "variable x;", "declare x;", "x := var;"],
                "correct_answers": [0],
                "explanation": "Variables in JavaScript are declared using var, let, or const keywords",
                "quality_score": 4.5,
            },
            {
                "tech_stack": "javascript",
                "difficulty": "easy",
                "question_type": "checkbox",
                "question_text": "Which are valid ways to declare variables in modern JavaScript?",
                "options": [
                    "var name",
                    "let age",
                    "const PI",
                    "variable count",
                    "declare value",
                ],
                "correct_answers": [0, 1, 2],
                "explanation": "var, let, and const are the valid keywords for declaring variables in JavaScript",
                "quality_score": 4.2,
            },
            # Python Medium Questions
            {
                "tech_stack": "python",
                "difficulty": "medium",
                "question_type": "multiple_choice",
                "question_text": 'What does the "self" parameter represent in Python class methods?',
                "options": [
                    "The class itself",
                    "The instance of the class",
                    "A static reference",
                    "The parent class",
                ],
                "correct_answers": [1],
                "explanation": "self refers to the instance of the class, allowing access to instance variables and methods",
                "quality_score": 4.3,
            },
            {
                "tech_stack": "python",
                "difficulty": "medium",
                "question_type": "checkbox",
                "question_text": "Which of the following are benefits of using list comprehensions?",
                "options": [
                    "More readable code",
                    "Better performance",
                    "Less memory usage",
                    "Automatic error handling",
                    "Built-in sorting",
                ],
                "correct_answers": [0, 1, 2],
                "explanation": "List comprehensions provide cleaner syntax, better performance, and more efficient memory usage",
                "quality_score": 4.1,
            },
            # JavaScript Medium Questions
            {
                "tech_stack": "javascript",
                "difficulty": "medium",
                "question_type": "multiple_choice",
                "question_text": 'What is the difference between "==" and "===" in JavaScript?',
                "options": [
                    "No difference",
                    "== checks type, === checks value",
                    "== checks value, === checks type and value",
                    "=== is deprecated",
                ],
                "correct_answers": [2],
                "explanation": "== performs type coercion while === checks both value and type without coercion",
                "quality_score": 4.4,
            },
            {
                "tech_stack": "javascript",
                "difficulty": "medium",
                "question_type": "checkbox",
                "question_text": "Which are characteristics of arrow functions in JavaScript?",
                "options": [
                    "Shorter syntax",
                    'No own "this" binding',
                    "Cannot be used as constructors",
                    "Always anonymous",
                    "Automatically return values",
                ],
                "correct_answers": [0, 1, 2],
                "explanation": "Arrow functions have concise syntax, lexical this binding, and cannot be used with new keyword",
                "quality_score": 4.0,
            },
            # Python Hard Questions
            {
                "tech_stack": "python",
                "difficulty": "hard",
                "question_type": "multiple_choice",
                "question_text": "What is the Global Interpreter Lock (GIL) in Python?",
                "options": [
                    "A security feature",
                    "A mutex that allows only one thread to execute Python bytecode",
                    "A memory management system",
                    "A debugging tool",
                ],
                "correct_answers": [1],
                "explanation": "The GIL is a mutex that prevents multiple threads from executing Python bytecode simultaneously",
                "quality_score": 4.6,
            },
            {
                "tech_stack": "python",
                "difficulty": "hard",
                "question_type": "checkbox",
                "question_text": "Which techniques can help with Python performance optimization?",
                "options": [
                    "Using generators",
                    "Caching with functools.lru_cache",
                    "List comprehensions over loops",
                    "Using multiprocessing",
                    "Always using classes",
                ],
                "correct_answers": [0, 1, 2, 3],
                "explanation": "Generators, caching, comprehensions, and multiprocessing all help improve Python performance",
                "quality_score": 4.2,
            },
            # React Questions
            {
                "tech_stack": "react",
                "difficulty": "easy",
                "question_type": "multiple_choice",
                "question_text": "What is JSX in React?",
                "options": [
                    "A new programming language",
                    "JavaScript XML syntax extension",
                    "A CSS framework",
                    "A testing library",
                ],
                "correct_answers": [1],
                "explanation": "JSX is a syntax extension for JavaScript that allows writing HTML-like code in React",
                "quality_score": 4.3,
            },
            {
                "tech_stack": "react",
                "difficulty": "medium",
                "question_type": "checkbox",
                "question_text": "Which are valid ways to manage state in React?",
                "options": [
                    "useState hook",
                    "Class component state",
                    "useReducer hook",
                    "Global variables",
                    "Context API",
                ],
                "correct_answers": [0, 1, 2, 4],
                "explanation": "React provides several state management options, but global variables are not recommended",
                "quality_score": 4.1,
            },
            # Java Questions
            {
                "tech_stack": "java",
                "difficulty": "easy",
                "question_type": "multiple_choice",
                "question_text": "What is the correct way to declare a constant in Java?",
                "options": [
                    "const int x = 5;",
                    "final int x = 5;",
                    "static int x = 5;",
                    "readonly int x = 5;",
                ],
                "correct_answers": [1],
                "explanation": "In Java, constants are declared using the final keyword",
                "quality_score": 4.4,
            },
            {
                "tech_stack": "java",
                "difficulty": "medium",
                "question_type": "checkbox",
                "question_text": "Which are principles of Object-Oriented Programming?",
                "options": [
                    "Encapsulation",
                    "Inheritance",
                    "Polymorphism",
                    "Abstraction",
                    "Compilation",
                ],
                "correct_answers": [0, 1, 2, 3],
                "explanation": "The four main OOP principles are encapsulation, inheritance, polymorphism, and abstraction",
                "quality_score": 4.5,
            },
        ]

        created_count = 0
        for question_data in sample_questions:
            question, created = QuestionBank.objects.get_or_create(
                tech_stack=question_data["tech_stack"],
                difficulty=question_data["difficulty"],
                question_text=question_data["question_text"],
                defaults=question_data,
            )

            if created:
                created_count += 1
                self.stdout.write(
                    f"Created: {question_data['tech_stack']} ({question_data['difficulty']}) - {question_data['question_text'][:50]}..."
                )
            else:
                self.stdout.write(
                    f"Already exists: {question_data['tech_stack']} ({question_data['difficulty']})"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully added {created_count} new questions to the question bank!"
            )
        )
