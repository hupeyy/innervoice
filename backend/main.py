from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import openai
import os
import random
import json
import sqlite3
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Import sample data
from sample_data import get_sample_journal_entries

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Global variables
conversations = []
SECRET_KEY = 'innervoice-encryption-key-2025'
MAX_INPUT_LENGTH = 1000
DATABASE_PATH = "journal.db"

# Database functions using built-in sqlite3
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        insights TEXT NOT NULL,
        sentiment_score REAL DEFAULT 0.0,
        primary_theme TEXT DEFAULT 'Daily Life',
        messages TEXT NOT NULL,
        user_notes TEXT DEFAULT '',
        mood TEXT DEFAULT 'Neutral'
    )
    ''')
    
    # Create index on date for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON journal_entries(date)')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This enables dict-like access to rows
    return conn

def load_sample_data_if_empty():
    """Load sample data if database is empty"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM journal_entries")
    count = cursor.fetchone()[0]
    
    if count == 0:
        sample_entries = get_sample_journal_entries()
        for entry_data in sample_entries:
            cursor.execute('''
            INSERT INTO journal_entries (date, title, summary, insights, sentiment_score, primary_theme, messages, user_notes, mood)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_data["date"],
                entry_data.get("title", "Journal Entry"),
                entry_data["summary"],
                json.dumps(entry_data["insights"]),
                analyze_mood_sentiment(entry_data.get("mood", "")),
                "Daily Life",
                json.dumps(entry_data.get("messages", [])),
                entry_data.get("userNotes", ""),
                entry_data.get("mood", "Neutral")
            ))
        
        conn.commit()
        print(f"Loaded {len(sample_entries)} sample entries into database")
    else:
        print("Database already has entries")
    
    conn.close()

# Enhanced sentiment analysis functions (same as before)
def analyze_mood_sentiment(mood_text):
    """Convert text mood to numeric sentiment score - Enhanced version"""
    if not mood_text:
        return 0.0
    
    mood = mood_text.lower()
    
    positive_keywords = [
        'optimistic', 'grateful', 'energized', 'proud', 'accomplished', 
        'excited', 'happy', 'joyful', 'confident', 'peaceful', 'hopeful',
        'satisfied', 'content', 'motivated', 'inspired', 'blessed'
    ]
    negative_keywords = [
        'anxious', 'nervous', 'hurt', 'frustrated', 'stressed', 'worried', 
        'sad', 'angry', 'disappointed', 'overwhelmed', 'exhausted', 'lonely',
        'confused', 'insecure', 'depressed', 'irritated'
    ]
    
    positive_score = sum(1 for word in positive_keywords if word in mood)
    negative_score = sum(1 for word in negative_keywords if word in mood)
    
    if positive_score > negative_score:
        return min(0.8, 0.2 + (positive_score * 0.2))
    elif negative_score > positive_score:
        return max(-0.8, -0.2 - (negative_score * 0.2))
    else:
        return 0.1

async def analyze_sentiment(text):
    """Enhanced GPT-4 sentiment analysis with advanced fallback"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": """You are an expert at analyzing emotions in personal journal entries. Consider context, mixed emotions, personal growth language, and emotional complexity. Be precise with sentiment scoring."""
            },
            {
                "role": "user", 
                "content": f"""Analyze this journal entry's emotional sentiment on a scale from -1.0 to 1.0:

"{text}"

Consider: emotional trajectory, hope vs despair, self-awareness, growth vs rumination.

Return ONLY JSON: {{"sentiment_score": 0.2, "primary_theme": "Personal Growth", "confidence": 0.85}}"""
            }],
            max_tokens=80,
            temperature=0.1,
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("sentiment_score", 0), result.get("primary_theme", "Daily Life")
        
    except Exception as e:
        print(f"Enhanced sentiment analysis failed: {e}")
        return analyze_mood_sentiment(text), "Daily Life"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database and load sample data
    init_database()
    load_sample_data_if_empty()
    yield
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

# Encryption functions (same as before)
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

# Time-aware functions (same as before)
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

def build_memory_context():
    """Extract key memories from recent journal entries for AI context"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT summary, insights FROM journal_entries ORDER BY date DESC LIMIT 5")
    recent_entries = cursor.fetchall()
    conn.close()
    
    if not recent_entries:
        return ""
    
    memories = []
    for entry in recent_entries:
        if entry['summary']:
            memories.append(entry['summary'])
        insights = json.loads(entry['insights'])
        for insight in insights[:2]:
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

