# used to record voice reference for keyword detection
import sounddevice as sd
import soundfile as sf
import os

# Make sure the public folder exists
os.makedirs("public", exist_ok=True)

print("🎙️ Recording will start in 5 seconds. Speak after the beep...")
sd.sleep(5000)
print("🎤 Start speaking NOW...")

duration = 15  # seconds
samplerate = 16000
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()

# Save the recording in the public folder
sf.write("public/reference1.wav", recording, samplerate)
print("✅ Saved as public/reference.wav")
