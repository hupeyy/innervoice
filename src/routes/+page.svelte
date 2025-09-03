<script>
  import { onMount, tick } from 'svelte';
  import HistorySidebar from '$lib/components/HistorySidebar.svelte';
  import VoiceInput from '$lib/components/VoiceInput.svelte';
  import CryptoJS from 'crypto-js';
  
  let messages = [];
  let newMessage = '';
  let isTyping = false;
  let activeTab = 'chat';
  let journalEntry = '';
  let showHistory = false;
  let textareaElement; // Reference to textarea
  let encryptionEnabled = true; // Toggle for encryption
  let isVoiceInputActive = false; // Track voice input state
  
  const SECRET_KEY = 'innervoice-encryption-key-2025'; // Same as backend
  
  // Updated encryption functions in +page.svelte
  function encryptData(data) {
    try {
      // Create a proper key
      const key = CryptoJS.SHA256(SECRET_KEY);
      
      // Generate random IV
      const iv = CryptoJS.lib.WordArray.random(16);
      
      // Encrypt with explicit IV and mode
      const encrypted = CryptoJS.AES.encrypt(JSON.stringify(data), key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      });
      
      // Combine IV and encrypted data
      const combined = iv.concat(encrypted.ciphertext);
      return CryptoJS.enc.Base64.stringify(combined);
      
    } catch (error) {
      console.error('Encryption failed:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  function decryptData(encryptedData) {
    try {
      const key = CryptoJS.SHA256(SECRET_KEY);
      
      // Parse the combined data
      const combined = CryptoJS.enc.Base64.parse(encryptedData);
      
      // Extract IV (first 16 bytes) and ciphertext
      const iv = CryptoJS.lib.WordArray.create(combined.words.slice(0, 4), 16);
      const ciphertext = CryptoJS.lib.WordArray.create(combined.words.slice(4));
      
      // Create cipher params
      const cipherParams = CryptoJS.lib.CipherParams.create({
        ciphertext: ciphertext
      });
      
      // Decrypt
      const decrypted = CryptoJS.AES.decrypt(cipherParams, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      });
      
      return JSON.parse(decrypted.toString(CryptoJS.enc.Utf8));
      
    } catch (error) {
      console.error('Decryption failed:', error);
      throw new Error('Failed to decrypt data');
    }
  }

  // Handle voice input transcript
  function handleVoiceTranscript(transcript) {
    newMessage = transcript;
    autoResize();
  }
  
  // Auto-resize functionality
  function autoResize() {
    if (textareaElement) {
      textareaElement.style.height = 'auto';
      textareaElement.style.height = Math.min(textareaElement.scrollHeight, 120) + 'px';
    }
  }
  
  // Handle input changes
  function handleInput() {
    autoResize();
  }
  
  // Handle Enter key (send message, Shift+Enter for new line)
  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }
  
  async function sendMessage() {
    if (!newMessage.trim()) return;
    
    // Add user message (store plain text locally for UI)
    messages = [...messages, { 
      text: newMessage, 
      sender: 'user', 
      timestamp: new Date() 
    }];
    
    const userInput = newMessage;
    newMessage = '';
    isTyping = true;
    
    // Reset textarea height after clearing message
    await tick();
    autoResize();
    
    try {
      let requestBody;
      
      if (encryptionEnabled) {
        // Encrypt the message before sending
        const encryptedMessage = encryptData({ message: userInput });
        requestBody = { encrypted_data: encryptedMessage };
      } else {
        // Fallback for non-encrypted requests
        requestBody = { message: userInput };
      }
      
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      let responseText, responseTimestamp;
      
      if (encryptionEnabled && data.encrypted_data) {
        // Decrypt the response
        const decryptedResponse = decryptData(data.encrypted_data);
        responseText = decryptedResponse.response;
        responseTimestamp = new Date(decryptedResponse.timestamp);
      } else {
        // Handle non-encrypted response
        responseText = data.response;
        responseTimestamp = new Date(data.timestamp);
      }
      
      messages = [...messages, { 
        text: responseText, 
        sender: 'ai', 
        timestamp: responseTimestamp 
      }];
      
      // Generate journal entry after each conversation
      await generateJournalEntry();
      
    } catch (error) {
      console.error('Error:', error);
      messages = [...messages, { 
        text: "Sorry, I'm having trouble connecting right now. Please try again.", 
        sender: 'ai', 
        timestamp: new Date() 
      }];
    } finally {
      isTyping = false;
    }
  }
  
  async function generateJournalEntry() {
    try {
      const response = await fetch('http://localhost:8000/api/journal/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        journalEntry = data.entry;
      }
    } catch (error) {
      console.error('Error generating journal:', error);
    }
  }
  
  function toggleHistory() {
    showHistory = !showHistory;
  }
  
  function closeHistory() {
    showHistory = false;
  }
  
  function toggleEncryption() {
    encryptionEnabled = !encryptionEnabled;
  }
  
  onMount(() => {
    // Welcome message
    messages = [{ 
      text: "Hi there! I'm here to listen. How are you feeling today?", 
      sender: 'ai', 
      timestamp: new Date() 
    }];
  });
