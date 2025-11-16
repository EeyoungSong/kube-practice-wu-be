from django.contrib import admin
from .models import Word, Sentence, Wordbook, SentenceWord, Category

# Register your models here.
@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    search_fields = ["text", "user__username", "created_at", "last_reviewed_at", "review_count", "is_last_review_successful"]
    list_display = [
        "id",
        "text", 
        "user",
        "created_at",
        "last_reviewed_at",
        "review_count",
        "is_last_review_successful"
        ]
    list_filter = ["user", "created_at", "last_reviewed_at", "review_count", "is_last_review_successful"]
    

@admin.register(Sentence)
class SentenceAdmin(admin.ModelAdmin):
    search_fields = ["text", "meaning", "user", "created_at", "last_reviewed_at", "review_count", "is_last_review_successful"]
    list_display = [
        "id",
        "text", 
        "meaning",
        "user",
        "created_at",
        "last_reviewed_at",
        "review_count",
        "is_last_review_successful"
        ]
    list_filter = ["user", "created_at", "last_reviewed_at", "review_count", "is_last_review_successful"]


@admin.register(Wordbook)
class WordbookAdmin(admin.ModelAdmin):
    search_fields = ["name", "user__username", "created_at"]
    list_display = [
        "id",
        "name", 
        "user",
        "created_at",
        ]
    list_filter = ["user", "created_at"]


@admin.register(SentenceWord)
class SentenceWordAdmin(admin.ModelAdmin):
    search_fields = ["sentence__text", "word__text", "meaning"]
    list_display = [
        "id",
        "sentence", 
        "word",
        "meaning",
        ]
    list_filter = ["sentence", "word"]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name", "user__username"]
    list_display = [
        "id",
        "name", 
        "user",
        ]
    list_filter = ["user"]

