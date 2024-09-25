# import os
# import logging
# import mimetypes
# import subprocess
# from google.cloud import speech_v1p1beta1 as speech
# from google.cloud import texttospeech

# # Set up logging
# logging.basicConfig(level=logging.DEBUG)

# # Factory Method for Google Cloud Clients
# class GoogleCloudClientFactory:
#     @staticmethod
#     def get_speech_client():
#         return speech.SpeechClient()

#     @staticmethod
#     def get_tts_client():
#         return texttospeech.TextToSpeechClient()

# # Service for Audio Transcription
# class TranscriptionService:
#     def __init__(self, client_factory):
#         self.speech_client = client_factory.get_speech_client()

#     def transcribe_audio(self, content, encoding, sample_rate_hertz=16000, language_code='en-US'):
#         audio = speech.RecognitionAudio(content=content)
#         config = speech.RecognitionConfig(
#             encoding=encoding,
#             sample_rate_hertz=sample_rate_hertz,
#             language_code=language_code
#         )
#         try:
#             response = self.speech_client.recognize(config=config, audio=audio)
#             transcription = ''.join([result.alternatives[0].transcript for result in response.results])
#             return transcription
#         except Exception as e:
#             logging.error(f"Transcription error: {str(e)}")
#             raise e

# # Service for Text-to-Speech
# class TextToSpeechService:
#     def __init__(self, client_factory):
#         self.tts_client = client_factory.get_tts_client()

#     def generate_audio(self, text, language_code='en-US', ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL):
#         input_text = texttospeech.SynthesisInput(text=text)
#         voice = texttospeech.VoiceSelectionParams(
#             language_code=language_code,
#             ssml_gender=ssml_gender
#         )
#         audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

#         try:
#             response = self.tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
#             return response.audio_content
#         except Exception as e:
#             logging.error(f"TTS error: {str(e)}")
#             raise e

# # Service for File Handling and Audio Conversion
# class AudioConversionService:
#     @staticmethod
#     def convert_webm_to_wav(input_path, output_path):
#         command = ['ffmpeg', '-y', '-i', input_path, '-ar', '16000', '-ac', '1', output_path]
#         try:
#             subprocess.run(command, check=True)
#             logging.info(f"Conversion to wav successful: {output_path}")
#             return True
#         except subprocess.CalledProcessError as e:
#             logging.error(f"Error converting file: {str(e)}")
#             return False

#     @staticmethod
#     def detect_mime_type(file_path):
#         return mimetypes.guess_type(file_path)[0]


# new code to do the thing
import os
import logging
import mimetypes
import subprocess
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
from django.core.files.storage import default_storage

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Factory Method for Google Cloud Clients
class GoogleCloudClientFactory:
    @staticmethod
    def get_speech_client():
        return speech.SpeechClient()

    @staticmethod
    def get_tts_client():
        return texttospeech.TextToSpeechClient()

# Service for Audio Transcription
class TranscriptionService:
    def __init__(self, client_factory):
        self.speech_client = client_factory.get_speech_client()

    def transcribe_audio(self, content, encoding, sample_rate_hertz=16000, language_code='en-US'):
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate_hertz,
            language_code=language_code
        )
        try:
            response = self.speech_client.recognize(config=config, audio=audio)
            transcription = ''.join([result.alternatives[0].transcript for result in response.results])
            return transcription
        except Exception as e:
            logging.error(f"Transcription error: {str(e)}")
            raise e

# Service for Text-to-Speech
class TextToSpeechService:
    def __init__(self, client_factory):
        self.tts_client = client_factory.get_tts_client()

    def generate_audio(self, text, language_code='en-US', ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL):
        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=ssml_gender
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        try:
            response = self.tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
            return response.audio_content
        except Exception as e:
            logging.error(f"TTS error: {str(e)}")
            raise e

# Service for File Handling and Audio Conversion
class AudioConversionService:
    @staticmethod
    def convert_webm_to_wav(input_path, output_path):
        # Get the absolute path of the input file
        abs_input_path = default_storage.path(input_path)

        # Ensure that the input file exists
        if not os.path.exists(abs_input_path):
            logging.error(f"Input file does not exist: {abs_input_path}")
            return False

        command = ['ffmpeg', '-y', '-i', abs_input_path, '-ar', '16000', '-ac', '1', output_path]
        
        # Log the full ffmpeg command for debugging
        logging.debug(f"Running ffmpeg command: {' '.join(command)}")

        try:
            subprocess.run(command, check=True)
            logging.info(f"Conversion to wav successful: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Error converting file: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during conversion: {str(e)}")
            return False

    @staticmethod
    def detect_mime_type(file_path):
        abs_file_path = default_storage.path(file_path)
        mime_type = mimetypes.guess_type(abs_file_path)[0]
        logging.debug(f"Detected MIME type for {file_path}: {mime_type}")
        return mime_type
