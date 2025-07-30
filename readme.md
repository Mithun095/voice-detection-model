# Keyword Detector

A simple voice keyword detector that listens for specific commands and verifies the speaker.

## Workflow

1. **Record Reference Voice**  
   Record your voice sample to use as a reference for speaker verification.
   so run "python record_reference.py"

2. **Generate Speaker Embedding**  
   Create a voice embedding from your reference recording.
   so run "python generate_embedding.py"

3. **Run the Flask Server**  
   Start the backend server for keyword detection.
   so run "python main.py"

4. **Use the Web Interface**  
   Open `index.html` in your browser to start/stop listening and see detected keywords.

## How to Clone

```bash
git clone http-link
cd keyword_detector

**Dependencies**
 Flask
 flask-cors
 sounddevice
 soundfile
 resemblyzer
 vosk
 numpy
 scipy

**to download all the dependency**
pip install flask flask-cors sounddevice soundfile resemblyzer vosk

## this is in main.py file you can change if the environment has som disturbance
SPEAKER_THRESHOLD = 0.69  # Adjust for your environment

