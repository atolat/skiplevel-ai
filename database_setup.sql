
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
