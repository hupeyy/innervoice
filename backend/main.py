from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import openai
import os
import random
import re
import json
from dotenv import load_dotenv

# Import sample data
from sample_data import get_sample_journal_entries

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Global variables
conversations = []
journal_entries = []
SECRET_KEY = 'innervoice-encryption-key-2025'
MAX_INPUT_LENGTH = 1000

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load sample data
    global journal_entries
    journal_entries.extend(get_sample_journal_entries())
    print(f"Loaded {len(journal_entries)} sample journal entries")
    yield
    # Shutdown
    print("Shutting down InnerVoice API")

app = FastAPI(title="InnerVoice API", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Encryption functions using pycryptodome
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import hashlib

def encrypt_data(data):
    """Python equivalent of your JavaScript encryption using pycryptodome"""
    try:
        key = hashlib.sha256(SECRET_KEY.encode()).digest()
        iv = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        json_str = json.dumps(data)
        plaintext = json_str.encode()
        encrypted = cipher.encrypt(pad(plaintext, AES.block_size))
        combined = iv + encrypted
        return base64.b64encode(combined).decode()
    except Exception as error:
        raise Exception('Failed to encrypt data')

def decrypt_data(encrypted_data):
    """Python equivalent of your JavaScript decryption using pycryptodome"""
    try:
        combined = base64.b64decode(encrypted_data)
        iv = combined[:16]
        ciphertext = combined[16:]
        key = hashlib.sha256(SECRET_KEY.encode()).digest()
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return json.loads(decrypted.decode())
    except Exception as error:
        raise Exception('Failed to decrypt data')

# Time-aware functions
def get_time_context():
    """Get contextual time of day"""
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"  
    elif hour < 21:
        return "evening"
    else:
        return "night"

def get_time_greeting():
    """Get appropriate greeting for time of day"""
    time_context = get_time_context()
    greetings = {
        "morning": ["Good morning!", "Morning!", "Rise and shine!", "Hello, hope you're having a good morning!"],
        "afternoon": ["Good afternoon!", "Afternoon!", "Hi there!", "Hope your afternoon is going well!"],
        "evening": ["Good evening!", "Evening!", "Hi!", "Hope you're having a nice evening!"],
        "night": ["Good evening!", "Hi there!", "Hope your night is peaceful!", "Evening check-in time!"]
    }
    return random.choice(greetings[time_context])

# Build memory context from past journals
def build_memory_context():
    """Extract key memories from recent journal entries for AI context"""
    if not journal_entries:
        return ""
    
    memories = []
    recent_entries = journal_entries[:5]
    
    for entry in recent_entries:
        if entry.get("summary"):
            memories.append(entry["summary"])
        if entry.get("insights"):
            for insight in entry["insights"][:2]:
                if insight and len(insight) > 20:
                    memories.append(insight)
    
    if memories:
        memory_text = "\n- ".join(memories)
        return f"Context from user's recent journal conversations:\n- {memory_text}\n\n"
    
    return ""

def _secure_response(request_data, text):
    """Helper to return encrypted or plaintext chat response"""
    response_payload = {
        "response": text,
        "timestamp": datetime.now().isoformat()
    }
    try:
        if "encrypted_data" in request_data:
            encrypted_response = encrypt_data(response_payload)
            return {"encrypted_data": encrypted_response}
        else:
            return response_payload
    except Exception:
        return response_payload

# Sentiment analysis function
async def analyze_sentiment(text):
    """Analyze sentiment of journal text using OpenAI"""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user", 
                "content": f"""Analyze the emotional sentiment of this journal entry and return a score between -1.0 (very negative) and 1.0 (very positive). 
                
                Also identify the primary emotional theme from these categories: Work & Productivity, Relationships, Health & Wellness, Creativity & Hobbies, Personal Growth, Daily Life.
                
                Text: "{text}"
                
                Respond with JSON format: {{"sentiment_score": 0.2, "primary_theme": "Work & Productivity"}}"""
            }],
            max_tokens=50,
            temperature=0.3,
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("sentiment_score", 0), result.get("primary_theme", "Daily Life")
        
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return 0, "Daily Life"

