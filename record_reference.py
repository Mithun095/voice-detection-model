"""
Record Reference Voice

Records audio from the microphone to create a reference voice sample
for speaker verification. The recording is saved as a WAV file.

Usage:
    python record_reference.py [--duration SECONDS] [--output PATH]

Examples:
    python record_reference.py
    python record_reference.py --duration 30
    python record_reference.py --output my_voice.wav
"""

import argparse
import os
import sys
from pathlib import Path

import sounddevice as sd
import soundfile as sf

from config import (
    REFERENCE_WAV_PATH,
    PUBLIC_DIR,
    SAMPLE_RATE,
    CHANNELS,
    RECORDING_DURATION,
    RECORDING_COUNTDOWN,
)


# Sample sentences containing all keywords for the recording
SAMPLE_SENTENCES = """
Speak naturally and include these keywords in your sentences:
────────────────────────────────────────────────────────────
• "Yes, please start the application now."
• "No, I don't want to continue — please exit the program."
• "Move the joystick to the left, then press up to jump."
• "Swipe right to go to the next screen."
• "Press down twice to open the menu and select cancel."
• "If you make a mistake, tap back to return to the previous step."
• "Once everything is set, hit start and wait for the process to complete."
• "To stop the operation immediately, click the stop button."
• "Yes, that's the correct file — go next to continue."
• "If you're done, select exit from the bottom-right corner."
• "The arrow keys let you move up, down, left, and right."
• "No, don't press cancel now — we're almost finished."
• "Click back if you need to review the previous instructions."
• "We need to start again — something went wrong."
• "To end the session, simply press stop and then exit."
────────────────────────────────────────────────────────────
"""


def countdown(seconds: int) -> None:
    """Display a countdown before recording starts."""
    print(f"\n⏱️  Recording will start in {seconds} seconds...")
    for i in range(seconds, 0, -1):
        print(f"   {i}...", end="\r")
        sd.sleep(1000)
    print("   GO!   ")


def record_audio(duration: int, output_path: str) -> bool:
    """
    Record audio from the microphone.
    
    Args:
        duration: Recording duration in seconds
        output_path: Path to save the WAV file
    
    Returns:
        True if successful, False otherwise
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print(f"\n🎙️  Recording for {duration} seconds...")
        print(f"📁 Output: {output_path}")
        print(SAMPLE_SENTENCES)
        
        # Countdown
        countdown(RECORDING_COUNTDOWN)
        
        # Start recording
        print("\n🎤 START SPEAKING NOW...")
        print("   (Recording in progress...)\n")
        
        recording = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16"
        )
        
        # Wait for recording to complete
        sd.wait()
        
        # Save recording
        sf.write(output_path, recording, SAMPLE_RATE)
        print(f"\n✅ Recording saved to: {output_path}")
        
        # Print file info
        file_size = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"📊 File size: {file_size:.2f} MB")
        print(f"📊 Duration: {duration} seconds")
        print(f"📊 Sample rate: {SAMPLE_RATE} Hz")
        
        print("\n💡 Next step: Run 'python generate_embedding.py' to create the speaker embedding.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during recording: {e}")
        return False


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Record reference voice for speaker verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python record_reference.py
  python record_reference.py --duration 30
  python record_reference.py --output recordings/my_voice.wav
        """
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=RECORDING_DURATION,
        help=f"Recording duration in seconds (default: {RECORDING_DURATION})"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=REFERENCE_WAV_PATH,
        help=f"Output WAV file path (default: {REFERENCE_WAV_PATH})"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  🎙️  REFERENCE VOICE RECORDER")
    print("=" * 60)
    
    success = record_audio(args.duration, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
