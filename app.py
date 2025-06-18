import chainlit as cl
import asyncio
import os
from agent_factory.config import load_config
from agent_factory.agent import BaseAgent
from agent_factory.supabase_client import SupabaseProfileClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
emreq_agent = None

def get_emreq_agent(user_profile=None):
    """Get or create the Emreq agent instance with optional user profile.
    
    Args:
        user_profile: Optional user profile data for personalization
    """
    try:
        config = load_config("configs/engineering_manager_emreq.yaml")
        if config:
            agent = BaseAgent(config, user_profile=user_profile)
            logger.info("Emreq agent loaded successfully")
            return agent
        else:
            logger.error("Failed to load Emreq agent config")
            return None
    except Exception as e:
        logger.error(f"Error loading Emreq agent: {e}")
        return None

def generate_personalized_welcome(user_profile):
    """Generate a personalized welcome message based on user profile.
    
    Args:
        user_profile: User profile data or None
    
    Returns:
        Personalized welcome message string
    """
    if not user_profile:
        # Default welcome message for non-authenticated users
        return """# Welcome to Emreq 🤖

I'm your AI Engineering Manager who cuts through the BS and gets things done.

**What I can help you with:**
- 🎯 **Performance Reviews** - Direct, actionable feedback
- 📊 **Team Management** - Real solutions for underperformance  
- 🔄 **Process Optimization** - Eliminate inefficiencies
- 📅 **Meeting Scheduling** - Automated calendar management
- 🔍 **Industry Research** - Current best practices and trends

**My Philosophy:** I don't do participation trophies, I do performance. Let's skip the small talk and solve your actual problems.

What challenge are you facing today?"""

    # Personalized welcome message
    name = user_profile.get("name", "")
    title = user_profile.get("title", "")
    level = user_profile.get("level", "")
    specialization = user_profile.get("specialization", "")
    years_exp = user_profile.get("years_experience")
    biggest_challenges = user_profile.get("biggest_challenges", "")
    career_goals = user_profile.get("career_goals", "")
    
    # Build personalized greeting
    greeting = f"# Well, well... {name} is back! 🤖"
    
    # Add role-specific commentary
    role_comment = ""
    if level and title:
        role_comment = f"A {level} {title}"
    elif title:
        role_comment = f"A {title}"
    
    if specialization:
        role_comment += f" in {specialization}"
    
    if years_exp:
        if years_exp <= 2:
            role_comment += f" with {years_exp} years under your belt. Still figuring things out, I see."
        elif years_exp <= 5:
            role_comment += f" with {years_exp} years of experience. You should know better by now."
        else:
            role_comment += f" with {years_exp} years of experience. Time to start acting like it."
    
    # Add challenge-specific sass
    challenge_comment = ""
    if biggest_challenges:
        challenge_comment = f"\n\nI see you're still wrestling with: *{biggest_challenges}*. Let's fix that, shall we?"
    
    # Add goal-oriented motivation
    goal_comment = ""
    if career_goals:
        goal_comment = f"\n\nYour goals: *{career_goals}*. Nice aspirations. Now let's talk about what you're actually DOING to get there."
    
    # Combine it all with Emreq's personality
    personalized_msg = f"""{greeting}

{role_comment}

Look, I've got your profile loaded, so let's skip the pleasantries. I know exactly where you are in your career and what you're trying to achieve.{challenge_comment}{goal_comment}

**Here's what I'm going to help you with:**
- 🎯 **Real Talk on Performance** - No sugar-coating your reviews
- 📊 **Team Reality Checks** - What's actually broken vs. what you think is broken
- 🔄 **Process Efficiency** - Stop wasting time on nonsense
- 📅 **Strategic Meetings** - Ones that actually matter
- 🔍 **Industry Benchmarking** - See how you actually stack up

**My Promise:** I'll tell you what you need to hear, not what you want to hear. Ready to get uncomfortable and grow?

What's the real problem you're avoiding today?"""

    return personalized_msg

@cl.action_callback("set_timezone")
async def on_set_timezone(action):
    """Handle timezone setting from frontend."""
    timezone = action.value
    if timezone:
        cl.user_session.set("user_timezone", timezone)
        logger.info(f"Timezone set via action: {timezone}")
        await cl.Message(content=f"✅ Timezone updated to: {timezone}").send()
    return "Timezone updated"