# Dynamic starter endpoints
@app.get("/api/conversation/starter")
async def get_dynamic_starter():
    """Get single personalized conversation starter with time awareness"""
    
    time_context = get_time_context()
    time_greeting = get_time_greeting()
    
    # If no journal history, return time-appropriate welcome
    if not journal_entries:
        welcome_starters = [
            f"{time_greeting} I'm here to listen. How are you feeling?",
            f"{time_greeting} What's on your mind this {time_context}?",
            f"{time_greeting} Ready to check in with yourself?",
            f"{time_greeting} How has your day been treating you?"
        ]
        return {"starter": random.choice(welcome_starters)}
    
    # Get recent context from journal entries
    recent_entries = journal_entries[:3]
    context_text = ""
    for entry in recent_entries:
        if entry.get("summary"):
            context_text += f"Previous reflection: {entry['summary']}\n"
        if entry.get("insights"):
            for insight in entry["insights"][:1]:
                context_text += f"Key insight: {insight}\n"
    
    try:
        # Generate contextual starter with OpenAI
        starter_prompt = f"""Create a warm, personalized conversation starter that:
1. Includes an appropriate greeting for {time_context} time
2. References their recent journal context naturally
3. Gives them options to continue previous topics or start fresh
4. Feels supportive and remembers their journey

Recent context:
{context_text}

Time context: It's {time_context} time.

Examples:
- "Good morning! I remember you were reflecting on work stress yesterday. How are you starting today?"
- "Evening check-in! Last time you mentioned feeling energized after your walk. How did today go?"
- "Good afternoon! You've been exploring work-life balance lately. What's been on your mind?"

Generate one warm, contextual starter (1-2 sentences):"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": starter_prompt}],
            max_tokens=80,
            temperature=0.8,
        )
        
        dynamic_starter = response.choices[0].message.content.strip()
        return {"starter": dynamic_starter}
        
    except Exception as e:
        # Fallback with time awareness
        last_entry = journal_entries[0]
        fallback_starters = [
            f"{time_greeting} I remember our last conversation about {last_entry.get('summary', 'your thoughts')}. How are things today?",
            f"{time_greeting} Ready to continue your journaling journey? What's present for you this {time_context}?",
            f"{time_greeting} How are you feeling compared to our last chat?"
        ]
        return {"starter": random.choice(fallback_starters)}

@app.get("/api/conversation/starters")
async def get_starter_options():
    """Get multiple conversation starter options with time awareness"""
    
    time_context = get_time_context()
    time_greeting = get_time_greeting()
    
    # If no journal history
    if not journal_entries:
        base_starters = [
            {
                "text": f"{time_greeting} How are you feeling right now?",
                "type": "mood_check",
                "icon": "😊"
            },
            {
                "text": f"What's been on your mind this {time_context}?",
                "type": "open_ended", 
                "icon": "💭"
            },
            {
                "text": f"Tell me about something good that happened today",
                "type": "positive_focus",
                "icon": "✨"
            },
            {
                "text": f"Is there a challenge you'd like to work through?",
                "type": "problem_solving",
                "icon": "🎯"
            }
        ]
        return {"starters": base_starters}
    
    # With journal history - create contextual options
    last_entry = journal_entries[0]
    summary = last_entry.get("summary", "")
    insights = last_entry.get("insights", [])
    
    contextual_starters = [
        {
            "text": f"{time_greeting} Want to follow up on what we discussed last time?",
            "type": "follow_up",
            "icon": "🔄",
            "context": summary[:50] + "..." if len(summary) > 50 else summary
        },
        {
            "text": f"How are you feeling this {time_context}?",
            "type": "mood_check",
            "icon": "😊"
        },
        {
            "text": f"What's most important to you right now?",
            "type": "priority_focus",
            "icon": "⭐"
        },
        {
            "text": f"Is there something new you'd like to explore?",
            "type": "exploration",
            "icon": "🌱"
        }
    ]
    
    # Add insight-based starter if available
    if insights:
        contextual_starters.insert(1, {
            "text": f"Last time you realized: '{insights[0][:60]}...' How does that feel now?",
            "type": "insight_reflection",
            "icon": "💡"
        })
    
    return {"starters": contextual_starters[:4]}

@app.post("/api/chat")
async def chat(request_data: dict):
    """Enhanced chat endpoint with memory context from journal history"""
    
    # Decrypt and extract user's message
    try:
        if "encrypted_data" in request_data:
            encrypted_message = request_data.get("encrypted_data", "")
            decrypted_data = decrypt_data(encrypted_message)
            message = decrypted_data.get("message", "")
        else:
            message = request_data.get("message", "")
    except Exception as e:
        safe_reply = "Sorry, your message couldn't be decrypted. Please refresh or retry."
        return _secure_response(request_data, safe_reply)

    # Input validation
    if not message or len(message.strip()) == 0:
        safe_reply = "Could you share a bit more? It looks like your message was empty."
        return _secure_response(request_data, safe_reply)
    if len(message) > MAX_INPUT_LENGTH:
        safe_reply = "That's quite a lot. Please try sending a shorter message!"
        return _secure_response(request_data, safe_reply)

    # Store user message
    conversations.append({
        "text": message,
        "sender": "user",
        "timestamp": datetime.now().isoformat(),
        "encrypted": True
    })

    # Build memory context and system prompt
    memory_context = build_memory_context()
    system_prompt = f"""{memory_context}You are InnerVoice, a compassionate AI journaling companion with a good memory. 
Your role is to help users process emotions, reflect on experiences, and offer supportive words. 
Be empathetic, conversational, and concise—2 to 4 sentences per reply.

When appropriate, gently reference or build upon things the user has shared in previous conversations, 
showing that you remember and care about their ongoing journey. Ask thoughtful follow-up questions when relevant.

