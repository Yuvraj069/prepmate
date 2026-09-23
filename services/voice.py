import os
import tempfile


class VoiceService:
    def __init__(self):
        self.key = os.getenv("AZURE_SPEECH_KEY")
        self.region = os.getenv("AZURE_SPEECH_REGION")

    @property
    def configured(self):
        return bool(self.key and self.region)

    def synthesize(self, text):
        if not self.configured:
            return None
        try:
            import azure.cognitiveservices.speech as speechsdk
            config = speechsdk.SpeechConfig(subscription=self.key, region=self.region)
            config.speech_synthesis_voice_name = os.getenv("AZURE_SPEECH_VOICE", "en-US-AvaMultilingualNeural")
            config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
            result = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None).speak_text_async(text).get()
            return result.audio_data if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted else None
        except Exception:
            return None

    def transcribe(self, upload, filename):
        if not self.configured:
            return None
        try:
            import azure.cognitiveservices.speech as speechsdk
            path = os.path.join(tempfile.gettempdir(), filename)
            upload.save(path)
            config = speechsdk.SpeechConfig(subscription=self.key, region=self.region)
            audio = speechsdk.audio.AudioConfig(filename=path)
            result = speechsdk.SpeechRecognizer(speech_config=config, audio_config=audio).recognize_once_async().get()
            try:
                os.remove(path)
            except OSError:
                pass
            return result.text if result.reason == speechsdk.ResultReason.RecognizedSpeech else None
        except Exception:
            return None
