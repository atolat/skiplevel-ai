#!/usr/bin/env python3
"""Test script to verify we can find user profile in Supabase."""

from agent_factory.supabase_client import SupabaseProfileClient

def test_profile_lookup():
    """Test looking up user profile by email."""
    
    email = "arpantolat30@gmail.com"
    
    try:
        client = SupabaseProfileClient()
        print(f"Looking up profile for: {email}")
        
        # Try to find profile by email
        profile = client.get_user_profile_by_email(email)
        
        if profile:
            print("✅ Profile found!")
            print(f"   Name: {profile.get('name', 'Not set')}")
            print(f"   Title: {profile.get('title', 'Not set')}")
            print(f"   Email: {profile.get('email', 'Not set')}")
            print(f"   ID: {profile.get('id', 'Not set')}")
            
            # Test formatting
            formatted = client.format_profile_for_agent(profile)
            print(f"   Formatted name: {formatted.get('name', 'Not set')}")
            
        else:
            print("❌ No profile found")
            print("   Have you completed the profile setup form?")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_profile_lookup() 