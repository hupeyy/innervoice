<script>
  import EncryptionToggle from './EncryptionToggle.svelte';
  import HistoryToggle from './HistoryToggle.svelte';
  
  export let encryptionEnabled = true;
  export let onToggleEncryption = () => {};
  export let onToggleHistory = () => {};
</script>

<header class="p-4 text-center">
  <div class="flex items-center justify-between max-w-2xl mx-auto">
    <EncryptionToggle {encryptionEnabled} onToggle={onToggleEncryption} />
    
    <div>
      <h1 class="text-2xl font-bold text-indigo-800">InnerVoice</h1>
      <p class="text-indigo-600">Your conversational journal companion</p>
    </div>
    
    <HistoryToggle onToggle={onToggleHistory} />
  </div>
</header>
