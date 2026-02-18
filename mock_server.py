#!/usr/bin/env python3
"""
Nature Quest API Mock Server
A Flask-based mock server that simulates all API endpoints for the Nature Quest Django project.
"""

import random
import time
import uuid
import sys
from datetime import datetime, timedelta, timezone
from functools import wraps
from threading import Lock

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration
MOCK_DELAY_MIN = 0.05  # Minimum delay in seconds
MOCK_DELAY_MAX = 0.15  # Maximum delay in seconds
SERVER_START_TIME = datetime.now(timezone.utc)

# In-memory data stores with thread safety
data_lock = Lock()
users = {}
user_profiles = {}
quests = {}
challenges = {}
quest_logs = {}
challenge_logs = {}
locations = {}
trivia_questions = {}
refresh_tokens = {}
access_tokens = {}

# New data stores for gamification features
checkpoints = {}
user_checkpoints = {}
badges = {}
user_badges = {}
carbon_impacts = {}
leaderboard_entries = {}

# Helper functions
def generate_id():
    """Generate a unique ID."""
    return str(uuid.uuid4().int % 1000000)

def generate_timestamp():
    """Generate ISO format timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "+00:00"

def generate_request_id():
    """Generate a short request ID."""
    return uuid.uuid4().hex[:8]

def generate_jwt_token():
    """Generate a mock JWT token."""
    return f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.{uuid.uuid4().hex}.{uuid.uuid4().hex}"

def simulate_delay():
    """Simulate network delay."""
    time.sleep(random.uniform(MOCK_DELAY_MIN, MOCK_DELAY_MAX))
    return True

def create_response(data, message="Success", errors=None, status_code=200):
    """Create a standardized API response."""
    response = {
        "success": status_code < 400,
        "message": message,
        "data": data,
        "errors": errors,
        "timestamp": generate_timestamp(),
        "request_id": generate_request_id()
    }
    return jsonify(response), status_code

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return create_response(None, "Authentication credentials were not provided", 
                                 {"detail": "Authentication credentials were not provided"}, 401)
        
        token = auth_header.split(' ')[1]
        with data_lock:
            if token not in access_tokens:
                return create_response(None, "Invalid or expired token",
                                     {"detail": "Token is invalid or expired"}, 401)
            
            # Check if token is expired (access tokens expire after 1 hour)
            token_data = access_tokens[token]
            if datetime.now(timezone.utc) > token_data.get('expires_at', datetime.min):
                return create_response(None, "Token has expired",
                                     {"detail": "Token has expired"}, 401)
            
            request.current_user = token_data['user']
        
        return f(*args, **kwargs)
    return decorated

# Initialize sample data
def init_sample_data():
    """Initialize sample data for the mock server."""
    with data_lock:
        # Sample locations
        locations['1'] = {
            "id": 1,
            "name": "Central Park",
            "latitude": 40.785091,
            "longitude": -73.968285,
            "address": "New York, NY 10024",
            "source": "manual",
            "metadata": {"park_type": "public", "size_acres": 843}
        }
        locations['2'] = {
            "id": 2,
            "name": "Golden Gate Park",
            "latitude": 37.769420,
            "longitude": -122.486214,
            "address": "San Francisco, CA 94122",
            "source": "manual",
            "metadata": {"park_type": "public", "size_acres": 1017}
        }
        
        # Sample quests
        quests['1'] = {
            "id": 1,
            "title": "Morning Nature Walk",
            "description": "Take a peaceful 30-minute walk through the park and observe local wildlife.",
            "quest_type": "outdoor",
            "difficulty": 1,
            "duration_minutes": 30,
            "experience_reward": 50,
            "requirements": {"min_steps": 1000, "photos_required": 1},
            "location": locations['1'],
            "is_active": True,
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        quests['2'] = {
            "id": 2,
            "title": "Tree Identification Challenge",
            "description": "Identify and photograph 5 different tree species in the park.",
            "quest_type": "outdoor",
            "difficulty": 2,
            "duration_minutes": 45,
            "experience_reward": 100,
            "requirements": {"min_trees": 5, "photos_required": 5},
            "location": locations['1'],
            "is_active": True,
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        quests['3'] = {
            "id": 3,
            "title": "Sunset Photography",
            "description": "Capture the perfect sunset photo from the park's highest point.",
            "quest_type": "outdoor",
            "difficulty": 3,
            "duration_minutes": 60,
            "experience_reward": 150,
            "requirements": {"photos_required": 3, "time_constraint": "sunset"},
            "location": locations['2'],
            "is_active": True,
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        
        # Sample challenges
        challenges['1'] = {
            "id": 1,
            "title": "Weekend Warrior",
            "description": "Complete 3 outdoor quests this weekend",
            "is_mandatory": False,
            "experience_reward": 300,
            "order": 1,
            "quests": [quests['1'], quests['2']],
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        challenges['2'] = {
            "id": 2,
            "title": "Nature Photographer",
            "description": "Complete all photography-related quests",
            "is_mandatory": False,
            "experience_reward": 500,
            "order": 2,
            "quests": [quests['3']],
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        
        # Sample trivia questions
        trivia_questions['1'] = {
            "id": 1,
            "question_text": "What is the largest living structure on Earth?",
            "choices": ["Great Barrier Reef", "Amazon Rainforest", "Grand Canyon", "Mount Everest"],
            "correct_answer": "Great Barrier Reef",
            "tags": ["nature", "ocean", "trivia"]
        }
        trivia_questions['2'] = {
            "id": 2,
            "question_text": "Which tree produces acorns?",
            "choices": ["Pine", "Oak", "Maple", "Birch"],
            "correct_answer": "Oak",
            "tags": ["trees", "nature", "botany"]
        }

        # Sample checkpoints for quests
        checkpoints['1'] = {
            "id": 1,
            "quest_id": 1,
            "name": "Park Entrance",
            "latitude": 40.785091,
            "longitude": -73.968285,
            "radius_meters": 50,
            "order": 1,
            "is_required": True
        }
        checkpoints['2'] = {
            "id": 2,
            "quest_id": 1,
            "name": "Bethesda Fountain",
            "latitude": 40.775,
            "longitude": -73.97,
            "radius_meters": 75,
            "order": 2,
            "is_required": True
        }
        checkpoints['3'] = {
            "id": 3,
            "quest_id": 2,
            "name": "Tree Trail Start",
            "latitude": 40.785,
            "longitude": -73.968,
            "radius_meters": 50,
            "order": 1,
            "is_required": True
        }

        # Sample badges
        badges['1'] = {
            "id": 1,
            "name": "First Steps",
            "description": "Complete your first quest",
            "icon": None,
            "tier": "bronze",
            "category": "quest_completion",
            "requirement_type": "quest_count",
            "requirement_value": 1,
            "quest_type_filter": None
        }
        badges['2'] = {
            "id": 2,
            "name": "Nature Explorer",
            "description": "Complete 5 outdoor quests",
            "icon": None,
            "tier": "silver",
            "category": "quest_type",
            "requirement_type": "quest_count",
            "requirement_value": 5,
            "quest_type_filter": "outdoor"
        }
        badges['3'] = {
            "id": 3,
            "name": "Eco Warrior",
            "description": "Save 10kg of CO2 through outdoor activities",
            "icon": None,
            "tier": "gold",
            "category": "environmental",
            "requirement_type": "carbon_saved",
            "requirement_value": 10000,  # in grams
            "quest_type_filter": None
        }
        badges['4'] = {
            "id": 4,
            "name": "XP Champion",
            "description": "Earn 1000 XP",
            "icon": None,
            "tier": "silver",
            "category": "quest_completion",
            "requirement_type": "xp_threshold",
            "requirement_value": 1000,
            "quest_type_filter": None
        }

        # Sample leaderboard entries
        for i in range(1, 11):
            leaderboard_entries[str(i)] = {
                "id": i,
                "user_id": f"user_{i}",
                "username": f"nature_lover_{i}",
                "display_name": f"Nature Lover {i}",
                "leaderboard_type": "global_xp",
                "region": "",
                "quest_type": None,
                "score": 1000 - (i * 50),
                "rank": i,
                "period": "all_time",
                "updated_at": generate_timestamp()
            }

# Health Check Endpoints
@app.route('/api/v1/health/', methods=['GET'])
def health_check():
    """Health check endpoint."""
    simulate_delay()
    uptime = (datetime.now(timezone.utc) - SERVER_START_TIME).total_seconds()
    
    data = {
        "status": "ok",
        "timestamp": generate_timestamp(),
        "django_version": "4.2.24",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "app_name": "Nature Quest",
        "app_version": "1.0.0",
        "uptime_seconds": int(uptime),
    }
    
    response = {
        "data": data,
        "meta": {
            "message": "Service is healthy",
            "docs_url": "https://docs.example.com",
        },
    }
    return jsonify(response), 200

# Authentication Endpoints
@app.route('/api/v1/users/auth/register/', methods=['POST'])
def register_user():
    """Register a new user."""
    simulate_delay()
    data = request.get_json()
    
    if not data:
        return create_response(None, "Validation failed", 
                             {"detail": "Request body is required"}, 400)
    
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    interests = data.get('interests', '')
    
    # Validation
    errors = {}
    if not email:
        errors['email'] = ["This field is required."]
    if not password:
        errors['password'] = ["This field is required."]
    if not username:
        errors['username'] = ["This field is required."]
    
    if errors:
        return create_response(None, "Validation failed", errors, 400)
    
    with data_lock:
        # Check if email already exists
        for user in users.values():
            if user['email'] == email:
                return create_response(None, "Validation failed",
                                     {"email": ["Email is already in use"]}, 400)
            if user['username'] == username:
                return create_response(None, "Validation failed",
                                     {"username": ["A user with that username already exists."]}, 400)
        
        # Create user
        user_id = generate_id()
        user = {
            "id": user_id,
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "interests": interests,
            "is_active": True,
            "is_staff": False,
            "groups": [],
            "user_permissions": []
        }
        users[user_id] = user
        
        # Create user profile
        user_profiles[user_id] = {
            "display_name": username,
            "email": email,
            "bio": "",
            "profile_pic": None,
            "points": 0,
            "level": 1
        }
        
        # Generate tokens
        refresh_token = generate_jwt_token()
        access_token = generate_jwt_token()
        
        refresh_tokens[refresh_token] = {
            'user': user,
            'expires_at': datetime.now(timezone.utc) + timedelta(days=7)
        }
        access_tokens[access_token] = {
            'user': user,
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
        }
    
    response_data = {
        "refresh": refresh_token,
        "access": access_token,
        "results": user
    }
    
    return create_response(response_data, "User registered successfully", None, 201)

@app.route('/api/v1/users/auth/login/', methods=['POST'])
def login_user():
    """Login user and return tokens."""
    simulate_delay()
    data = request.get_json()
    
    if not data:
        return create_response(None, "Request validation failed",
                             {"detail": "Request body is required"}, 400)
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return create_response(None, "Request validation failed",
                             {"email": ["This field is required."],
                              "password": ["This field is required."]}, 400)
    
    with data_lock:
        # Find user by email
        user = None
        for u in users.values():
            if u['email'] == email:
                user = u
                break
        
        if not user:
            return create_response(None, "No active account found with the given credentials",
                                 {"detail": "No active account found with the given credentials"}, 401)
        
        # Generate tokens
        refresh_token = generate_jwt_token()
        access_token = generate_jwt_token()
        
        refresh_tokens[refresh_token] = {
            'user': user,
            'expires_at': datetime.now(timezone.utc) + timedelta(days=7)
        }
        access_tokens[access_token] = {
            'user': user,
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
        }
    
    response_data = {
        "refresh": refresh_token,
        "access": access_token
    }
    
    return create_response(response_data, "Login successful")

@app.route('/api/v1/users/auth/token/refresh/', methods=['POST'])
def refresh_token():
    """Refresh access token."""
    simulate_delay()
    data = request.get_json()
    
    if not data or not data.get('refresh'):
        return create_response(None, "Request validation failed",
                             {"refresh": ["This field is required."]}, 400)
    
    refresh_token_val = data['refresh']
    
    with data_lock:
        if refresh_token_val not in refresh_tokens:
            return create_response(None, "Token is invalid or expired",
                                 {"detail": "Token is invalid or expired"}, 401)
        
        token_data = refresh_tokens[refresh_token_val]
        if datetime.now(timezone.utc) > token_data['expires_at']:
            return create_response(None, "Token is invalid or expired",
                                 {"detail": "Token is invalid or expired"}, 401)
        
        # Generate new access token
        access_token = generate_jwt_token()
        access_tokens[access_token] = {
            'user': token_data['user'],
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)
        }
    
    response_data = {
        "access": access_token,
        "message": "Token refreshed successfully"
    }
    
    return create_response(response_data, "Token refreshed successfully")

@app.route('/api/v1/users/auth/me/', methods=['GET'])
@require_auth
def get_user_profile():
    """Get current user profile."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        profile = user_profiles.get(user['id'], {
            "display_name": user['username'],
            "email": user['email'],
            "bio": "",
            "profile_pic": None,
            "points": 0,
            "level": 1
        })
    
    return create_response(profile, "Profile retrieved successfully")

