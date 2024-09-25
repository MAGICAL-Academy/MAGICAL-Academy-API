import os
import openai
from dotenv import load_dotenv

class LLMAdapter:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    async def stream_generate(self, prompt: str):
        """
        Generate text from the LLM and stream the response.
        """
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        async for chunk in response:
            if 'choices' in chunk:
                choice = chunk['choices'][0]
                if 'delta' in choice and 'content' in choice['delta']:
                    yield choice['delta']['content']

    def generate_choices(self, choice_type: str, context: str) -> list:
        """
        Generate story choices from the LLM based on context and choice type.
        """
        prompt = (
            f"Based on the following context:\n{context}\n"
            f"Generate 5 creative {choice_type} options for an interactive story."
        )
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        choices = [line.strip() for line in content.splitlines() if line.strip()]
        return choices

    def generate_final_story(self, context: str) -> str:
        """
        Generate the final story from the LLM based on the accumulated context.
        """
        prompt = f"Based on the following context:\n{context}\nGenerate the final story."
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content

    def generate_initial_choice_and_options(self, prompt: str):
        """
        Generate the initial choice type and options for starting the story.
        """
        response = self.generate_choices("initial", prompt)

        # The first item in the response should be the choice type, and the rest should be the options
        choice_type = response[0].replace("Choice Type:", "").strip()
        choices = response[1:6]  # Get the next 5 lines, which are the choices

        return choice_type, choices
