from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime, timedelta
import json
import random
import os
import hashlib
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
from contextlib import asynccontextmanager

# Enhanced in-memory storage
conversations = []
journal_entries = []

SECRET_KEY = 'innervoice-encryption-key-2025'  # In production, use environment variable

def decrypt_data(encrypted_data: str) -> dict:
    """Decrypt data using AES decryption compatible with CryptoJS"""
    try:
        # Create key from secret
        key = hashlib.sha256(SECRET_KEY.encode()).digest()[:32]
        
        # Decode the base64 encrypted data
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Extract IV (first 16 bytes) and ciphertext
        iv = encrypted_bytes[:16]
        ciphertext = encrypted_bytes[16:]
        
        # Decrypt using AES CBC mode
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        
        # Remove padding and parse JSON
        decrypted_text = unpad(decrypted_padded, 16).decode('utf-8')
        return json.loads(decrypted_text)
        
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

def encrypt_data(data: dict) -> str:
    """Encrypt data for sending back to frontend"""
    try:
        # Create key from secret
        key = hashlib.sha256(SECRET_KEY.encode()).digest()[:32]
        
        # Generate random IV
        iv = os.urandom(16)
        
        # Encrypt data
        cipher = AES.new(key, AES.MODE_CBC, iv)
        json_data = json.dumps(data).encode('utf-8')
        
        # Pad data and encrypt
        padded_data = pad(json_data, 16)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Combine IV and encrypted data, then base64 encode
        result = base64.b64encode(iv + encrypted_data).decode('utf-8')
        return result
        
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")

# Generate some sample data for demo
def generate_sample_data():
    if not journal_entries:
        sample_entries = [
            {
                "date": (datetime.now() - timedelta(days=1)).isoformat(),
                "content": "**Yesterday**\n\nI reflected on work stress and how it affects my sleep. The conversation helped me realize I need better boundaries between work and personal time.\n\n**What I shared:**\n• Feeling overwhelmed with deadlines\n• Trouble sleeping due to work thoughts\n\n**Reflections:**\n• I need to create a shutdown ritual after work\n• Taking breaks during the day is not optional",
                "messageCount": 8,
                "mood": "Reflective"
            },
            {
                "date": (datetime.now() - timedelta(days=2)).isoformat(),
                "content": "**Two Days Ago**\n\nI talked about feeling excited about a new project but also anxious about the responsibility.\n\n**What I shared:**\n• Got assigned to lead a big project\n• Excited but nervous about the expectations\n\n**Reflections:**\n• Mixed emotions are normal and valid\n• I can handle more than I think I can",
                "messageCount": 12,
                "mood": "Mixed"
            },
            {
                "date": (datetime.now() - timedelta(days=3)).isoformat(),
                "content": "**Three Days Ago**\n\nI discussed my weekend plans and how I wanted to spend more time outdoors.\n\n**What I shared:**\n• Planning a hiking trip\n• Feeling disconnected from nature\n\n**Reflections:**\n• Nature time is essential for my mental health\n• I should schedule outdoor time like any other important appointment",
                "messageCount": 6,
                "mood": "Peaceful"
            }
        ]
        journal_entries.extend(sample_entries)

