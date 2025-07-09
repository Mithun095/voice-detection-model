# File: main.py
from resemblyzer import VoiceEncoder, preprocess_wav
from scipy.spatial.distance import cosine
import numpy as np
import tempfile
import soundfile as sf
from flask import Flask, jsonify
from flask_cors import CORS
from vosk import Model, KaldiRecognizer
from pathlib import Path
import sounddevice as sd
import queue
import json
import time
import threading

app = Flask(__name__)
CORS(app)

model = Model("modelins")
recognizer = KaldiRecognizer(model, 16000)
q = queue.Queue()

# Store final results and control flags
results = {"transcript": [], "keywords": []}
listening = False
keywords = ["yes", "no", "correct", "wrong", "next", "okay", "cancel", "back", "start", "stop", "exit"]
# Load reference speaker embedding
print("🔐 Loading voice reference from public/reference_embedding.npy")
reference_embedding = np.load("public/reference_embedding.npy")
encoder = VoiceEncoder()


# Callback to receive audio data
def callback(indata, frames, time_, status):
    if status:
        print("⚠️ Microphone error:", status)
    q.put(bytes(indata))

# def listen_loop():
#     global listening
#     results["transcript"].clear()
#     results["keywords"].clear()
#     with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
#                            channels=1, callback=callback):
#         print("🎧 Listening started")
#         while listening:
#             try:
#                 data = q.get(timeout=0.5)
#                 if recognizer.AcceptWaveform(data):
#                     result = json.loads(recognizer.Result())
#                     text = result.get("text", "").lower()
#                     if text:
#                         print("🗣️ You said:", text)
#                         results["transcript"].append(text)
#                         words = text.split()
#                         for word in keywords:
#                             if word in words and word not in results["keywords"]:
#                                 results["keywords"].append(word)
#                                 print(f"🔔 Detected: {word}")
#                                 if word == "stop":
#                                     print("🛑 Listening stopped")
#                                     listening = False
#                                     return
#             except queue.Empty:
#                 continue
#         print("🛑 Listening stopped")

def listen_loop():
    global listening
    results["transcript"].clear()
    results["keywords"].clear()

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("🎧 Listening started")
        audio_buffer = []

        while listening:
            try:
                data = q.get(timeout=0.5)
                audio_buffer.append(data)

                # Keep 2 seconds worth of audio for speaker check
                if len(audio_buffer) > 4:
                    audio_buffer.pop(0)  # keep it rolling

                # Check every 1 second
                if len(audio_buffer) >= 2:
                    combined = b''.join(audio_buffer)
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                        sf.write(tmpfile.name, np.frombuffer(combined, dtype=np.int16), 16000)
                        sample_wav = preprocess_wav(tmpfile.name)
                        new_embedding = encoder.embed_utterance(sample_wav)

                        similarity = 1 - cosine(new_embedding, reference_embedding)
                        print(f"👤 Speaker similarity: {similarity:.3f}")

                        if similarity < 0.75:  # Threshold — tweak as needed
                            print("🚫 Speaker mismatch — ignoring")
                            continue  # Ignore non-matching speaker

                # If speaker verified, run Vosk
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower()
                    if text:
                        print("🗣️ You said:", text)
                        results["transcript"].append(text)
                        words = text.split()
                        for word in keywords:
                            if word in words and word not in results["keywords"]:
                                results["keywords"].append(word)
                                print(f"🔔 Detected: {word}")
                                if word == "stop":
                                    print("I have stopped listening")
                                    listening = False
                                    return

            except queue.Empty:
                continue

    print("🛑 Listening stopped")


# Route to start listening
@app.route("/start", methods=["GET"])
def start_listening():
    global listening
    if not listening:
        listening = True
        threading.Thread(target=listen_loop, daemon=True).start()
    return jsonify({"status": "listening started"})

# Route to stop listening and return results
@app.route("/stop", methods=["GET"])
def stop_listening():
    global listening
    listening = False
    # Wait briefly to let the last chunk process
    time.sleep(1)
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "transcript": results["transcript"],
        "keywords": results["keywords"]
    }
    with open("session_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
