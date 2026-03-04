document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const userMessage = chatInput.value.trim();

        if (!userMessage) {
            return;
        }

        // Display user's message
        appendMessage(userMessage, 'user');
        chatInput.value = '';

        try {
            // Send message to the backend
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();

            // Display bot's response
            if (data.response) {
                appendMessage(data.response, 'bot');
            } else if (data.error) {
                appendMessage(`Error: ${data.error}`, 'bot');
            }

        } catch (error) {
            console.error('Error sending message:', error);
            appendMessage('Sorry, something went wrong. Please try again.', 'bot');
        }
    });

    function appendMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        
        const paragraph = document.createElement('p');
        paragraph.textContent = message;
        messageElement.appendChild(paragraph);
        
        chatWindow.appendChild(messageElement);

        // Scroll to the bottom of the chat window
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});