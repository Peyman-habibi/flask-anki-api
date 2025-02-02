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

# AnkiConnect URL
ANKI_CONNECT_URL = "http://localhost:8765"

# API Key (Optional for security)
API_KEY = "your-secret-api-key"

def get_longman_data(word):
    """Scrapes Longman Dictionary to get phonetics, part of speech, meanings, and examples."""
    try:
        print(f"🔍 Scraping data for word: {word}")

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        url = f"https://www.ldoceonline.com/dictionary/{word}"
        driver.get(url)
        time.sleep(3)  # Wait for page to load

        # Extract phonetic transcription
        try:
            phonetic = driver.find_element(By.CLASS_NAME, "PronCodes").text
        except:
            phonetic = "Not found"

        # Extract part of speech
        try:
            part_of_speech = driver.find_element(By.CLASS_NAME, "POS").text
        except:
            part_of_speech = "Not found"

        # Extract meanings and examples
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

    except Exception as e:
        print(f"❌ Error in get_longman_data: {e}")
        return "Not found", "Not found", "Error fetching data."

def generate_audio(word):
    """Generate pronunciation audio using Google Text-to-Speech (gTTS)."""
    try:
        print(f"🔊 Generating audio for: {word}")
        audio_file = f"{word}.mp3"
        tts = gTTS(text=word, lang="en", tld="com.au")
        tts.save(audio_file)

        with open(audio_file, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")

        os.remove(audio_file)  # Delete after encoding
        return audio_data

    except Exception as e:
        print(f"❌ Error in generate_audio: {e}")
        return None

def add_card_to_anki(word, phonetic, part_of_speech, back_card, audio_data):
    """Send the card data to Anki via AnkiConnect."""
    try:
        print(f"📩 Sending card to Anki for: {word}")
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": "Default",
                    "modelName": "Basic",
                    "fields": {
                        "Front": f"<b>{word}</b><br><i>{phonetic}</i><br>{part_of_speech}",
                        "Back": back_card
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

        if result.get("error"):
            print(f"❌ Error adding card to Anki: {result['error']}")
            return False

        print(f"✅ Successfully added '{word}' to Anki!")
        return True

    except Exception as e:
        print(f"❌ Error in add_card_to_anki: {e}")
        return False

@app.route("/add_word", methods=["POST"])
def add_word():
    """Receive word from iOS app, process it, and add to Anki."""
    try:
        # Check API key (Optional security feature)
        api_key = request.headers.get("Authorization")
        if api_key and api_key != API_KEY:
            return jsonify({"success": False, "error": "Unauthorized"}), 401

        data = request.json
        if not data or "word" not in data:
            return jsonify({"success": False, "error": "Word is required"}), 400

        word = data["word"]
        print(f"📥 Received word: {word}")

        phonetic, part_of_speech, back_card = get_longman_data(word)
        audio_data = generate_audio(word)

        if audio_data is None:
            return jsonify({"success": False, "error": "Failed to generate audio"}), 500

        success = add_card_to_anki(word, phonetic, part_of_speech, back_card, audio_data)

        return jsonify({
            "success": success,
            "word": word,
            "phonetic": phonetic,
            "part_of_speech": part_of_speech,
            "back_card": back_card
        })

    except Exception as e:
        print(f"🔥 Error in /add_word: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))  # Render uses dynamic port mapping
    app.run(host="0.0.0.0", port=port, debug=True)
