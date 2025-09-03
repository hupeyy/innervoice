<script>
  export let message;
  export let encryptionEnabled = false;
</script>

<div class="flex {message.sender === 'user' ? 'justify-end' : 'justify-start'}">
  <div class="message-bubble {message.sender === 'user' ? 'bg-indigo-500 text-white' : 'bg-white text-gray-800 shadow-md'}">
    <div class="flex items-start justify-between">
      <span class="flex-1">{message.text.trim()}</span>
      {#if encryptionEnabled}
        <span class="ml-2 text-xs opacity-50" title="Message encrypted">🔐</span>
      {/if}
    </div>
  </div>
</div>

<style>
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