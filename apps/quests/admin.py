from django.contrib import admin
from .models import Quest, Location, Challenge, QuestLog, ChallengeLog, TriviaQuestion
# Register your models here.
class ChallengeInline(admin.TabularInline):
    model = Challenge
    extra = 1
    ordering = ('order',)

@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    inlines = (ChallengeInline,)
    list_display = ('title', 'quest_type', 'difficulty', 'duration_minutes', 'experience_reward', 'is_active')
    list_filter = ('quest_type', 'difficulty', 'is_active')
    search_fields = ('title', 'description')
    filter_horizontal = ('challenges',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'address', 'source', 'metadata')
    list_filter = ('source',)
    search_fields = ('name', 'address')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'quest', 'order')
    list_filter = ('quest',)
    search_fields = ('title', 'quest__title')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(QuestLog)
class QuestLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'quest', 'status', 'start_time', 'end_time', 'experience_earned')
    list_filter = ('user', 'quest', 'status')
    search_fields = ('user__username', 'quest__title')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ChallengeLog)
class ChallengeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'completed_at', 'experience_earned')
    list_filter = ('user', 'challenge')
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TriviaQuestion)
class TriviaQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'correct_answer', 'tags')
    list_filter = ('tags',)
    search_fields = ('question_text', 'correct_answer')
    readonly_fields = ('created_at', 'updated_at')
