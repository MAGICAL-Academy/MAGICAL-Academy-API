import os
import uuid
import asyncio
import socketio
from aiohttp import web
from dotenv import load_dotenv
from service.story_generator.llm_adapter import LLMAdapter
from repository.graph_db import GraphDB  # Ensure this is implemented

# Load environment variables
load_dotenv()

# Initialize Socket.IO server
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# Initialize LLM adapter and database
llm = LLMAdapter()

graph_db_uri = os.getenv("GRAPH_DB_URI")
graph_db_username = os.getenv("GRAPH_DB_USERNAME")
graph_db_password = os.getenv("GRAPH_DB_PASSWORD")
db = GraphDB(graph_db_uri, graph_db_username, graph_db_password)

# Event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def start_story(sid, data):
    story_id = str(uuid.uuid4())
    db.create_story(story_id)

    # Starting prompt to explain the story and the process
    starting_prompt = (
        "We are about to embark on an interactive story. "
        "At each step, you will make choices that shape the story. "
        "Let's begin!"
    )

    # Generate initial choice type and options
    choice_type, choices = llm.generate_initial_choice_and_options(starting_prompt)

    # Send initial choices to client
    await sio.emit('initial_choices', {
        'story_id': story_id,
        'choice_type': choice_type,
        'choices': choices,
        'current_node_id': 0  # Assuming 0 is the root node
    }, room=sid)

@sio.event
async def make_choice(sid, data):
    story_id = data.get('story_id')
    user_choice = data.get('user_choice')
    current_node_id = data.get('current_node_id')

    if not all([story_id, user_choice, current_node_id is not None]):
        await sio.emit('error', {'message': 'Invalid data received.'}, room=sid)
        return

    # Retrieve the current story context from the database
    context = db.get_story_context(story_id)

    # Store the user's choice in the database
    next_content = f"User chose: {user_choice}"
    next_node_id = db.create_node(story_id, next_content, is_choice_point=True)
    db.create_edge(current_node_id, next_node_id, user_choice)

    # Generate the next part of the story and stream it to the client
    prompt = f"{context}\nUser chose '{user_choice}'. Continue the story in second person."
    async for chunk in llm.stream_generate(prompt):
        await sio.emit('story_update', {'content': chunk}, room=sid)

    # After streaming the story, generate the next set of choices
    choice_prompt = f"{context}\nUser chose '{user_choice}'. What should the user decide next? Provide 5 options."
    next_choice_type, next_choices = llm.generate_initial_choice_and_options(choice_prompt)

    # Send the next choices to the client
    await sio.emit('next_choices', {
        'next_choice_type': next_choice_type,
        'choices': next_choices,
        'current_node_id': next_node_id
    }, room=sid)

@sio.event
async def get_final_story(sid, data):
    story_id = data.get('story_id')

    if not story_id:
        await sio.emit('error', {'message': 'Invalid data received.'}, room=sid)
        return

    # Get the entire story context
    context = db.get_story_context(story_id)

    # Generate the final story
    final_story = llm.generate_final_story(context)

    # Send the final story to the client
    await sio.emit('final_story', {'content': final_story}, room=sid)

# Run the Socket.IO server
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8000)
