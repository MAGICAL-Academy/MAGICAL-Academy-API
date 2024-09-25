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

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), 'client/static')
app.router.add_static('/static/', path=os.path.join(static_dir))
app.router.add_get('/', lambda request: web.FileResponse(os.path.join(static_dir, 'index.html')))

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

    # Get the initial prompt from the LLM
    try:
        initial_prompt = await llm.get_initial_prompt()
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, room=sid)
        return

    # Store initial prompt in the context
    initial_node_id = db.create_node(story_id, f"LLM: {initial_prompt}", is_choice_point=False)

    # Send the initial prompt to the client
    await sio.emit('llm_question', {
        'story_id': story_id,
        'current_node_id': initial_node_id,
        'question': initial_prompt
    }, room=sid)

@sio.event
async def user_response(sid, data):
    story_id = data.get('story_id')
    user_input = data.get('user_input')
    current_node_id = data.get('current_node_id')

    if not all([story_id, user_input, current_node_id is not None]):
        await sio.emit('error', {'message': 'Invalid data received.'}, room=sid)
        return

    # Retrieve the current story context from the database
    context = db.get_story_context(story_id)

    # Store the user's input in the database
    user_node_content = f"User: {user_input}"
    user_node_id = db.create_node(story_id, user_node_content, is_choice_point=True)
    db.create_edge(current_node_id, user_node_id, "User Input")

    # Generate the next LLM response based on the context and user input
    try:
        llm_response = await llm.generate_llm_response(context, user_input)
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, room=sid)
        return

    # Store the LLM's response in the database
    llm_node_content = f"LLM: {llm_response}"
    llm_node_id = db.create_node(story_id, llm_node_content, is_choice_point=False)
    db.create_edge(user_node_id, llm_node_id, "LLM Response")

    # Send the LLM's response (question or story continuation) to the client
    await sio.emit('llm_question', {
        'story_id': story_id,
        'current_node_id': llm_node_id,
        'question': llm_response
    }, room=sid)

# Run the Socket.IO server
if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8000)