</script>

<main class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col">
  <header class="p-4 text-center">
    <div class="flex items-center justify-between max-w-2xl mx-auto">
      <div class="flex items-center space-x-2">
        <!-- Encryption Status Indicator -->
        <div class="flex items-center space-x-2">
          <button 
            on:click={toggleEncryption}
            class="flex items-center space-x-1 px-2 py-1 rounded-full text-xs {
              encryptionEnabled 
                ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                : 'bg-red-100 text-red-800 hover:bg-red-200'
            } transition-colors"
            title="{encryptionEnabled ? 'Encryption enabled' : 'Encryption disabled'}"
            aria-label="{encryptionEnabled ? 'Disable encryption' : 'Enable encryption'}"
          >
            <span class="text-sm">{encryptionEnabled ? '🔐' : '🔓'}</span>
            <span>{encryptionEnabled ? 'Encrypted' : 'Plain'}</span>
          </button>
        </div>
      </div>
      
      <div>
        <h1 class="text-2xl font-bold text-indigo-800">InnerVoice</h1>
        <p class="text-indigo-600">Your conversational journal companion</p>
      </div>
      
      <!-- History Toggle Button -->
      <button 
        on:click={toggleHistory}
        class="p-2 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-100 rounded-full transition-colors"
        title="View journal history"
        aria-label="Open journal history sidebar"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253z">
          </path>
        </svg>
      </button>
    </div>
    
    <!-- Tab Navigation -->
    <nav class="mt-4">
      <div class="flex justify-center space-x-1 bg-white rounded-lg p-1 max-w-xs mx-auto shadow-sm">
        <button 
          on:click={() => activeTab = 'chat'}
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors {
            activeTab === 'chat' 
              ? 'bg-indigo-500 text-white' 
              : 'text-indigo-600 hover:text-indigo-800'
          }"
          aria-label="Switch to chat tab"
          aria-pressed={activeTab === 'chat'}
        >
          💬 Chat
        </button>
        <button 
          on:click={() => activeTab = 'journal'}
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors {
            activeTab === 'journal' 
              ? 'bg-indigo-500 text-white' 
              : 'text-indigo-600 hover:text-indigo-800'
          }"
          aria-label="Switch to today's journal tab"
          aria-pressed={activeTab === 'journal'}
        >
          📔 Today
        </button>
      </div>
    </nav>
  </header>
  
  <div class="flex-1 max-w-2xl mx-auto w-full p-4 flex flex-col">
    
    <!-- Chat Tab Content -->
    {#if activeTab === 'chat'}
      <!-- Messages Container -->
      <div class="flex-1 overflow-y-auto space-y-4 mb-4 overflow-x-hidden" role="log" aria-label="Conversation messages">
        {#each messages as message}
          <div class="flex {message.sender === 'user' ? 'justify-end' : 'justify-start'}">
            <div class="message-bubble {
              message.sender === 'user' 
                ? 'bg-indigo-500 text-white' 
                : 'bg-white text-gray-800 shadow-md'
            }"
            aria-label="{message.sender === 'user' ? 'Your message' : 'AI response'}">
              <div class="flex items-start justify-between">
                <span class="flex-1">{message.text.trim()}</span>
                {#if encryptionEnabled}
                  <span class="ml-2 text-xs opacity-50" title="Message encrypted">🔐</span>
                {/if}
              </div>
            </div>
          </div>
        {/each}
        
        {#if isTyping}
          <div class="flex justify-start">
            <div class="message-bubble bg-white text-gray-800 shadow-md" aria-label="AI is typing">
              <div class="flex space-x-1">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              </div>
            </div>
          </div>
        {/if}
      </div>
      
      <!-- Enhanced Multi-line Input Form with Voice Input -->
      <form on:submit|preventDefault={sendMessage} class="flex gap-3 items-end">
        <div class="flex-1 relative">
          <textarea 
            bind:this={textareaElement}
            bind:value={newMessage}
            on:input={handleInput}
            on:keydown={handleKeydown}
            placeholder="Share what's on your mind... (Enter to send, Shift+Enter for new line)"
            class="message-input"
            disabled={isTyping}
            rows="1"
            aria-label="Type your message to InnerVoice"
          ></textarea>
        </div>
        
        <!-- Voice Input Button -->
        <VoiceInput 
          onTranscript={handleVoiceTranscript}
          isDisabled={isTyping}
        />
        
        <button 
          type="submit" 
          disabled={isTyping || !newMessage.trim()}
          class="send-button"
          aria-label="Send message to InnerVoice"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
          </svg>
        </button>
      </form>
    
    <!-- Today's Journal Tab Content -->
    {:else if activeTab === 'journal'}
      <div class="flex-1 bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-gray-800">Today's Journal Entry</h2>
          <span class="text-sm text-gray-500">{new Date().toLocaleDateString()}</span>
        </div>
        
        {#if journalEntry}
          <div class="prose prose-indigo max-w-none">
            <div class="bg-amber-50 border-l-4 border-amber-400 p-4 mb-4">
              <p class="text-sm text-amber-700">
                ✨ This entry was automatically generated from your encrypted conversation with InnerVoice
              </p>
            </div>
            
            <div class="journal-content">
              {journalEntry.trim()}
            </div>
          </div>
        {:else}
          <div class="text-center py-12">
            <div class="text-6xl mb-4">📝</div>
            <h3 class="text-lg font-medium text-gray-600 mb-2">No journal entry yet</h3>
            <p class="text-gray-500">Start a conversation in the Chat tab to generate your first journal entry!</p>
            <button 
              on:click={() => activeTab = 'chat'}
              class="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600 transition-colors"
              aria-label="Switch to chat tab to start journaling"
            >
              Start Chatting
            </button>
          </div>
        {/if}
      </div>
    {/if}
    
  </div>
</main>

<!-- History Sidebar Component -->
<HistorySidebar 
  isOpen={showHistory} 
  onClose={closeHistory}
/>

<style>
  /* Chat message bubble styles */
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
    text-decoration: none;
    outline: none;
    border: none;
  }

  /* Journal content styling */
  .journal-content {
    white-space: pre-line;
    word-wrap: break-word;
    word-break: break-word;
    overflow-wrap: break-word;
    line-height: 1.6;
    color: #374151;
  }

  /* Auto-growing textarea styles */
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
    
    /* Hide scrollbar for all browsers */
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  /* Hide scrollbar for Webkit browsers (Chrome, Safari, Edge) */
  .message-input::-webkit-scrollbar {
    display: none;
  }

  .message-input:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  }

  .message-input:disabled {
    background-color: #f8fafc;
    color: #94a3b8;
    cursor: not-allowed;
  }

  .message-input::placeholder {
    color: #94a3b8;
    font-style: italic;
  }

  /* Send button styles */
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

  /* Prevent horizontal scrolling globally */
  :global(body) {
    overflow-x: hidden;
  }

  :global(.max-w-2xl) {
    overflow-x: hidden;
  }
</style>