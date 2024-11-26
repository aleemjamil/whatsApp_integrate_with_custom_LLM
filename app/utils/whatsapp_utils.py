import logging
from flask import current_app, jsonify
import json
import requests
import os
from openai import OpenAI
from dotenv import dotenv_values

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import glob
from langchain_community.document_loaders import PyPDFLoader
from PyPDF2 import PdfReader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import sqlite3
import pdb
import time
import re
from dotenv import load_dotenv
from pathlib import Path
import subprocess
import speech_recognition as sr
import whisper
import ffmpeg
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'



mobile_number = ""
input_mesage = ""
output_message = ""
MODEL = whisper.load_model("small") 
import os



# from app.services.openai_service import generate_response


dotenv_values()


# Load the .env file from two directories up
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

api_key = os.environ.get("OPENAI_API_KEY")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
api_key = OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def download_media(url):
    if not url:
        print("Error: URL parameter is required.")
        return

    try:
        # Fetch the audio data from the external URL with the auth token
        headers = {
            'Authorization': f"Bearer {ACCESS_TOKEN}",
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        # Generate a unique file name
        file_name = f"{int(time.time())}_audio.ogg"

        # Save the audio stream to a file
        with open(file_name, 'wb') as audio_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive chunks
                    audio_file.write(chunk)

        print(f"Audio file downloaded successfully: {file_name}")
        return file_name

    except requests.RequestException as e:
        print(f"Error fetching audio data: {str(e)}")
        
def extract_link(audio_id):
    access_token = ACCESS_TOKEN  # Replace with your access token
    url = f"https://graph.facebook.com/v21.0/{audio_id}"
    
    # Fetching the audio file from WhatsApp API
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    
    return response.json()['url']

# def convert_audio_to_text(audio_file_path):
#     """
#     Convert audio to text using Google Speech Recognition API.
#     """
#     recognizer = sr.Recognizer()

#     # Open the audio file using speech_recognition
#     with sr.AudioFile(audio_file_path) as source:
#         audio_data = recognizer.record(source)  # Record the audio data

#         try:
#             # Recognize the speech in the audio file using Google's API
#             text = recognizer.recognize_google(audio_data, language="ur")
#             return text
#         except sr.UnknownValueError:
#             return "آپ کی آواز واضح نہیں ہے"  # "Your voice is unclear"
#         except sr.RequestError:
#             return "Sorry, my speech service is down"

def convert_opus_to_wav(opus_file, output_file="temp_audio.wav"):
    """
    Converts an .opus audio file to .wav format using FFmpeg.
    """
    try:
        ffmpeg.input(opus_file).output(output_file, format="wav").run(quiet=True, overwrite_output=True)
        print(f"Converted {opus_file} to {output_file}")
        return output_file
    except Exception as e:
        print("Error converting audio:", e)
        return None

def process_audio(opus_file, model):
    """
    Transcribes Urdu audio from an .opus file to text using Whisper.
    """
    # Convert the .opus file to .wav format
    wav_file = convert_opus_to_wav(opus_file)
    if not wav_file:
        return "Error in audio conversion."

    # Transcribe the audio
    result = model.transcribe(wav_file, language="ur")  # 'ur' is the language code for Urdu
    text = result.get("text", "")

    # Cleanup temporary .wav file
    os.remove(wav_file)

    return text




# def convert_opus_to_wav(opus_file_path, wav_file_path):
#     """
#     Convert an .opus audio file to .wav format using ffmpeg via subprocess.
#     Suppresses normal ffmpeg output.
#     """
#     command = ['ffmpeg', '-i', opus_file_path, wav_file_path]
#     subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# def process_audio(opus_file_path):
#     """
#     Full process to convert OPUS file to WAV, then convert WAV to text.
#     """
#     # Define the output .wav file path
#     wav_file_path = "converted_audio.wav"
#     # Convert OPUS to WAV
#     convert_opus_to_wav(opus_file_path, wav_file_path)
#     # Convert WAV to text
#     text = convert_audio_to_text(wav_file_path)
#     return text


def insert_into_database(database_name, input_message, output_message, mobile_number):
    with sqlite3.connect(database_name) as conn:
        cursor = conn.cursor()

        # Insert into input_message table
        cursor.execute('''
            INSERT INTO input_message (message) VALUES (?)
        ''', (input_message,))
        
        # Insert into output_message table
        cursor.execute('''
            INSERT INTO output_message (message) VALUES (?)
        ''', (output_message,))

        # Insert into mobile_number table
        cursor.execute('''
            INSERT INTO mobile_number (number) VALUES (?)
        ''', (mobile_number,))

        conn.commit()
        print("Data inserted successfully.")

# Example usage:
# insert_into_database('database.db', 'Hello2, Input!', 'Hello2, Output!', '123412567890')


def generate_response(response):
    global input_mesage
    global output_message
    global mobile_number
    input_mesage = response
    print("*"*100,mobile_number)

    # embeddings = OpenAIEmbeddings() 
    embeddings = OpenAIEmbeddings(model = "text-embedding-3-large")
    # pdb.set_trace()
    # Documents/
    persisted_vectorstore = FAISS.load_local("/Users/fahadali/Documents/open_ai_testing/embeddings_for_test_store/", embeddings, allow_dangerous_deserialization=True)
    # persisted_vectorstore = FAISS.load_local("/Users/fahadali/Documents/whatapp_setup/whatsapp_messenger_connect_with_custom_chatbot/start/faiss_index_constitution_update", embeddings, allow_dangerous_deserialization=True)
    qa = RetrievalQA.from_chain_type(llm=OpenAI(), chain_type="stuff", retriever=persisted_vectorstore.as_retriever())
    query = response
    result = qa.run(query)
    response =  result

    output_message = result

    database_name = 'database/database.db'
    insert_into_database(database_name,input_mesage, output_message, mobile_number)
    return response


# def generate_response(response):
#     # Return text in uppercase
#     return response.upper()


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response
    

def download_media(url):
    if not url:
        print("Error: URL parameter is required.")
        return

    try:
        # Fetch the audio data from the external URL with the auth token
        headers = {
            'Authorization': f"Bearer {ACCESS_TOKEN}",
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        # Generate a unique file name
        file_name = f"{int(time.time())}_audio.ogg"
        file_name = 'audio/'+file_name

        # Save the audio stream to a file
        with open(file_name, 'wb') as audio_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive chunks
                    audio_file.write(chunk)

        print(f"Audio file downloaded successfully: {file_name}")
        return file_name

    except requests.RequestException as e:
        print(f"Error fetching audio data: {str(e)}")
        
def extract_link(audio_id):
    access_token = ACCESS_TOKEN  # Replace with your access token
    url = f"https://graph.facebook.com/v21.0/{audio_id}"
    
    # Fetching the audio file from WhatsApp API
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    
    return response.json()['url']


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text

def convert_audio_to_text(message):
    audio_id = message['audio']['id']
    url_ = extract_link(audio_id)
    file_name = download_media(url_)
    print(file_name)
    return file_name
    


# def process_whatsapp_message(body):
#     print('abc')
#     print('abc')
#     print(body)


#     wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
#     name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

#     message = body["entry"][0]["changes"][0]["value"]["messages"][0]

#     if """type': 'audio""" in str(message):
#         pdb.set_trace()
#         file_name = convert_audio_to_text(message)
#         result_text = process_audio(file_name)
#         response = result_text
#     if """type': 'text""" in str(message):
#         message_body = message["text"]["body"]
#         response = "this is test"

#     data = get_text_message_input(mobile_number, response)
#     send_message(data)

import threading
import pdb

# Create a lock object
lock = threading.Lock()

def process_whatsapp_message(body):
    # with lock:  # Ensure thread-safe access to the critical section
    print('abc')
    print('abc')
    print(body)

    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]

    if """type': 'audio""" in str(message):
        # pdb.set_trace()
        file_name = convert_audio_to_text(message)
        result_text = process_audio(file_name, MODEL)
        response = generate_response(result_text)
        # result_text = process_audio(file_name)
        # response = result_text
    elif """type': 'text""" in str(message):  # Use `elif` to avoid checking both conditions unnecessarily
        message_body = message["text"]["body"]
        response = generate_response(message_body)
        # response = "this is test"
    else:
        response = "Unsupported message type."

    # Ensure mobile_number is defined or extracted (assuming it's `wa_id` here)
    # mobile_number = wa_id  # Or derive it based on your app's logic
    
    data = get_text_message_input(mobile_number, response)
    send_message(data)



def is_valid_whatsapp_message(body):
    global mobile_number
    # print("body"*100,body, "\n"*20)
    mobile_number = "+"+body['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
