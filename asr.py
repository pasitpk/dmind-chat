import io
import torch
import pydub

from transformers import pipeline

class ASRPipe:

    def __init__(self, asr_pipe_path):

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.pipe = pipeline("automatic-speech-recognition",
                                model=asr_pipe_path,
                                device=device,
                                )
   
    def transcribe(self, message_content):
        audio = self.get_audio(message_content)
        text = self.pipe(audio)['text']
        return text

    def get_audio(self, message_content):
        with io.BytesIO() as fd:
            for chunk in message_content.iter_content():
                fd.write(chunk)
            fd.seek(0)
            audio = pydub.AudioSegment.from_file(fd)
        return audio.export(format="wav").read()