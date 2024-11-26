import speech_recognition as sr
from pydub import AudioSegment

def convert_audio_to_text(audio_file_path):
    """
    Convert audio to text using Google Speech Recognition API.
    """
    recognizer = sr.Recognizer()

    # Open the audio file using speech_recognition
    with sr.AudioFile(audio_file_path) as source:
        audio_data = recognizer.record(source)  # Record the audio data

        try:
            # Recognize the speech in the audio file using Google's API
            text = recognizer.recognize_google(audio_data, language="ur")
            return text
        except sr.UnknownValueError:
            return "آپ کی آواز واضح نہیں ہے"  # "Your voice is unclear"
        except sr.RequestError:
            return "Sorry, my speech service is down"

def convert_opus_to_wav(opus_file_path, wav_file_path):
    """
    Convert an .opus audio file to .wav format using pydub.
    """
    # Load the OPUS file using pydub
    audio = AudioSegment.from_file(opus_file_path, format="opus")
    
    # Export the audio as a WAV file
    audio.export(wav_file_path, format="wav")

def process_audio(opus_file_path):
    """
    Full process to convert OPUS file to WAV, then convert WAV to text.
    """
    # Define the output .wav file path
    wav_file_path = "converted_audio.wav"
    
    # Convert OPUS to WAV
    convert_opus_to_wav(opus_file_path, wav_file_path)
    
    # Convert WAV to text
    text = convert_audio_to_text(wav_file_path)
    
    return text

# Example usage:
# opus_file = "output_audio.opus"  # Replace with your .opus file path
# result_text = process_audio(opus_file)

# print(result_text)  # Print the result from speech-to-text


# Example usage:
opus_file = "/Users/fahadali/Downloads/output_audio.opus"  # Replace with your .opus file path
result_text = process_audio(opus_file)

print(result_text)  # Print the result from speech-to-text