# Quest Endpoints
@app.route('/api/v1/quests/', methods=['GET'])
@require_auth
def list_quests():
    """List all quests with filtering."""
    simulate_delay()
    
    # Get query parameters
    quest_type = request.args.get('quest_type')
    difficulty = request.args.get('difficulty')
    is_active = request.args.get('is_active')
    search = request.args.get('search')
    
    with data_lock:
        result = list(quests.values())
        
        # Apply filters
        if quest_type:
            result = [q for q in result if q['quest_type'] == quest_type]
        if difficulty:
            result = [q for q in result if q['difficulty'] == int(difficulty)]
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            result = [q for q in result if q['is_active'] == is_active_bool]
        if search:
            result = [q for q in result if search.lower() in q['title'].lower() 
                     or search.lower() in q['description'].lower()]
    
    return create_response(result, "Quests retrieved successfully")

@app.route('/api/v1/quests/', methods=['POST'])
@require_auth
def create_quest():
    """Create a new quest."""
    simulate_delay()
    data = request.get_json()
    
    if not data:
        return create_response(None, "Validation failed",
                             {"detail": "Request body is required"}, 400)
    
    with data_lock:
        quest_id = generate_id()
        quest = {
            "id": quest_id,
            "title": data.get('title', ''),
            "description": data.get('description', ''),
            "quest_type": data.get('quest_type', 'outdoor'),
            "difficulty": data.get('difficulty', 1),
            "duration_minutes": data.get('duration_minutes', 30),
            "experience_reward": data.get('experience_reward', 50),
            "requirements": data.get('requirements', {}),
            "location": locations.get(str(data.get('location_id', 1)), locations.get('1')),
            "is_active": data.get('is_active', True),
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        quests[quest_id] = quest
    
    return create_response(quest, "Quest created successfully", None, 201)

@app.route('/api/v1/quests/<quest_id>/', methods=['GET'])
@require_auth
def get_quest(quest_id):
    """Get a specific quest."""
    simulate_delay()
    
    with data_lock:
        quest = quests.get(quest_id)
        if not quest:
            return create_response(None, "Quest not found",
                                 {"detail": "Quest not found"}, 404)
    
    return create_response(quest, "Quest retrieved successfully")

@app.route('/api/v1/quests/<quest_id>/', methods=['PUT'])
@require_auth
def update_quest(quest_id):
    """Update a quest."""
    simulate_delay()
    data = request.get_json()
    
    with data_lock:
        if quest_id not in quests:
            return create_response(None, "Quest not found",
                                 {"detail": "Quest not found"}, 404)
        
        quest = quests[quest_id]
        quest.update({
            "title": data.get('title', quest['title']),
            "description": data.get('description', quest['description']),
            "quest_type": data.get('quest_type', quest['quest_type']),
            "difficulty": data.get('difficulty', quest['difficulty']),
            "duration_minutes": data.get('duration_minutes', quest['duration_minutes']),
            "experience_reward": data.get('experience_reward', quest['experience_reward']),
            "requirements": data.get('requirements', quest['requirements']),
            "is_active": data.get('is_active', quest['is_active']),
            "updated_at": generate_timestamp()
        })
    
    return create_response(quest, "Quest updated successfully")

@app.route('/api/v1/quests/<quest_id>/', methods=['DELETE'])
@require_auth
def delete_quest(quest_id):
    """Delete a quest."""
    simulate_delay()
    
    with data_lock:
        if quest_id not in quests:
            return create_response(None, "Quest not found",
                                 {"detail": "Quest not found"}, 404)
        
        del quests[quest_id]
    
    return create_response(None, "Quest deleted successfully", status_code=204)

@app.route('/api/v1/quests/<quest_id>/start/', methods=['POST'])
@require_auth
def start_quest(quest_id):
    """Start a quest."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        if quest_id not in quests:
            return create_response(None, "Quest not found",
                                 {"detail": "Quest not found"}, 404)
        
        log_id = f"{user['id']}_{quest_id}"
        quest_log = {
            "id": log_id,
            "user": user['id'],
            "quest": quests[quest_id],
            "status": "in_progress",
            "progress": 0,
            "experience_earned": 0,
            "start_time": generate_timestamp(),
            "end_time": None,
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        quest_logs[log_id] = quest_log
    
    return create_response(quest_log, "Quest started successfully", None, 201)



@app.route('/api/v1/quests/<quest_id>/abandon/', methods=['POST'])
@require_auth
def abandon_quest(quest_id):
    """Abandon a quest."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        log_id = f"{user['id']}_{quest_id}"
        if log_id not in quest_logs:
            return create_response(None, "Quest log not found",
                                 {"detail": "Quest has not been started"}, 400)
        
        quest_log = quest_logs[log_id]
        quest_log['status'] = 'abandoned'
        quest_log['updated_at'] = generate_timestamp()
    
    return create_response(quest_log, "Quest abandoned successfully")

@app.route('/api/v1/quests/find-nearby/', methods=['GET'])
@require_auth
def find_quests_nearby():
    """Find quests near a location."""
    simulate_delay()
    
    try:
        latitude = float(request.args.get('latitude', 0))
        longitude = float(request.args.get('longitude', 0))
        radius = float(request.args.get('radius', 10))
    except (TypeError, ValueError):
        return create_response(None, "Invalid parameters",
                             {"error": "Invalid parameters"}, 400)
    
    with data_lock:
        # Return all quests with mock distance calculations
        result = []
        for quest in quests.values():
            mock_distance = random.uniform(0.5, radius)
            quest_data = {**quest, 'distance_km': round(mock_distance, 2)}
            result.append(quest_data)
        
        result.sort(key=lambda x: x['distance_km'])
    
    return jsonify({
        "quests": result,
        "page": 1,
        "total_pages": 1,
        "has_next": False,
        "has_previous": False,
        "total_count": len(result)
    })

# Challenge Endpoints
@app.route('/api/v1/challenges/', methods=['GET'])
@require_auth
def list_challenges():
    """List all challenges."""
    simulate_delay()
    
    with data_lock:
        result = list(challenges.values())
    
    return create_response(result, "Challenges retrieved successfully")

@app.route('/api/v1/challenges/', methods=['POST'])
@require_auth
def create_challenge():
    """Create a new challenge."""
    simulate_delay()
    data = request.get_json()
    
    with data_lock:
        challenge_id = generate_id()
        challenge = {
            "id": challenge_id,
            "title": data.get('title', ''),
            "description": data.get('description', ''),
            "is_mandatory": data.get('is_mandatory', False),
            "experience_reward": data.get('experience_reward', 100),
            "order": data.get('order', 1),
            "quests": [],
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        challenges[challenge_id] = challenge
    
    return create_response(challenge, "Challenge created successfully", None, 201)

@app.route('/api/v1/challenges/<challenge_id>/', methods=['GET'])
@require_auth
def get_challenge(challenge_id):
    """Get a specific challenge."""
    simulate_delay()
    
    with data_lock:
        challenge = challenges.get(challenge_id)
        if not challenge:
            return create_response(None, "Challenge not found",
                                 {"detail": "Challenge not found"}, 404)
    
    return create_response(challenge, "Challenge retrieved successfully")

@app.route('/api/v1/challenges/<challenge_id>/start/', methods=['POST'])
@require_auth
def start_challenge(challenge_id):
    """Start a challenge."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        if challenge_id not in challenges:
            return create_response(None, "Challenge not found",
                                 {"detail": "Challenge not found"}, 404)
        
        log_id = f"{user['id']}_{challenge_id}"
        challenge_log = {
            "id": log_id,
            "user": user['id'],
            "challenge": challenges[challenge_id],
            "completed_at": None,
            "experience_earned": 0,
            "created_at": generate_timestamp(),
            "updated_at": generate_timestamp()
        }
        challenge_logs[log_id] = challenge_log
    
    return create_response(challenge_log, "Challenge started successfully", None, 201)

@app.route('/api/v1/challenges/<challenge_id>/complete/', methods=['POST'])
@require_auth
def complete_challenge(challenge_id):
    """Complete a challenge."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        log_id = f"{user['id']}_{challenge_id}"
        if log_id not in challenge_logs:
            return create_response(None, "Challenge log not found",
                                 {"detail": "Challenge has not been started"}, 400)
        
        challenge_log = challenge_logs[log_id]
        challenge = challenges.get(challenge_id, {})
        challenge_log['completed_at'] = generate_timestamp()
        challenge_log['experience_earned'] = challenge.get('experience_reward', 0)
        challenge_log['updated_at'] = generate_timestamp()
        
        # Update user profile points
        if user['id'] in user_profiles:
            user_profiles[user['id']]['points'] += challenge_log['experience_earned']
    
    return create_response(challenge_log, "Challenge completed successfully")

@app.route('/api/v1/challenges/<challenge_id>/abandon/', methods=['POST'])
@require_auth
def abandon_challenge(challenge_id):
    """Abandon a challenge."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        log_id = f"{user['id']}_{challenge_id}"
        if log_id in challenge_logs:
            del challenge_logs[log_id]
    
    return create_response({"message": "Challenge abandoned successfully"}, 
                         "Challenge abandoned successfully")


# ========== NEW LOCATION-BASED ENDPOINTS ==========

@app.route('/api/v1/quests/discover/', methods=['GET'])
@require_auth
def discover_quests():
    """Smart radius quest discovery based on user location."""
    simulate_delay()
    
    try:
        lat = float(request.args.get('latitude'))
        lng = float(request.args.get('longitude'))
        min_radius = float(request.args.get('min_radius', 1))
        max_radius = float(request.args.get('max_radius', 50))
        target_count = int(request.args.get('target_count', 10))
    except (TypeError, ValueError):
        return create_response(None, "Invalid parameters",
                             {"error": "latitude and longitude are required"}, 400)
    
    with data_lock:
        # Mock smart radius algorithm - return all quests with mock distances
        result = []
        for quest in quests.values():
            mock_distance = random.uniform(0.5, min_radius * 2)
            if mock_distance <= max_radius:
                # Add checkpoints to quest data
                quest_checkpoints = [cp for cp in checkpoints.values() if cp['quest_id'] == quest['id']]
                quest_data = {
                    **quest,
                    'distance_km': round(mock_distance, 2),
                    'checkpoints': quest_checkpoints
                }
                result.append(quest_data)
        
        result.sort(key=lambda x: x['distance_km'])
        result = result[:target_count]
    
    return Response({
        "quests": result,
        "search_radius_km": min_radius * 2 if len(result) >= target_count else max_radius,
        "total_found": len(result)
    })


@app.route('/api/v1/quests/<quest_id>/validate-location/', methods=['POST'])
@require_auth
def validate_location(quest_id):
    """Validate user is at quest location or checkpoint."""
    simulate_delay()
    user = request.current_user
    data = request.get_json() or {}
    
    try:
        user_lat = float(data.get('latitude'))
        user_lng = float(data.get('longitude'))
    except (TypeError, ValueError):
        return create_response(None, "Invalid coordinates",
                             {"error": "latitude and longitude are required"}, 400)
    
    checkpoint_id = data.get('checkpoint_id')
    
    with data_lock:
        if quest_id not in quests:
            return create_response(None, "Quest not found",
                                 {"detail": "Quest not found"}, 404)
        
        quest = quests[quest_id]
        log_id = f"{user['id']}_{quest_id}"
        
        # Mock distance calculation
        distance = random.uniform(10, 150)
        
        if checkpoint_id:
            checkpoint = checkpoints.get(str(checkpoint_id))
            if not checkpoint:
                return create_response(None, "Checkpoint not found",
                                     {"detail": "Checkpoint not found"}, 404)
            is_valid = distance <= checkpoint['radius_meters']
            required_radius = checkpoint['radius_meters']
        else:
            is_valid = distance <= 100
            required_radius = 100
        
        if is_valid:
            # Record checkpoint visit
            if log_id not in quest_logs:
                quest_logs[log_id] = {
                    "id": log_id,
                    "user": user['id'],
                    "quest": quest,
                    "status": "in_progress",
                    "progress": 0,
                    "experience_earned": 0,
                    "start_time": generate_timestamp(),
                    "end_time": None
                }
            
            if checkpoint_id:
                visit_id = f"{log_id}_{checkpoint_id}"
                user_checkpoints[visit_id] = {
                    "id": visit_id,
                    "quest_log_id": log_id,
                    "checkpoint_id": checkpoint_id,
                    "visited_at": generate_timestamp(),
                    "latitude": user_lat,
                    "longitude": user_lng
                }
            
            # Count checkpoints
            quest_checkpoints = [cp for cp in checkpoints.values() if cp['quest_id'] == int(quest_id)]
            visited_count = len([uc for uc in user_checkpoints.values() 
                               if uc['quest_log_id'] == log_id])
            
            return create_response({
                "valid": True,
                "distance_meters": round(distance, 2),
                "checkpoint_completed": checkpoint_id is not None,
                "all_required_checkpoints_visited": visited_count >= len([
                    cp for cp in quest_checkpoints if cp['is_required']
                ])
            }, "Location validated successfully")
        
        return create_response({
            "valid": False,
            "distance_meters": round(distance, 2),
            "required_radius_meters": required_radius
        }, "Location validation failed", status_code=400)


# ========== GAMIFICATION ENDPOINTS ==========

@app.route('/api/v1/gamification/profile/', methods=['GET'])
@require_auth
def get_gamification_profile():
    """Get user's complete gamification profile."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        profile = user_profiles.get(user['id'], {
            "display_name": user['username'],
            "points": 0,
            "level": 1
        })
        
        # Calculate XP to next level
        next_level_xp = int(100 * (profile['level'] ** 1.5))
        
        # Count completed quests
        completed_quests = len([ql for ql in quest_logs.values() 
                               if ql['user'] == user['id'] and ql['status'] == 'completed'])
        
        # Count completed challenges
        completed_challenges = len([cl for cl in challenge_logs.values() 
                                   if cl['user'] == user['id'] and cl['completed_at']])
        
        # Get user's badges
        user_badge_list = [ub for ub in user_badges.values() if ub['user_id'] == user['id']]
        
        # Calculate environmental impact
        user_impacts = [ci for ci in carbon_impacts.values() if ci['user_id'] == user['id']]
        total_carbon = sum(imp['carbon_saved_kg'] for imp in user_impacts)
        total_trees = sum(imp['trees_equivalent'] for imp in user_impacts)
    
    return create_response({
        "level": profile['level'],
        "total_xp": profile['points'],
        "next_level_xp": next_level_xp,
        "xp_to_next_level": next_level_xp - profile['points'],
        "category_progress": [
            {"quest__quest_type": "outdoor", "count": completed_quests, "total_xp": profile['points']}
        ],
        "recent_badges": [
            {
                "badge": badges.get(str(ub['badge_id']), {}),
                "progress": ub['progress'],
                "progress_percentage": min(
                    100,
                    int((ub['progress'] / badges.get(str(ub['badge_id']), {}).get(
                        'requirement_value', 1)) * 100)
                ),
                "is_complete": ub['is_complete'],
                "earned_at": ub['earned_at']
            }
            for ub in sorted(user_badge_list, key=lambda x: x['earned_at'], reverse=True)[:5]
        ],
        "environmental_impact": {
            "total_carbon_saved": round(total_carbon, 4),
            "total_trees_equivalent": round(total_trees, 4)
        },
        "quests_completed": completed_quests,
        "challenges_completed": completed_challenges
    }, "Profile retrieved successfully")


