import speech_recognition as sr
import pyttsx3
from agent.smart_home_agent import run_agent

recognizer = sr.Recognizer()
engine = pyttsx3.init()

print("Voice Smart Home Assistant - say 'exit' to stop")

while True:
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print("You:", text)
        if text.lower() in {"exit", "quit", "stop assistant"}:
            break
        answer = run_agent(text)
        print("Assistant:", answer)
        engine.say(answer)
        engine.runAndWait()
    except sr.UnknownValueError:
        print("I could not understand that.")
    except sr.RequestError as exc:
        print("Speech recognition error:", exc)
    except Exception as exc:
        print("Error:", exc)
