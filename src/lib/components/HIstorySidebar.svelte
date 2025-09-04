<script>
  import { onMount } from 'svelte';
  
  export let isOpen = false;
  export let onClose = () => {};
  export let journalEntries = []; // Add this prop for reactive updates
  
  let journals = [];
  let loading = false;
  let searchQuery = '';
  let searchDate = '';
  let selectedEntry = null;
  let showModal = false;
  
  // Title editing state for modal
  let isEditingModalTitle = false;
  let editableModalTitle = '';
  
  // Watch for changes in journalEntries prop - this updates the sidebar
  $: if (journalEntries) {
    journals = journalEntries;
  }
  
  // Timezone-aware date matching function
  function dateMatchesEntry(entryDateString, selectedDateString) {
    if (!selectedDateString) return true;
    
    const selectedDate = new Date(selectedDateString + 'T00:00:00');
    const entryDate = new Date(entryDateString);
    
    const selectedYear = selectedDate.getFullYear();
    const selectedMonth = selectedDate.getMonth();
    const selectedDay = selectedDate.getDate();
    
    const entryYear = entryDate.getFullYear();
    const entryMonth = entryDate.getMonth();  
    const entryDay = entryDate.getDate();
    
    return selectedYear === entryYear && 
           selectedMonth === entryMonth && 
           selectedDay === entryDay;
  }
  
  // Group journals by date for display
  function groupJournalsByDate(journals) {
    const grouped = {};
    
    journals.forEach(journal => {
      const date = new Date(journal.date).toDateString();
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(journal);
    });
    
    // Sort entries within each day by time (newest first)
    Object.keys(grouped).forEach(date => {
      grouped[date].sort((a, b) => new Date(b.date) - new Date(a.date));
    });
    
    return grouped;
  }
  
  // Display date for search
  $: displaySearchDate = searchDate ? new Date(searchDate + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }) : '';
  
  // Enhanced filtering with timezone-aware date matching
  $: filteredJournals = journals.filter(entry => {
    if (searchDate && !dateMatchesEntry(entry.date, searchDate)) {
      return false;
    }
    
    if (!searchQuery) return true;
    
    const query = searchQuery.toLowerCase();
    const entryTitle = (entry.title || '').toLowerCase();
    const entrySummary = (entry.summary || '').toLowerCase();
    
    return entryTitle.includes(query) || entrySummary.includes(query);
  });
  
  // Group filtered journals by date
  $: groupedJournals = groupJournalsByDate(filteredJournals);
  
  // Get today's entries for display
  $: todaysEntries = journals.filter(journal => {
    const today = new Date().toDateString();
    const journalDate = new Date(journal.date).toDateString();
    return today === journalDate;
  });
  
  // Fallback fetch function - only called if no entries provided via props
  async function fetchJournalHistory() {
    if (!isOpen || journalEntries.length > 0) return;
    
    loading = true;
    try {
      console.log('Fetching journal history from:', 'http://localhost:8000/api/journal/all');
      
      const response = await fetch('http://localhost:8000/api/journal/all', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data && data.journals) {
        journals = data.journals;
        console.log('Loaded journals:', journals.length);
      } else {
        console.warn('No journals found in response');
        journals = [];
      }
      
    } catch (error) {
      console.error('Error fetching journal history:', error);
    } finally {
      loading = false;
    }
  }
  
  // Create new blank entry
  async function createNewEntry() {
    try {
      const response = await fetch('http://localhost:8000/api/journal/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        journals = [data.journal, ...journals];
        openEntryModal(data.journal);
      }
    } catch (error) {
      console.error('Error creating new entry:', error);
    }
  }
  
  // Delete entry
  async function deleteEntry(entryId) {
    if (!entryId) {
      console.error('Cannot delete entry: ID is undefined', entryId);
      return;
    }
    
    if (!confirm('Are you sure you want to delete this journal entry?')) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/journal/${entryId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        journals = journals.filter(journal => journal.id !== entryId);
        if (selectedEntry && selectedEntry.id === entryId) {
          closeModal();
        }
        console.log('Entry deleted successfully');
      } else {
        console.error('Failed to delete entry:', await response.text());
      }
    } catch (error) {
      console.error('Error deleting entry:', error);
    }
  }
  
  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  }
  
  function formatTime(dateString) {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  }
  
  function truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }
  
  function openEntryModal(entry) {
    selectedEntry = entry;
    editableModalTitle = entry.title || 'Untitled Entry';
    showModal = true;
    isEditingModalTitle = false;
  }
  
  function closeModal() {
    showModal = false;
    selectedEntry = null;
    isEditingModalTitle = false;
    editableModalTitle = '';
  }
  
  function handleModalBackdropClick(event) {
    if (event.target === event.currentTarget) {
      closeModal();
    }
  }
  
  // Modal title editing functions
  function startEditingModalTitle() {
    isEditingModalTitle = true;
    editableModalTitle = selectedEntry.title || '';
    setTimeout(() => {
      const titleInput = document.querySelector('.modal-title-input');
      if (titleInput) {
        titleInput.focus();
        titleInput.select();
      }
    }, 10);
  }
  
  async function saveModalTitle() {
    if (!selectedEntry) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/journal/${selectedEntry.id}/title`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editableModalTitle.trim() })
      });
      
      if (response.ok) {
        const journalIndex = journals.findIndex(j => j.id === selectedEntry.id);
        if (journalIndex !== -1) {
          journals[journalIndex] = { ...journals[journalIndex], title: editableModalTitle.trim() };
          journals = [...journals];
        }
        
        selectedEntry = { ...selectedEntry, title: editableModalTitle.trim() };
        console.log('Modal title updated successfully');
      } else {
        console.error('Failed to update modal title:', await response.text());
        editableModalTitle = selectedEntry.title || '';
      }
    } catch (error) {
      console.error('Error updating modal title:', error);
      editableModalTitle = selectedEntry.title || '';
    }
    
    isEditingModalTitle = false;
  }
  
  function handleModalTitleKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      saveModalTitle();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      editableModalTitle = selectedEntry.title || '';
      isEditingModalTitle = false;
    }
  }
  
  function handleModalTitleBlur() {
    saveModalTitle();
  }
  
  // Fetch history when sidebar opens (only if no entries provided)
  $: if (isOpen && journalEntries.length === 0) {
    fetchJournalHistory();
  }
</script>

{#if isOpen}
  <div class="sidebar-backdrop" on:click={onClose} on:keydown={(e) => e.key === 'Escape' && onClose()} role="button" tabindex="0">
    <div class="sidebar" on:click|stopPropagation on:keydown|stopPropagation role="dialog" aria-modal="true" aria-labelledby="sidebar-title" tabindex="-1">
      <div class="sidebar-header">
        <h2 class="text-lg font-semibold text-indigo-800">Journal History</h2>
        <button on:click={onClose} class="close-button">×</button>
      </div>
      
      <!-- Journal Actions -->
      <div class="journal-actions">
        <button class="new-entry-btn" on:click={createNewEntry}>
          ✏️ New Entry
        </button>
        
        {#if todaysEntries.length > 0}
          <span class="today-count">{todaysEntries.length} entries today</span>
        {/if}
      </div>
      
      <!-- Enhanced Search Section with Date Filter -->
      <div class="search-section">
        <div class="search-container">
          <input
            type="text"
            bind:value={searchQuery}
            placeholder="Search by title or content..."
            class="search-input"
          />
        </div>
        
        <div class="date-filter-container">
          <input
            type="date"
            bind:value={searchDate}
            class="date-input"
            title="Filter by date"
          />
          {#if searchDate}
            <button 
              class="clear-date-btn" 
              on:click={() => searchDate = ''}
              title="Clear date filter"
            >
              ×
            </button>
          {/if}
        </div>
      </div>
      
      <div class="sidebar-content">
        {#if loading}
          <div class="loading">Loading your journals...</div>
        {:else if Object.keys(groupedJournals).length === 0}
          <div class="empty-state">
            {#if searchQuery || searchDate}
              <div class="text-4xl mb-2">🔍</div>
              <p class="text-gray-600">No entries found</p>
              {#if searchQuery && searchDate}
                <p class="text-sm text-gray-500 mb-3">for "{searchQuery}" on {displaySearchDate}</p>
              {:else if searchQuery}
                <p class="text-sm text-gray-500 mb-3">for "{searchQuery}"</p>
              {:else if searchDate}
                <p class="text-sm text-gray-500 mb-3">on {displaySearchDate}</p>
              {/if}
              <div class="filter-actions">
                {#if searchQuery}
                  <button 
                    class="clear-search-btn" 
                    on:click={() => searchQuery = ''}
                  >
                    Clear search
                  </button>
                {/if}
                {#if searchDate}
                  <button 
                    class="clear-search-btn" 
                    on:click={() => searchDate = ''}
                  >
                    Clear date
                  </button>
                {/if}
              </div>
            {:else}
              <div class="text-4xl mb-2">📖</div>
              <p class="text-gray-600">No journal entries yet</p>
              <button class="start-journaling-btn" on:click={createNewEntry}>
                Start your first entry
              </button>
            {/if}
          </div>
        {:else}
          <div class="journal-list">
            {#each Object.entries(groupedJournals) as [date, entries]}
              <div class="date-group">
                <div class="date-header">
                  <h3>{formatDate(date)}</h3>
                  <span class="entry-count">{entries.length} {entries.length === 1 ? 'entry' : 'entries'}</span>
                </div>
                
                {#each entries as entry}
                  <div 
                    class="journal-entry-card" 
                    on:click={() => openEntryModal(entry)}
                    role="button"
                    tabindex="0"
                    on:keydown={(e) => e.key === 'Enter' && openEntryModal(entry)}
                  >
                    <div class="entry-header">
                      <div class="entry-time">{formatTime(entry.date)}</div>
                      <div class="entry-sentiment">
                        {entry.sentimentScore > 0.2 ? '😊' : entry.sentimentScore < -0.2 ? '😔' : '😐'}
                      </div>
                      <button 
                        on:click|stopPropagation={() => deleteEntry(entry.id)}
                        title="Delete entry"
                        disabled={!entry.id}
                      >
                        🗑️
                      </button> 
                    </div>
                    <div class="entry-title">{entry.title || 'Untitled Entry'}</div>
                    <div class="entry-summary">{truncateText(entry.summary)}</div>
                    <div class="entry-insights">
                      {#if entry.insights && entry.insights.length > 0}
                        <div class="insight-preview">💡 {truncateText(entry.insights[0], 60)}</div>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<!-- Journal Entry Modal with Editable Title -->
{#if showModal && selectedEntry}
  <div class="modal-backdrop" on:click={handleModalBackdropClick}>
    <div class="modal" on:click|stopPropagation>
      <div class="modal-header">
        <div class="modal-title-container">
          {#if isEditingModalTitle}
            <input
              class="modal-title-input"
              type="text"
              bind:value={editableModalTitle}
              on:keydown={handleModalTitleKeydown}
              on:blur={handleModalTitleBlur}
              placeholder="Enter journal title..."
            />
          {:else}
            <h2 
              class="modal-title-editable" 
              on:click={startEditingModalTitle}
              role="button"
              tabindex="0"
              on:keydown={(e) => e.key === 'Enter' && startEditingModalTitle()}
            >
              {selectedEntry.title || 'Untitled Entry'}
              <span class="modal-edit-icon">✏️</span>
            </h2>
          {/if}
        </div>
        <button on:click={closeModal} class="modal-close-button">×</button>
      </div>
      
      <div class="modal-content">
        <div class="modal-date">
          {formatDate(selectedEntry.date)} at {formatTime(selectedEntry.date)}
          {#if selectedEntry.mood}
            <span class="modal-mood">• {selectedEntry.mood}</span>
          {/if}
        </div>
        
        <div class="modal-section">
          <h3 class="section-title">Summary</h3>
          <p class="summary-text">{selectedEntry.summary}</p>
        </div>
        
        {#if selectedEntry.insights && selectedEntry.insights.length > 0}
          <div class="modal-section">
            <h3 class="section-title">Key Insights</h3>
            <ul class="insights-list">
              {#each selectedEntry.insights as insight}
                <li>{insight}</li>
              {/each}
            </ul>
          </div>
        {/if}
        
        {#if selectedEntry.messages && selectedEntry.messages.length > 0}
          <div class="modal-section">
            <h3 class="section-title">Conversation</h3>
            <div class="conversation-transcript">
              {#each selectedEntry.messages as message}
                <div class="message-entry {message.role}">
                  <span class="message-role">{message.role === 'ai' ? 'InnerVoice' : 'You'}:</span>
                  <span class="message-text">{message.text}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
        
        {#if selectedEntry.userNotes}
          <div class="modal-section">
            <h3 class="section-title">Your Notes</h3>
            <p class="user-notes">{selectedEntry.userNotes}</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  /* Sidebar styles */
  .sidebar-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    display: flex;
    justify-content: flex-end;
  }
  
  .sidebar {
    width: 400px;
    height: 100%;
    background: white;
    box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
  }
  
  .sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .close-button {
    width: 32px;
    height: 32px;
    border: none;
    background: #f3f4f6;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .close-button:hover {
    background: #e5e7eb;
  }
  
  /* Journal actions */
  .journal-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .new-entry-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 25px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }
  
  .new-entry-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  }
  
  .today-count {
    font-size: 0.875rem;
    color: #6b7280;
  }
  
  /* Enhanced search section */
  .search-section {
    padding: 1rem;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .search-container {
    display: flex;
    flex-direction: column;
  }
  
  .search-input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.875rem;
  }
  
  .search-input:focus {
    outline: none;
    border-color: #6366f1;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
  }
  
  .date-filter-container {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  
  .date-input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.875rem;
    color: #374151;
    background: #f9fafb;
  }
  
  .date-input:focus {
    outline: none;
    border-color: #6366f1;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
    background: white;
  }
  
  .clear-date-btn {
    width: 28px;
    height: 28px;
    border: none;
    background: #ef4444;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    flex-shrink: 0;
  }
  
  .clear-date-btn:hover {
    background: #dc2626;
    transform: scale(1.1);
  }
  
  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .loading {
    text-align: center;
    padding: 2rem;
    color: #6b7280;
  }
  
  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
  }
  
  .start-journaling-btn {
    margin-top: 1rem;
    padding: 0.75rem 1.5rem;
    background: #6366f1;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.2s;
  }
  
  .start-journaling-btn:hover {
    background: #4f46e5;
  }
  
  .filter-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    margin-top: 1rem;
  }
  
  .clear-search-btn {
    padding: 0.5rem 1rem;
    background: #6366f1;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: background 0.2s;
  }
  
  .clear-search-btn:hover {
    background: #4f46e5;
  }
  
  .journal-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  /* Date grouping */
  .date-group {
    margin-bottom: 1.5rem;
  }
  
  .date-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: rgba(99, 102, 241, 0.1);
    border-radius: 8px;
    margin-bottom: 0.75rem;
  }
  
  .date-header h3 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    color: #4f46e5;
  }
  
  .entry-count {
    font-size: 0.875rem;
    color: #6b7280;
  }
  
  .journal-entry-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 0.5rem;
  }
  
  .journal-entry-card:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .entry-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  
  .entry-time {
    font-size: 0.75rem;
    color: #6366f1;
    font-weight: 500;
  }
  
  .entry-sentiment {
    font-size: 1rem;
  }
  
  .delete-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    opacity: 0.6;
    transition: opacity 0.2s;
    font-size: 0.875rem;
  }
  
  .delete-btn:hover {
    opacity: 1;
  }
  
  .entry-title {
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 0.5rem;
  }
  
  .entry-summary {
    font-size: 0.875rem;
    color: #4b5563;
    line-height: 1.4;
    margin-bottom: 0.5rem;
  }
  
  .insight-preview {
    font-size: 0.75rem;
    color: #7c3aed;
    font-style: italic;
  }
  
  /* Modal Styles */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }
  
  .modal {
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 600px;
    max-height: 80vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
    gap: 1rem;
  }
  
  .modal-title-container {
    flex: 1;
  }
  
  .modal-title-editable {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    background: none;
    border: none;
    text-align: left;
  }
  
  .modal-title-editable:hover {
    background: #f9fafb;
    color: #6366f1;
  }
  
  .modal-edit-icon {
    font-size: 0.875rem;
    opacity: 0;
    transition: opacity 0.2s;
  }
  
  .modal-title-editable:hover .modal-edit-icon {
    opacity: 1;
  }
  
  .modal-title-input {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    border: 2px solid #6366f1;
    border-radius: 6px;
    padding: 0.5rem;
    width: 100%;
    background: white;
  }
  
  .modal-title-input:focus {
    outline: none;
    border-color: #4f46e5;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  }
  
  .modal-close-button {
    width: 32px;
    height: 32px;
    border: none;
    background: #f3f4f6;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    cursor: pointer;
    transition: background 0.2s;
    flex-shrink: 0;
  }
  
  .modal-close-button:hover {
    background: #e5e7eb;
  }
  
  .modal-content {
    padding: 1.5rem;
    overflow-y: auto;
    flex: 1;
  }
  
  .modal-date {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 1.5rem;
  }
  
  .modal-mood {
    color: #059669;
    font-weight: 500;
  }
  
  .modal-section {
    margin-bottom: 1.5rem;
  }
  
  .section-title {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
  }
  
  .summary-text {
    color: #4b5563;
    line-height: 1.6;
  }
  
  .insights-list {
    list-style: disc;
    margin-left: 1.5rem;
    color: #4b5563;
  }
  
  .insights-list li {
    margin-bottom: 0.5rem;
  }
  
  .conversation-transcript {
    background: #f9fafb;
    border-radius: 6px;
    padding: 1rem;
    max-height: 300px;
    overflow-y: auto;
  }
  
  .message-entry {
    margin-bottom: 0.75rem;
    font-size: 0.875rem;
  }
  
  .message-entry.user {
    color: #6366f1;
  }
  
  .message-entry.ai {
    color: #059669;
  }
  
  .message-role {
    font-weight: 600;
  }
  
  .message-text {
    margin-left: 0.5rem;
  }
  
  .user-notes {
    background: #fef3c7;
    padding: 1rem;
    border-radius: 6px;
    color: #92400e;
    font-style: italic;
  }
  
  /* Utility classes */
  .text-4xl {
    font-size: 2.25rem;
  }
  
  .mb-2 {
    margin-bottom: 0.5rem;
  }
  
  .mb-3 {
    margin-bottom: 0.75rem;
  }
  
  .text-gray-600 {
    color: #4b5563;
  }
  
  .text-gray-500 {
    color: #6b7280;
  }
  
  .text-sm {
    font-size: 0.875rem;
  }
</style>