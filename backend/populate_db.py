import sqlite3
import json
from datetime import datetime, timedelta

# Your sample data
def get_sample_journal_entries():
    """Returns sample journal entries for demo purposes"""
    return [
        {
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "title": "Job Interview Preparation",
            "summary": "Feeling nervous but excited about tomorrow's interview at TechCorp for the software engineering position. Spent time preparing answers and researching the company culture.",
            "insights": [
                "Preparation helps reduce anxiety and build confidence",
                "It's natural to feel nervous before big opportunities",
                "Researching company values shows genuine interest in the role"
            ],
            "messages": [
                {
                    "role": "user",
                    "text": "I have this big job interview tomorrow at TechCorp and I'm so nervous. What if I mess it up?",
                    "timestamp": (datetime.now() - timedelta(days=1, hours=2)).isoformat()
                },
                {
                    "role": "ai", 
                    "text": "It sounds like this opportunity really matters to you! Feeling nervous before an important interview is completely normal. What aspects of the interview are you most concerned about?",
                    "timestamp": (datetime.now() - timedelta(days=1, hours=2)).isoformat()
                },
                {
                    "role": "user",
                    "text": "I'm worried about the technical questions and whether I'll fit in with their team culture.",
                    "timestamp": (datetime.now() - timedelta(days=1, hours=2)).isoformat()
                },
                {
                    "role": "ai",
                    "text": "Those are valid concerns that show you care about doing well. Have you had a chance to research their tech stack and company values? Sometimes preparation can help transform that nervous energy into confidence.",
                    "timestamp": (datetime.now() - timedelta(days=1, hours=2)).isoformat()
                }
            ],
            "userNotes": "Remember to ask about their mentorship program and work-life balance.",
            "mood": "Anxious but optimistic"
        },
        
        {
            "date": (datetime.now() - timedelta(days=3)).isoformat(),
            "title": "Relationship Stress",
            "summary": "Had a difficult conversation with Sarah about our friendship. Feeling hurt by some things that were said, but also recognizing my own part in the misunderstanding.",
            "insights": [
                "Healthy relationships require honest communication, even when it's uncomfortable",
                "It's important to listen to understand, not just to respond",
                "Conflict can strengthen relationships when handled with care and empathy"
            ],
            "messages": [
                {
                    "role": "user",
                    "text": "Sarah and I got into this huge argument and I don't know if our friendship will recover. She said some really hurtful things.",
                    "timestamp": (datetime.now() - timedelta(days=3, hours=1)).isoformat()
                },
                {
                    "role": "ai",
                    "text": "I'm sorry you're going through this pain with Sarah. Arguments with close friends can feel especially difficult because we care so much. What do you think triggered the argument?",
                    "timestamp": (datetime.now() - timedelta(days=3, hours=1)).isoformat()
                },
                {
                    "role": "user",
                    "text": "I think it started because I felt like she wasn't listening to me about my job stress, and then it just escalated from there.",
                    "timestamp": (datetime.now() - timedelta(days=3, hours=1)).isoformat()
                }
            ],
            "userNotes": "Maybe I should reach out to apologize for my part in the argument.",
            "mood": "Hurt but reflective"
        },
        
        {
            "date": (datetime.now() - timedelta(days=5)).isoformat(),
            "title": "Family Weekend",
            "summary": "Wonderful weekend visiting Mom and Dad. Felt grateful for their support and enjoyed cooking together. Made me realize how much I miss being home.",
            "insights": [
                "Quality time with family helps put life's challenges in perspective",
                "Sharing meals together creates meaningful connection and memories",
                "It's okay to feel homesick - it shows how much love and support means to us"
            ],
            "messages": [
                {
                    "role": "user",
                    "text": "I just got back from visiting my parents and I'm feeling really emotional. In a good way, but also sad to leave.",
                    "timestamp": (datetime.now() - timedelta(days=5)).isoformat()
                },
                {
                    "role": "ai",
                    "text": "It sounds like you had a really meaningful time with your parents. Those bittersweet feelings after family visits are so common - the joy of connection mixed with the sadness of separation. What made this visit especially special?",
                    "timestamp": (datetime.now() - timedelta(days=5)).isoformat()
                }
            ],
            "userNotes": "Call Mom more often. Maybe plan monthly visits?",
            "mood": "Grateful and nostalgic"
        },
        
        {
            "date": (datetime.now() - timedelta(days=7)).isoformat(),
            "title": "Workout Motivation",
            "summary": "Started a new fitness routine this week. Feeling sore but accomplished. Surprised by how much I'm enjoying the morning runs, even though I've never been a 'morning person'.",
            "insights": [
                "Small consistent actions can lead to surprising discoveries about ourselves",
                "Physical activity has powerful effects on mood and mental clarity",
                "Building new habits takes patience but the early wins feel incredible"
            ],
            "messages": [
                {
                    "role": "user",
                    "text": "I actually woke up early to go for a run today! I can't believe it. I've always hated mornings but something felt different.",
                    "timestamp": (datetime.now() - timedelta(days=7)).isoformat()
                },
                {
                    "role": "ai",
                    "text": "That's fantastic! What a great way to start building a healthy routine. How did you feel during and after the run?",
                    "timestamp": (datetime.now() - timedelta(days=7)).isoformat()
                }
            ],
            "userNotes": "Track progress - aim for 3 runs per week to start.",
            "mood": "Energized and proud"
        },
        
        {
            "date": (datetime.now() - timedelta(days=10)).isoformat(),
            "title": "Creative Block",
            "summary": "Struggling with creative block on my photography project. Feeling frustrated that the images aren't capturing what I envision. Wondering if I should take a different approach or just push through.",
            "insights": [
                "Creative blocks are a natural part of the artistic process, not a sign of failure",
                "Sometimes stepping away from a project can provide fresh perspective",
                "Perfectionism can be the enemy of creativity and progress"
            ],
            "messages": [
                {
                    "role": "user",
                    "text": "I've been working on this photography series for weeks and nothing feels right. I'm starting to wonder if I'm just not good at this.",
                    "timestamp": (datetime.now() - timedelta(days=10)).isoformat()
                },
                {
                    "role": "ai",
                    "text": "Creative struggles can feel so discouraging, especially when you care deeply about the work. What drew you to photography in the first place? Sometimes reconnecting with that initial passion can help break through blocks.",
                    "timestamp": (datetime.now() - timedelta(days=10)).isoformat()
                }
            ],
            "userNotes": "Try shooting something completely different tomorrow - maybe street photography instead of landscapes.",
            "mood": "Frustrated but determined"
        }
    ]

