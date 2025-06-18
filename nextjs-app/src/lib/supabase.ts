import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://bgxlrdewvlpbntysqqxf.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJneGxyZGV3dmxwYm50eXNxcXhmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAxOTM2MjcsImV4cCI6MjA2NTc2OTYyN30.9mLjZqa2swL7oCtTUZu96UoskENqgMlQCIO-c_YDBTA'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type Database = {
  public: {
    Tables: {
      employee_profiles: {
        Row: {
          id: string
          email: string
          name: string
          title: string
          level: string | null
          team: string | null
          years_experience: number | null
          years_at_company: number | null
          specialization: string
          tech_skills: string[] | null
          current_projects: string[] | null
          career_goals: string[] | null
          biggest_challenges: string[] | null
          strengths: string[] | null
          learning_goals: string[] | null
          last_review_date: string | null
          last_review_rating: string | null
          last_review_feedback: string | null
          last_reviewer: string | null
          communication_style: string | null
          feedback_frequency: string | null
          meeting_style: string | null
          created_at: string
          updated_at: string
          profile_completed: boolean
        }
        Insert: {
          id: string
          email: string
          name: string
          title: string
          level?: string | null
          team?: string | null
          years_experience?: number | null
          years_at_company?: number | null
          specialization: string
          tech_skills?: string[] | null
          current_projects?: string[] | null
          career_goals?: string[] | null
          biggest_challenges?: string[] | null
          strengths?: string[] | null
          learning_goals?: string[] | null
          last_review_date?: string | null
          last_review_rating?: string | null
          last_review_feedback?: string | null
          last_reviewer?: string | null
          communication_style?: string | null
          feedback_frequency?: string | null
          meeting_style?: string | null
          created_at?: string
          updated_at?: string
          profile_completed?: boolean
        }
        Update: {
          id?: string
          email?: string
          name?: string
          title?: string
          level?: string | null
          team?: string | null
          years_experience?: number | null
          years_at_company?: number | null
          specialization?: string
          tech_skills?: string[] | null
          current_projects?: string[] | null
          career_goals?: string[] | null
          biggest_challenges?: string[] | null
          strengths?: string[] | null
          learning_goals?: string[] | null
          last_review_date?: string | null
          last_review_rating?: string | null
          last_review_feedback?: string | null
          last_reviewer?: string | null
          communication_style?: string | null
          feedback_frequency?: string | null
          meeting_style?: string | null
          created_at?: string
          updated_at?: string
          profile_completed?: boolean
        }
      }
    }
  }
}

export type Profile = Database['public']['Tables']['employee_profiles']['Row'] 