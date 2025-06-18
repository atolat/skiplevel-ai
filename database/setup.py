"""Database setup and table creation for Emreq employee profiles."""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
    
    return create_client(url, key)

def get_table_creation_sql():
    """Get the complete SQL for creating the employee_profiles table."""
    return """
-- Create employee profiles table
CREATE TABLE IF NOT EXISTS employee_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    level TEXT,
    team TEXT,
    years_experience INTEGER,
    years_at_company INTEGER,
    specialization TEXT NOT NULL,
    tech_skills TEXT[],
    current_projects TEXT[],
    career_goals TEXT[],
    biggest_challenges TEXT[],
    strengths TEXT[],
    learning_goals TEXT[],
    
    -- Last human manager assessment (legacy)
    last_review_date DATE,
    last_review_rating TEXT,
    last_review_feedback TEXT,
    last_reviewer TEXT,
    
    -- AI management preferences
    communication_style TEXT,
    feedback_frequency TEXT,
    meeting_style TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    profile_completed BOOLEAN DEFAULT FALSE
);

-- Enable Row Level Security
ALTER TABLE employee_profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Employees can view own profile" ON employee_profiles;
DROP POLICY IF EXISTS "Employees can insert own profile" ON employee_profiles;
DROP POLICY IF EXISTS "Employees can update own profile" ON employee_profiles;

-- Create policies so employees can only see/edit their own profile
CREATE POLICY "Employees can view own profile" ON employee_profiles
FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Employees can insert own profile" ON employee_profiles
FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Employees can update own profile" ON employee_profiles
FOR UPDATE USING (auth.uid() = id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop trigger if exists
DROP TRIGGER IF EXISTS update_employee_profiles_updated_at ON employee_profiles;

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_employee_profiles_updated_at 
    BEFORE UPDATE ON employee_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
"""

def create_employee_profiles_table():
    """Create the employee_profiles table."""
    print("📋 To create the employee_profiles table, follow these steps:")
    print()
    print("1. Go to your Supabase Dashboard")
    print("2. Navigate to 'SQL Editor'")
    print("3. Copy and paste the following SQL:")
    print()
    print("=" * 80)
    print(get_table_creation_sql())
    print("=" * 80)
    print()
    print("4. Click 'RUN' to execute the SQL")
    print()
    print("Alternatively, you can save this SQL to a file and run it:")
    
    # Save SQL to file
    sql_file = "database_setup.sql"
    with open(sql_file, 'w') as f:
        f.write(get_table_creation_sql())
    
    print(f"📁 SQL saved to: {sql_file}")
    print()
    print("After running the SQL, you can test the connection with:")
    print("python -c 'from database.setup import check_table_exists; check_table_exists()'")

def check_table_exists():
    """Check if the employee_profiles table exists."""
    supabase = get_supabase_client()
    
    try:
        result = supabase.table('employee_profiles').select('id').limit(1).execute()
        print("✅ employee_profiles table exists and is accessible")
        print(f"🔗 Connected to: {os.getenv('SUPABASE_URL')}")
        return True
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        print()
        print("💡 This usually means:")
        print("   1. The table hasn't been created yet")
        print("   2. Row Level Security is blocking access")
        print("   3. Your credentials are incorrect")
        print()
        print("📋 To fix this:")
        print("   1. Run the SQL creation script in Supabase Dashboard")
        print("   2. Make sure you're authenticated as a user")
        print("   3. Check your SUPABASE_URL and SUPABASE_ANON_KEY")
        return False

def test_connection():
    """Test basic Supabase connection."""
    try:
        supabase = get_supabase_client()
        print("✅ Supabase client created successfully")
        print(f"🔗 Connected to: {os.getenv('SUPABASE_URL')}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up Emreq database...")
    print()
    
    # Test connection first
    if test_connection():
        print()
        create_employee_profiles_table()
        print()
        print("🧪 Testing table access...")
        check_table_exists()
    else:
        print("❌ Cannot proceed without valid Supabase connection") 