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

// Handle LLM questions
socket.on('llm_question', (data) => {
    storyId = data.story_id;
    currentNodeId = data.current_node_id;
    const question = data.question;

    appendToStory(`\nLLM: ${question}\n`);
    displayInputField();
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

function displayInputField() {
    choicesDiv.innerHTML = '';
    const inputField = document.createElement('input');
    inputField.type = 'text';
    inputField.id = 'user-input';
    inputField.placeholder = 'Your response...';
    inputField.style.width = '80%';
    inputField.style.padding = '10px';
    inputField.style.fontSize = '16px';

    const sendButton = document.createElement('button');
    sendButton.textContent = 'Send';
    sendButton.style.padding = '10px';
    sendButton.style.fontSize = '16px';
    sendButton.style.marginLeft = '10px';

    sendButton.addEventListener('click', () => {
        const userInput = inputField.value.trim();
        if (userInput !== '') {
            sendUserResponse(userInput);
            inputField.value = '';
        }
    });

    inputField.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            sendButton.click();
        }
    });

    choicesDiv.appendChild(inputField);
    choicesDiv.appendChild(sendButton);
    inputField.focus();
}

function appendToStory(text) {
    storyDiv.textContent += text;
    storyDiv.scrollTop = storyDiv.scrollHeight; // Scroll to bottom
}

function sendUserResponse(userInput) {
    appendToStory(`\nYou: ${userInput}\n`);
    choicesDiv.innerHTML = ''; // Clear input field
    socket.emit('user_response', {
        story_id: storyId,
        user_input: userInput,
        current_node_id: currentNodeId
    });
}
