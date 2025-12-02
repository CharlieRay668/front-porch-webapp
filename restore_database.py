#!/usr/bin/env python3
"""
Database restoration script for Front Porch Volunteer Signup app.

This script parses the HTML snapshot file and restores all volunteer signups
to the production SQLite database.

Usage: Run this inside the Docker container:
  python restore_database.py
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import List, Tuple
from html import unescape

def parse_html_signups(html_content: str) -> List[Tuple[str, str, int]]:
    """
    Parse HTML content to extract volunteer signups.
    
    Returns:
        List of tuples (name, day, hour)
    """
    signups = []
    
    # Find all slot-wrapper divs - use a more flexible pattern
    # Split by slot-wrapper divs and process each one
    slot_wrapper_pattern = r'<div class="cell slot-wrapper">(.*?)(?=<div class="cell slot-wrapper">|<div class="cell header time-header">|$)'
    
    slots = re.findall(slot_wrapper_pattern, html_content, re.DOTALL)
    
    for slot_html in slots:
        # Extract day and hour from the button data attributes
        day_match = re.search(r'data-day="(\w+)"', slot_html)
        hour_match = re.search(r'data-hour="(\d+)"', slot_html)
        
        if not day_match or not hour_match:
            continue
            
        day = day_match.group(1)
        hour = int(hour_match.group(1))
        
        # Skip unavailable slots (Saturday/Friday evening restrictions)
        if 'unavailable' in slot_html:
            continue
            
        # Find all signup names directly in this slot
        name_pattern = r'<span class="signup-name">([^<]+)</span>'
        names = re.findall(name_pattern, slot_html)
        
        for name in names:
            # Unescape HTML entities (like &#39; codes)
            clean_name = unescape(name.strip())
            signups.append((clean_name, day, hour))
    
    return signups

def create_database_tables(db_path: str):
    """Create the database tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables (matching the SQLModel structure)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            day TEXT NOT NULL,
            hour INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def clear_existing_signups(db_path: str):
    """Clear all existing signups from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM signup')
    
    conn.commit()
    conn.close()
    print("Cleared existing signups from database")

def insert_signups(db_path: str, signups: List[Tuple[str, str, int]]):
    """Insert all signups into the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.executemany(
        'INSERT INTO signup (name, day, hour) VALUES (?, ?, ?)',
        signups
    )
    
    conn.commit()
    conn.close()
    print(f"Inserted {len(signups)} signups into database")

def create_admin_if_not_exists(db_path: str):
    """Create the admin user if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if admin exists
    cursor.execute('SELECT COUNT(*) FROM admin WHERE username = ?', ('frontporchadmin',))
    if cursor.fetchone()[0] == 0:
        # Insert default admin (password: toomanymugs)
        cursor.execute(
            'INSERT INTO admin (username, password) VALUES (?, ?)',
            ('frontporchadmin', 'toomanymugs')
        )
        conn.commit()
        print("Created default admin user")
    else:
        print("Admin user already exists")
    
    conn.close()

def validate_restoration(db_path: str) -> dict:
    """Validate the restoration by counting signups."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count total signups
    cursor.execute('SELECT COUNT(*) FROM signup')
    total_count = cursor.fetchone()[0]
    
    # Count by day
    cursor.execute('''
        SELECT day, COUNT(*) 
        FROM signup 
        GROUP BY day 
        ORDER BY 
            CASE day 
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2 
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END
    ''')
    day_counts = dict(cursor.fetchall())
    
    # Count by time slot
    cursor.execute('''
        SELECT hour, COUNT(*) 
        FROM signup 
        GROUP BY hour 
        ORDER BY hour
    ''')
    hour_counts = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        'total': total_count,
        'by_day': day_counts,
        'by_hour': hour_counts
    }

def main():
    """Main restoration function."""
    
    # Paths
    html_file = "Volunteer Signup-snapshot.html"
    db_path = "volunteers.db"
    
    print("🔄 Starting database restoration...")
    
    # Check if HTML snapshot exists
    if not os.path.exists(html_file):
        print(f"❌ Error: HTML snapshot file '{html_file}' not found!")
        print("   Please make sure the file is in the same directory as this script.")
        return
    
    try:
        # Read HTML file
        print(f"📖 Reading HTML snapshot: {html_file}")
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse signups from HTML
        print("🔍 Parsing volunteer signups from HTML...")
        signups = parse_html_signups(html_content)
        
        if not signups:
            print("❌ No signups found in HTML file!")
            return
        
        print(f"✅ Found {len(signups)} volunteer signups")
        
        # Create database and tables
        print("🗄️  Setting up database...")
        create_database_tables(db_path)
        
        # Clear existing data
        print("🧹 Clearing existing signups...")
        clear_existing_signups(db_path)
        
        # Insert all signups
        print("📝 Inserting volunteer signups...")
        insert_signups(db_path, signups)
        
        # Create admin if needed
        print("👤 Setting up admin user...")
        create_admin_if_not_exists(db_path)
        
        # Validate restoration
        print("✅ Validating restoration...")
        stats = validate_restoration(db_path)
        
        print("\n🎉 Database restoration completed successfully!")
        print(f"   Total signups restored: {stats['total']}")
        print("\n📊 Signups by day:")
        for day, count in stats['by_day'].items():
            print(f"   {day}: {count}")
        
        print("\n⏰ Signups by time (24h format):")
        for hour, count in stats['by_hour'].items():
            time_str = f"{hour}:00" if hour < 12 else f"{hour}:00"
            period = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            if display_hour == 0:
                display_hour = 12
            print(f"   {display_hour}:00 {period}: {count}")
        
        print(f"\n💾 Database saved as: {db_path}")
        
    except Exception as e:
        print(f"❌ Error during restoration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()