"""
Generate Speaker Embedding

Creates a voice embedding from a reference audio recording for speaker verification.
The embedding is saved as a numpy file for use by the main application.

Usage:
    python generate_embedding.py [--input PATH] [--output PATH]

Examples:
    python generate_embedding.py
    python generate_embedding.py --input my_voice.wav --output my_embedding.npy
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav

from config import REFERENCE_WAV_PATH, REFERENCE_EMBEDDING_PATH, PUBLIC_DIR


def generate_embedding(input_path: str, output_path: str) -> bool:
    """
    Generate a speaker embedding from an audio file.
    
    Args:
        input_path: Path to the input WAV file
        output_path: Path to save the embedding (.npy file)
    
    Returns:
        True if successful, False otherwise
    """
    # Validate input file
    wav_path = Path(input_path)
    if not wav_path.exists():
        print(f"❌ Error: Input file not found: {wav_path}")
        print(f"💡 Tip: Run 'python record_reference.py' first to create a reference recording.")
        return False
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load and preprocess audio
        print(f"🔍 Loading audio from: {wav_path}")
        wav = preprocess_wav(wav_path)
        
        # Generate embedding
        print("🧠 Generating speaker embedding...")
        encoder = VoiceEncoder()
        embedding = encoder.embed_utterance(wav)
        
        # Save embedding
        output_file = Path(output_path)
        np.save(output_file, embedding)
        print(f"✅ Voice embedding saved to: {output_file}")
        
        # Print embedding info
        print(f"📊 Embedding shape: {embedding.shape}")
        print(f"📊 Embedding dtype: {embedding.dtype}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return False


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate speaker embedding from audio file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_embedding.py
  python generate_embedding.py --input custom_voice.wav
  python generate_embedding.py --input voice.wav --output embeddings/speaker.npy
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=REFERENCE_WAV_PATH,
        help=f"Path to input WAV file (default: {REFERENCE_WAV_PATH})"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=REFERENCE_EMBEDDING_PATH,
        help=f"Path to save embedding (default: {REFERENCE_EMBEDDING_PATH})"
    )
    
    args = parser.parse_args()
    
    success = generate_embedding(args.input, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
