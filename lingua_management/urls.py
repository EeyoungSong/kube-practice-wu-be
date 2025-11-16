from django.urls import path

from .views.wordbook_views import (
    WordbookListView,
    WordbookCreateView,
    WordbookDetailView,
)
from .views.word_views import WordManageView, WordContextWithTextView
from .views.sentence_views import SentenceManageView
from .views.category_views import CategoryListView
from .views.review_views import (
    get_wordbook_review_words_with_id,
    submit_wordbook_review,
    get_wordbook_review_words,
    GraphDataView,
)

app_name = 'lingua_management'

urlpatterns = [
    # 1. Management APIs - Wordbook
    path('wordbooks/', WordbookListView.as_view(), name='wordbook-list'),
    path('wordbooks/save/', WordbookCreateView.as_view(), name='wordbook-create'),
    path('wordbooks/<int:wordbook_id>/', WordbookDetailView.as_view(), name='wordbook-detail'),

    # 2. Management APIs - Word
    path('words/<int:word_id>/', WordManageView.as_view(), name='word-detail'),
    path('words/context/', WordContextWithTextView.as_view(), name='word-context-with-text'),

    # 3. Management APIs - Sentence
    path('sentences/<int:sentence_id>/', SentenceManageView.as_view(), name='sentence-detail'),

    # 4. Management APIs - Category
    path('categories/', CategoryListView.as_view(), name='category-list'),

    # 5. Management APIs - Language
    # path('languages/', LanguageListView.as_view(), name='language-list'),

    # 6. Review APIs
    path('wordbooks/review/<int:wordbook_id>/', get_wordbook_review_words_with_id, name='wordbook-review-words'),
    path('wordbooks/review/', get_wordbook_review_words, name='category-review-words'),
    path('wordbooks/<int:wordbook_id>/review/submit/', submit_wordbook_review, name='submit-wordbook-review'),

    path('graph/', GraphDataView.as_view(), name='graph-data'),
]
