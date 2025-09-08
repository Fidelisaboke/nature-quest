from django.contrib import admin
from .models import Quiz, Question, QuizAttempt, QuestionResponse, QuestionBank, QuizMetrics


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'tech_stack', 'difficulty', 'score', 'passed', 'created_at', 'completed_at']
    list_filter = ['difficulty', 'tech_stack', 'passed', 'created_at']
    search_fields = ['user__username', 'tech_stack']
    readonly_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'quiz', 'question_type', 'tech_stack', 'difficulty', 'order']
    list_filter = ['question_type', 'tech_stack', 'difficulty']
    search_fields = ['question_text', 'tech_stack']
    ordering = ['quiz', 'order']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'quiz', 'user', 'total_score', 'started_at', 'submitted_at']
    list_filter = ['started_at', 'submitted_at']
    search_fields = ['quiz__user__username']
    readonly_fields = ['started_at', 'submitted_at']
    
    def user(self, obj):
        return obj.quiz.user.username
    user.short_description = 'User'

@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ['id', 'attempt', 'question_text', 'is_correct', 'points_earned', 'answered_at']
    list_filter = ['is_correct', 'answered_at']
    readonly_fields = ['answered_at']
    
    def question_text(self, obj):
        return obj.question.question_text[:50] + "..." if len(obj.question.question_text) > 50 else obj.question.question_text
    question_text.short_description = 'Question'


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ['id', 'tech_stack', 'difficulty', 'question_type', 'times_used', 
                   'quality_score', 'generated_by_hf', 'is_active']
    list_filter = ['tech_stack', 'difficulty', 'question_type', 'generated_by_hf', 'is_active']
    search_fields = ['question_text', 'tech_stack']
    readonly_fields = ['created_at', 'updated_at', 'times_used']
    ordering = ['-created_at']


@admin.register(QuizMetrics)
class QuizMetricsAdmin(admin.ModelAdmin):
    list_display = ['tech_stack', 'difficulty', 'total_quizzes', 'total_passes', 
                   'pass_rate_display', 'average_score', 'last_updated']
    list_filter = ['tech_stack', 'difficulty', 'last_updated']
    readonly_fields = ['last_updated']
    
    def pass_rate_display(self, obj):
        return f"{obj.pass_rate:.1f}%"
    pass_rate_display.short_description = 'Pass Rate'
