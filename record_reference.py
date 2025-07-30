# used to record voice reference for keyword detection
import sounddevice as sd
import soundfile as sf
import os

# Make sure the public folder exists
os.makedirs("public", exist_ok=True)

print("🎙️ Recording will start in 5 seconds. Speak after the beep...")
sd.sleep(5000)
print("🎤 Start speaking NOW...")
print("You can say things like:")
print(
    "Yes, please start the application now.\n"
    "No, I don’t want to continue — please exit the program.\n"
    "Move the joystick to the left, then press up to jump.\n"
    "Swipe right to go to the next screen.\n"
    "Press down twice to open the menu and select cancel.\n"
    "If you make a mistake, tap back to return to the previous step.\n"
    "Once everything is set, hit start and wait for the process to complete.\n"
    "To stop the operation immediately, click the stop button.\n"
    "Yes, that’s the correct file — go next to continue.\n"
    "If you're done, select exit from the bottom-right corner.\n"
    "The arrow keys let you move up, down, left, and right.\n"
    "No, don’t press cancel now — we’re almost finished.\n"
    "Click back if you need to review the previous instructions.\n"
    "We need to start again — something went wrong.\n"
    "To end the session, simply press stop and then exit.\n"
 "\n"
 "if you are done reading this start reading again until it stops "
)


duration =100  # seconds
samplerate = 16000
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()

# Save the recording in the public folder
sf.write("public/reference.wav", recording, samplerate)
print("✅ Saved as public/reference.wav")
