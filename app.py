import tkinter as tk
from tkinter import scrolledtext
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import queue
import json
import threading
import time

# 🎯 Your target keywords
keywords = ["yes", "no", "correct", "wrong", "next", "okay", "cancel", "back", "start", "stop","go", "exit"]

# 🧠 Global variables
q = queue.Queue()
model = Model("vosk-model-small-hi-0.22")
recognizer = KaldiRecognizer(model, 16000)

# 🎧 Audio callback
def callback(indata, frames, time_, status):
    if status:
        print("⚠️", status)
    q.put(bytes(indata))

# 🔊 Recognition loop (runs in background)
def recognize_audio(text_box, keyword_box, start_button, timer_label):
    text_box.delete('1.0', tk.END)
    keyword_box.delete('1.0', tk.END)
    start_button.config(state=tk.DISABLED)

    duration = 10
    start_time = time.time()

    # Timer update loop (in another thread)
    def update_timer():
        while time.time() - start_time < duration:
            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed
            timer_label.config(text=f"Listening... {remaining}s left")
            time.sleep(1)
        timer_label.config(text="Done!")

    threading.Thread(target=update_timer, daemon=True).start()

    # Audio stream
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while time.time() - start_time < duration:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                if text:
                    text_box.insert(tk.END, f"You said: {text}\n")
                    words = text.split()
                    for word in keywords:
                        if word in words:
                            keyword_box.insert(tk.END, f"✅ Detected: {word}\n")

    start_button.config(state=tk.NORMAL)

# 🚀 Start recognition on button click
def start_listening():
    threading.Thread(target=recognize_audio, args=(text_area, keyword_area, start_btn, timer_lbl), daemon=True).start()

# 🖼 UI Setup
root = tk.Tk()
root.title("🎤 Keyword Detector")
root.geometry("5000x500")
root.configure(bg="white")

title_lbl = tk.Label(root, text="Keyword Detector", font=("Arial", 20), bg="white")
title_lbl.pack(pady=10)

start_btn = tk.Button(root, text="🎙 Start Listening (10s)", font=("Arial", 14), command=start_listening)
start_btn.pack(pady=10)

timer_lbl = tk.Label(root, text="Waiting to start...", font=("Arial", 12), bg="white")
timer_lbl.pack()

text_area = scrolledtext.ScrolledText(root, height=8, width=50, font=("Arial", 10))
text_area.pack(pady=10)
text_area.insert(tk.END, "You said:\n")

keyword_area = scrolledtext.ScrolledText(root, height=5, width=50, font=("Arial", 10))
keyword_area.pack(pady=10)
keyword_area.insert(tk.END, "Detected keywords:\n")
root.mainloop()
