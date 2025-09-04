<script>
  import { onMount, tick } from 'svelte';
  import Header from '$lib/components/Header.svelte';
  import TabNavigation from '$lib/components/TabNavigation.svelte';
  import ChatMessages from '$lib/components/ChatMessages.svelte';
  import ChatInput from '$lib/components/ChatInput.svelte';
  import JournalView from '$lib/components/JournalView.svelte';
  import HistorySidebar from '$lib/components/HistorySidebar.svelte';
  import SentimentDashboard from '$lib/components/SentimentDashboard.svelte';

  // State variables
  let messages = [];
  let newMessage = '';
  let isTyping = false;
  let activeTab = 'chat';
  let showHistory = false;
  let encryptionEnabled = true;
  let journal = null;
  let userNotes = '';
  let isLoadingStarter = true;
  let showStarterOptions = false;
  let starterOptions = [];
  let allJournals = []; // For sentiment dashboard
  let allJournalsForSidebar = []; // For history sidebar
  let saveInProgress = false;
  let lastSaveTimestamp = 0;
  let beforeUnloadExecuted = false;
  let lastSaveRequest = null;

  async function handleTitleChange(newTitle) {
    if (!journal) return;
    
    try {
      const journalDate = new Date(journal.date).toISOString().split('T')[0];
      
      const response = await fetch(`http://localhost:8000/api/journal/${journalDate}/title`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle })
      });
      
      if (response.ok) {
        // Update local journal object
        journal = { ...journal, title: newTitle };
        console.log('Title updated successfully');
      } else {
        console.error('Failed to update title:', await response.text());
      }
    } catch (error) {
      console.error('Error updating title:', error);
    }
  }

  function hasUserInteractions() {
    return messages.some(msg => msg.sender === 'user');
  }

  // Shared save function with better duplicate prevention
  async function saveCurrentSession(source = 'manual') {
    if (!hasUserInteractions()) {
      console.log('No interactions to save');
      return null;
    }

    if (saveInProgress) {
      console.log(`Save already in progress, skipping ${source} save`);
      return null;
    }

    // Stronger deduplication - check if we just made this exact same request
    const requestKey = `${source}-${Date.now()}`;
    if (lastSaveRequest && Date.now() - lastSaveRequest < 3000) {
      console.log(`Duplicate save request blocked: ${requestKey}`);
      return null;
    }

    saveInProgress = true;
    lastSaveRequest = Date.now();
    console.log(`Starting ${source} save: ${requestKey}`);

    try {
      const response = await fetch('http://localhost:8000/api/journal/save-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        console.log(`${source} save successful:`, data.journal.title);
        lastSaveTimestamp = Date.now();
        
        // Refresh journal data
        await loadHistoricalJournals();
        
        return data;
      } else {
        console.error(`${source} save failed:`, await response.text());
        return null;
      }
    } catch (error) {
      console.error(`Error during ${source} save:`, error);
      return null;
    } finally {
      saveInProgress = false;
    }
  }

  // Improved beforeunload handler
  async function handleBeforeUnload() {
    if (beforeUnloadExecuted) {
      console.log('beforeunload already executed, skipping');
      return;
    }
    
    beforeUnloadExecuted = true;
    console.log('Executing beforeunload save...');
    
    await saveCurrentSession('auto');
    
    // Reset flag after longer delay
    setTimeout(() => {
      beforeUnloadExecuted = false;
    }, 5000);
  }

  // Simplified handleNewEntry
  async function handleNewEntry() {
    try {
      isTyping = true;
      const savedData = await saveCurrentSession('manual');
      
      if (savedData) {
        // Clear current session
        clearCurrentSession();
        await loadDynamicStarter();
        await loadHistoricalJournals();
        console.log('New session started!');
      } else if (!hasUserInteractions()) {
        clearCurrentSession();
        await loadDynamicStarter();
      }
    } finally {
      isTyping = false;
    }
  }

  // Clear current chat session
  function clearCurrentSession() {
    messages = [];
    newMessage = '';
    journal = null;
    userNotes = '';
    showStarterOptions = false;
  }

  // Dynamic starter functionality
  onMount(async () => {
    await loadDynamicStarter();
    await loadHistoricalJournals();
    
    // Add auto-save listener
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }); 

  async function loadDynamicStarter() {
    try {
      isLoadingStarter = true;
      
      // Get single starter first (for immediate display)
      const starterResponse = await fetch('http://localhost:8000/api/conversation/starter');
      
      if (starterResponse.ok) {
        const starterData = await starterResponse.json();
        messages = [{ 
          text: starterData.starter, 
          sender: 'ai', 
          timestamp: new Date() 
        }];
      }
      
      // Preload starter options for "Show more options" feature
      const optionsResponse = await fetch('http://localhost:8000/api/conversation/starters');
      
      if (optionsResponse.ok) {
        const optionsData = await optionsResponse.json();
        starterOptions = optionsData.starters;
      }
      
    } catch (error) {
      console.error('Error loading dynamic starter:', error);
      // Fallback
      const hour = new Date().getHours();
      const timeGreeting = hour < 12 ? "Good morning!" : hour < 17 ? "Good afternoon!" : "Good evening!";
      messages = [{ 
        text: `${timeGreeting} I'm here to listen. How are you feeling?`, 
        sender: 'ai', 
        timestamp: new Date() 
      }];
    } finally {
      isLoadingStarter = false;
    }
  }

  async function loadHistoricalJournals() {
    try {
      const response = await fetch('http://localhost:8000/api/journal/all');
      if (response.ok) {
        const data = await response.json(); // Read once
        console.log('Fetched journal history:', data); // Log the data variable
        allJournals = data.journals || [];
        allJournalsForSidebar = data.journals || [];
      }
    } catch (error) {
      console.error('Error loading historical journals:', error);
    }
  }

  function showMoreStarters() {
    showStarterOptions = true;
  }

  function selectStarter(starterText) {
    // Replace the initial message with selected starter
    messages = [{ 
      text: starterText, 
      sender: 'ai', 
      timestamp: new Date() 
    }];
    showStarterOptions = false;
  }

  function hideStarterOptions() {
    showStarterOptions = false;
  }

  // Chat functionality
  async function sendMessage() {
    if (!newMessage.trim()) return;

    messages = [...messages, { 
      text: newMessage, 
      sender: 'user', 
      timestamp: new Date() 
    }];

    const currentInput = newMessage;
    newMessage = '';
    isTyping = true;

    await tick();

    try {
      let requestBody;
      if (encryptionEnabled) {
        // Note: You'll need to import your encryption functions
        // const encrypted = encryptData({ message: currentInput });
        // requestBody = { encrypted_data: encrypted };
        // For now, using plain text for demo:
        requestBody = { message: currentInput };
      } else {
        requestBody = { message: currentInput };
      }

      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) throw new Error('Network error');

      const data = await response.json();
      let responseText, responseTimestamp;

      if (encryptionEnabled && data.encrypted_data) {
        // const decrypted = decryptData(data.encrypted_data);
        // responseText = decrypted.response;
        // responseTimestamp = new Date(decrypted.timestamp);
        // For now:
        responseText = data.response;
        responseTimestamp = new Date(data.timestamp);
      } else {
        responseText = data.response;
        responseTimestamp = new Date(data.timestamp);
      }

      messages = [...messages, { 
        text: responseText, 
        sender: 'ai', 
        timestamp: responseTimestamp 
      }];

      await generateJournalEntry();
    } catch (error) {
      console.error('Error:', error);
      messages = [...messages, { 
        text: 'Sorry, something went wrong. Please try again.', 
        sender: 'ai', 
        timestamp: new Date() 
      }];
    } finally {
      isTyping = false;
    }
  }

  // Journal functionality with sentiment analysis
  async function generateJournalEntry() {
    try {
      const response = await fetch('http://localhost:8000/api/journal/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        journal = data.journal;
        if (journal) {
          userNotes = journal.userNotes || '';
          // Refresh historical journals to include new entry with sentiment data
          await loadHistoricalJournals();
          console.log('Journal generated successfully:', journal);
        }
      }
    } catch (error) {
      console.error('Error generating journal:', error);
      journal = null;
    }
  }

  // Event handlers
  function handleVoiceTranscript(text) {
    newMessage = text;
  }

  function handleTabChange(tab) {
    activeTab = tab;
    // Load historical journals when switching to journal tab for sentiment dashboard
    if (tab === 'journal' && allJournals.length === 0) {
      loadHistoricalJournals();
    }
  }

  function handleToggleEncryption() {
    encryptionEnabled = !encryptionEnabled;
  }

  function handleToggleHistory() {
    showHistory = !showHistory;
  }

  function handleCloseHistory() {
    showHistory = false;
  }

  function handleNotesChange(notes) {
    userNotes = notes;
  }

  function handleSwitchToChat() {
    activeTab = 'chat';
  }
