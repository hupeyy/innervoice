<script>
  export let userNotes = '';
  export let onNotesChange = (notes) => {};
  
  function handleChange(event) {
    onNotesChange(event.target.value);
  }
</script>

<div class="mt-4">
  <label for="user-notes" class="block font-medium mb-1 text-indigo-700">Your Notes:</label>
  <textarea 
    id="user-notes"
    class="border border-indigo-200 rounded-md w-full p-2" 
    rows="4" 
    value={userNotes} 
    on:input={handleChange} 
    placeholder="Add your additional personal reflections or actions here..."
  ></textarea>
  <div class="text-xs text-gray-400 mt-1">Notes are saved locally.</div>
</div>