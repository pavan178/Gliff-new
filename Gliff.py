from flask import Flask, request, jsonify, render_template
import nltk
from PyPDF2 import PdfReader
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from collections import defaultdict
import string
import io

import pyttsx3
from elevenlabs import Voice, VoiceSettings, play
from elevenlabs.client import ElevenLabs

# Initialize the TTS engine
engine = pyttsx3.init()

# Initialize ElevenLabs client
client = ElevenLabs(api_key="53924389fd4d801ae08ad6340a4c35bd")


app = Flask(__name__)

# Download necessary NLTK resources
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')

# Define global variables
pdf_text = ""  # Store PDF text

def preprocess_text(text):
    # Tokenize the text
    tokens = word_tokenize(text.lower())
    
    # Remove punctuation
    table = str.maketrans('', '', string.punctuation)
    tokens = [w.translate(table) for w in tokens]
    
    # Remove non-alphabetic tokens
    tokens = [word for word in tokens if word.isalpha()]
    
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if not word in stop_words]
    
    # Lemmatize words
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    return tokens

def index_sentences(text):
    sentences = sent_tokenize(text)
    index = defaultdict(list)
    for i, sentence in enumerate(sentences):
        for term in preprocess_text(sentence):
            index[term].append(i)
    return index, sentences

def search_index(query, index, sentences):
    result = set()
    for term in preprocess_text(query):
        result.update(index[term])
    return [sentences[i] for i in sorted(result)]

def extract_text_from_pdf(file):
    text = ""
    with io.BytesIO(file.read()) as f:
        pdf_reader = PdfReader(f)
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    global pdf_text
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.pdf'):
                with io.BytesIO(file.read()) as f:
                    pdf_text = extract_text_from_pdf(f)
                return render_template('text_display.html', text=pdf_text)
            else:
                return jsonify({'error': 'Unsupported file format'})
        elif 'question' in request.form:
            query = request.form['question']
            if pdf_text:
                index, sentences = index_sentences(pdf_text)
                results = search_index(query, index, sentences)
                if results:
                    return jsonify({'answer': results})
            return jsonify({'answer': 'Sorry, I couldn\'t find any relevant information.'})
    
    return render_template('index.html')

@app.route('/speak', methods=['POST'])
def speak_text():
    text = request.form['text']
    if 'pause' in request.form:
        engine.pause()
    elif 'resume' in request.form:
        engine.resume()
    elif 'stop' in request.form:
        engine.stop()
        return jsonify({'message': 'Text-to-speech stopped'})
    else:
        # Generate audio using ElevenLabs
        audio = client.generate(
            text=text,
            voice=Voice(
                voice_id='2EiwWnXFnvU5JabPnv8n',
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            )
        )
        # Play the audio
        
    return play(audio)

if __name__ == "__main__":
    app.run(debug=True)
