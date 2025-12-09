"""
Keyword Detector - Main Application

A Flask-based keyword detection server with speaker verification.
Only accepts voice commands from the authorized (registered) speaker.

Usage:
    python main.py

API Endpoints:
    GET /start  - Start listening for keywords
    GET /stop   - Stop listening and return results
    GET /status - Get real-time status and detected keywords
"""

from typing import Dict, List, Any
import queue
import json
import time
import threading
import os

import numpy as np
from scipy.spatial.distance import cosine
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from vosk import Model, KaldiRecognizer
import sounddevice as sd
from resemblyzer import VoiceEncoder

from config import (
    VOSK_MODEL_PATH,
    REFERENCE_EMBEDDING_PATH,
    SAMPLE_RATE,
    BLOCK_SIZE,
    CHANNELS,
    AUDIO_DTYPE,
    SPEAKER_MIN_SIMILARITY,
    SPEAKER_CHECK_INTERVAL,
    MIN_SAMPLES_FOR_EMBEDDING,
    KEYWORDS,
    STOP_KEYWORDS,
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG,
)


# ===========================================
# FLASK SETUP
# ===========================================
app = Flask(__name__)
CORS(app)


# ===========================================
# GLOBAL STATE
# ===========================================
audio_queue: queue.Queue = queue.Queue()
results: Dict[str, Any] = {
    "transcript": [],
    "keywords": [],
    "partial": "",
    "speaker_similarity": 0.0,
    "is_verified": False,
    "last_keyword": None,
    "keyword_timestamps": []
}
listening: bool = False
vosk_model = None
recognizer = None
reference_embedding = None
encoder = None


# ===========================================
# MODEL INITIALIZATION
# ===========================================
def load_models() -> tuple:
    """Load Vosk speech recognition and speaker verification models."""
    global vosk_model, recognizer, reference_embedding, encoder
    
    print("🧠 Loading Vosk model...")
    vosk_model = Model(VOSK_MODEL_PATH)
    
    # Create grammar-constrained recognizer for keywords only
    # Use individual words for better matching
    grammar = json.dumps(KEYWORDS)
    recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE, grammar)
    recognizer.SetWords(True)  # Enable word-level timestamps
    
    print("🔐 Loading reference speaker embedding...")
    reference_embedding = np.load(REFERENCE_EMBEDDING_PATH)
    encoder = VoiceEncoder()
    
    return recognizer, reference_embedding, encoder


# Initialize models
load_models()


# ===========================================
# ROOT ROUTES
# ===========================================
@app.route("/", methods=["GET"])
def index():
    """Serve the web interface."""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.route("/info", methods=["GET"])
def info():
    """API information endpoint."""
    return jsonify({
        "name": "Keyword Detector API",
        "version": "2.0.0",
        "endpoints": {
            "/": "Web interface",
            "/start": "Start listening for keywords",
            "/stop": "Stop listening and return results",
            "/status": "Get real-time status (poll this for live updates)",
            "/info": "API information (this endpoint)"
        },
        "keywords": KEYWORDS,
        "speaker_threshold": SPEAKER_MIN_SIMILARITY
    })


