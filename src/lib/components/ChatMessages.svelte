<script>
  import MessageBubble from './MessageBubble.svelte';
  
  export let messages = [];
  export let isTyping = false;
  export let encryptionEnabled = false;
</script>

<div class="chat-messages-container flex-1 overflow-y-auto space-y-4 mb-4 pr-2" role="log">
  {#each messages as message}
    <MessageBubble {message} {encryptionEnabled} />
  {/each}
  
  {#if isTyping}
    <div class="flex justify-start">
      <div class="message-bubble bg-white text-gray-800 shadow-md">
        <div class="flex space-x-1">
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .chat-messages-container {
    scrollbar-width: thin;
    scrollbar-color: #cbd5e1 #f1f5f9;
  }
  
  .chat-messages-container::-webkit-scrollbar {
    width: 6px;
  }
  
  .chat-messages-container::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
  }
  
  .chat-messages-container::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  .message-bubble {
    max-width: min(75%, 500px);
    min-width: 40px;
    padding: 12px 16px;
    border-radius: 1.5rem;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-wrap: break-word;
    word-break: normal;
    hyphens: none;
    line-height: 1.4;
  }
</style>
