<script>
  import { onMount } from 'svelte';
  
  export let onTranscript = (text) => {};
  export let isDisabled = false;
  
  let isListening = false;
  let recognition = null;
  let browserSupportsRecognition = false;
  let microphoneAvailable = true;
  let interimText = '';
  let finalText = '';
  
  console.log("VoiceInput component loaded!");
  
  onMount(() => {
    console.log("VoiceInput onMount called");
    
    // Check if browser supports speech recognition
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      console.log("SpeechRecognition support:", !!SpeechRecognition);
      
      if (SpeechRecognition) {
        browserSupportsRecognition = true;
        console.log("Speech recognition supported!");
        recognition = new SpeechRecognition();
        
        // Configure recognition
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        // Handle results
        recognition.onresult = (event) => {
          let interim = '';
          let final = '';
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
              final += result[0].transcript;
            } else {
              interim += result[0].transcript;
            }
          }
          
          interimText = interim;
          finalText += final;
          
          // Send combined text back to parent
          if (final || interim) {
            onTranscript(finalText + interim);
          }
        };
        
        // Handle errors
        recognition.onerror = (event) => {
          console.error('Speech recognition error:', event.error);
          if (event.error === 'not-allowed') {
            microphoneAvailable = false;
          }
          stopListening();
        };
        
        // Handle end
        recognition.onend = () => {
          isListening = false;
        };
      } else {
        console.log("Speech recognition NOT supported");
      }
    }
    
    console.log("Final state:", { browserSupportsRecognition, microphoneAvailable });
  });
  
  function startListening() {
    if (!recognition || isDisabled) return;
    
    finalText = '';
    interimText = '';
    isListening = true;
    
    try {
      recognition.start();
    } catch (error) {
      console.error('Error starting recognition:', error);
      isListening = false;
    }
  }
  
  function stopListening() {
    if (!recognition) return;
    
    isListening = false;
    recognition.stop();
  }
  
  function toggleListening() {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }
</script>

<!-- Voice Input Button -->
<div>
  <!-- Debug info -->
  <!-- <div style="font-size: 12px; color: gray;">
    Debug: browserSupported={browserSupportsRecognition}, micAvailable={microphoneAvailable}
  </div> -->
  
  {#if browserSupportsRecognition && microphoneAvailable}
    <button
      on:click={toggleListening}
      disabled={isDisabled}
      class="voice-button {isListening ? 'listening' : ''}"
      aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
      title={isListening ? 'Stop recording' : 'Start voice recording'}
    >
      {#if isListening}
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.93V21h2v-3.07c3.39-.5 6-3.4 6-6.93h-2z"/>
          <circle cx="12" cy="8" r="2" class="pulse"/>
        </svg>
      {:else}
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.93V21h2v-3.07c3.39-.5 6-3.4 6-6.93h-2z"/>
        </svg>
      {/if}
    </button>
  {:else if !microphoneAvailable}
    <div class="voice-error" title="Microphone access denied">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.93V21h2v-3.07c3.39-.5 6-3.4 6-6.93h-2z"/>
        <line x1="3" y1="3" x2="21" y2="21" stroke="currentColor" stroke-width="2"/>
      </svg>
    </div>
  {:else}
    <div class="voice-error" title="Speech recognition not supported">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.93V21h2v-3.07c3.39-.5 6-3.4 6-6.93h-2z"/>
      </svg>
      <span style="font-size: 10px;">Not Supported</span>
    </div>
  {/if}
</div>

<!-- Same styles as before -->
<style>
  .voice-button {
    width: 44px;
    height: 44px;
    border: none;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    background-color: #e5e7eb; /* gray-200 */
    color: #6b7280; /* gray-500 */
  }
  
  .voice-button:hover:not(:disabled) {
    background-color: #d1d5db; /* gray-300 */
    transform: scale(1.05);
  }
  
  .voice-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: scale(1);
  }
  
  .voice-button.listening {
    background-color: #ef4444; /* red-500 */
    color: white;
    animation: pulse 2s infinite;
  }
  
  .voice-button.listening:hover {
    background-color: #dc2626; /* red-600 */
  }
  
  .voice-error {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    background-color: #fef2f2; /* red-50 */
    color: #dc2626; /* red-600 */
  }
  
  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.1);
    }
  }
  
  .pulse {
    animation: ping 1s cubic-bezier(0, 0, 0.2, 1) infinite;
  }
  
  @keyframes ping {
    75%, 100% {
      transform: scale(2);
      opacity: 0;
    }
  }
</style>