@app.route('/api/v1/gamification/badges/', methods=['GET'])
@require_auth
def get_badges():
    """Get all badges with user's progress."""
    simulate_delay()
    user = request.current_user
    
    category = request.args.get('category')
    tier = request.args.get('tier')
    
    with data_lock:
        badge_list = list(badges.values())
        if category:
            badge_list = [b for b in badge_list if b['category'] == category]
        if tier:
            badge_list = [b for b in badge_list if b['tier'] == tier]
        
        # Get user's badge progress
        user_badge_dict = {ub['badge_id']: ub for ub in user_badges.values() if ub['user_id'] == user['id']}
        
        result = []
        for badge in badge_list:
            user_badge = user_badge_dict.get(badge['id'])
            result.append({
                "badge": badge,
                "progress": user_badge['progress'] if user_badge else 0,
                "is_complete": user_badge['is_complete'] if user_badge else False,
                "earned_at": user_badge['earned_at'] if user_badge else None
            })
    
    return create_response(result, "Badges retrieved successfully")


@app.route('/api/v1/gamification/leaderboards/', methods=['GET'])
@require_auth
def get_leaderboards():
    """Get leaderboard data."""
    simulate_delay()
    user = request.current_user
    
    leaderboard_type = request.args.get('type', 'global_xp')
    region = request.args.get('region', '')
    quest_type = request.args.get('quest_type')
    period = request.args.get('period', 'all_time')
    
    with data_lock:
        entries = [e for e in leaderboard_entries.values()
                  if e['leaderboard_type'] == leaderboard_type
                  and e['region'] == region
                  and e['period'] == period]
        
        if quest_type:
            entries = [e for e in entries if e['quest_type'] == quest_type]
        
        entries.sort(key=lambda x: x['rank'])
        entries = entries[:100]
        
        # Find user's rank
        user_entry = next((e for e in leaderboard_entries.values()
                          if e['user_id'] == user['id']
                          and e['leaderboard_type'] == leaderboard_type
                          and e['region'] == region
                          and e['period'] == period), None)
    
    return create_response({
        "leaderboard": [
            {
                "rank": e['rank'],
                "username": e['username'],
                "display_name": e['display_name'],
                "score": e['score'],
                "updated_at": e['updated_at']
            }
            for e in entries
        ],
        "user_rank": {
            "rank": user_entry['rank'],
            "score": user_entry['score']
        } if user_entry else None,
        "total_participants": len([e for e in leaderboard_entries.values()
                                   if e['leaderboard_type'] == leaderboard_type
                                   and e['region'] == region
                                   and e['period'] == period])
    }, "Leaderboard retrieved successfully")


