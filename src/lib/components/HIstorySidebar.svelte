<script>
  import { onMount } from 'svelte';
  
  export let isOpen = false;
  export let onClose = () => {};
  
  let pastEntries = [];
  let searchDate = '';
  let selectedEntry = null;
  let loading = false;
  
  async function loadPastEntries() {
    loading = true;
    try {
      const response = await fetch('http://localhost:8000/api/journal/history');
      if (response.ok) {
        const data = await response.json();
        pastEntries = data.entries;
      }
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      loading = false;
    }
  }
  
  async function searchByDate() {
    if (!searchDate) {
      loadPastEntries();
      return;
    }
    
    loading = true;
    try {
      const response = await fetch(`http://localhost:8000/api/journal/search?date=${searchDate}`);
      if (response.ok) {
        const data = await response.json();
        pastEntries = data.entries;
      }
    } catch (error) {
      console.error('Error searching by date:', error);
    } finally {
      loading = false;
    }
  }
  
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });
  }
  
  function getRelativeDate(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      const daysAgo = Math.floor((today - date) / (1000 * 60 * 60 * 24));
      return `${daysAgo} days ago`;
    }
  }
  
  function viewEntry(entry) {
    selectedEntry = entry;
  }
  
  function closeEntryView() {
    selectedEntry = null;
  }
  
  // Load entries when sidebar opens
  $: if (isOpen) {
    loadPastEntries();
  }
  
  // Handle escape key to close sidebar
  function handleKeydown(event) {
    if (event.key === 'Escape') {
      if (selectedEntry) {
        closeEntryView();
      } else {
        onClose();
      }
    }
  }
  
  // Handle overlay click - only close if clicking the overlay itself
  function handleOverlayClick(event) {
    if (event.target === event.currentTarget) {
      onClose();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<!-- Sidebar Container - Only show when open -->
{#if isOpen}
  <!-- Backdrop with blur effect -->
  <div 
    class="fixed inset-0 backdrop-blur-xs z-40 transition-all duration-300"
    on:click={handleOverlayClick}
    role="button"
    tabindex="0"
    aria-label="Close history sidebar by clicking outside"
  >
    <!-- Sidebar -->
    <div 
      class="fixed top-0 right-0 h-full w-96 bg-white shadow-2xl transform transition-transform duration-300 z-50 translate-x-0"
      on:click|stopPropagation
      role="dialog"
      aria-modal="true"
      aria-labelledby="sidebar-title"
    >
      
      <!-- Sidebar Header -->
      <div class="p-4 border-b border-gray-200 bg-indigo-50">
        <div class="flex items-center justify-between">
          <div>
            <h2 id="sidebar-title" class="text-lg font-semibold text-indigo-800">Journal History</h2>
            <p class="text-sm text-indigo-600">Your past reflections</p>
          </div>
          <button 
            on:click={onClose}
            class="p-2 hover:bg-indigo-100 rounded-full transition-colors"
            aria-label="Close history sidebar"
          >
            <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <!-- Date Search -->
        <div class="mt-4 flex gap-2">
          <input 
            type="date" 
            bind:value={searchDate}
            class="flex-1 px-3 py-2 text-sm border border-indigo-200 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="Search by date..."
            aria-label="Select date to search journal entries"
          />
          <button 
            on:click={searchByDate}
            class="px-3 py-2 bg-indigo-500 text-white text-sm rounded-md hover:bg-indigo-600 transition-colors"
            aria-label="Search journal entries by selected date"
          >
            Search
          </button>
        </div>
        
        {#if searchDate}
          <button 
            on:click={() => { searchDate = ''; loadPastEntries(); }}
            class="mt-2 text-sm text-indigo-600 hover:text-indigo-800"
            aria-label="Clear date search and show all entries"
          >
            Clear search
          </button>
        {/if}
      </div>
      
      <!-- Sidebar Content -->
      <div class="flex-1 overflow-y-auto p-4 h-[calc(100vh-180px)]">
        {#if loading}
          <div class="flex justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" aria-label="Loading journal entries"></div>
          </div>
        {:else if pastEntries.length > 0}
          <div class="space-y-4">
            {#each pastEntries as entry}
              <div class="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors cursor-pointer"
                   on:click={() => viewEntry(entry)}
                   on:keydown={(e) => e.key === 'Enter' && viewEntry(entry)}
                   role="button"
                   tabindex="0"
                   aria-label="View journal entry from {formatDate(entry.date)}">
                
                <div class="flex items-center justify-between mb-2">
                  <h3 class="font-medium text-gray-800 text-sm">{formatDate(entry.date)}</h3>
                  <span class="text-xs text-indigo-600 bg-indigo-100 px-2 py-1 rounded-full">
                    {getRelativeDate(entry.date)}
                  </span>
                </div>
                
                <p class="text-sm text-gray-600 line-clamp-3">
                  {entry.content.length > 100 ? entry.content.substring(0, 100) + '...' : entry.content}
                </p>
                
                <div class="flex items-center mt-2 space-x-3 text-xs text-gray-500">
                  <span>💬 {entry.messageCount} messages</span>
                  <span>😊 {entry.mood || 'Neutral'}</span>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-center py-12">
            <div class="text-4xl mb-4">📚</div>
            <h3 class="text-lg font-medium text-gray-600 mb-2">No entries found</h3>
            <p class="text-sm text-gray-500">
              {searchDate ? 'No journal entries for this date.' : 'Your journal history will appear here.'}
            </p>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<!-- Full Entry Modal -->
{#if selectedEntry}
  <div class="fixed inset-0 backdrop-blur-xs bg-opacity-50 z-60 flex items-center justify-center p-4">
    <div class="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto" 
         on:click|stopPropagation
         role="dialog"
         aria-modal="true"
         aria-labelledby="entry-title">
      <div class="p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 id="entry-title" class="text-xl font-semibold text-gray-800">
            {formatDate(selectedEntry.date)}
          </h2>
          <button 
            on:click={closeEntryView}
            class="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close journal entry view"
          >
            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div class="prose prose-sm max-w-none">
          <div class="bg-amber-50 border-l-4 border-amber-400 p-4 mb-4">
            <p class="text-sm text-amber-700">
              ✨ Generated from your conversation with InnerVoice
            </p>
          </div>
          
          <div class="whitespace-pre-wrap text-gray-700 leading-relaxed">
            {selectedEntry.content}
          </div>
        </div>
        
        <div class="flex items-center mt-6 space-x-4 text-sm text-gray-500">
          <span>💬 {selectedEntry.messageCount} messages</span>
          <span>😊 {selectedEntry.mood || 'Neutral'}</span>
          <span>🕒 {getRelativeDate(selectedEntry.date)}</span>
        </div>
      </div>
    </div>
  </div>
{/if}