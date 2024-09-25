// Connect to the Socket.IO server
const socket = io('http://localhost:8000');

// DOM elements
const startButton = document.getElementById('start-button');
const storyDiv = document.getElementById('story');
const choicesDiv = document.getElementById('choices');

let storyId = null;
let currentNodeId = null;

// Event listener for the start button
startButton.addEventListener('click', () => {
    startButton.disabled = true;
    startButton.textContent = 'Story in Progress...';
    socket.emit('start_story', {});
});

// Handle initial choices
socket.on('initial_choices', (data) => {
    storyId = data.story_id;
    currentNodeId = data.current_node_id;
    const choiceType = data.choice_type;
    const choices = data.choices;

    displayMessage(`Choose a ${choiceType}:`);
    displayChoices(choices);
});

// Handle story updates (streamed content)
socket.on('story_update', (data) => {
    const content = data.content;
    appendToStory(content);
});

// Handle next choices
socket.on('next_choices', (data) => {
    currentNodeId = data.current_node_id;
    const choiceType = data.next_choice_type;
    const choices = data.choices;

    displayMessage(`Choose a ${choiceType}:`);
    displayChoices(choices);
});

// Handle final story
socket.on('final_story', (data) => {
    const content = data.content;
    appendToStory('\n\nThe End.\n\n');
    appendToStory(content);
    displayMessage('Story Completed!');
    startButton.disabled = false;
    startButton.textContent = 'Start New Story';
});

// Handle errors
socket.on('error', (data) => {
    console.error('Error:', data.message);
    displayMessage(`Error: ${data.message}`);
    startButton.disabled = false;
    startButton.textContent = 'Start Story';
});

// Functions to update the UI
function displayMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.style.fontWeight = 'bold';
    messageDiv.style.marginTop = '20px';
    messageDiv.textContent = message;
    choicesDiv.innerHTML = '';
    choicesDiv.appendChild(messageDiv);
}

function displayChoices(choices) {
    choices.forEach(choice => {
        const button = document.createElement('button');
        button.className = 'choice-button';
        button.textContent = choice;
        button.addEventListener('click', () => {
            makeChoice(choice);
        });
        choicesDiv.appendChild(button);
    });
}

function appendToStory(text) {
    storyDiv.textContent += text;
    storyDiv.scrollTop = storyDiv.scrollHeight; // Scroll to bottom
}

function makeChoice(choice) {
    choicesDiv.innerHTML = '';
    socket.emit('make_choice', {
        story_id: storyId,
        user_choice: choice,
        current_node_id: currentNodeId
    });
}

// Optional: Request the final story (if applicable)
// function requestFinalStory() {
//     socket.emit('get_final_story', { story_id: storyId });
// }
