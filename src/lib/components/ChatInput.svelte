<script>
  export let message = '';
  export let isTyping = false;
  export let onSendMessage;
  export let onVoiceTranscript;

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (message.trim() && !isTyping) {
        onSendMessage();
      }
    }
  }

  function handleSend() {
    if (message.trim() && !isTyping) {
      onSendMessage();
    }
  }
</script>

<div class="input-wrapper">
  <div class="input-container">
    <textarea
      bind:value={message}
      on:keydown={handleKeyDown}
      placeholder="Share your thoughts..."
      disabled={isTyping}
      rows="1"
      class="message-textarea"
    ></textarea>
    
    <button 
      class="send-button"
      on:click={handleSend}
      disabled={!message.trim() || isTyping}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
      </svg>
    </button>
  </div>
</div>

<style>
  .input-wrapper {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    padding: 0.75rem;
  }

  .input-container {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
  }

  .message-textarea {
    flex: 1;
    background: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 14px;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    line-height: 1.4;
    color: #333;
    resize: none;
    min-height: 44px;
    max-height: 120px;
    font-family: inherit;
    transition: all 0.2s ease;
  }

  .message-textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    background: rgba(255, 255, 255, 0.95);
  }

  .message-textarea::placeholder {
    color: rgba(51, 51, 51, 0.6);
  }

  .message-textarea:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .send-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 50%;
    color: white;
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }

  .send-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  }

  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
</style>