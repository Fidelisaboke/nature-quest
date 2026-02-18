from django.contrib import admin
from .models import Quest, Location, Challenge, QuestLog, ChallengeLog, TriviaQuestion


class ChallengeInline(admin.TabularInline):
    model = Quest.challenges.through
    extra = 1
    autocomplete_fields = ['challenge']


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    inlines = (ChallengeInline,)
    list_display = ('title', 'quest_type', 'difficulty', 'duration_minutes', 'experience_reward', 'is_active')
    list_filter = ('quest_type', 'difficulty', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('challenges',)  # We'll use the inline for this


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'address', 'source')
    list_filter = ('source',)
    search_fields = ('name', 'address')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_mandatory', 'experience_reward')
    list_filter = ('is_mandatory',)
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('quests',)


@admin.register(QuestLog)
class QuestLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'quest', 'status', 'progress', 'start_time', 'end_time', 'experience_earned')
    list_filter = ('status', 'quest')
    search_fields = ('user__username', 'quest__title')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'quest')


@admin.register(ChallengeLog)
class ChallengeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'completed_at', 'experience_earned')
    list_filter = ('challenge',)
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'challenge')


@admin.register(TriviaQuestion)
class TriviaQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'correct_answer')
    search_fields = ('question_text', 'correct_answer')
    readonly_fields = ('created_at', 'updated_at')