</script>

<main class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col">
  <!-- Header Component -->
  <Header 
    {encryptionEnabled} 
    onToggleEncryption={handleToggleEncryption}
    onToggleHistory={handleToggleHistory}
  />
  
  <!-- Tab Navigation Component -->
  <TabNavigation 
    {activeTab} 
    onTabChange={handleTabChange}
  />
  
  <!-- Loading State -->
  {#if isLoadingStarter && activeTab === 'chat'}
    <div class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">Preparing your personalized greeting...</p>
    </div>
  {:else}
    <!-- Main Content Area -->
    <div class="flex-1 max-w-4xl mx-auto w-full p-4 flex flex-col main-content" 
        style="height: calc(100vh - 200px);">
      
      {#if activeTab === 'chat'}
        <div class="chat-container">
          <!-- Chat Messages (scrollable area) -->
          <div class="chat-messages-area">
            <ChatMessages 
              {messages} 
              {isTyping} 
              {encryptionEnabled} 
            />
            
            <!-- NEW: Add session actions -->
            {#if messages.length > 0}
              <div class="session-actions">
                {#if hasUserInteractions()}
                  <button class="new-session-btn" on:click={handleNewEntry}>
                    💾 Save & Start New Session
                  </button>
                {/if}
              </div>
            {/if}
            
            <!-- Show "More options" button for initial AI message -->
            {#if messages.length === 1 && messages[0].sender === 'ai' && !showStarterOptions}
              <div class="more-starters-container">
                <button class="more-starters-btn" on:click={showMoreStarters}>
                  💭 Show more conversation starters
                </button>
              </div>
            {/if}
          </div>
          
          <!-- Fixed Chat Input at Bottom -->
          <div class="chat-input-fixed">
            <ChatInput 
              bind:message={newMessage}
              {isTyping}
              onSendMessage={sendMessage}
            />
          </div>
        </div>
        
      {:else if activeTab === 'journal'}
        <!-- Journal View Component -->
        <div class="journal-section">
          <JournalView 
            {journal}
            {userNotes}
            onNotesChange={handleNotesChange}
            onSwitchToChat={handleSwitchToChat}
            onTitleChange={handleTitleChange}
          />
        </div>
        
      {:else if activeTab === 'analysis'}
        <div class="analysis-section">
          <div class="analysis-header">
            <h2>📊 Emotional Insights & Analysis</h2>
            <p>Discover patterns in your emotional journey and gain insights into your mental well-being.</p>
          </div>
          
          <div class="w-full mx-auto">
            <SentimentDashboard journalEntries={allJournals} />
          </div>
          
          <div class="analysis-tips">
            <div class="tip-card">
              <h3>🎯 Using Your Insights</h3>
              <ul>
                <li>Regular journaling helps identify emotional patterns</li>
                <li>Look for triggers that affect your mood positively or negatively</li>
                <li>Celebrate positive streaks and improvements in your journey</li>
                <li>Use insights to build healthier daily habits and routines</li>
              </ul>
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- History Sidebar Component -->
  <HistorySidebar 
    isOpen={showHistory} 
    onClose={handleCloseHistory}
    journalEntries={allJournalsForSidebar}
  />

  <!-- Starter Options Modal -->
  {#if showStarterOptions}
    <div class="starter-modal-backdrop" role="button" tabindex="0" on:click={hideStarterOptions} on:keydown={(e) => e.key === 'Escape' && hideStarterOptions()}>
      <div class="starter-modal" role="dialog" tabindex="0" on:click|stopPropagation on:keydown|stopPropagation>
        <div class="starter-modal-header">
          <h3>What would you like to talk about?</h3>
          <button on:click={hideStarterOptions} class="close-starter-btn">×</button>
        </div>
        
        <div class="starter-options">
          {#each starterOptions as starter}
            <button 
              class="starter-option-btn" 
              on:click={() => selectStarter(starter.text)}
            >
              <span class="starter-icon">{starter.icon}</span>
              <div class="starter-content">
                <div class="starter-text">{starter.text}</div>
                {#if starter.context}
                  <div class="starter-context">{starter.context}</div>
                {/if}
              </div>
            </button>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  .main-content {
    scrollbar-width: thin;
    scrollbar-color: #cbd5e1 #f1f5f9;
  }
  
  .main-content::-webkit-scrollbar {
    width: 6px;
  }
  
  .main-content::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 3px;
  }
  
  .main-content::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  .journal-section {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    height: 100%;
    overflow-y: auto;
  }

  /* Loading Styles */
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    gap: 1rem;
  }

  .loading-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid #e5e7eb;
    border-top: 3px solid #6366f1;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  .loading-text {
    color: #6b7280;
    font-size: 0.875rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Starter Options Styles */
  .starter-modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  
  .starter-modal {
    background: white;
    border-radius: 12px;
    width: 100%;
    max-width: 500px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  }
  
  .starter-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .starter-modal-header h3 {
    margin: 0;
    color: #374151;
    font-size: 1.125rem;
    font-weight: 600;
  }
  
  .close-starter-btn {
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
  
  .close-starter-btn:hover {
    background: #e5e7eb;
  }
  
  .starter-options {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .starter-option-btn {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }
  
  .starter-option-btn:hover {
    border-color: #6366f1;
    background: #f8fafc;
    transform: translateY(-1px);
  }
  
  .starter-icon {
    font-size: 1.5rem;
    flex-shrink: 0;
  }
  
  .starter-content {
    flex: 1;
  }
  
  .starter-text {
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.25rem;
  }
  
  .starter-context {
    font-size: 0.875rem;
    color: #6b7280;
    font-style: italic;
  }
  
  .more-starters-container {
    text-align: center;
    margin: 1rem 0;
  }
  
  .more-starters-btn {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    color: #6366f1;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .more-starters-btn:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }

  @media (max-width: 768px) {
    .main-content {
      max-width: 100%;
      padding: 1rem;
    }
  }

  .analysis-section {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    height: 100%;
    overflow-y: auto;
  }

  .analysis-header {
    text-align: center;
    padding: 2rem;
    background: white;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
  }

  .analysis-header h2 {
    margin: 0 0 0.5rem 0;
    color: #374151;
    font-size: 1.75rem;
    font-weight: 700;
  }

  .analysis-header p {
    margin: 0;
    color: #6b7280;
    font-size: 1rem;
  }

  .analysis-tips {
    margin-top: 1rem;
  }

  .tip-card {
    background-color: white;
    border-radius: 12px;
    padding: 2rem;
    border: 1px solid #e2e8f0;
  }

  .tip-card h3 {
    margin: 0 0 1rem 0;
    color: #374151;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .tip-card ul {
    margin: 0;
    padding-left: 1.5rem;
    color: #4b5563;
  }

  .tip-card li {
    margin-bottom: 0.5rem;
    line-height: 1.5;
  }

  @media (max-width: 768px) {
    .analysis-header {
      padding: 1.5rem;
    }
    
    .analysis-header h2 {
      font-size: 1.5rem;
    }
    
    .tip-card {
      padding: 1.5rem;
    }
  }

  .chat-container {
    position: relative;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .chat-messages-area {
    flex: 1;
    overflow-y: auto;
    padding-bottom: 80px; /* Space for fixed input */
    max-height: calc(100vh - 280px); /* Adjust based on your layout */
  }

  .chat-input-fixed {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    max-width: 800px; /* Match your chat width */
    z-index: 1000;
    padding: 0 1rem;
  }

  .more-starters-container {
    display: flex;
    justify-content: center;
    padding: 1rem 0;
  }

  .more-starters-btn {
    background: rgba(255, 255, 255, 0.9);
    color: #333;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 25px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
  }

  .more-starters-btn:hover {
    background: rgba(255, 255, 255, 1);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  }

  .session-actions {
    display: flex;
    justify-content: center;
    padding: 1rem;
    margin: 1rem 0;
  }

  .new-session-btn {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 25px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .new-session-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
  }

  .clear-btn {
    background: rgba(255, 255, 255, 0.9);
    color: #6b7280;
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 0.75rem 1.5rem;
    border-radius: 25px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s ease;
    font-size: 0.875rem;
    backdrop-filter: blur(10px);
  }

  .clear-btn:hover {
    background: rgba(255, 255, 255, 1);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  }
</style>