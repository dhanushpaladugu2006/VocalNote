#10-20 seconds

import io
import pickle
import numpy as np
from tqdm import tqdm
from pydub import AudioSegment
from scipy.io import wavfile
from kokoro import KPipeline
import torch
from asttokens import ASTTokens
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading Kokoro model...")
pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')

BASE_DIR = Path("E:/Projects/NoteBookLlama-(GPU)Final")
INPUT_FILE = BASE_DIR / "resources" / "processed_transcript.pkl"
PODCAST_FILE = BASE_DIR / "resources" / "podcast.wav"

with open(INPUT_FILE, 'rb') as f:
    PODCAST_TEXT = pickle.load(f)

print(f"Type of PODCAST_TEXT: {type(PODCAST_TEXT)}")
if isinstance(PODCAST_TEXT, list):
    print(f"First element: {PODCAST_TEXT[0]}")
else:
    print(f"Content sample: {str(PODCAST_TEXT)[:100]}...")

if isinstance(PODCAST_TEXT, str):
    import re
    PODCAST_TEXT = re.sub(r"^```(?:python)?\s*", "", PODCAST_TEXT, flags=re.IGNORECASE)
    PODCAST_TEXT = re.sub(r"\s*```$", "", PODCAST_TEXT, flags=re.IGNORECASE)
    PODCAST_TEXT = PODCAST_TEXT.strip()

    try:
        import ast
        PODCAST_TEXT = ast.literal_eval(PODCAST_TEXT)
        print(f"Parsed PODCAST_TEXT as list. First element: {PODCAST_TEXT[0]}")
    except (ValueError, SyntaxError) as e:
        print(f"Failed to parse PODCAST_TEXT: {str(e)}. Attempting to repair truncated python list structure...")
        lines = PODCAST_TEXT.splitlines()
        parsed = None
        while lines:
            candidate = "\n".join(lines)
            candidate_stripped = candidate.strip()
            if not candidate_stripped.endswith("]"):
                candidate = candidate.rstrip()
                if candidate.endswith(","):
                    candidate += "\n]"
                else:
                    candidate += ",\n]"
            try:
                import ast
                parsed = ast.literal_eval(candidate)
                break
            except Exception:
                lines.pop()

        if parsed is not None:
            PODCAST_TEXT = parsed
            print(f"Successfully repaired and parsed transcript. Got {len(PODCAST_TEXT)} turns. First element: {PODCAST_TEXT[0]}")
        else:
            raise ValueError(f"Failed to parse PODCAST_TEXT string as list of tuples: {e}")

if not isinstance(PODCAST_TEXT, list):
    raise ValueError("PODCAST_TEXT must be a list of tuples after parsing")

def generate_kokoro_audio(text, voice):
    generator = pipeline(text, voice=voice)
    audio_segments = []
    for _, _, audio in generator:
        audio_segments.append(audio)
    full_audio = np.concatenate(audio_segments)
    return full_audio, 24000

def numpy_to_audio_segment(audio_arr, sampling_rate):
    audio_int16 = (audio_arr * 32767).astype(np.int16)
    byte_io = io.BytesIO()
    wavfile.write(byte_io, sampling_rate, audio_int16)
    byte_io.seek(0)
    return AudioSegment.from_wav(byte_io)

final_audio = None

print("Generating podcast segments...")
for speaker, text in tqdm(PODCAST_TEXT, desc="Generating", unit="segment"):
    if not text.strip():
        continue

    voice = 'am_fenrir' if speaker == "Speaker 1" else 'bf_emma'
    audio_arr, rate = generate_kokoro_audio(text, voice=voice)
    segment = numpy_to_audio_segment(audio_arr, rate)

    if final_audio is None:
        final_audio = segment
    else:
        final_audio += segment

try:
    final_audio.export(PODCAST_FILE, format="wav")
    print(f"Podcast exported to {PODCAST_FILE}")
except Exception as e:
    print(f"Failed to export podcast: {e}")