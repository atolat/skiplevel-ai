"""Supabase client for loading user profiles."""

import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class SupabaseProfileClient:
    """Client for loading user profiles from Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url:
            raise ValueError("SUPABASE_URL must be set in environment")
        
        # Try to use service role key first (bypasses RLS), fallback to anon key
        if self.service_key:
            print("Using Supabase service role key (bypasses RLS)")
            self.client: Client = create_client(self.url, self.service_key)
        elif self.anon_key:
            print("Using Supabase anon key (subject to RLS)")
            self.client: Client = create_client(self.url, self.anon_key)
        else:
            raise ValueError("Either SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY must be set in environment")
    
    def validate_session_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Validate a Supabase session token and return user info.
        
        Args:
            access_token: The Supabase access token to validate
            
        Returns:
            User info if token is valid, None otherwise
        """
        try:
            # Set the auth token for this request
            self.client.auth.set_session(access_token, refresh_token="")
            
            # Get the current user
            user_response = self.client.auth.get_user(access_token)
            
            if user_response and user_response.user:
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "created_at": str(user_response.user.created_at) if user_response.user.created_at else None
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error validating session token: {e}")
            return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user profile from Supabase.
        
        Args:
            user_id: The user's UUID from Supabase auth
            
        Returns:
            User profile data or None if not found
        """
        try:
            # For RLS, we need to bypass it or use service role key
            # Let's try without .single() first to see what we get
            response = self.client.table('employee_profiles').select('*').eq('id', user_id).execute()
            
            print(f"DEBUG: Query response for user_id {user_id}: {response}")
            
            if response.data and len(response.data) > 0:
                return response.data[0]  # Get first result
            else:
                print(f"DEBUG: No data returned for user_id: {user_id}")
                return None
                
        except Exception as e:
            print(f"Error loading user profile: {e}")
            return None
    
    def get_user_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Load user profile from Supabase by email.
        
        Args:
            email: The user's email address
            
        Returns:
            User profile data or None if not found
        """
        try:
            # For RLS, we need to bypass it or use service role key
            # Let's try without .single() first to see what we get
            response = self.client.table('employee_profiles').select('*').eq('email', email).execute()
            
            print(f"DEBUG: Query response for email {email}: {response}")
            
            if response.data and len(response.data) > 0:
                return response.data[0]  # Get first result
            else:
                print(f"DEBUG: No data returned for email: {email}")
                return None
                
        except Exception as e:
            print(f"Error loading user profile by email: {e}")
            return None
    
    def format_profile_for_agent(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format profile data for agent memory system.
        
        Args:
            profile_data: Raw profile data from Supabase
            
        Returns:
            Formatted profile data for agent memory
        """
        if not profile_data:
            return {}
        
        # Convert arrays to strings for easier processing
        def array_to_string(arr):
            if isinstance(arr, list) and arr:
                return ", ".join(str(item) for item in arr if item)
            return ""
        
        formatted = {
            "name": profile_data.get("name", ""),
            "title": profile_data.get("title", ""),
            "level": profile_data.get("level", ""),
            "specialization": profile_data.get("specialization", ""),
            "years_experience": profile_data.get("years_experience"),
            "years_at_company": profile_data.get("years_at_company"),
            "team": profile_data.get("team", ""),
            "tech_skills": array_to_string(profile_data.get("tech_skills")),
            "current_projects": array_to_string(profile_data.get("current_projects")),
            "career_goals": array_to_string(profile_data.get("career_goals")),
            "biggest_challenges": array_to_string(profile_data.get("biggest_challenges")),
            "strengths": array_to_string(profile_data.get("strengths")),
            "learning_goals": array_to_string(profile_data.get("learning_goals")),
            "communication_style": profile_data.get("communication_style", ""),
            "feedback_frequency": profile_data.get("feedback_frequency", ""),
            "meeting_style": profile_data.get("meeting_style", ""),
            "email": profile_data.get("email", "")
        }
        
        return formatted
    
    def generate_personalized_context(self, profile_data: Dict[str, Any]) -> str:
        """Generate personalized context for the agent based on profile data.
        
        Args:
            profile_data: Formatted profile data
            
        Returns:
            Personalized context string for the agent
        """
        if not profile_data:
            return ""
        
        context_parts = []
        
        # Basic info
        name = profile_data.get("name", "")
        title = profile_data.get("title", "")
        level = profile_data.get("level", "")
        specialization = profile_data.get("specialization", "")
        email = profile_data.get("email", "")
        
        if name:
            context_parts.append(f"You are speaking with {name}")
            
        if title and level:
            context_parts.append(f"who is a {level} {title}")
        elif title:
            context_parts.append(f"who is a {title}")
            
        if specialization:
            context_parts.append(f"specializing in {specialization}")
        
        # Experience
        years_exp = profile_data.get("years_experience")
        years_company = profile_data.get("years_at_company")
        
        if years_exp:
            context_parts.append(f"with {years_exp} years of experience")
            
        if years_company:
            context_parts.append(f"and {years_company} years at their current company")
        
        # Team context
        team = profile_data.get("team", "")
        if team:
            if team == "Solo":
                context_parts.append("working as a solo contributor")
            else:
                context_parts.append(f"working on a {team.lower()} team")
        
        # Contact information - make this prominent for scheduling
        contact_context = ""
        if email:
            contact_context = f"Their email address is {email}."
        
        # Current challenges and goals
        challenges = profile_data.get("biggest_challenges", "")
        goals = profile_data.get("career_goals", "")
        
        challenge_context = ""
        if challenges:
            challenge_context = f"Their biggest challenges right now: {challenges}."
            
        goal_context = ""
        if goals:
            goal_context = f"Their career goals: {goals}."
        
        # Skills and projects
        skills = profile_data.get("tech_skills", "")
        projects = profile_data.get("current_projects", "")
        learning_goals = profile_data.get("learning_goals", "")
        
        skills_context = ""
        if skills:
            skills_context = f"Technical skills: {skills}."
            
        projects_context = ""
        if projects:
            projects_context = f"Current projects: {projects}."
            
        learning_context = ""
        if learning_goals:
            learning_context = f"Learning goals: {learning_goals}."
        
        # Communication preferences
        comm_style = profile_data.get("communication_style", "")
        feedback_freq = profile_data.get("feedback_frequency", "")
        meeting_style = profile_data.get("meeting_style", "")
        
        pref_context = ""
        if comm_style or feedback_freq or meeting_style:
            prefs = []
            if comm_style:
                prefs.append(f"prefers {comm_style.lower()} communication")
            if feedback_freq:
                prefs.append(f"wants {feedback_freq.lower()} feedback")
            if meeting_style:
                prefs.append(f"likes {meeting_style.lower()} meetings")
            
            if prefs:
                pref_context = f"Management preferences: {', '.join(prefs)}."
        
        # Combine all context
        full_context = ". ".join([part for part in context_parts if part]) + "."
        
        # Add contact info first, then other details
        additional_context = " ".join([
            contact_context, challenge_context, goal_context, skills_context, 
            projects_context, learning_context, pref_context
        ]).strip()
        
        if additional_context:
            full_context += f"\n\n{additional_context}"
        
        # Add explicit scheduling instructions
        if email:
            full_context += f"\n\nIMPORTANT: When scheduling meetings or sending calendar invites, use their email address {email}. Do not ask for their email address as you already have it."
        
        return full_context 