# API Endpoints
@app.get("/api/conversation/starter")
async def get_dynamic_starter():
    """Get single personalized conversation starter with time awareness"""
    
    time_context = get_time_context()
    time_greeting = get_time_greeting()
    
    # Check if there are any journal entries
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT summary, insights FROM journal_entries ORDER BY date DESC LIMIT 3")
    recent_entries = cursor.fetchall()
    conn.close()
    
    # If no journal history, return time-appropriate welcome
    if not recent_entries:
        welcome_starters = [
            f"{time_greeting} I'm here to listen. How are you feeling?",
            f"{time_greeting} What's on your mind this {time_context}?",
            f"{time_greeting} Ready to check in with yourself?",
            f"{time_greeting} How has your day been treating you?"
        ]
        return {"starter": random.choice(welcome_starters)}
    
    # Get recent context from journal entries
    context_text = ""
    for entry in recent_entries:
        if entry['summary']:
            context_text += f"Previous reflection: {entry['summary']}\n"
        insights = json.loads(entry['insights'])
        if insights:
            context_text += f"Key insight: {insights[0]}\n"
    
    try:
        starter_prompt = f"""Create a warm, personalized conversation starter that:
1. Includes an appropriate greeting for {time_context} time
2. References their recent journal context naturally
3. Gives them options to continue previous topics or start fresh
4. Feels supportive and remembers their journey

Recent context:
{context_text}

Time context: It's {time_context} time.

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
        if recent_entries:
            last_entry = recent_entries[0]
            fallback_starters = [
                f"{time_greeting} I remember our last conversation about {last_entry['summary'][:50]}. How are things today?",
                f"{time_greeting} Ready to continue your journaling journey? What's present for you this {time_context}?",
                f"{time_greeting} How are you feeling compared to our last chat?"
            ]
            return {"starter": random.choice(fallback_starters)}
        else:
            return {"starter": f"{time_greeting} I'm here to listen. How are you feeling?"}

@app.get("/api/conversation/starters")
async def get_starter_options():
    """Get multiple conversation starter options with time awareness"""
    
    time_context = get_time_context()
    time_greeting = get_time_greeting()
    
    # Check for journal history
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT summary, insights FROM journal_entries ORDER BY date DESC LIMIT 1")
    recent_entry = cursor.fetchone()
    conn.close()
    
    # If no journal history
    if not recent_entry:
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
    summary = recent_entry['summary']
    insights = json.loads(recent_entry['insights'])
    
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
    """Generate journal preview without saving to database"""
    
    # Get messages from global conversations variable
    global conversations
    
    if not conversations:
        raise HTTPException(status_code=400, detail="No session to generate journal")
    
    user_messages = [msg for msg in conversations if msg["sender"] == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user messages to generate journal")

    # Build conversation text for analysis
    conversation_text = "\n".join([
        f"{'User' if msg['sender'] == 'user' else 'InnerVoice'}: {msg['text']}" 
        for msg in conversations
    ])

    # Generate summary (reuse existing logic)
    try:
        summary_prompt = f"""You are a compassionate journaling assistant. Write a warm, personal journal entry in the first person, as if the user is reflecting in their own private journal.

    Use gentle, introspective language with phrases like:
    - "I noticed..."
    - "I felt..." 
    - "Today I realized..."
    - "I'm grateful for..."
    - "I'm curious about..."
    - "Something that struck me was..."

    Avoid clinical or analytical language. Write as the user's own voice, capturing meaningful insights and emotions from our conversation.

    Our conversation:
    {conversation_text}

    Write a 2-3 sentence personal journal reflection:"""

        summary_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=120,
            temperature=0.8,  # Higher for more natural, personal voice
        )
        summary = summary_response.choices[0].message.content.strip()
    except Exception as e:
        summary = "I'm grateful for this time I took to reflect on what's been on my mind. There's something valuable about pausing to explore my thoughts and feelings in this space."
    
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

    # Enhanced sentiment analysis
    user_text = " ".join([msg["text"] for msg in user_messages])
    sentiment_score, primary_theme = await analyze_sentiment(user_text)

    # Get current time for preview
    now = datetime.now()
    
    # Return preview data WITHOUT saving to database
    return {
        "journal": {
            "date": now.isoformat(),
            "title": f"Journal Entry - {now.strftime('%B %d, %Y')}",
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
    }

@app.get("/api/journal/all")
async def get_all_journals():
    """Get all journal entries for the user"""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, date, title, summary, insights, sentiment_score, 
                   primary_theme, messages, user_notes, mood
            FROM journal_entries 
            ORDER BY date DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        journals = []
        for row in rows:
            journal_entry = {
                "id": row["id"],
                "date": row["date"],
                "title": row["title"],
                "summary": row["summary"],
                "insights": json.loads(row["insights"]) if row["insights"] else [],
                "sentimentScore": row["sentiment_score"],
                "primaryTheme": row["primary_theme"],
                "messages": json.loads(row["messages"]) if row["messages"] else [],
                "userNotes": row["user_notes"],
                "mood": row["mood"]
            }
            journals.append(journal_entry)
        
        return {"journals": journals}
        
    except Exception as e:
        print(f"Error in get_all_journals: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/journal/create")
async def create_new_journal():
    """Create a new blank journal entry for today"""
    now = datetime.now()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO journal_entries (date, title, summary, insights, sentiment_score, primary_theme, messages, user_notes, mood)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        now.isoformat(),
        f"New Entry - {now.strftime('%I:%M %p')}",
        "Start writing your thoughts here...",
        json.dumps(["Ready to explore your inner world."]),
        0.0,
        "Daily Life",
        json.dumps([]),
        "",
        "Curious"
    ))
    
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "journal": {
            "id": entry_id,
            "date": now.isoformat(),
            "title": f"New Entry - {now.strftime('%I:%M %p')}",
            "summary": "Start writing your thoughts here...",
            "insights": ["Ready to explore your inner world."],
            "sentimentScore": 0.0,
            "primaryTheme": "Daily Life",
            "messages": [],
            "userNotes": "",
            "mood": "Curious"
        }
    }

@app.post("/api/journal/save-session")
async def save_current_session():
    """Save current chat session as a new journal entry"""
    
    # Get messages from global conversations variable
    global conversations
    
    if not conversations:
        raise HTTPException(status_code=400, detail="No session to save")
    
    user_messages = [msg for msg in conversations if msg["sender"] == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user messages to save")

    # Build conversation text for analysis
    conversation_text = "\n".join([
        f"{'User' if msg['sender'] == 'user' else 'InnerVoice'}: {msg['text']}" 
        for msg in conversations
    ])

    # Generate summary (reuse existing logic)
    try:
        summary_prompt = f"""You are a compassionate journaling assistant. Write a warm, personal journal entry in the first person, as if the user is reflecting in their own private journal.

    Use gentle, introspective language with phrases like:
    - "I noticed..."
    - "I felt..." 
    - "Today I realized..."
    - "I'm grateful for..."
    - "I'm curious about..."
    - "Something that struck me was..."

    Avoid clinical or analytical language. Write as the user's own voice, capturing meaningful insights and emotions from our conversation.

    Our conversation:
    {conversation_text}

    Write a 2-3 sentence personal journal reflection:"""

        summary_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=120,
            temperature=0.8,  # Higher for more natural, personal voice
        )
        summary = summary_response.choices[0].message.content.strip()
    except Exception as e:
        summary = "I'm grateful for this time I took to reflect on what's been on my mind. There's something valuable about pausing to explore my thoughts and feelings in this space."

    
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

    # Enhanced sentiment analysis
    user_text = " ".join([msg["text"] for msg in user_messages])
    sentiment_score, primary_theme = await analyze_sentiment(user_text)

    # Save to database
    now = datetime.now()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO journal_entries (date, title, summary, insights, sentiment_score, primary_theme, messages, user_notes, mood)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        now.isoformat(),
        f"Session - {now.strftime('%I:%M %p')}", # Time-based title to avoid conflicts
        summary,
        json.dumps(insights),
        sentiment_score,
        primary_theme,
        json.dumps([
            {
                "role": msg["sender"],
                "text": msg["text"],
                "timestamp": msg["timestamp"]
            } for msg in conversations
        ]),
        "",
        "Reflective"
    ))
    
    entry_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Clear the global conversations after saving
    conversations = []
    print("hello is this working")
    return {
        "journal": {
            "id": entry_id,
            "date": now.isoformat(),
            "title": f"Session - {now.strftime('%I:%M %p')}",
            "summary": summary,
            "insights": insights,
            "sentimentScore": sentiment_score,
            "primaryTheme": primary_theme,
            "messages": [
                {
                    "role": msg["sender"],
                    "text": msg["text"],
                    "timestamp": msg["timestamp"]
                } for msg in conversations  # Note: This will be empty since we cleared it above
            ],
            "userNotes": "",
            "mood": "Reflective"
        }
    }

@app.patch("/api/journal/{journal_date}/title")
async def update_journal_title(journal_date: str, request_data: dict):
    """Update the title of a specific journal entry"""
    new_title = request_data.get("title", "").strip()
    
    if not new_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE journal_entries SET title = ? WHERE date LIKE ?", (new_title, f"{journal_date}%"))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Title updated successfully", "title": new_title}

@app.get("/api/journal/{date}")
async def get_journal_by_date(date: str):
    """Get a specific journal entry by date"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM journal_entries WHERE date LIKE ?", (f"{date}%",))
    entry = cursor.fetchone()
    conn.close()
    
    if entry:
        return {
            "journal": {
                "date": entry['date'],
                "title": entry['title'],
                "summary": entry['summary'],
                "insights": json.loads(entry['insights']),
                "sentimentScore": entry['sentiment_score'],
                "primaryTheme": entry['primary_theme'],
                "messages": json.loads(entry['messages']),
                "userNotes": entry['user_notes'],
                "mood": entry['mood']
            }
        }
    return {"journal": None}