@app.route('/api/v1/gamification/environmental-impact/', methods=['GET'])
@require_auth
def get_environmental_impact():
    """Get detailed environmental impact data."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        user_impacts = [ci for ci in carbon_impacts.values() if ci['user_id'] == user['id']]
        
        # Group by activity type
        impact_by_type = {}
        for imp in user_impacts:
            activity = imp['activity_type']
            if activity not in impact_by_type:
                impact_by_type[activity] = {
                    "total_carbon_saved": 0,
                    "total_trees": 0,
                    "total_distance": 0,
                    "quest_count": 0
                }
            impact_by_type[activity]['total_carbon_saved'] += imp['carbon_saved_kg']
            impact_by_type[activity]['total_trees'] += imp['trees_equivalent']
            impact_by_type[activity]['total_distance'] += imp['distance_km']
            impact_by_type[activity]['quest_count'] += 1
    
    return create_response({
        "impact_by_type": [
            {
                "activity_type": k,
                "total_carbon_saved": round(v['total_carbon_saved'], 4),
                "total_trees": round(v['total_trees'], 4),
                "total_distance": round(v['total_distance'], 2),
                "quest_count": v['quest_count']
            }
            for k, v in impact_by_type.items()
        ],
        "monthly_trends": [],  # Mock empty for now
        "total_impact": {
            "carbon_saved_kg": round(sum(imp['carbon_saved_kg'] for imp in user_impacts), 4),
            "trees_equivalent": round(sum(imp['trees_equivalent'] for imp in user_impacts), 4),
            "distance_km": round(sum(imp['distance_km'] for imp in user_impacts), 2)
        }
    }, "Environmental impact retrieved successfully")


# Helper function to update user badges after quest completion
def update_user_badges(user_id):
    """Check and update user badges after quest completion."""
    with data_lock:
        user = users.get(user_id)
        if not user:
            return
        
        profile = user_profiles.get(user_id, {"points": 0})
        
        # Count completed quests
        completed_quests = [ql for ql in quest_logs.values() 
                          if ql['user'] == user_id and ql['status'] == 'completed']
        quest_count = len(completed_quests)
        
        # Count outdoor quests
        outdoor_quests = len([ql for ql in completed_quests 
                             if ql['quest']['quest_type'] == 'outdoor'])
        
        # Check each badge
        for badge in badges.values():
            badge_id = badge['id']
            user_badge_id = f"{user_id}_{badge_id}"
            
            # Calculate progress
            if badge['requirement_type'] == 'quest_count':
                if badge['quest_type_filter']:
                    progress = outdoor_quests if badge['quest_type_filter'] == 'outdoor' else 0
                else:
                    progress = quest_count
            elif badge['requirement_type'] == 'xp_threshold':
                progress = profile['points']
            else:
                progress = 0
            
            is_complete = progress >= badge['requirement_value']
            
            # Update or create user badge
            if user_badge_id in user_badges:
                user_badges[user_badge_id]['progress'] = progress
                if is_complete and not user_badges[user_badge_id]['is_complete']:
                    user_badges[user_badge_id]['is_complete'] = True
                    user_badges[user_badge_id]['earned_at'] = generate_timestamp()
            else:
                user_badges[user_badge_id] = {
                    "id": user_badge_id,
                    "user_id": user_id,
                    "badge_id": badge_id,
                    "progress": progress,
                    "is_complete": is_complete,
                    "earned_at": generate_timestamp() if is_complete else None
                }


# Helper function to calculate carbon impact
def calculate_carbon_impact(quest_log):
    """Calculate environmental impact for a quest completion."""
    CARBON_RATES = {
        'outdoor': 0.12,
        'indoor': 0.08,
        'team': 0.10,
        'individual': 0.12,
    }
    
    quest = quest_log['quest']
    hours = quest['duration_minutes'] / 60
    estimated_distance = hours * 5  # km
    
    carbon_saved = estimated_distance * CARBON_RATES.get(quest['quest_type'], 0.10)
    trees_equivalent = carbon_saved / 22
    
    return {
        "activity_type": quest['quest_type'],
        "distance_km": estimated_distance,
        "carbon_saved_kg": carbon_saved,
        "trees_equivalent": trees_equivalent
    }


@app.route('/api/v1/quests/<quest_id>/complete/', methods=['POST'])
@require_auth
def complete_quest(quest_id):
    """Complete a quest with gamification processing."""
    simulate_delay()
    user = request.current_user
    
    with data_lock:
        log_id = f"{user['id']}_{quest_id}"
        if log_id not in quest_logs:
            return create_response(None, "Quest log not found",
                                 {"detail": "Quest has not been started"}, 400)
        
        quest_log = quest_logs[log_id]
        quest = quest_log['quest']
        
        # Update quest log
        quest_log['status'] = 'completed'
        quest_log['progress'] = 100
        quest_log['experience_earned'] = quest['experience_reward']
        quest_log['end_time'] = generate_timestamp()
        quest_log['updated_at'] = generate_timestamp()
        
        # Update user profile
        if user['id'] in user_profiles:
            user_profiles[user['id']]['points'] += quest['experience_reward']
            # Check for level up
            new_level = int((user_profiles[user['id']]['points'] / 100) ** (2/3))
            if new_level > user_profiles[user['id']]['level']:
                user_profiles[user['id']]['level'] = new_level
        
        # Calculate carbon impact
        impact = calculate_carbon_impact(quest_log)
        impact_id = generate_id()
        carbon_impacts[impact_id] = {
            "id": impact_id,
            "user_id": user['id'],
            "quest_log_id": log_id,
            **impact,
            "calculated_at": generate_timestamp()
        }
        
        # Update badges
        update_user_badges(user['id'])
    
    return create_response(quest_log, "Quest completed successfully")


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return create_response(None, "Not found", {"detail": "The requested resource was not found"}, 404)

@app.errorhandler(500)
def internal_error(error):
    return create_response(None, "Internal server error", {"detail": "An internal server error occurred"}, 500)

if __name__ == '__main__':
    init_sample_data()
    print("=" * 60)
    print("Nature Quest Mock Server")
    print("=" * 60)
    print("Endpoints:")
    print("  Health:    http://localhost:5000/api/v1/health/")
    print("  Auth:      http://localhost:5000/api/v1/users/auth/")
    print("  Quests:    http://localhost:5000/api/v1/quests/")
    print("  Challenges:http://localhost:5000/api/v1/challenges/")
    print("=" * 60)
    print("Sample users: Register a new user or use any email/password")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)
