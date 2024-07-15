from flask import Flask, render_template, request, flash
import requests
import logging
import json
import PyPDF2
import io
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class SummarizationStep:
    def __init__(self, level, pieces, summaries, final_summary):
        self.level = level
        self.pieces = pieces
        self.summaries = summaries
        self.final_summary = final_summary

def call_llama_api(prompt):
    payload = {
        "model": "dolphin-llama3",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_API_URL, json=payload)
    if response.status_code == 200:
        return response.json()['response']
    else:
        logger.error(f"Error in API call: {response.status_code}")
        return ""

def summarize(text, maxSummarylength=500):
    prompt = f"Summarize the following text in about {maxSummarylength} characters:\n\n{text}"
    return call_llama_api(prompt)

def get_clauses(text):
    prompt = f"Extract and list the main clauses and sub clauses from the following legal contract. Each clause should be on a new line with its sub clause:\n\n{text}"
    response = call_llama_api(prompt)
    return [clause.strip() for clause in response.split('\n') if clause.strip()]

def preprocess_text(text):
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    preprocessed_sentences = []
    
    for sentence in sentences:
        words = word_tokenize(sentence)
        filtered_sentence = ' '.join([word for word in words if word.lower() not in stop_words])
        preprocessed_sentences.append(filtered_sentence)
    
    return ' '.join(preprocessed_sentences)

def split_text_into_pieces(text, max_chars=1500, overlapPercent=10):
    overlap_chars = int(max_chars * overlapPercent / 100)
    pieces = [text[i:i + max_chars] for i in range(0, len(text), max_chars - overlap_chars)]
    return pieces

def recursive_summarize(text, max_length=1500, recursionLevel=0):
    recursionLevel += 1
    logger.info(f"Recursion Level: {recursionLevel}")
    
    expectedCountOfChunks = len(text) / max_length
    max_length = int(len(text) / expectedCountOfChunks) + 2
    pieces = split_text_into_pieces(text, max_chars=max_length)
    
    logger.info(f"Number of pieces: {len(pieces)}")
    
    summaries = []
    for k, piece in enumerate(pieces):
        logger.info(f"Processing piece {k+1}/{len(pieces)}")
        summary = summarize(piece, maxSummarylength=max_length/2)
        summaries.append(summary)
    
    concatenated_summary = ' '.join(summaries)
    
    step = SummarizationStep(recursionLevel, pieces, summaries, concatenated_summary)
    
    if len(concatenated_summary) > max_length and recursionLevel < 3:
        logger.info("Concatenated summary is too long. Starting next recursion level.")
        next_step, all_steps = recursive_summarize(concatenated_summary, max_length=max_length, recursionLevel=recursionLevel)
        return next_step, [step] + all_steps
    else:
        if len(pieces) > 1:
            final_summary = summarize(concatenated_summary, maxSummarylength=max_length)
            step.final_summary = final_summary
        return step, [step]

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    steps = []
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return render_template('index.html', steps=steps, zip=zip, get_clauses=get_clauses)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return render_template('index.html', steps=steps, zip=zip, get_clauses=get_clauses)
        
        if file:
            try:
                if file.filename.endswith('.pdf'):
                    text = extract_text_from_pdf(file)
                elif file.filename.endswith('.txt'):
                    text = file.read().decode('utf-8')
                else:
                    flash('Unsupported file format. Please upload a PDF or TXT file.')
                    return render_template('index.html', steps=steps, zip=zip, get_clauses=get_clauses)
                
                # Preprocess the text
                preprocessed_text = preprocess_text(text)
                
                # Perform summarization
                _, steps = recursive_summarize(preprocessed_text)
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
                return render_template('index.html', steps=steps, zip=zip, get_clauses=get_clauses)
    
    return render_template('index.html', steps=steps, zip=zip, get_clauses=get_clauses)

if __name__ == '__main__':
    app.run(debug=True)