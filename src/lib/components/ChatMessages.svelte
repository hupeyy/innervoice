<script>
  import { afterUpdate } from 'svelte';
  
  export let messages = [];
  export let isTyping = false;
  export let encryptionEnabled = true;
  
  let messagesContainer;

  // Auto-scroll to bottom when new messages arrive
  afterUpdate(() => {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  });
</script>

<div class="messages-container" bind:this={messagesContainer}>
  {#each messages as message, index (index)}
    <div class="message message-{message.sender}">
      <div class="message-content">
        <div class="message-text">{message.text}</div>
        {#if message.timestamp}
          <div class="message-time">
            {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </div>
        {/if}
      </div>
    </div>
  {/each}
  
  {#if isTyping}
    <div class="message message-ai">
      <div class="message-content">
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .messages-container {
    padding: 1rem;
    min-height: 200px;
  }

  .message {
    margin-bottom: 1.5rem;
    display: flex;
    max-width: 75%;
  }

  .message-user {
    margin-left: auto;
    justify-content: flex-end;
  }

  .message-ai {
    margin-right: auto;
    justify-content: flex-start;
  }

  .message-content {
    padding: 0.75rem 1rem;
    border-radius: 18px;
    word-wrap: break-word;
    line-height: 1.4;
  }

  .message-user .message-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-bottom-right-radius: 6px;
  }

  .message-ai .message-content {
    background: rgba(255, 255, 255, 0.9);
    color: #333;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-bottom-left-radius: 6px;
    backdrop-filter: blur(10px);
  }

  .message-text {
    margin-bottom: 0.25rem;
  }

  .message-time {
    font-size: 0.75rem;
    opacity: 0.7;
  }

  /* Typing indicator */
  .typing-indicator {
    display: flex;
    gap: 4px;
    align-items: center;
    padding: 4px 0;
  }

  .typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #667eea;
    animation: typing 1.4s ease-in-out infinite;
  }

  .typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }

  .typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes typing {
    0%, 60%, 100% {
      transform: translateY(0);
      opacity: 0.4;
    }
    30% {
      transform: translateY(-8px);
      opacity: 1;
    }
  }
</style>