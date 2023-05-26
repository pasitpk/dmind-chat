import io
import pydub
from google.cloud import speech
from google.oauth2.service_account import Credentials
# import speech_recognition as sr

class ASRPipe:

    def __init__(self, cred_file):
        # self.recognizer = sr.Recognizer()
        creds = Credentials.from_service_account_file(cred_file)
        self.client = speech.SpeechClient(credentials=creds)
   
    def transcribe(self, message_content):
        audio = self.get_audio(message_content)
        text = self.transcribe_audio_file(audio)
        return text

    def transcribe_audio_file(self, audio_file):
        # audio = sr.AudioFile(audio_file)
        # with audio as source:
        #     audio_data = self.recognizer.record(audio)
        # transcript = self.recognizer.recognize_whisper_api(audio_data, api_key=self.api_key)
        audio = speech.RecognitionAudio(content=audio_file.read())
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="th-TH",
        )
        response = self.client.recognize(config=config, audio=audio)
        transcript = ' '.join([result.alternatives[0].transcript for result in response.results])
        return transcript

    def get_audio(self, message_content):
        with io.BytesIO() as fd:
            for chunk in message_content.iter_content():
                fd.write(chunk)
            fd.seek(0)
            audio = pydub.AudioSegment.from_file(fd)
        return audio.export(format="wav")