# Initialize sample data on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    generate_sample_data()
    print(f"Initialized {len(journal_entries)} sample journal entries with encryption enabled")
    yield

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat")
async def chat(request_data: dict):
    """Handle encrypted chat messages and generate AI responses"""
    
    # DEBUG: Log what we receive
    print("=== INCOMING REQUEST DEBUG ===")
    print(f"Request keys: {list(request_data.keys())}")
    print(f"Request data: {request_data}")
    
    try:
        # Check if data is encrypted
        if "encrypted_data" in request_data:
            print("Found encrypted_data field")
            encrypted_message = request_data.get("encrypted_data", "")
            print(f"Encrypted message length: {len(encrypted_message)}")
            decrypted_data = decrypt_data(encrypted_message)
            message = decrypted_data.get("message", "")
        else:
            print("No encrypted_data field, using fallback")
            message = request_data.get("message", "")
        
        print(f"Final message: {message}")
        
    except ValueError as e:
        print(f"DECRYPTION ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Decryption error: {str(e)}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Request processing error: {str(e)}")
    
    # Store user message
    conversations.append({
        "text": message,
        "sender": "user",
        "timestamp": datetime.now().isoformat(),
        "encrypted": True
    })
    
    # Contextual AI responses for InnerVoice
    empathetic_responses = [
        "Thank you for sharing that with me. How did that make you feel?",
        "I can hear that this is important to you. What thoughts come up when you reflect on it?",
        "That sounds like a meaningful experience. What would you like to explore about it?",
        "I'm listening. How has this been affecting your daily life?",
        "It sounds like you've been carrying this with you. What support would be helpful right now?",
        "I appreciate you opening up about this. What emotions are you noticing right now?",
        "That takes courage to share. How would you like things to be different?",
        "I can sense this matters deeply to you. What insights are coming up for you?"
    ]
    
    response_text = empathetic_responses[len(conversations) % len(empathetic_responses)]
    
    # Store AI response
    conversations.append({
        "text": response_text,
        "sender": "ai",
        "timestamp": datetime.now().isoformat(),
        "encrypted": True
    })
    
    # Encrypt response before sending back
    try:
        if "encrypted_data" in request_data:
            encrypted_response = encrypt_data({
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            })
            return {"encrypted_data": encrypted_response}
        else:
            # Fallback for non-encrypted requests
            return {
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            }
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Response encryption error: {str(e)}")

@app.post("/api/journal/generate")
async def generate_journal():
    """Generate a journal entry from the conversation"""
    
    user_messages = [msg for msg in conversations if msg["sender"] == "user"]
    
    if not user_messages:
        return {"entry": ""}
    
    today = datetime.now().strftime("%B %d, %Y")
    
    journal_parts = []
    journal_parts.append(f"**{today}**\n")
    journal_parts.append("Today I took some time to reflect on my thoughts and feelings through conversation.\n")
    
    if len(user_messages) >= 1:
        journal_parts.append("**What I shared:**")
        for msg in user_messages[-3:]:
            journal_parts.append(f"• {msg['text']}")
        journal_parts.append("")
    
    journal_parts.append("**Reflections:**")
    
    if any("stress" in msg["text"].lower() or "anxious" in msg["text"].lower() for msg in user_messages):
        journal_parts.append("• I noticed some stress coming up in my thoughts today. It's important to acknowledge these feelings.")
    
    if any("happy" in msg["text"].lower() or "good" in msg["text"].lower() or "great" in msg["text"].lower() for msg in user_messages):
        journal_parts.append("• There were positive moments in my day that I'm grateful for.")
    
    journal_parts.append("• Taking time to express my thoughts helped me process my experiences.")
    journal_parts.append("• I'm learning to listen to my inner voice with compassion and curiosity.")
    
    journal_parts.append("\n**Looking forward:**")
    journal_parts.append("Tomorrow I will continue to check in with myself and honor my emotional experiences.")
    
    journal_entry = "\n".join(journal_parts)
    
    # Store today's entry (replace if it already exists)
    today_entry = {
        "date": datetime.now().isoformat(),
        "content": journal_entry,
        "messageCount": len(user_messages),
        "mood": "Reflective"
    }
    
    # Remove existing today entry and add new one
    journal_entries[:] = [entry for entry in journal_entries if not entry["date"].startswith(datetime.now().strftime("%Y-%m-%d"))]
    journal_entries.insert(0, today_entry)
    
    return {"entry": journal_entry}

@app.get("/api/journal/history")
async def get_journal_history():
    """Get the last 5 days of journal entries"""
    # Sort by date (newest first) and return last 5 days
    sorted_entries = sorted(journal_entries, key=lambda x: x["date"], reverse=True)
    return {"entries": sorted_entries[:5]}

@app.get("/api/journal/search")
async def search_journal_by_date(date: str = Query(...)):
    """Search journal entries by date"""
    # Filter entries by date
    filtered_entries = [
        entry for entry in journal_entries 
        if entry["date"].startswith(date)
    ]
    
    return {"entries": filtered_entries}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
