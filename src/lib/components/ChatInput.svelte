<script>
  import { tick } from 'svelte';
  import VoiceInput from './VoiceInput.svelte';
  
  export let message = '';
  export let isTyping = false;
  export let onSendMessage = () => {};
  export let onVoiceTranscript = (text) => {};
  
  let textareaElement;

  function autoResize() {
    if (textareaElement) {
      textareaElement.style.height = 'auto';
      textareaElement.style.height = Math.min(textareaElement.scrollHeight, 120) + 'px';
    }
  }

  function handleInput() {
    autoResize();
  }

  async function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      await onSendMessage();
      await tick();
      if (textareaElement) {
        textareaElement.focus();
      }
    }
  }

  async function handleSubmit() {
    await onSendMessage();
    await tick();
    if (textareaElement) {
      textareaElement.focus();
    }
  }
</script>

<form on:submit|preventDefault={handleSubmit} class="flex gap-3 items-end flex-shrink-0">
  <div class="flex-1 relative">
    <textarea 
      bind:this={textareaElement}
      bind:value={message}
      on:input={handleInput}
      on:keydown={handleKeydown}
      placeholder="Share what's on your mind... (Enter to send, Shift+Enter for new line)"
      class="message-input"
      disabled={isTyping}
      rows="1"
    ></textarea>
  </div>
  
  <VoiceInput onTranscript={onVoiceTranscript} isDisabled={isTyping} />
  
  <button type="submit" disabled={isTyping || !message.trim()} class="send-button" aria-label="Send message">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
    </svg>
  </button>
</form>

<style>
  .message-input {
    width: 100%;
    min-height: 44px;
    max-height: 120px;
    padding: 12px 16px;
    border: 2px solid #e0e7ff;
    border-radius: 22px;
    font-family: inherit;
    font-size: 14px;
    line-height: 1.4;
    resize: none;
    overflow-y: auto;
    overflow-x: hidden;
    background-color: white;
    transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    outline: none;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .message-input::-webkit-scrollbar { display: none; }
  .message-input:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  }

  .send-button {
    width: 44px;
    height: 44px;
    background-color: #6366f1;
    color: white;
    border: none;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    flex-shrink: 0;
  }

  .send-button:hover:not(:disabled) {
    background-color: #5338f3;
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  }

  .send-button:disabled {
    background-color: #cbd5e1;
    cursor: not-allowed;
    transform: scale(1);
    box-shadow: none;
  }
</style>