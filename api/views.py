import os
import io
import mimetypes
import subprocess
import logging
import json  # For JSON parsing

from django.http import JsonResponse, FileResponse, Http404
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
from dotenv import load_dotenv
from .services import GoogleCloudClientFactory, TranscriptionService, TextToSpeechService, AudioConversionService
from django.conf import settings
from django.shortcuts import render

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)


def index(request):
    """Render the main index page."""
    return render(request, 'index.html')


# Endpoint to transcribe audio from file upload
@csrf_exempt
def transcribe_audio(request):
    """Transcribes an uploaded audio file."""
    if request.method == 'POST' and 'audio' in request.FILES:
        file = request.FILES['audio']
        file_path = default_storage.save(file.name, file)

        mime_type = AudioConversionService.detect_mime_type(file_path)
        logging.debug(f"Detected MIME type: {mime_type}")

        if mime_type == 'audio/mpeg':
            encoding = speech.RecognitionConfig.AudioEncoding.MP3
        elif mime_type in ['audio/wav', 'audio/x-wav']:
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        else:
            logging.error(f"Unsupported audio format: {mime_type}")
            return JsonResponse({'error': 'Unsupported audio format'}, status=400)

        try:
            with default_storage.open(file_path, 'rb') as audio_file:
                content = audio_file.read()

            transcription_service = TranscriptionService(GoogleCloudClientFactory)
            transcription = transcription_service.transcribe_audio(content, encoding)

            logging.debug(f"Transcription: {transcription}")
            return JsonResponse({'transcription': transcription})

        except Exception as e:
            logging.error(f"Error during transcription: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'No audio file uploaded'}, status=400)


# Endpoint to generate audio from text
@csrf_exempt
def generate_audio(request):
    """Converts text input into audio using Google Cloud Text-to-Speech API."""
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body.decode('utf-8'))
            text = data.get('text', '')
            if not text:
                logging.error("No text input provided")
                return JsonResponse({'error': 'Text input is required'}, status=400)

            logging.debug(f"Text to be converted: {text}")

            tts_service = TextToSpeechService(GoogleCloudClientFactory)
            audio_content = tts_service.generate_audio(text)

            # Generate a filename and save the audio file
            filename = f"{text[:10]}.mp3"
            file_path = os.path.join(settings.MEDIA_ROOT, filename)

            with default_storage.open(file_path, 'wb') as out_file:
                out_file.write(audio_content)

            logging.debug(f"Audio file saved: {file_path}")
            return JsonResponse({'audioFile': f"{settings.MEDIA_URL}{filename}"})

        except json.JSONDecodeError:
            logging.error("Invalid JSON in request")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logging.error(f"Error generating audio: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


# Endpoint to transcribe recorded audio (e.g., webm)
@csrf_exempt
def record_transcribe(request):
    if request.method == 'POST' and 'audio' in request.FILES:
        file = request.FILES['audio']
        file_path = default_storage.save(file.name, file)

        logging.debug(f"Saved file at: {file_path}")  # Log the saved file path

        mime_type = AudioConversionService.detect_mime_type(file_path)
        logging.debug(f"Detected MIME type: {mime_type}")

        if mime_type == 'video/webm':
            wav_filename = file_path.rsplit('.', 1)[0] + '.wav'
            wav_file_path = os.path.join(settings.MEDIA_ROOT, wav_filename)
            logging.debug(f"Converting {file_path} to {wav_file_path}")

            if not AudioConversionService.convert_webm_to_wav(file_path, wav_file_path):
                logging.error("Failed to convert webm to wav")
                return JsonResponse({'error': 'Failed to convert webm to wav'}, status=500)

            file_path = wav_file_path
            mime_type = 'audio/wav'

        try:
            with default_storage.open(file_path, 'rb') as audio_file:
                content = audio_file.read()

            transcription_service = TranscriptionService(GoogleCloudClientFactory)
            transcription = transcription_service.transcribe_audio(content, speech.RecognitionConfig.AudioEncoding.LINEAR16)

            logging.debug(f"Transcription: {transcription}")
            return JsonResponse({'transcription': transcription})

        except Exception as e:
            logging.error(f"Error during transcription: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


# Serve uploaded files
def download_file(request, filename):
    """Serve uploaded files from the MEDIA_ROOT."""
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if default_storage.exists(file_path):
        logging.debug(f"Serving file: {file_path}")
        return FileResponse(default_storage.open(file_path, 'rb'))
    else:
        logging.error(f"File not found: {file_path}")
        raise Http404("File not found")
