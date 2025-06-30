from flask import Flask, jsonify
from vosk import Model, KaldiRecognizer
import sounddevice as sd
import queue
import json
import time
# Initialize Flask app
app = Flask(__name__)

model = Model("modelins")
recognizer = KaldiRecognizer(model, 16000)
q = queue.Queue()
# Define your target keywords
keywords = ["yes", "no", "correct", "wrong", "next", "okay", "cancel", "back", "start", "stop", "go", "exit"]
# Microphone callback to feed audio data into the queue
def callback(indata, frames, time_, status):
    if status:
        print("⚠️ Microphone error:", status)
    q.put(bytes(indata))

# Flask route to listen for 10 seconds and return detected text + keywords
@app.route("/listen", methods=["GET"])
def listen_for_keywords():
    results = {"transcript": [], "keywords": []}
    duration = 10  # seconds
    start_time = time.time()
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("🎧 Listening for 10 seconds...")
        while time.time() - start_time < duration:
            data = q.get()
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
        print("✅ Final Transcript:", results["transcript"])
        print("✅ Detected Keywords:", results["keywords"])
        # Session logging
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "transcript": results["transcript"],
            "keywords": results["keywords"]
        }
        with open("session_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        return jsonify(results)
    
    # Start the Flask server
if __name__ == "__main__":
    app.run(debug=True)