def analyze_mood_sentiment(mood_text):
    """Convert text mood to numeric sentiment score"""
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

def populate_database():
    """Populate the database with sample data"""
    DATABASE_PATH = "journal.db"
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Initialize database structure
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
    
    # Create index
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON journal_entries(date)')
    
    # Check if database is empty
    cursor.execute("SELECT COUNT(*) FROM journal_entries")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"Database already has {count} entries. Clearing for fresh sample data...")
        cursor.execute("DELETE FROM journal_entries")
    
    # Get sample data
    sample_entries = get_sample_journal_entries()
    
    print(f"Inserting {len(sample_entries)} sample journal entries...")
    
    # Insert sample data
    for entry_data in sample_entries:
        sentiment_score = analyze_mood_sentiment(entry_data.get("mood", ""))
        
        cursor.execute('''
        INSERT INTO journal_entries (date, title, summary, insights, sentiment_score, primary_theme, messages, user_notes, mood)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry_data["date"],
            entry_data["title"],
            entry_data["summary"],
            json.dumps(entry_data["insights"]),
            sentiment_score,
            "Daily Life",
            json.dumps(entry_data["messages"]),
            entry_data.get("userNotes", ""),
            entry_data.get("mood", "Neutral")
        ))
    
    conn.commit()
    
    # Verify data was inserted with IDs
    cursor.execute("SELECT id, title, date FROM journal_entries ORDER BY date DESC")
    entries = cursor.fetchall()
    
    print("\n✅ Successfully populated database!")
    print("Sample entries:")
    for entry in entries:
        date_formatted = datetime.fromisoformat(entry['date']).strftime('%Y-%m-%d')
        print(f"  ID: {entry['id']}, Title: {entry['title']}, Date: {date_formatted}")
    
    conn.close()
    print(f"\nDatabase now contains {len(entries)} entries with proper IDs!")

if __name__ == "__main__":
    populate_database()
