document.addEventListener('DOMContentLoaded', function() {
    console.log('🔥 Health & Glow Chat Loaded');
    
    // SAFE element access - No more null errors
    const chatInput = document.getElementById('chatInput');
    const chatForm = document.getElementById('chatForm');
    const messagesDiv = document.getElementById('messages');
    
    if (!chatInput || !chatForm || !messagesDiv) {
        console.error('❌ Chat elements missing');
        return;
    }
    
    // Send message
    chatForm.onsubmit = async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, 'user');
        chatInput.value = '';
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: new URLSearchParams({message})
            });
            const data = await response.json();
            addMessage(data.message || 'Processing...', 'bot');
        } catch (error) {
            addMessage('Connection error', 'bot');
        }
    };
    
    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = `message ${type}`;
        div.textContent = text;
        messagesDiv.appendChild(div);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
});
