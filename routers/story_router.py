import os

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
import uuid
from repository.graph_db import GraphDB  # Import from the db module
from service.story_generator.llm_adapter import LLMAdapter  # Import the LLM Adapter

app = FastAPI()
story_router = APIRouter()

# Initialize Neo4j database connection
graph_db_uri = os.getenv("GRAPH_DB_URI")
graph_db_username = os.getenv("GRAPH_DB_USERNAME")
graph_db_password = os.getenv("GRAPH_DB_PASSWORD")
db = GraphDB(graph_db_uri, graph_db_username, graph_db_password)

# Initialize LLM adapter
llm = LLMAdapter()

# Pydantic Models for API validation
class StartStoryResponse(BaseModel):
    story_id: str
    initial_choice_type: str
    initial_choices: list

class GenerateChoicesRequest(BaseModel):
    story_id: str
    current_node_id: int
    user_choice: str

class SelectChoiceRequest(BaseModel):
    story_id: str
    current_node_id: int
    choice_text: str

class StartStoryRequest(BaseModel):
    story_id: str


# 1. Start the story with an introduction prompt and ask the LLM for the first choice type
@story_router.post("/story/start", response_model=StartStoryResponse)
async def start_story():
    story_id = str(uuid.uuid4())
    db.create_story(story_id)

    # Starting prompt to explain the story and the process
    starting_prompt = (
        "We are about to embark on an interactive story. "
        "At each step, we will ask the user to make a choice that will shape the story. "
        "Please provide the first type of choice the user should make (e.g., hero, villain, place, etc.), "
        "and then provide 5 creative options for that choice."
    )

    # The LLM should respond with the first choice type and the initial options
    initial_choice_type, initial_choices = llm.generate_initial_choice_and_options(starting_prompt)

    # Return the story ID, the first choice type, and the initial choices
    return {"story_id": story_id, "initial_choice_type": initial_choice_type, "initial_choices": initial_choices}


# 2. Endpoint to generate the next set of choices based on the user's current selection
@story_router.post("/story/next-choices")
async def generate_choices(generate_choices_request: GenerateChoicesRequest):
    story_id = generate_choices_request.story_id
    current_node_id = generate_choices_request.current_node_id
    user_choice = generate_choices_request.user_choice

    # Retrieve the current story context from Neo4j
    context = db.get_story_context(story_id)

    # Store the user's choice in the context
    next_content = f"Next part of the story based on the choice: {user_choice}"
    next_node_id = db.create_node(story_id, next_content, is_choice_point=True)

    # Create an edge from the current node to the next node based on the user's choice
    db.create_edge(current_node_id, next_node_id, user_choice)

    # Ask the LLM what the next choice type should be
    choice_type_prompt = (
        f"Based on the following context:\n{context}\n"
        f"The user chose '{user_choice}'. "
        "What type of choice should the user make next (e.g., hero, villain, place, etc.)?"
    )
    next_choice_type, next_choices = llm.generate_initial_choice_and_options(choice_type_prompt)

    # Return the next choice type and available options to the user
    return {"next_choice_type": next_choice_type, "choices": next_choices, "next_node_id": next_node_id}


# 3. Endpoint to store the user's selected choice and proceed to the next stage
@story_router.post("/story/select-choice")
async def select_choice(select_choice_request: SelectChoiceRequest):
    story_id = select_choice_request.story_id
    current_node_id = select_choice_request.current_node_id
    user_choice = select_choice_request.choice_text

    # Retrieve the current story context
    context = db.get_story_context(story_id)

    # Add the user's choice to the Neo4j graph and update the story path
    next_content = f"Next part of the story based on the choice: {user_choice}"
    next_node_id = db.create_node(story_id, next_content, is_choice_point=True)

    # Create an edge from the current node to the next node based on the user's choice
    db.create_edge(current_node_id, next_node_id, user_choice)

    return {"message": "Choice stored successfully", "next_node_id": next_node_id}


# 4. Endpoint to generate the final story from the accumulated context
@story_router.post("/story/start-story")
async def start_story(start_story_request: StartStoryRequest):
    story_id = start_story_request.story_id

    # Get the entire story context (path of choices) from Neo4j
    context = db.get_story_context(story_id)

    # Generate the final story using the LLM
    story_intro = llm.generate_final_story(context)

    return {"story_intro": story_intro}


# Close the Neo4j connection when shutting down
@app.on_event("shutdown")
def shutdown_event():
    db.close()

