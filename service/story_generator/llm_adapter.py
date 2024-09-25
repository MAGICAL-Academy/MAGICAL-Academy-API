import os
from mistralai import Mistral, UserMessage
from dotenv import load_dotenv
import asyncio

class LLMAdapter:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.client = Mistral(api_key=self.api_key)
        self.model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    async def generate_llm_response(self, context: str, user_input: str = None):
        """
        Generate the next LLM response based on the context and optional user input.
        If user_input is provided, it's incorporated into the context.
        """
        if user_input:
            context += f"\nUser: {user_input}"

        prompt = context

        messages = [UserMessage(content=prompt)]
        response = await self.client.chat.complete_async(
            model=self.model,
            messages=messages,
        )
        content = response.choices[0].message.content.strip()
        return content

    async def stream_llm_response(self, context: str, user_input: str = None):
        """
        Stream the LLM response based on the context and optional user input.
        """
        if user_input:
            context += f"\nUser: {user_input}"

        prompt = context

        messages = [UserMessage(content=prompt)]
        response = self.client.chat.stream(
            model=self.model,
            messages=messages,
        )

        async for event in response:
            if event.delta:
                yield event.delta

    async def get_initial_prompt(self):
        """
        Use the LLM to generate the initial prompt to start the story.
        """
        system_prompt = "Let's start an interactive story. You'll ask the user questions to help shape the story. Begin by asking an open-ended question to start the story."

        messages = [UserMessage(content=system_prompt)]
        response = await self.client.chat.complete_async(
            model=self.model,
            messages=messages,
        )
        initial_prompt = response.choices[0].message.content.strip()
        return initial_prompt
