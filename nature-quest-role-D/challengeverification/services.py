import requests
import json
import cv2
import numpy as np
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import exifread
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone as django_timezone
from django.core.files.base import ContentFile

from .models import Challenge, ChallengeAttempt, PhotoAnalysis, LocationVerification, FraudDetection

logger = logging.getLogger(__name__)


class PhotoVerificationService:
    """Service for analyzing and verifying submitted photos"""
    
    def __init__(self):
        self.quality_threshold = 0.6
        self.authenticity_threshold = 0.7
    
    def analyze_photo(self, image_file, challenge: Challenge) -> Dict[str, Any]:
        """
        Comprehensive photo analysis including EXIF, quality, and content
        """
        try:
            # Read image
            image = Image.open(image_file)
            image_array = np.array(image)
            
            # Reset file pointer for EXIF reading
            image_file.seek(0)
            
            analysis_results = {
                'exif_data': self._extract_exif_data(image_file),
                'quality_score': self._calculate_image_quality(image_array),
                'authenticity_score': self._check_authenticity(image_array),
                'detected_objects': self._detect_nature_elements(image_array),
                'timestamp_valid': False,
                'location_from_exif': None,
                'has_required_elements': False
            }
            
            # Validate timestamp (photo should be recent)
            if analysis_results['exif_data'].get('timestamp'):
                analysis_results['timestamp_valid'] = self._validate_timestamp(
                    analysis_results['exif_data']['timestamp']
                )
            
            # Check for required elements
            if challenge.required_elements:
                analysis_results['has_required_elements'] = self._check_required_elements(
                    analysis_results['detected_objects'], challenge.required_elements
                )
            else:
                analysis_results['has_required_elements'] = True  # No specific requirements
            
            # Overall verification score
            analysis_results['verification_passed'] = (
                analysis_results['quality_score'] >= self.quality_threshold and
                analysis_results['authenticity_score'] >= self.authenticity_threshold and
                analysis_results['timestamp_valid'] and
                analysis_results['has_required_elements']
            )
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing photo: {str(e)}")
            return {
                'error': str(e),
                'verification_passed': False
            }
    
    def _extract_exif_data(self, image_file) -> Dict[str, Any]:
        """Extract EXIF metadata from image"""
        exif_data = {
            'has_exif': False,
            'timestamp': None,
            'gps_coordinates': None,
            'camera_info': {},
            'technical_details': {}
        }
        
        try:
            # Using PIL for basic EXIF
            image = Image.open(image_file)
            exif = image.getexif()
            
            if exif:
                exif_data['has_exif'] = True
                
                # Extract basic info
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    if tag == 'DateTime':
                        try:
                            exif_data['timestamp'] = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            pass
                    elif tag in ['Make', 'Model']:
                        exif_data['camera_info'][tag.lower()] = str(value)
                    elif tag in ['ExposureTime', 'FNumber', 'ISO']:
                        exif_data['technical_details'][tag.lower()] = str(value)
                
                # Extract GPS data if available
                gps_info = exif.get_ifd(0x8825)  # GPS IFD
                if gps_info:
                    gps_coords = self._parse_gps_data(gps_info)
                    if gps_coords:
                        exif_data['gps_coordinates'] = gps_coords
            
            # Reset file pointer
            image_file.seek(0)
            
            # Try exifread for more detailed extraction
            try:
                tags = exifread.process_file(image_file)
                if tags:
                    exif_data['detailed_tags'] = {str(k): str(v) for k, v in tags.items()}
            except Exception:
                pass
            
        except Exception as e:
            logger.warning(f"Error extracting EXIF data: {str(e)}")
        
        return exif_data
    
    def _parse_gps_data(self, gps_info) -> Optional[Dict[str, float]]:
        """Parse GPS coordinates from EXIF GPS data"""
        try:
            def convert_to_degrees(value):
                """Convert GPS coordinate to decimal degrees"""
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = gps_info.get(2)  # GPSLatitude
            lat_ref = gps_info.get(1)  # GPSLatitudeRef
            lon = gps_info.get(4)  # GPSLongitude
            lon_ref = gps_info.get(3)  # GPSLongitudeRef
            
            if lat and lon and lat_ref and lon_ref:
                latitude = convert_to_degrees(lat)
                longitude = convert_to_degrees(lon)
                
                if lat_ref == 'S':
                    latitude = -latitude
                if lon_ref == 'W':
                    longitude = -longitude
                
                return {'latitude': latitude, 'longitude': longitude}
        
        except Exception as e:
            logger.warning(f"Error parsing GPS data: {str(e)}")
        
        return None
    
    def _calculate_image_quality(self, image_array: np.ndarray) -> float:
        """Calculate image quality score based on various metrics"""
        try:
            # Convert to grayscale for analysis
            if len(image_array.shape) == 3:
                gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_array
            
            # Calculate sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000.0, 1.0)  # Normalize
            
            # Calculate brightness and contrast
            brightness = np.mean(gray) / 255.0
            contrast = np.std(gray) / 255.0
            
            # Check resolution
            height, width = gray.shape
            resolution_score = min((height * width) / (1920 * 1080), 1.0)  # Normalize to Full HD
            
            # Combine scores
            quality_score = (
                sharpness_score * 0.4 +
                min(brightness, 1.0 - brightness) * 0.2 +  # Penalize too bright/dark
                contrast * 0.2 +
                resolution_score * 0.2
            )
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating image quality: {str(e)}")
            return 0.0
    
    def _check_authenticity(self, image_array: np.ndarray) -> float:
        """Basic authenticity checks for image manipulation"""
        try:
            authenticity_score = 1.0
            
            # Check for obvious digital artifacts
            # This is a simplified implementation
            
            # 1. Check for JPEG compression artifacts
            # 2. Analyze noise patterns
            # 3. Look for inconsistent lighting
            # 4. Check metadata consistency
            
            # For now, return a baseline score
            # In production, you'd want more sophisticated detection
            
            return authenticity_score
            
        except Exception as e:
            logger.error(f"Error checking authenticity: {str(e)}")
            return 0.0
    
    def _detect_nature_elements(self, image_array: np.ndarray) -> List[Dict[str, Any]]:
        """Detect nature elements in the image"""
        detected_elements = []
        
        try:
            # Simplified nature detection
            # In production, you'd use a trained model like YOLO or a nature-specific classifier
            
            # Basic color analysis for nature detection
            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
            
            # Green detection (vegetation)
            lower_green = np.array([35, 40, 40])
            upper_green = np.array([85, 255, 255])
            green_mask = cv2.inRange(hsv, lower_green, upper_green)
            green_percentage = np.sum(green_mask > 0) / green_mask.size
            
            if green_percentage > 0.1:  # 10% green
                detected_elements.append({
                    'element': 'vegetation',
                    'confidence': min(green_percentage * 2, 1.0),
                    'description': 'Green vegetation detected'
                })
            
            # Blue detection (water/sky)
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            blue_percentage = np.sum(blue_mask > 0) / blue_mask.size
            
            if blue_percentage > 0.15:  # 15% blue
                detected_elements.append({
                    'element': 'water_or_sky',
                    'confidence': min(blue_percentage * 1.5, 1.0),
                    'description': 'Water or sky detected'
                })
            
            # Brown detection (earth/rocks)
            lower_brown = np.array([10, 30, 30])
            upper_brown = np.array([25, 255, 200])
            brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
            brown_percentage = np.sum(brown_mask > 0) / brown_mask.size
            
            if brown_percentage > 0.1:  # 10% brown
                detected_elements.append({
                    'element': 'earth_or_rocks',
                    'confidence': min(brown_percentage * 2, 1.0),
                    'description': 'Earth or rock formations detected'
                })
            
        except Exception as e:
            logger.error(f"Error detecting nature elements: {str(e)}")
        
        return detected_elements
    
    def _validate_timestamp(self, timestamp: datetime) -> bool:
        """Validate that photo was taken recently"""
        try:
            now = datetime.now()
            time_diff = now - timestamp
            
            # Allow photos taken within the last 24 hours
            return time_diff <= timedelta(hours=24)
            
        except Exception:
            return False
    
    def _check_required_elements(self, detected_elements: List[Dict], 
                               required_elements: List[str]) -> bool:
        """Check if detected elements match required elements"""
        try:
            detected_types = [elem['element'] for elem in detected_elements]
            
            # Simple matching - can be made more sophisticated
            for required in required_elements:
                found = any(required.lower() in detected.lower() or 
                          detected.lower() in required.lower() 
                          for detected in detected_types)
                if not found:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking required elements: {str(e)}")
            return False