# ===========================================
# AUDIO CALLBACK
# ===========================================
def audio_callback(indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
    """Callback function for audio stream - pushes audio data to queue."""
    if status:
        print(f"⚠️ Microphone error: {status}")
    audio_queue.put(bytes(indata))


# ===========================================
# SPEAKER VERIFICATION
# ===========================================
def verify_speaker(audio_np: np.ndarray) -> float:
    """
    Verify if the current speaker matches the reference embedding.
    
    Args:
        audio_np: Audio data as numpy array (float32, normalized)
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    try:
        embedding = encoder.embed_utterance(audio_np)
        similarity = 1 - cosine(embedding, reference_embedding)
        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
    except Exception as e:
        print(f"⚠️ Speaker verification error: {e}")
        return 0.0


# ===========================================
# LISTENING LOOP (IMPROVED)
# ===========================================
def listen_loop() -> None:
    """
    Main listening loop with improved accuracy:
    1. Larger audio buffer for better recognition
    2. Partial results for real-time feedback
    3. Optimized speaker verification
    """
    global listening, recognizer
    
    # Reset recognizer for fresh start
    grammar = json.dumps(KEYWORDS)
    recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE, grammar)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)
    
    # Reset state
    results["transcript"].clear()
    results["keywords"].clear()
    results["keyword_timestamps"].clear()
    results["partial"] = ""
    results["speaker_similarity"] = 0.0
    results["is_verified"] = False
    results["last_keyword"] = None
    
    buffer_frames: List[bytes] = []
    last_embedding_time: float = 0
    speaker_verified: bool = False
    
    # Clear any stale audio data
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except:
            break

    print("🎧 Listening started")

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=4000,  # Smaller blocks for more responsive recognition
        dtype=AUDIO_DTYPE,
        channels=CHANNELS,
        callback=audio_callback
    ):
        while listening:
            try:
                data = audio_queue.get(timeout=0.3)
                buffer_frames.append(data)

                # Keep last ~3 seconds of audio for speaker verification
                max_buffer_frames = int(3 * SAMPLE_RATE / 4000)  # 3 seconds
                if len(buffer_frames) > max_buffer_frames:
                    buffer_frames.pop(0)

                # Perform speaker verification periodically
                current_time = time.time()
                if current_time - last_embedding_time > SPEAKER_CHECK_INTERVAL:
                    audio_data = b''.join(buffer_frames)
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    if len(audio_np) >= MIN_SAMPLES_FOR_EMBEDDING:
                        similarity = verify_speaker(audio_np)
                        last_embedding_time = current_time
                        
                        results["speaker_similarity"] = round(similarity, 3)
                        speaker_verified = similarity >= SPEAKER_MIN_SIMILARITY
                        results["is_verified"] = speaker_verified

                        if speaker_verified:
                            print(f"✅ Speaker verified: {similarity:.3f}")
                        else:
                            print(f"❌ Speaker similarity: {similarity:.3f} (threshold: {SPEAKER_MIN_SIMILARITY})")

                # Process speech with Vosk (always process, verification is advisory)
                if recognizer.AcceptWaveform(data):
                    result_json = json.loads(recognizer.Result())
                    text = result_json.get("text", "").strip().lower()
                    
                    results["partial"] = ""  # Clear partial on final result
                    
                    if text:
                        print(f"🗣️ Recognized: {text}")
                        
                        # Only accept if speaker is verified
                        if speaker_verified:
                            results["transcript"].append(text)
                            
                            # Check for keywords
                            for word in text.split():
                                word_clean = word.strip().lower()
                                if word_clean in KEYWORDS:
                                    if word_clean not in results["keywords"]:
                                        results["keywords"].append(word_clean)
                                    
                                    results["last_keyword"] = word_clean
                                    results["keyword_timestamps"].append({
                                        "keyword": word_clean,
                                        "time": time.strftime("%H:%M:%S")
                                    })
                                    print(f"🔔 KEYWORD DETECTED: {word_clean}")

                                    # Handle stop command
                                    if word_clean in STOP_KEYWORDS:
                                        print("🛑 Stop command received. Ending session.")
                                        listening = False
                                        return
                        else:
                            print(f"⚠️ Ignored (unverified speaker): {text}")
                else:
                    # Get partial results for real-time feedback
                    partial_json = json.loads(recognizer.PartialResult())
                    partial_text = partial_json.get("partial", "").strip()
                    if partial_text:
                        results["partial"] = partial_text

            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️ Error in listen loop: {e}")
                continue

    print("🛑 Listening ended")


# ===========================================
# API ROUTES
# ===========================================
@app.route("/start", methods=["GET"])
def start_listening() -> Dict[str, str]:
    """Start the keyword detection listener."""
    global listening
    
    if not listening:
        listening = True
        threading.Thread(target=listen_loop, daemon=True).start()
        return jsonify({
            "status": "listening",
            "message": "Keyword detection started",
            "keywords": KEYWORDS
        })
    
    return jsonify({
        "status": "already_listening",
        "message": "Already listening for keywords"
    })


@app.route("/stop", methods=["GET"])
def stop_listening() -> Dict[str, Any]:
    """Stop the listener and return detected keywords."""
    global listening
    listening = False
    time.sleep(0.5)  # Allow listener thread to finish

    # Log session results
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "transcript": results["transcript"],
        "keywords": results["keywords"],
        "keyword_timestamps": results["keyword_timestamps"]
    }
    
    try:
        with open("session_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"⚠️ Failed to write log: {e}")

    return jsonify({
        "status": "stopped",
        "transcript": results["transcript"],
        "keywords": results["keywords"],
        "keyword_timestamps": results["keyword_timestamps"],
        "total_keywords": len(results["keywords"])
    })


@app.route("/status", methods=["GET"])
def get_status() -> Dict[str, Any]:
    """Get real-time listener status and detected keywords."""
    return jsonify({
        "listening": bool(listening),
        "partial": str(results.get("partial", "")),
        "transcript": list(results.get("transcript", [])),
        "keywords": list(results.get("keywords", [])),
        "last_keyword": results.get("last_keyword"),
        "speaker_similarity": float(results.get("speaker_similarity", 0.0)),
        "is_verified": bool(results.get("is_verified", False)),
        "keyword_count": int(len(results.get("keywords", []))),
        "transcript_count": int(len(results.get("transcript", [])))
    })


# ===========================================
# MAIN ENTRY POINT
# ===========================================
if __name__ == "__main__":
    print(f"\n{'='*50}")
    print("🎙️  KEYWORD DETECTOR SERVER")
    print(f"{'='*50}")
    print(f"📍 Open http://localhost:{FLASK_PORT}/ in your browser")
    print(f"🔑 Keywords: {', '.join(KEYWORDS)}")
    print(f"{'='*50}\n")
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
