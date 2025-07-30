# File: main.py
from resemblyzer import VoiceEncoder, preprocess_wav
from scipy.spatial.distance import cosine
import numpy as np
import soundfile as sf
from flask import Flask, jsonify
from flask_cors import CORS
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import json
import time
import threading

# === CONFIG ===
VOSK_MODEL_PATH = "modelins"
REFERENCE_EMBEDDING_PATH = "public/reference_embedding.npy"
SPEAKER_THRESHOLD = 0.68  # Adjust for your environment
KEYWORDS = ["yes", "no", "left", "right", "up", "down", "next", "cancel", "back", "start", "stop", "exit"]

# === FLASK SETUP ===
app = Flask(__name__)
CORS(app)

# === MODELS ===
print("🧠 Loading Vosk model...")
vosk_model = Model(VOSK_MODEL_PATH)

# ✅ Limit recognizer to specific keywords only using grammar
grammar = f'["{" ".join(KEYWORDS)}"]'
recognizer = KaldiRecognizer(vosk_model, 16000, grammar)

print("🔐 Loading reference speaker embedding...")
reference_embedding = np.load(REFERENCE_EMBEDDING_PATH)
encoder = VoiceEncoder()

# === GLOBAL STATE ===
q = queue.Queue()
results = {"transcript": [], "keywords": []}
listening = False

# === AUDIO CALLBACK ===
def callback(indata, frames, time_, status):
    if status:
        print("⚠️ Microphone error:", status)
    q.put(bytes(indata))

# === LISTENING LOOP ===
def listen_loop():
    global listening
    results["transcript"].clear()
    results["keywords"].clear()
    buffer_frames = []
    last_embedding_time = 0

    print("🎧 Listening started")

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while listening:
            try:
                data = q.get(timeout=0.5)
                buffer_frames.append(data)

                # Keep last ~2 seconds
                if len(buffer_frames) > 4:
                    buffer_frames.pop(0)

                # Recalculate speaker similarity only every 2 sec
                if time.time() - last_embedding_time > 2:
                    audio_data = b''.join(buffer_frames)
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    if len(audio_np) >= 24000:
                        embedding = encoder.embed_utterance(audio_np)
                        similarity = 1 - cosine(embedding, reference_embedding)
                        last_embedding_time = time.time()

                        print(f"👤 Speaker similarity: {similarity:.3f}")
                        if similarity < 0.6:
                            print("🚫 Speaker too different — skipping recognition.")
                            continue  # Skip Vosk recognition for unknown speaker

                # Run Vosk only if speaker verified
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip().lower()
                    if not text:
                        continue

                    print("🗣️ You said:", text)
                    results["transcript"].append(text)

                    for word in text.split():
                        if word in KEYWORDS and word not in results["keywords"]:
                            results["keywords"].append(word)
                            print(f"🔔 Detected keyword: {word}")

                            if word == "stop":
                                print("🛑 Stop command received. Ending session.")
                                listening = False
                                return

            except queue.Empty:
                continue

    print("🛑 Listening ended")


# === API ROUTES ===
@app.route("/start", methods=["GET"])
def start_listening():
    global listening
    if not listening:
        listening = True
        threading.Thread(target=listen_loop, daemon=True).start()
        return jsonify({"status": "listening started"})
    else:
        return jsonify({"status": "already listening"})

@app.route("/stop", methods=["GET"])
def stop_listening():
    global listening
    listening = False
    time.sleep(1)

    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "transcript": results["transcript"],
        "keywords": results["keywords"]
    }
    with open("session_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return jsonify(results)

# === RUN APP ===
if __name__ == "__main__":
    app.run(debug=True)
