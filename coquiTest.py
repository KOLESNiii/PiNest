from TTS.api import TTS
from tqdm import tqdm
import os
import torch
# Phrase to say


# Output folder
output_dir = "vctk_outputs"
os.makedirs(output_dir, exist_ok=True)

# Load the VCTK multi-speaker TTS model (GPU if available)
tts = TTS("xtts", progress_bar=True).to("cpu")

filename = "out.wav"
filepath = os.path.join(output_dir, filename)

current_dir = os.path.dirname(os.path.abspath(__file__))
wavPath = os.path.join(current_dir, "idk_man.wav")

phrase = "bih bek is a nigger and loves huge jew dih"

tts.tts_to_file(text=phrase, file_path=filepath, language="en", speaker_wav="ronaldo.wav")
    