class LocationVerificationService:
    """Service for verifying location using Foursquare API and geographic validation"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'FOURSQUARE_API_KEY', '')
        self.base_url = "https://api.foursquare.com/v3/places"
    
    def verify_location(self, latitude: float, longitude: float, 
                       challenge: Challenge) -> Dict[str, Any]:
        """
        Verify location using Foursquare API and geographic checks
        """
        verification_results = {
            'is_valid_coordinate': self._validate_coordinates(latitude, longitude),
            'foursquare_verification': None,
            'location_type_match': False,
            'distance_to_target': None,
            'confidence_score': 0.0,
            'verification_passed': False
        }
        
        if not verification_results['is_valid_coordinate']:
            verification_results['error'] = 'Invalid coordinates'
            return verification_results
        
        try:
            # Verify with Foursquare
            foursquare_result = self._verify_with_foursquare(
                latitude, longitude, challenge
            )
            verification_results['foursquare_verification'] = foursquare_result
            
            if foursquare_result.get('success'):
                verification_results['location_type_match'] = foursquare_result.get('type_match', False)
                verification_results['distance_to_target'] = foursquare_result.get('distance', float('inf'))
                
                # Calculate confidence based on distance and type match
                distance = verification_results['distance_to_target']
                if distance <= challenge.verification_radius:
                    base_confidence = 1.0 - (distance / challenge.verification_radius)
                    if verification_results['location_type_match']:
                        verification_results['confidence_score'] = min(base_confidence + 0.2, 1.0)
                    else:
                        verification_results['confidence_score'] = base_confidence * 0.7
                
                # Pass if within radius and reasonable confidence
                verification_results['verification_passed'] = (
                    distance <= challenge.verification_radius and
                    verification_results['confidence_score'] >= 0.6
                )
            
        except Exception as e:
            logger.error(f"Error in location verification: {str(e)}")
            verification_results['error'] = str(e)
        
        return verification_results
    
    def _validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """Basic coordinate validation"""
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)
    
    def _verify_with_foursquare(self, latitude: float, longitude: float, 
                              challenge: Challenge) -> Dict[str, Any]:
        """Verify location using Foursquare Places API"""
        if not self.api_key:
            return {'success': False, 'error': 'Foursquare API key not configured'}
        
        try:
            headers = {
                'Authorization': self.api_key,
                'Accept': 'application/json'
            }
            
            # Search for nearby places
            params = {
                'll': f"{latitude},{longitude}",
                'radius': challenge.verification_radius,
                'limit': 10
            }
            
            # Add category filter based on location type
            category = self._map_location_type_to_foursquare_category(challenge.location_type)
            if category:
                params['categories'] = category
            
            response = requests.get(
                f"{self.base_url}/nearby",
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                places = data.get('results', [])
                
                if places:
                    closest_place = places[0]  # Foursquare returns sorted by distance
                    
                    # Calculate distance (Foursquare provides this)
                    distance = closest_place.get('distance', float('inf'))
                    
                    # Check if location type matches
                    place_categories = [cat.get('name', '').lower() 
                                      for cat in closest_place.get('categories', [])]
                    type_match = self._check_location_type_match(
                        challenge.location_type, place_categories
                    )
                    
                    return {
                        'success': True,
                        'closest_place': closest_place,
                        'distance': distance,
                        'type_match': type_match,
                        'all_places': places
                    }
                else:
                    return {
                        'success': False,
                        'error': f'No {challenge.location_type} found within {challenge.verification_radius}m'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Foursquare API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Foursquare API error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _map_location_type_to_foursquare_category(self, location_type: str) -> str:
        """Map our location types to Foursquare category IDs"""
        category_mapping = {
            'park': '16032',
            'forest': '16019', 
            'lake': '16043',
            'mountain': '16038',
            'beach': '16044',
            'garden': '16032',
            'trail': '16019',
            'wildlife_area': '16022',
            'nature_reserve': '16022',
            'river': '16043',
            'waterfall': '16043',
            'desert': '16019'
        }
        return category_mapping.get(location_type.lower(), '')
    
    def _check_location_type_match(self, expected_type: str, 
                                 place_categories: List[str]) -> bool:
        """Check if place categories match expected location type"""
        expected_keywords = {
            'park': ['park', 'recreation', 'green'],
            'forest': ['forest', 'woods', 'wilderness', 'nature'],
            'lake': ['lake', 'water', 'reservoir'],
            'mountain': ['mountain', 'hill', 'peak', 'summit'],
            'beach': ['beach', 'shore', 'coast', 'seaside'],
            'garden': ['garden', 'botanical', 'park'],
            'trail': ['trail', 'path', 'hiking', 'walking'],
            'wildlife_area': ['wildlife', 'sanctuary', 'preserve'],
            'nature_reserve': ['reserve', 'preserve', 'conservation'],
            'river': ['river', 'stream', 'creek', 'water'],
            'waterfall': ['waterfall', 'falls', 'cascade'],
            'desert': ['desert', 'arid', 'dry']
        }
        
        keywords = expected_keywords.get(expected_type.lower(), [expected_type.lower()])
        
        for category in place_categories:
            if any(keyword in category.lower() for keyword in keywords):
                return True
        
        return False


class FraudDetectionService:
    """Service for detecting fraudulent or suspicious challenge submissions"""
    
    def __init__(self):
        self.image_hash_cache = {}  # In production, use Redis or database
    
    def analyze_submission(self, attempt: ChallengeAttempt) -> Dict[str, Any]:
        """Analyze submission for potential fraud"""
        risk_factors = []
        risk_score = 0.0
        
        try:
            # Check for duplicate images
            duplicate_check = self._check_duplicate_image(attempt.submitted_photo)
            if duplicate_check['is_duplicate']:
                risk_factors.append('Duplicate image detected')
                risk_score += 0.4
            
            # Check submission patterns
            rapid_submission_check = self._check_rapid_submissions(attempt.user)
            if rapid_submission_check['is_suspicious']:
                risk_factors.append('Suspicious submission pattern')
                risk_score += 0.3
            
            # Check location plausibility
            location_check = self._check_location_plausibility(attempt)
            if location_check['is_suspicious']:
                risk_factors.append('Implausible location pattern')
                risk_score += 0.3
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = 'critical'
            elif risk_score >= 0.6:
                risk_level = 'high'
            elif risk_score >= 0.3:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'risk_factors': risk_factors,
                'requires_manual_review': risk_score >= 0.6,
                'duplicate_image_detected': duplicate_check['is_duplicate'],
                'suspicious_location': location_check['is_suspicious'],
                'rapid_submissions': rapid_submission_check['is_suspicious']
            }
            
        except Exception as e:
            logger.error(f"Error in fraud detection: {str(e)}")
            return {
                'risk_level': 'low',
                'risk_score': 0.0,
                'risk_factors': [],
                'requires_manual_review': False,
                'error': str(e)
            }
    
    def _check_duplicate_image(self, image_file) -> Dict[str, Any]:
        """Check if image has been submitted before using perceptual hashing"""
        try:
            # Calculate image hash
            image = Image.open(image_file)
            image_hash = self._calculate_image_hash(image)
            
            # Check against known hashes (simplified - use database in production)
            for existing_hash in self.image_hash_cache:
                if self._hash_similarity(image_hash, existing_hash) > 0.9:
                    return {
                        'is_duplicate': True,
                        'similarity': self._hash_similarity(image_hash, existing_hash)
                    }
            
            # Store hash for future comparisons
            self.image_hash_cache[image_hash] = django_timezone.now()
            
            return {'is_duplicate': False}
            
        except Exception as e:
            logger.error(f"Error checking duplicate image: {str(e)}")
            return {'is_duplicate': False, 'error': str(e)}
    
    def _calculate_image_hash(self, image: Image.Image) -> str:
        """Calculate perceptual hash of image"""
        try:
            # Resize to small size
            image = image.resize((8, 8), Image.LANCZOS).convert('L')
            
            # Calculate average pixel value
            pixels = list(image.getdata())
            avg = sum(pixels) / len(pixels)
            
            # Create hash based on pixels above/below average
            hash_bits = ''.join('1' if pixel > avg else '0' for pixel in pixels)
            return hash_bits
            
        except Exception:
            return ''
    
    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two hashes"""
        if len(hash1) != len(hash2):
            return 0.0
        
        matches = sum(a == b for a, b in zip(hash1, hash2))
        return matches / len(hash1)
    
    def _check_rapid_submissions(self, user: User) -> Dict[str, Any]:
        """Check for suspiciously rapid submissions"""
        try:
            # Check submissions in last hour
            one_hour_ago = django_timezone.now() - timedelta(hours=1)
            recent_submissions = ChallengeAttempt.objects.filter(
                user=user,
                created_at__gte=one_hour_ago
            ).count()
            
            # Flag if more than 5 submissions in an hour
            is_suspicious = recent_submissions > 5
            
            return {
                'is_suspicious': is_suspicious,
                'recent_count': recent_submissions
            }
            
        except Exception as e:
            logger.error(f"Error checking rapid submissions: {str(e)}")
            return {'is_suspicious': False}
    
    def _check_location_plausibility(self, attempt: ChallengeAttempt) -> Dict[str, Any]:
        """Check if location submissions are plausible"""
        try:
            # Check if user has multiple submissions from the exact same coordinates
            same_location_count = ChallengeAttempt.objects.filter(
                user=attempt.user,
                submitted_latitude=attempt.submitted_latitude,
                submitted_longitude=attempt.submitted_longitude
            ).exclude(id=attempt.id).count()
            
            # Check if user is "teleporting" between distant locations quickly
            last_attempt = ChallengeAttempt.objects.filter(
                user=attempt.user,
                created_at__lt=attempt.created_at
            ).order_by('-created_at').first()
            
            suspicious_travel = False
            if last_attempt:
                time_diff = (attempt.created_at - last_attempt.created_at).total_seconds() / 3600  # hours
                distance = self._calculate_distance(
                    last_attempt.submitted_latitude, last_attempt.submitted_longitude,
                    attempt.submitted_latitude, attempt.submitted_longitude
                )
                
                # Flag if travel speed > 100 km/h (unrealistic for nature activities)
                if time_diff > 0 and distance / time_diff > 100:
                    suspicious_travel = True
            
            is_suspicious = same_location_count > 3 or suspicious_travel
            
            return {
                'is_suspicious': is_suspicious,
                'same_location_count': same_location_count,
                'suspicious_travel': suspicious_travel
            }
            
        except Exception as e:
            logger.error(f"Error checking location plausibility: {str(e)}")
            return {'is_suspicious': False}
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers"""
        try:
            from math import radians, sin, cos, sqrt, atan2
            
            R = 6371  # Earth's radius in km
            
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            return R * c
            
        except Exception:
            return 0.0