@app.patch("/api/journal/{journal_date}/notes")
async def update_journal_notes(journal_date: str, request_data: dict):
    """Update the notes of a specific journal entry"""
    notes = request_data.get("notes", "")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE journal_entries SET user_notes = ? WHERE date LIKE ?", (notes, f"{journal_date}%"))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Notes updated successfully", "notes": notes}

@app.post("/api/journal/backfill-sentiment")
async def backfill_sentiment():
    """Add sentiment scores to existing entries that don't have them"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, mood FROM journal_entries WHERE sentiment_score = 0.0")
    entries = cursor.fetchall()
    
    updated_count = 0
    for entry in entries:
        new_score = analyze_mood_sentiment(entry['mood'])
        cursor.execute("UPDATE journal_entries SET sentiment_score = ? WHERE id = ?", (new_score, entry['id']))
        updated_count += 1
    
    conn.commit()
    conn.close()
    
    return {"message": f"Updated {updated_count} entries with sentiment scores"}

@app.delete("/api/journal/{entry_id}")
async def delete_journal_entry(entry_id: int):
    """Delete a specific journal entry"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Journal entry deleted successfully"}

@app.get("/")
async def root():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM journal_entries")
    count = cursor.fetchone()[0]
    conn.close()
    
    return {"message": "InnerVoice API is running with SQLite database", "entries": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)