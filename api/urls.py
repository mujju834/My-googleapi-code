from django.urls import path
from . import views

urlpatterns = [
    path('transcribe/', views.transcribe_audio, name='transcribe_audio'),
    path('generate-audio/', views.generate_audio, name='generate_audio'),
    path('record-transcribe/', views.record_transcribe, name='record_transcribe'),
    path('uploads/<str:filename>/', views.download_file, name='download_file'),
]
