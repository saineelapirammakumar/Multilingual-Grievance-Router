"""No implicit downloads. Configure a local CTranslate2 faster-whisper model."""
import os,threading
from functools import lru_cache
_lock=threading.Lock()
@lru_cache(maxsize=1)
def get_model(path):
    from faster_whisper import WhisperModel
    return WhisperModel(path,device='cpu',compute_type='int8',local_files_only=True,cpu_threads=2)
def transcribe_audio(path, language=None):
    model_path=os.getenv('ASR_MODEL_PATH','')
    if not model_path:raise RuntimeError('ASR unavailable: install optional dependencies and set ASR_MODEL_PATH to a local model directory.')
    try:model=get_model(model_path)
    except (ImportError,OSError,ValueError,RuntimeError) as e:raise RuntimeError('ASR model could not be loaded locally.') from e
    try:
        import av
        with av.open(path) as container:
            # Decode a bounded clip to verify duration before Whisper inference.
            stream=container.streams.audio[0];seconds=0
            for frame in container.decode(stream):
                seconds+=frame.samples/frame.sample_rate
                if seconds>120:raise ValueError('Audio exceeds the 120-second limit')
        with _lock:
            # A user-selected language is a decoding hint, not a forced transcript translation.
            # Whisper uses ISO-639-1 language codes for Hindi and Tamil.
            language_code = {'English': 'en', 'Hindi': 'hi', 'Tamil': 'ta'}.get(language, language)
            segments,info=model.transcribe(
                path,
                language=language_code or None,
                task='transcribe',
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
                without_timestamps=True,
            )
            text=' '.join(s.text.strip() for s in segments).strip()
        if len(text)<2:raise ValueError('No speech detected; try a clearer recording or enter text.')
        if len(text)>5000:raise ValueError('Transcript exceeds 5000 characters')
        return text,getattr(info,'language',None)
    except (ImportError,TypeError,AttributeError) as e:raise RuntimeError('ASR runtime dependency incompatibility; use requirements-optional.txt.') from e
    except (ValueError,IndexError) as e:raise ValueError(str(e)) from e
    except Exception as e:raise ValueError('Invalid or undecodable audio') from e