@cl.on_chat_start
async def start():
    """Initialize the chat session with Emreq."""
    global emreq_agent
    
    try:
        # Try to get user profile from Supabase session
        user_profile = None
        user_id = None
        user_email = None
        user_timezone = None
        
        # Get timezone from session (set by JavaScript)
        user_timezone = cl.user_session.get("user_timezone")
        
        # Alternative: try to get from environment variable set by frontend
        if not user_timezone:
            user_timezone = os.getenv("USER_TIMEZONE_OVERRIDE")
        
        # Alternative: check if we can get it from a custom header or other source
        if not user_timezone:
            # For now, let's try to detect from user's profile location or set a reasonable default
            # You can extend this logic based on user's profile data
            user_timezone = "America/Los_Angeles"  # Your actual timezone as detected by browser
            logger.info(f"Using hardcoded timezone (detected by browser): {user_timezone}")
        
        if user_timezone:
            logger.info(f"User timezone detected: {user_timezone}")
        else:
            # Fallback to Eastern Time
            user_timezone = "America/New_York"
            logger.info(f"No timezone detected, using default: {user_timezone}")
        
        # Store timezone in session for future use
        cl.user_session.set("user_timezone", user_timezone)
        
        # First, try to get session data from browser storage
        # We'll implement a JavaScript bridge to pass this data
        logger.info("Waiting for Supabase session data...")
        
        # For now, let's check if we have session data in user_session
        # This will be populated by our JavaScript bridge
        session_data = cl.user_session.get("supabase_session")
        
        if session_data:
            logger.info("Found Supabase session data in user session")
            access_token = session_data.get("access_token")
            user_id = session_data.get("user_id")
            user_email = session_data.get("user_email")
            
            # Validate the session token with Supabase
            if access_token:
                try:
                    profile_client = SupabaseProfileClient()
                    validated_user = profile_client.validate_session_token(access_token)
                    
                    if validated_user:
                        user_id = validated_user["id"]
                        user_email = validated_user["email"]
                        logger.info(f"Validated Supabase session for user: {user_email}")
                    else:
                        logger.warning("Failed to validate Supabase session token")
                        user_id = None
                        user_email = None
                except Exception as e:
                    logger.error(f"Error validating Supabase session: {e}")
                    user_id = None
                    user_email = None
        
        # TEMPORARY: For testing, let's hardcode your user data
        # TODO: Remove this once the session bridge is working
        if not user_id:
            logger.info("No session data found, trying hardcoded test user...")
            user_id = "5b6f17db-bf7e-4a9d-a25b-b37234f2cb55"  # Your actual user ID
            user_email = "arpantolat30@gmail.com"
            logger.info(f"Using hardcoded test user: {user_email}")
        
        # Load user profile if we have a valid user
        if user_id:
            try:
                profile_client = SupabaseProfileClient()
                
                # Try to get profile by user ID first
                raw_profile = profile_client.get_user_profile(user_id)
                
                # If not found by ID, try by email
                if not raw_profile and user_email:
                    raw_profile = profile_client.get_user_profile_by_email(user_email)
                
                if raw_profile:
                    user_profile = profile_client.format_profile_for_agent(raw_profile)
                    # Add timezone to user profile
                    user_profile["timezone"] = user_timezone
                    logger.info(f"Loaded profile for user: {user_profile.get('name', 'Unknown')} ({user_email}) in {user_timezone}")
                else:
                    logger.info(f"No profile found for user: {user_email}")
            except Exception as e:
                logger.warning(f"Could not load user profile: {e}")
        else:
            logger.info("No authenticated user found - using default experience")
            # Even for anonymous users, create a basic profile with timezone
            user_profile = {"timezone": user_timezone}
        
        # Load Emreq agent with user profile (including timezone)
        emreq_agent = get_emreq_agent(user_profile=user_profile)
        if not emreq_agent:
            await cl.Message(content="Error: Failed to initialize Emreq").send()
            return
        
        logger.info("Emreq agent loaded successfully")
        
        # Generate personalized welcome message
        welcome_msg = generate_personalized_welcome(user_profile)
        
        # Debug: Log whether we have profile data
        if user_profile:
            logger.info(f"Sending personalized welcome for: {user_profile.get('name', 'Unknown')}")
        else:
            logger.info("Sending default welcome message")
        
        await cl.Message(content=welcome_msg).send()
        
        # Add example buttons with correct Action API
        actions = [
            cl.Action(
                name="performance_review", 
                value="performance_review", 
                payload={"message": "How do I conduct effective performance reviews?"},
                label="🎯 Performance Reviews", 
                description="How to conduct effective performance reviews"
            ),
            cl.Action(
                name="team_performance", 
                value="team_performance", 
                payload={"message": "My team is underperforming. What should I do?"},
                label="📊 Team Performance", 
                description="My team is underperforming. What should I do?"
            ),
            cl.Action(
                name="schedule_meeting", 
                value="schedule_meeting", 
                payload={"message": "Schedule a 1:1 with john@company.com next Tuesday at 2pm"},
                label="📅 Schedule Meeting", 
                description="Schedule a 1:1 with john@company.com next Tuesday at 2pm"
            ),
            cl.Action(
                name="industry_research", 
                value="industry_research", 
                payload={"message": "Research latest engineering management trends"},
                label="🔍 Industry Research", 
                description="Research latest engineering management trends"
            )
        ]
        
        await cl.Message(content="**Quick Actions:**", actions=actions).send()
        
    except Exception as e:
        logger.error(f"Error initializing Emreq: {e}")
        await cl.Message(content=f"Error loading Emreq: {str(e)}").send()

@cl.action_callback("performance_review")
async def on_performance_review(action):
    await handle_message(action.payload["message"])

@cl.action_callback("team_performance")
async def on_team_performance(action):
    await handle_message(action.payload["message"])

@cl.action_callback("schedule_meeting")
async def on_schedule_meeting(action):
    await handle_message(action.payload["message"])

@cl.action_callback("industry_research")
async def on_industry_research(action):
    await handle_message(action.payload["message"])

async def handle_message(message_content: str):
    """Handle a message and stream the response."""
    global emreq_agent
    
    if not emreq_agent:
        await cl.Message(content="Error: Emreq agent not initialized").send()
        return
    
    try:
        # Create a message to stream the response
        msg = cl.Message(content="")
        await msg.send()
        
        # Stream the response from Emreq
        response_chunks = []
        for chunk in emreq_agent.chat_stream(message_content):
            response_chunks.append(chunk)
            # Update message with accumulated response
            msg.content = "".join(response_chunks)
            await msg.update()
        
        # Final update to ensure complete response is shown
        final_response = "".join(response_chunks)
        msg.content = final_response
        await msg.update()
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await cl.Message(content=f"Error: {str(e)}").send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    await handle_message(message.content) 