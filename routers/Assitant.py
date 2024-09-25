from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
import os
import asyncio
import json

router = APIRouter()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Define request models
class CreateAssistantRequest(BaseModel):
    name: str
    instructions: str
    model: str = "gpt-4-turbo-preview"
    tools: Optional[List[dict]] = None


class CreateMessageRequest(BaseModel):
    content: str


class RunAssistantRequest(BaseModel):
    assistant_id: str
    thread_id: str


async def stream_run_events(thread_id: str, run_id: str):
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            yield f"data: {json.dumps({'status': run.status})}\n\n"

            if run.status == 'completed':
                messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
                if messages.data:
                    latest_message = messages.data[0]
                    yield f"data: {json.dumps({'content': latest_message.content[0].text.value})}\n\n"
                break
            elif run.status in ['failed', 'cancelled']:
                yield f"data: {json.dumps({'error': f'Run {run.status}'})}\n\n"
                break

            await asyncio.sleep(1)
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            break

    yield "data: [DONE]\n\n"


@router.post("/assistants")
async def create_assistant(request: CreateAssistantRequest):
    try:
        assistant = client.beta.assistants.create(
            name=request.name,
            instructions=request.instructions,
            model=request.model,
            tools=request.tools or []
        )
        return {"assistant_id": assistant.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads")
async def create_thread():
    try:
        thread = client.beta.threads.create()
        return {"thread_id": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/threads/{thread_id}/messages")
async def create_message(thread_id: str, request: CreateMessageRequest):
    try:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.content
        )
        return {"message_id": message.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_assistant(request: RunAssistantRequest):
    try:
        run = client.beta.threads.runs.create(
            thread_id=request.thread_id,
            assistant_id=request.assistant_id
        )
        return StreamingResponse(stream_run_events(request.thread_id, run.id), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional endpoints can be added here as needed