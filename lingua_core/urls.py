from django.urls import path

from lingua_core.views import (
    # OcrView,
    # OcrSentenceView,
    SentenceAnalyzeView,
    # SentenceSplitView,
)

app_name = 'lingua_core'

urlpatterns = [
    # path('extract/ocr/', OcrView.as_view(), name='extract-ocr'),
    # path('extract/ocr/sentence/', OcrSentenceView.as_view(), name='extract-ocr-sentence'),
    path('analyze/sentences/', SentenceAnalyzeView.as_view(), name='extract-sentences'),
    # path('split/sentences/', SentenceSplitView.as_view(), name='extract-sentences-split'),
]
