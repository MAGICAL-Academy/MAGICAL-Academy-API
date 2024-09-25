import os
import json
import shutil
from datetime import datetime


class FileStorageService:
    def __init__(self, base_path):
        self.base_path = base_path
        self.audio_path = os.path.join(base_path, 'audio')
        self.image_path = os.path.join(base_path, 'images')
        self.json_path = os.path.join(base_path, 'json')

        # Create directories if they don't exist
        for path in [self.audio_path, self.image_path, self.json_path]:
            os.makedirs(path, exist_ok=True)

    def store_audio(self, audio_data, filename):
        file_path = os.path.join(self.audio_path, filename)
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        return file_path

    def store_image(self, image_data, filename):
        file_path = os.path.join(self.image_path, filename)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        return file_path

    def store_json(self, data, filename):
        file_path = os.path.join(self.json_path, filename)
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return file_path

    def store_llm_interaction(self, input_data, output_data, model):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llm_interaction_{timestamp}.json"
        data = {
            "input": input_data,
            "output": output_data,
            "model": model,
            "timestamp": timestamp
        }
        return self.store_json(data, filename)

    def get_file(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return f.read()
        return None

    def get_json(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None


# Usage example
if __name__ == "__main__":
    storage_service = FileStorageService('/path/to/your/storage')

    # Store an audio file
    with open('sample_audio.mp3', 'rb') as audio_file:
        audio_data = audio_file.read()
    audio_path = storage_service.store_audio(audio_data, 'sample_audio.mp3')
    print(f"Stored audio file at: {audio_path}")

    # Store an image file
    with open('sample_image.jpg', 'rb') as image_file:
        image_data = image_file.read()
    image_path = storage_service.store_image(image_data, 'sample_image.jpg')
    print(f"Stored image file at: {image_path}")

    # Store an LLM interaction
    json_path = storage_service.store_llm_interaction(
        input_data={"prompt": "Generate a space adventure for kids"},
        output_data={"story": "Astro the Space Dog embarked on an exciting journey..."},
        model="GPT-3.5-turbo"
    )
    print(f"Stored LLM interaction JSON at: {json_path}")