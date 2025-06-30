from flask import Flask, jsonify
from flask_cors import CORS
from vosk import Model, KaldiRecognizer
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

# Callback to receive audio data
def callback(indata, frames, time_, status):
    if status:
        print("⚠️ Microphone error:", status)
    q.put(bytes(indata))

def listen_loop():
    global listening
    results["transcript"].clear()
    results["keywords"].clear()
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("🎧 Listening started")
        while listening:
            try:
                data = q.get(timeout=0.5)
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
                                    print("🛑 Listening stopped")
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