Never give medical, financial, or legal advice, and never offer diagnoses. 
Always maintain a warm, nonjudgmental, human-like conversational tone."""

    # Build conversation context
    messages_for_openai = [{"role": "system", "content": system_prompt}]
    for msg in conversations[-10:]:
        role = "assistant" if msg["sender"] == "ai" else "user"
        messages_for_openai.append({"role": role, "content": msg["text"]})

    # Call OpenAI API
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages_for_openai,
            temperature=0.75,
            top_p=0.92,
            max_tokens=180,
            presence_penalty=0.4,
            frequency_penalty=0.2,
        )
        ai_text = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        ai_text = ""

    # Handle empty responses
    if not ai_text or len(ai_text.strip()) == 0:
        safe_reply = "I'm here for you, but I couldn't generate a response to that. Can you rephrase or try again?"
    else:
        safe_reply = ai_text

    # Store AI response
    conversations.append({
        "text": safe_reply,
        "sender": "ai",
        "timestamp": datetime.now().isoformat(),
        "encrypted": True
    })

    return _secure_response(request_data, safe_reply)

@app.post("/api/journal/generate")
async def generate_journal():
    """Generate journal with improved memory extraction, title, and sentiment analysis"""
    
    user_messages = [msg for msg in conversations if msg["sender"] == "user"]
    if not user_messages:
        return {"journal": None}

    # Build conversation text
    conversation_text = "\n".join([
        f"{'User' if msg['sender'] == 'user' else 'InnerVoice'}: {msg['text']}" 
        for msg in conversations
    ])

    # Generate summary
    try:
        summary_prompt = f"""Create a warm, empathetic summary of this journaling conversation in 2-3 sentences. 
        Focus on the user's main feelings, experiences, and any specific events, people, or goals they mentioned:

{conversation_text}"""

        summary_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=120,
            temperature=0.7,
        )
        summary = summary_response.choices[0].message.content.strip()
    except Exception as e:
        summary = "Reflected on current thoughts and feelings in today's conversation."

    # Generate insights
    try:
        memory_context = build_memory_context()
        insights_prompt = f"""{memory_context}Based on this conversation, provide 2-3 supportive insights or gentle suggestions for growth. 
        Consider any patterns or connections to previous conversations. Format as separate bullet points:

{conversation_text}"""

        insights_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": insights_prompt}],
            max_tokens=150,
            temperature=0.7,
        )
        insights_text = insights_response.choices[0].message.content.strip()
        
        # Parse insights
        insights = []
        for line in insights_text.split('\n'):
            cleaned = line.strip().lstrip('•-*').strip()
            if cleaned and len(cleaned) > 15:
                insights.append(cleaned)
        
        if not insights:
            insights = ["Taking time for self-reflection supports personal growth and emotional well-being."]
            
    except Exception:
        insights = ["Regular journaling helps process emotions and gain valuable perspective."]

    # Analyze sentiment of the conversation
    user_text = " ".join([msg["text"] for msg in user_messages])
    sentiment_score, primary_theme = await analyze_sentiment(user_text)

    # Create journal entry with sentiment data
    journal_entry = {
        "date": datetime.now().isoformat(),
        "title": f"Journal Entry - {datetime.now().strftime('%B %d, %Y')}",
        "summary": summary,
        "insights": insights,
        "sentimentScore": sentiment_score,
        "primaryTheme": primary_theme,
        "messages": [
            {
                "role": msg["sender"],
                "text": msg["text"],
                "timestamp": msg["timestamp"]
            } for msg in conversations
        ],
        "userNotes": "",
        "mood": "Reflective"
    }

    # Store entry (replace today's if exists)
    today_date = datetime.now().strftime("%Y-%m-%d")
    journal_entries[:] = [entry for entry in journal_entries if not entry["date"].startswith(today_date)]
    journal_entries.insert(0, journal_entry)

    return {"journal": journal_entry}

@app.patch("/api/journal/{journal_date}/title")
async def update_journal_title(journal_date: str, request_data: dict):
    """Update the title of a specific journal entry"""
    new_title = request_data.get("title", "").strip()
    
    if not new_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    # Find and update the journal entry
    for entry in journal_entries:
        if entry["date"].startswith(journal_date):
            entry["title"] = new_title
            return {"message": "Title updated successfully", "title": new_title}
    
    raise HTTPException(status_code=404, detail="Journal entry not found")

@app.get("/api/journal/all")
async def get_all_journals():
    """Return all journal entries for history sidebar and sentiment analysis"""
    return {"journals": journal_entries}

@app.get("/api/journal/{date}")
async def get_journal_by_date(date: str):
    """Get a specific journal entry by date"""
    for entry in journal_entries:
        if entry["date"].startswith(date):
            return {"journal": entry}
    return {"journal": None}

@app.patch("/api/journal/{journal_date}/notes")
async def update_journal_notes(journal_date: str, request_data: dict):
    """Update the notes of a specific journal entry"""
    notes = request_data.get("notes", "")
    
    # Find and update the journal entry
    for entry in journal_entries:
        if entry["date"].startswith(journal_date):
            entry["userNotes"] = notes
            return {"message": "Notes updated successfully", "notes": notes}
    
    raise HTTPException(status_code=404, detail="Journal entry not found")


@app.get("/")
async def root():
    return {"message": "InnerVoice API is running", "entries": len(journal_entries)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)