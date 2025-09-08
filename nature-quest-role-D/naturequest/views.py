from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """
    API root endpoint providing navigation to all available APIs
    """
    return Response({
        'message': 'Welcome to Nature Quest API!',
        'apis': {
            'user_progress': {
                'url': request.build_absolute_uri('/api/progress/'),
                'description': 'User profiles, badges, levels, and progress tracking'
            },
            'quiz': {
                'url': request.build_absolute_uri('/api/quiz/'),
                'description': 'AI-powered quiz generation and management'
            },
            'challenge_verification': {
                'url': request.build_absolute_uri('/api/challenge-verification/'),
                'description': 'Photo and location verification for nature challenges'
            }
        },
        'authentication': {
            'method': 'Token Authentication',
            'header': 'Authorization: Token <your_token>',
            'obtain_token': '/api/auth/token/',
            'note': 'Use the create_sample_users command to get test tokens'
        },
        'admin': {
            'url': '/admin/',
            'description': 'Django admin interface for content management'
        },
        'documentation': {
            'browsable_api': '/api/',
            'description': 'Django REST Framework browsable API'
        }
    })


@api_view(['GET'])
def simple_root(request):
    """
    Simple root endpoint for the main site
    """
    return Response({
        'message': 'Nature Quest - Gamified Learning Platform',
        'api_root': '/api/',
        'admin': '/admin/',
        'status': 'Server is running successfully!'
    })
