<script>
  import JournalNotes from './JournalNotes.svelte';
  
  export let journal = null;
  export let userNotes = '';
  export let onNotesChange = (notes) => {};
  export let onSwitchToChat = () => {};
  export let onTitleChange = (title) => {};
  
  let showTranscript = false;
  let isEditingTitle = false;
  let editableTitle = '';
  
  // Initialize editable title when journal changes
  $: if (journal && journal.title) {
    editableTitle = journal.title;
  }
  
  function startEditingTitle() {
    isEditingTitle = true;
    editableTitle = journal.title || '';
    setTimeout(() => {
      const titleInput = document.querySelector('.title-input');
      if (titleInput) {
        titleInput.focus();
        titleInput.select();
      }
    }, 10);
  }
  
  function saveTitle() {
    if (editableTitle.trim()) {
      onTitleChange(editableTitle.trim());
    } else {
      editableTitle = journal.title || '';
    }
    isEditingTitle = false;
  }
  
  function handleTitleKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault(); // 🔧 FIX: Prevent default form submission
      saveTitle();
    } else if (event.key === 'Escape') {
      event.preventDefault(); // 🔧 FIX: Prevent default escape behavior
      editableTitle = journal.title || '';
      isEditingTitle = false;
    }
  }
  
  function handleTitleBlur() {
    saveTitle();
  }
</script>

<div class="journal-container flex-1 bg-white rounded-lg shadow-md p-6 overflow-y-auto">
  {#if journal}
    <!-- Editable Title Section -->
    <div class="mb-6">
      <div class="title-section mb-4">
        {#if isEditingTitle}
          <input
            class="title-input"
            type="text"
            bind:value={editableTitle}
            on:keydown={handleTitleKeydown}
            on:blur={handleTitleBlur}
            placeholder="Enter journal title..."
          />
        {:else}
          <button 
            class="journal-title" 
            on:click={startEditingTitle}
            on:keydown={(e) => e.key === 'Enter' && startEditingTitle()}
          >
            {journal.title || 'Untitled Entry'}
            <span class="edit-icon">✏️</span>
          </button>
        {/if}
        <div class="journal-date">
          {new Date(journal.date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </div>
      </div>
      
      <!-- Rest of your component remains the same -->
      <h2 class="text-xl font-semibold text-indigo-700 mb-2">Session Summary</h2>
      <p class="text-lg text-gray-800 mb-2 whitespace-pre-line">{journal.summary}</p>
      <hr class="mb-2">
      <div>
        <h3 class="font-medium text-indigo-700 mb-1">Key Insights</h3>
        <ul class="list-disc ml-6 text-gray-700">
          {#each journal.insights as insight}
            <li>{insight}</li>
          {/each}
        </ul>
      </div>
      {#if journal.mood}
        <div class="mt-3 text-sm text-indigo-500">Mood: <span class="font-semibold">{journal.mood}</span></div>
      {/if}
    </div>
    
    <div class="mb-5">
      <button class="text-xs underline text-indigo-600" on:click={() => showTranscript = !showTranscript}>
        {showTranscript ? 'Hide Transcript' : 'Show Full Conversation Transcript'}
      </button>
      {#if showTranscript}
        <div class="bg-gray-50 rounded-md p-3 mt-2 max-h-40 overflow-y-auto text-xs text-gray-700">
          {#each journal.messages as entry}
            <div class="mb-1">
              <span class="font-bold">{entry.role === 'ai' ? 'InnerVoice' : 'You'}:</span>
              <span class="ml-2">{entry.text}</span>
              <span class="ml-2 text-gray-400">({new Date(entry.timestamp).toLocaleTimeString()})</span>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    
    <JournalNotes {userNotes} {onNotesChange} />
  {:else}
    <div class="text-center py-12">
      <div class="text-4xl mb-4">📔</div>
      <h3 class="text-lg font-medium text-gray-600 mb-2">No journal yet</h3>
      <p class="text-gray-500">Have a conversation in Chat to generate your first entry!</p>
      <button on:click={onSwitchToChat} class="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600 transition-colors">
        Start Chatting
      </button>
    </div>
  {/if}
</div>

<style>
  .journal-container {
    scrollbar-width: thin;
    scrollbar-color: #cbd5e1 #f1f5f9;
  }
  
  .journal-container::-webkit-scrollbar {
    width: 6px;
  }
  
  .journal-container::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
  }
  
  .journal-container::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }
  
  /* Title Styles */
  .title-section {
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 1rem;
  }
  
  .journal-title {
    font-size: 1.75rem;
    font-size: 1.75rem;
    font-weight: 700;
    color: #1f2937;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    border: none;
    background: none;
    text-align: left;
  }

  .edit-icon {
    font-size: 1rem;
    opacity: 0;
    transition: opacity 0.2s;
  }
  
  .journal-title:hover .edit-icon {
    opacity: 1;
  }
  
  .title-input {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1f2937;
    border: 2px solid #6366f1;
    border-radius: 6px;
    padding: 0.5rem;
    width: 100%;
    background: white;
    margin-bottom: 0.5rem;
  }
  
  .title-input:focus {
    outline: none;
    border-color: #4f46e5;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  }
  
  .journal-date {
    font-size: 0.875rem;
    color: #6b7280;
    font-style: italic;
  }
</style>