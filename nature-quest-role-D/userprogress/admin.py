from django.contrib import admin
from .models import UserProfile, Badge, Level, UserBadge, PointsTransaction


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['level_number', 'name', 'points_required']
    ordering = ['level_number']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['animal', 'name', 'points_required', 'is_special']
    list_filter = ['is_special']
    ordering = ['points_required']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_techie', 'total_points', 'current_level', 
                   'challenges_completed', 'quizzes_completed']
    list_filter = ['is_techie', 'current_level']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at', 'points_when_earned']
    list_filter = ['badge', 'earned_at']
    search_fields = ['user__username']
    readonly_fields = ['earned_at']


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'points', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']
