import sqlite3
import json

def migrate_database():
    # Use the same path as your backend
    DATABASE_PATH = "journal.db"
    
    # Connect to your database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # 1. First, let's see what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Existing tables: {[table[0] for table in tables]}")
    
    # 2. Check if journal_entries exists and what columns it has
    try:
        cursor.execute("PRAGMA table_info(journal_entries)")
        columns = cursor.fetchall()
        print("Current journal_entries columns:")
        for col in columns:
            print(f"  {col[1]} - {col[2]} - Primary Key: {col[5]}")
    except sqlite3.OperationalError as e:
        print(f"Table info error: {e}")
        return
    
    # 3. Check if we already have proper IDs
    cursor.execute("SELECT COUNT(*) FROM journal_entries WHERE id IS NOT NULL")
    entries_with_ids = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM journal_entries")
    total_entries = cursor.fetchone()[0]
    
    print(f"Total entries: {total_entries}")
    print(f"Entries with IDs: {entries_with_ids}")
    
    if entries_with_ids == total_entries and total_entries > 0:
        print("✅ All entries already have IDs! No migration needed.")
        
        # Let's check what a sample entry looks like
        cursor.execute("SELECT id, title, date FROM journal_entries LIMIT 3")
        sample = cursor.fetchall()
        print("Sample entries:")
        for row in sample:
            print(f"  ID: {row[0]}, Title: {row[1]}")
        
        conn.close()
        return
    
    # 4. If we need to fix data, create a temporary table and migrate
    print("🔄 Migrating data to ensure proper IDs...")
    
    # Export existing data
    cursor.execute("SELECT date, title, summary, insights, sentiment_score, primary_theme, messages, user_notes, mood FROM journal_entries")
    existing_data = cursor.fetchall()
    
    print(f"Backing up {len(existing_data)} entries...")
    
    # Drop and recreate table
    cursor.execute("DROP TABLE IF EXISTS journal_entries_backup")
    cursor.execute("ALTER TABLE journal_entries RENAME TO journal_entries_backup")
    
    # Create fresh table with proper schema
    cursor.execute('''
    CREATE TABLE journal_entries (
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
    
    # Insert data back
    for row in existing_data:
        cursor.execute('''
        INSERT INTO journal_entries (date, title, summary, insights, sentiment_score, primary_theme, messages, user_notes, mood)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)
    
    # Create index
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON journal_entries(date)')
    
    conn.commit()
    
    # 5. Verify migration
    cursor.execute("SELECT id, title FROM journal_entries LIMIT 5")
    sample_data = cursor.fetchall()
    
    print("✅ Migration completed!")
    print("Sample entries with new IDs:")
    for row in sample_data:
        print(f"  ID: {row[0]}, Title: {row[1]}")
    
    # Clean up backup table
    cursor.execute("DROP TABLE journal_entries_backup")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_database()