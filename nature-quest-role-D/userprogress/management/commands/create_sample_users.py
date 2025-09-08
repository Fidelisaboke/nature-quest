from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = 'Create sample users for testing API endpoints'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of users to create (default: 5)'
        )
        
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing users (except superusers) before creating new ones'
        )
        
        parser.add_argument(
            '--with-superuser',
            action='store_true',
            help='Create an admin superuser'
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            # Don't delete superusers
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(
                self.style.WARNING('Cleared all non-superuser accounts')
            )
        
        count = options['count']
        created_users = []
        
        # Sample user data
        user_templates = [
            {
                'username': 'naturelover',
                'email': 'naturelover@example.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'password': 'nature123'
            },
            {
                'username': 'hikerboy',
                'email': 'hikerboy@example.com',
                'first_name': 'Bob',
                'last_name': 'Smith',
                'password': 'hiking456'
            },
            {
                'username': 'photoexplorer',
                'email': 'photoexplorer@example.com',
                'first_name': 'Carol',
                'last_name': 'Davis',
                'password': 'photo789'
            },
            {
                'username': 'wildlifefan',
                'email': 'wildlifefan@example.com',
                'first_name': 'David',
                'last_name': 'Wilson',
                'password': 'wildlife321'
            },
            {
                'username': 'adventurer',
                'email': 'adventurer@example.com',
                'first_name': 'Eva',
                'last_name': 'Brown',
                'password': 'adventure654'
            },
            {
                'username': 'questseeker',
                'email': 'questseeker@example.com',
                'first_name': 'Frank',
                'last_name': 'Miller',
                'password': 'quest987'
            },
            {
                'username': 'trailblazer',
                'email': 'trailblazer@example.com',
                'first_name': 'Grace',
                'last_name': 'Taylor',
                'password': 'trail147'
            },
            {
                'username': 'natureguru',
                'email': 'natureguru@example.com',
                'first_name': 'Henry',
                'last_name': 'Anderson',
                'password': 'guru258'
            }
        ]
        
        # Create superuser if requested
        if options['with_superuser']:
            try:
                if not User.objects.filter(username='admin').exists():
                    admin_user = User.objects.create_superuser(
                        username='admin',
                        email='admin@naturequest.com',
                        password='admin123',
                        first_name='Admin',
                        last_name='User'
                    )
                    # Create token for admin
                    token, created = Token.objects.get_or_create(user=admin_user)
                    self.stdout.write(
                        self.style.SUCCESS(f'Created superuser: admin (token: {token.key})')
                    )
                else:
                    admin_user = User.objects.get(username='admin')
                    token, created = Token.objects.get_or_create(user=admin_user)
                    self.stdout.write(
                        self.style.WARNING(f'Superuser already exists: admin (token: {token.key})')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating superuser: {str(e)}')
                )
        
        # Create regular users
        for i in range(count):
            template = user_templates[i % len(user_templates)]
            username = template['username']
            
            # Add number suffix if we're creating more users than templates
            if i >= len(user_templates):
                username = f"{template['username']}{i + 1}"
                template['username'] = username
                template['email'] = f"{template['username']}@example.com"
            
            try:
                with transaction.atomic():
                    # Check if user already exists
                    if User.objects.filter(username=username).exists():
                        self.stdout.write(
                            self.style.WARNING(f'User {username} already exists, skipping...')
                        )
                        continue
                    
                    # Create user
                    user = User.objects.create_user(
                        username=template['username'],
                        email=template['email'],
                        password=template['password'],
                        first_name=template['first_name'],
                        last_name=template['last_name']
                    )
                    
                    # Create authentication token
                    token, created = Token.objects.get_or_create(user=user)
                    
                    created_users.append({
                        'user': user,
                        'token': token.key,
                        'password': template['password']
                    })
                    
                    self.stdout.write(
                        f"Created user: {user.username} ({user.email}) - Token: {token.key}"
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating user {username}: {str(e)}")
                )
        
        # Display summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(created_users)} users!'))
        self.stdout.write('='*60)
        
        # Display authentication information
        self.stdout.write('\n--- Authentication Tokens ---')
        for user_info in created_users:
            self.stdout.write(
                f"Username: {user_info['user'].username} | "
                f"Password: {user_info['password']} | "
                f"Token: {user_info['token']}"
            )
        
        # Display API testing information
        self.stdout.write('\n--- API Testing Instructions ---')
        self.stdout.write('1. Use these tokens in API requests:')
        self.stdout.write('   Header: Authorization: Token <token_value>')
        self.stdout.write('')
        self.stdout.write('2. Example curl commands:')
        if created_users:
            token = created_users[0]['token']
            self.stdout.write(f'   curl -H "Authorization: Token {token}" http://127.0.0.1:8000/api/challenge-verification/challenges/')
            self.stdout.write(f'   curl -H "Authorization: Token {token}" http://127.0.0.1:8000/api/progress/profile/')
            self.stdout.write(f'   curl -H "Authorization: Token {token}" http://127.0.0.1:8000/api/quiz/quizzes/')
        
        self.stdout.write('\n3. Available API endpoints:')
        self.stdout.write('   - User Progress: /api/progress/')
        self.stdout.write('   - Quiz System: /api/quiz/')
        self.stdout.write('   - Challenge Verification: /api/challenge-verification/')
        self.stdout.write('   - DRF Browsable API: /api/')
        self.stdout.write('   - Admin Interface: /admin/')
        
        self.stdout.write('\n4. Login credentials for web interface:')
        for user_info in created_users[:3]:  # Show first 3 users
            self.stdout.write(
                f"   {user_info['user'].username} / {user_info['password']}"
            )
        
        self.stdout.write(f'\nTotal users in database: {User.objects.count()}')
        try:
            total_tokens = Token.objects.count()
            self.stdout.write(f'Total tokens created: {total_tokens}')
        except Exception:
            self.stdout.write('Total tokens: Unable to count (Token app may not be installed)')
