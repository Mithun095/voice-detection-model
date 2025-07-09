from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import numpy as np
import os

# Ensure the folder exists
os.makedirs("public", exist_ok=True)

# Load the reference recording
wav_fpath = Path("public/reference.wav")
print(f"🔍 Loading {wav_fpath}")
wav = preprocess_wav(wav_fpath)

# Generate speaker embedding
encoder = VoiceEncoder()
embedding = encoder.embed_utterance(wav)

# Save embedding to public folder
output_path = Path("public/reference_embedding.npy")
np.save(output_path, embedding)
print(f"✅ Voice embedding saved at {output_path}")
