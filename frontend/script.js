document.addEventListener('DOMContentLoaded', () => {
  const chatLog = document.getElementById('chat-log');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');

  const appendMessage = (text, sender) => {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    msgDiv.textContent = text;
    chatLog.appendChild(msgDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
  };

  const sendMessage = async (message) => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Chat error', err);
      return { reply: '[SYSTEM] Communication error.', ended: false };
    }
  };

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;
    appendMessage(message, 'user');
    userInput.value = '';
    const { reply, ended } = await sendMessage(message);
    appendMessage(reply, 'bot');
    if (ended) {
      // Disable further input
      userInput.disabled = true;
      chatForm.querySelector('button').disabled = true;
    }
  });
});
