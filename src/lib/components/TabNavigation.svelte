<script>
  export let activeTab = 'chat';
  export let onTabChange = (tab) => {};
</script>

<nav class="mt-4">
  <div class="flex justify-center space-x-1 bg-white rounded-lg p-1 max-w-xs mx-auto shadow-sm">
    <button 
      on:click={() => onTabChange('chat')} 
      class="px-4 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'chat' ? 'bg-indigo-500 text-white' : 'text-indigo-600 hover:text-indigo-800'}"
    >
      💬 Chat
    </button>
    <button 
      on:click={() => onTabChange('journal')} 
      class="px-4 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'journal' ? 'bg-indigo-500 text-white' : 'text-indigo-600 hover:text-indigo-800'}"
    >
      📔 Today
    </button>
    <button 
      on:click={() => onTabChange('analysis')} 
      class="px-4 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'analysis' ? 'bg-indigo-500 text-white' : 'text-indigo-600 hover:text-indigo-800'}"
    >
      📊 Analysis
    </button>
  </div>
</nav>
