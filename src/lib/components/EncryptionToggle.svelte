<script>
  export let encryptionEnabled = true;
  export let onToggle = () => {};
</script>

<button 
  on:click={onToggle}
  class="flex items-center space-x-1 px-2 py-1 rounded-full text-xs {encryptionEnabled ? 'bg-green-100 text-green-800 hover:bg-green-200' : 'bg-red-100 text-red-800 hover:bg-red-200'} transition-colors"
  title={encryptionEnabled ? 'Encryption enabled' : 'Encryption disabled'}
>
  <span class="text-sm">{encryptionEnabled ? '🔐' : '🔓'}</span>
  <span>{encryptionEnabled ? 'Encrypted' : 'Plain'}</span>
</button>