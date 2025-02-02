from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from gtts import gTTS
import base64
import os
import requests

app = Flask(__name__)

ANKI_CONNECT_URL = "http://localhost:8765"

def get_longman_data(word):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = f"https://www.ldoceonline.com/dictionary/{word}"
    driver.get(url)
    time.sleep(3)

    try:
        phonetic = driver.find_element(By.CLASS_NAME, "PronCodes").text.encode("utf-8").decode("utf-8")
    except:
        phonetic = "Not found"

    try:
        part_of_speech = driver.find_element(By.CLASS_NAME, "POS").text
    except:
        part_of_speech = "Not found"

    meaning_texts = []
    sense_elements = driver.find_elements(By.CLASS_NAME, "Sense")

    for num, sense in enumerate(sense_elements, start=1):
        try:
            definition = sense.find_element(By.CLASS_NAME, "DEF").text.strip()
        except:
            definition = None  

        if definition:
            meaning_texts.append(f"<b>Definition {num}:</b> {definition}")
            example_elements = sense.find_elements(By.CLASS_NAME, "EXAMPLE")

            for num_2, example in enumerate(example_elements, start=1):
                example_text = example.text.strip()
                if example_text:
                    meaning_texts.append(f"🔹 Example {num_2}: {example_text}")

    driver.quit()

    back_card = "<br>".join(meaning_texts) if meaning_texts else "No definitions found."
    return phonetic, part_of_speech, back_card

def generate_audio(word):
    audio_file = f"{word}.mp3"
    tts = gTTS(text=word, lang="en", tld="com.au")
    tts.save(audio_file)

    with open(audio_file, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")
    
    os.remove(audio_file)  # Delete after encoding

    return audio_data

def add_card_to_anki(word, phonetic, part_of_speech, back_card, audio_data):
    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": "Default",
                "modelName": "Basic",
                "fields": {
                    "Front": f"<b>{word}</b><br><i>{phonetic}</i><br>{part_of_speech}".encode("utf-8").decode("utf-8"),
                    "Back": back_card.encode("utf-8").decode("utf-8")
                },
                "tags": ["longman", "anki", "vocabulary"],
                "audio": [
                    {
                        "filename": f"{word}.mp3",
                        "data": audio_data,
                        "fields": ["Front"]
                    }
                ]
            }
        }
    }

    response = requests.post(ANKI_CONNECT_URL, json=payload)
    result = response.json()

    return result.get("error") is None

@app.route("/add_word", methods=["POST"])
def add_word():
    data = request.json
    word = data.get("word")

    phonetic, part_of_speech, back_card = get_longman_data(word)
    audio_data = generate_audio(word)

    success = add_card_to_anki(word, phonetic, part_of_speech, back_card, audio_data)

    return jsonify({
        "success": success,
        "word": word,
        "phonetic": phonetic,
        "part_of_speech": part_of_speech,
        "back_card": back_card
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)