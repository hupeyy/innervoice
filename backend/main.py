from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime, timedelta
import json
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced in-memory storage
conversations = []
journal_entries = []

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

# ADD THIS: Initialize sample data on startup
@app.on_event("startup")
async def startup_event():
    generate_sample_data()
    print(f"Initialized {len(journal_entries)} sample journal entries")

@app.post("/api/chat")
async def chat(request_data: dict):
    """Handle chat messages and generate AI responses"""
    
    message = request_data.get("message", "")
    
    # Store user message
    conversations.append({
        "text": message,
        "sender": "user",
        "timestamp": datetime.now().isoformat()
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
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "response": response_text,
        "timestamp": datetime.now().isoformat()
    }

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
        "mood": "Reflective"  # Simple mood detection could be added here
    }
    
    # Remove existing today entry and add new one
    journal_entries[:] = [entry for entry in journal_entries if not entry["date"].startswith(datetime.now().strftime("%Y-%m-%d"))]
    journal_entries.insert(0, today_entry)
    
    return {"entry": journal_entry}

@app.get("/api/journal/history")
async def get_journal_history():
    """Get the last 5 days of journal entries"""
    # Removed generate_sample_data() call from here
    
    # Sort by date (newest first) and return last 5 days
    sorted_entries = sorted(journal_entries, key=lambda x: x["date"], reverse=True)
    return {"entries": sorted_entries[:5]}

@app.get("/api/journal/search")
async def search_journal_by_date(date: str = Query(...)):
    """Search journal entries by date"""
    # Removed generate_sample_data() call from here
    
    # Filter entries by date
    filtered_entries = [
        entry for entry in journal_entries 
        if entry["date"].startswith(date)
    ]
    
    return {"entries": filtered_entries}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
