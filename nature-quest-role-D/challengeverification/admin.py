from django.contrib import admin
from .models import (
    Challenge, ChallengeAttempt, PhotoAnalysis, 
    LocationVerification, VerificationMetrics, FraudDetection
)

# Simple admin registration - will enhance later
admin.site.register(Challenge)
admin.site.register(ChallengeAttempt)
admin.site.register(PhotoAnalysis)
admin.site.register(LocationVerification)
admin.site.register(VerificationMetrics)
admin.site.register(FraudDetection)
