// Supabase Authentication Integration
(function() {
    console.log('Starting Supabase initialization...');
    
    let supabase;
    
    // Load Supabase SDK
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
    script.onload = initializeSupabase;
    document.head.appendChild(script);

    function initializeSupabase() {
        console.log('Supabase SDK loaded, initializing client...');
        
        const { createClient } = window.supabase;
        supabase = createClient(
            'https://bgxlrdewvlpbntysqqxf.supabase.co',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJneGxyZGV3dmxwYm50eXNxcXhmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAxOTM2MjcsImV4cCI6MjA2NTc2OTYyN30.9mLjZqa2swL7oCtTUZu96UoskENqgMlQCIO-c_YDBTA'
        );
        
        console.log('Supabase client initialized');
        
        // Check current auth state
        checkAuthState();
    }

    async function checkAuthState() {
        console.log('Checking auth state...');
        
        // Check if we should skip authentication (for demo/public access)
        const skipAuth = new URLSearchParams(window.location.search).get('skip_auth') === 'true';
        if (skipAuth) {
            console.log('Skipping authentication, showing chat interface directly');
            showChatInterface(null);
            return;
        }
        
        const { data: { session } } = await supabase.auth.getSession();
        console.log('Current session:', session);
        
        if (session?.user) {
            console.log('User is logged in:', session.user.email);
            
            // Check if user has completed profile in Supabase
            // First try by user ID
            let { data: profile, error } = await supabase
                .from('employee_profiles')
                .select('*')
                .eq('id', session.user.id)
                .single();

            // If not found by ID, try by email
            if (error && error.code === 'PGRST116') {
                console.log('Profile not found by ID, trying email...');
                const emailResult = await supabase
                    .from('employee_profiles')
                    .select('*')
                    .eq('email', session.user.email)
                    .single();
                
                profile = emailResult.data;
                error = emailResult.error;
            }

            if (error && error.code !== 'PGRST116') {
                console.error('Error checking profile:', error);
            }

            // Check if profile exists and is completed
            if (profile && profile.profile_completed) {
                console.log('User has completed profile, showing chat');
                localStorage.setItem('currentUser', JSON.stringify(profile));
                showChatInterface(session.user);
            } else {
                console.log('User needs to complete profile');
                console.log('Profile data:', profile);
                showProfileSetup(session.user);
            }
        } else {
            console.log('User not logged in');
            // Instead of forcing login, show chat interface with option to login
            showChatInterface(null);
        }
    }

    function showLoginUI() {
        // Hide chat interface
        const chatContainer = document.querySelector('#root');
        if (chatContainer) {
            chatContainer.style.display = 'none';
        }

        // Create login/signup UI
        const loginContainer = document.createElement('div');
        loginContainer.id = 'login-container';
        loginContainer.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: #f8fafc;">
                <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 400px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h1 style="margin: 0;">Welcome to Emreq</h1>
                        <button id="back-to-chat" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #666;">×</button>
                    </div>
                    <p style="text-align: center; color: #666; margin-bottom: 1.5rem; font-size: 0.9rem;">Sign in for personalized AI management experience</p>
                    
                    <div id="login-form">
                        <input type="email" id="email" placeholder="Email" style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px;">
                        <input type="password" id="password" placeholder="Password" style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px;">
                        <button id="login-btn" style="width: 100%; padding: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 1rem;">Sign In</button>
                        <button id="show-signup" style="width: 100%; padding: 0.75rem; background: transparent; color: #2563eb; border: 1px solid #2563eb; border-radius: 4px; cursor: pointer;">Create New Account</button>
                    </div>
                    
                    <div id="signup-form" style="display: none;">
                        <input type="email" id="signup-email" placeholder="Email" style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px;">
                        <input type="password" id="signup-password" placeholder="Password (min 6 characters)" style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px;">
                        <button id="signup-btn" style="width: 100%; padding: 0.75rem; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 1rem;">Create Account</button>
                        <button id="show-login" style="width: 100%; padding: 0.75rem; background: transparent; color: #2563eb; border: 1px solid #2563eb; border-radius: 4px; cursor: pointer;">Back to Sign In</button>
                    </div>
                    
                    <div id="auth-message" style="margin-top: 1rem; text-align: center;"></div>
                    
                    <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #eee; text-align: center;">
                        <button id="continue-anonymous" style="color: #666; background: none; border: none; cursor: pointer; text-decoration: underline; font-size: 0.875rem;">Continue without signing in</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(loginContainer);

        // Add event listeners
        setupAuthListeners();
        
        // Add back to chat functionality
        document.getElementById('back-to-chat').onclick = () => showChatInterface(null);
        document.getElementById('continue-anonymous').onclick = () => showChatInterface(null);
    }

    function showProfileSetup(user) {
        // Hide chat interface
        const chatContainer = document.querySelector('#root');
        if (chatContainer) {
            chatContainer.style.display = 'none';
        }

        // Create profile setup UI
        const profileContainer = document.createElement('div');
        profileContainer.id = 'profile-container';
        profileContainer.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f8fafc; padding: 2rem;">
                <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; width: 100%;">
                    <h1 style="text-align: center; margin-bottom: 0.5rem;">Welcome to Emreq! 🤖</h1>
                    <p style="text-align: center; color: #6b7280; margin-bottom: 2rem;">Let's set up your engineering profile</p>
                    
                    <h3 style="color: #555; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #eee; font-size: 1rem;">👤 Basic Information</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Your Name *</label>
                        <input type="text" id="display-name" placeholder="e.g., Alex Smith" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Your Title *</label>
                        <select id="title" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select your title</option>
                            <option value="Software Engineer">Software Engineer</option>
                            <option value="Senior Software Engineer">Senior Software Engineer</option>
                            <option value="Staff Software Engineer">Staff Software Engineer</option>
                            <option value="Principal Engineer">Principal Engineer</option>
                            <option value="Tech Lead">Tech Lead</option>
                            <option value="Frontend Engineer">Frontend Engineer</option>
                            <option value="Backend Engineer">Backend Engineer</option>
                            <option value="Full Stack Engineer">Full Stack Engineer</option>
                            <option value="DevOps Engineer">DevOps Engineer</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Specialization *</label>
                        <select id="specialization" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select specialization</option>
                            <option value="Frontend">Frontend</option>
                            <option value="Backend">Backend</option>
                            <option value="Full-stack">Full-stack</option>
                            <option value="DevOps">DevOps/Infrastructure</option>
                            <option value="Mobile">Mobile</option>
                            <option value="Data">Data Engineering</option>
                            <option value="Machine Learning">Machine Learning</option>
                            <option value="Security">Security</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Level</label>
                        <select id="level" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select level</option>
                            <option value="Junior">Junior</option>
                            <option value="Mid">Mid-level</option>
                            <option value="Senior">Senior</option>
                            <option value="Staff">Staff</option>
                            <option value="Principal">Principal</option>
                            <option value="Distinguished">Distinguished</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Years of Experience</label>
                        <select id="years-experience" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select experience</option>
                            <option value="1">0-1 years</option>
                            <option value="2">2 years</option>
                            <option value="3">3 years</option>
                            <option value="4">4 years</option>
                            <option value="5">5 years</option>
                            <option value="7">6-7 years</option>
                            <option value="10">8-10 years</option>
                            <option value="15">10+ years</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Years at Company</label>
                        <select id="years-at-company" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select years at company</option>
                            <option value="0">Less than 1 year</option>
                            <option value="1">1-2 years</option>
                            <option value="3">3-4 years</option>
                            <option value="5">5+ years</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Team Size</label>
                        <select id="team-size" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select team size</option>
                            <option value="Solo">Solo contributor</option>
                            <option value="Small">Small team (2-5)</option>
                            <option value="Medium">Medium team (6-10)</option>
                            <option value="Large">Large team (10+)</option>
                        </select>
                    </div>
                    
                    <h3 style="color: #555; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #eee; font-size: 1rem;">🛠️ Skills & Experience</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Tech Skills</label>
                        <textarea id="tech-skills" placeholder="e.g., Python, React, AWS, PostgreSQL, Docker..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;"></textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Current Projects</label>
                        <textarea id="current-projects" placeholder="e.g., User authentication system, Payment processing redesign..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;"></textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <h3 style="color: #555; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #eee; font-size: 1rem;">🎯 Goals & Development</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Career Goals</label>
                        <textarea id="career-goals" placeholder="e.g., Become tech lead, Learn machine learning, Move to product management..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;"></textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Key Strengths</label>
                        <textarea id="strengths" placeholder="e.g., Problem solving, Code reviews, Mentoring, System design..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;"></textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Learning Goals</label>
                        <textarea id="learning-goals" placeholder="e.g., System design, Leadership skills, New programming language..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;"></textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <h3 style="color: #555; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #eee; font-size: 1rem;">🤝 Management Preferences</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Communication Style</label>
                        <select id="communication-style" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select style</option>
                            <option value="Direct">Direct & straightforward</option>
                            <option value="Supportive">Supportive & encouraging</option>
                            <option value="Data-driven">Data-driven & analytical</option>
                            <option value="Collaborative">Collaborative & team-focused</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Feedback Frequency</label>
                        <select id="feedback-frequency" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select frequency</option>
                            <option value="Daily">Daily check-ins</option>
                            <option value="Weekly">Weekly updates</option>
                            <option value="Bi-weekly">Bi-weekly reviews</option>
                            <option value="Monthly">Monthly deep-dives</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Meeting Style</label>
                        <select id="meeting-style" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select style</option>
                            <option value="Structured">Structured agenda</option>
                            <option value="Flexible">Flexible conversation</option>
                            <option value="Problem-focused">Problem-focused</option>
                            <option value="Goal-oriented">Goal-oriented</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 2rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Biggest Challenge Right Now</label>
                        <textarea id="biggest-challenge" placeholder="e.g., Learning system design, improving code quality, work-life balance..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 80px; resize: vertical;"></textarea>
                    </div>
                    
                    <button id="save-profile" style="width: 100%; padding: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem;">Complete Setup</button>
                    
                    <div id="profile-message" style="margin-top: 1rem; text-align: center;"></div>
                </div>
            </div>
        `;
        document.body.appendChild(profileContainer);

        // Add save functionality
        document.getElementById('save-profile').onclick = () => saveProfile(user);
    }

    async function saveProfile(user) {
        // Helper function to split comma-separated values into array
        const splitToArray = (value) => {
            if (!value || !value.trim()) return null;
            return value.split(',').map(item => item.trim()).filter(item => item);
        };

        const profile = {
            id: user.id,
            email: user.email,
            name: document.getElementById('display-name').value,
            title: document.getElementById('title').value,
            specialization: document.getElementById('specialization').value,
            level: document.getElementById('level').value || null,
            years_experience: parseInt(document.getElementById('years-experience').value) || null,
            years_at_company: parseInt(document.getElementById('years-at-company').value) || null,
            team: document.getElementById('team-size').value || null,
            tech_skills: splitToArray(document.getElementById('tech-skills').value),
            current_projects: splitToArray(document.getElementById('current-projects').value),
            career_goals: splitToArray(document.getElementById('career-goals').value),
            strengths: splitToArray(document.getElementById('strengths').value),
            learning_goals: splitToArray(document.getElementById('learning-goals').value),
            biggest_challenges: splitToArray(document.getElementById('biggest-challenge').value),
            communication_style: document.getElementById('communication-style').value || null,
            feedback_frequency: document.getElementById('feedback-frequency').value || null,
            meeting_style: document.getElementById('meeting-style').value || null,
            profile_completed: true
        };

        // Validate required fields
        if (!profile.name || !profile.title || !profile.specialization) {
            document.getElementById('profile-message').innerHTML = `<span style="color: red;">Please fill in all required fields</span>`;
            return;
        }

        console.log('Saving profile to Supabase:', profile);

        try {
            // Save to Supabase
            const { data, error } = await supabase
                .from('employee_profiles')
                .upsert(profile)
                .select();

            if (error) {
                console.error('Supabase error:', error);
                document.getElementById('profile-message').innerHTML = `<span style="color: red;">Error saving profile: ${error.message}</span>`;
                return;
            }

            console.log('Profile saved successfully:', data);
            document.getElementById('profile-message').innerHTML = `<span style="color: green;">Profile saved! Loading Emreq...</span>`;

            // Also save to localStorage for immediate access
            localStorage.setItem('currentUser', JSON.stringify(profile));

            setTimeout(() => {
                showChatInterface(user);
            }, 1000);

        } catch (err) {
            console.error('Error saving profile:', err);
            document.getElementById('profile-message').innerHTML = `<span style="color: red;">Error saving profile. Please try again.</span>`;
        }
    }

    function setupAuthListeners() {
        // Toggle between login and signup
        document.getElementById('show-signup').onclick = () => {
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('signup-form').style.display = 'block';
        };

        document.getElementById('show-login').onclick = () => {
            document.getElementById('signup-form').style.display = 'none';
            document.getElementById('login-form').style.display = 'block';
        };

        // Login functionality
        document.getElementById('login-btn').onclick = handleLogin;
        
        // Signup functionality
        document.getElementById('signup-btn').onclick = handleSignup;
    }

    async function handleLogin() {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        console.log('Attempting login for:', email);
        
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password
        });

        if (error) {
            console.error('Login error:', error);
            console.error('Error code:', error.status);
            console.error('Error message:', error.message);
            
            let errorMessage = error.message;
            if (error.message.includes('Invalid login credentials')) {
                errorMessage = 'Invalid email or password. Please check your credentials.';
            } else if (error.message.includes('Email not confirmed')) {
                errorMessage = 'Please check your email and confirm your account first.';
            }
            
            document.getElementById('auth-message').innerHTML = `<span style="color: red;">Error: ${errorMessage}</span>`;
        } else {
            console.log('Login successful:', data.user.email);
            console.log('Session:', data.session);
            // checkAuthState will be called automatically and handle profile check
            checkAuthState();
        }
    }

    async function handleSignup() {
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        
        console.log('Attempting signup for:', email);
        
        const { data, error } = await supabase.auth.signUp({
            email,
            password
        });

        if (error) {
            console.error('Signup error:', error);
            document.getElementById('auth-message').innerHTML = `<span style="color: red;">Error: ${error.message}</span>`;
        } else {
            console.log('Signup successful:', data);
            console.log('User created:', data.user);
            console.log('Session:', data.session);
            
            if (data.user && !data.session) {
                // Email confirmation required
                document.getElementById('auth-message').innerHTML = `<span style="color: orange;">Account created! Please check your email and confirm your account before signing in.</span>`;
            } else if (data.session) {
                // Immediate login (email confirmation disabled)
                document.getElementById('auth-message').innerHTML = `<span style="color: green;">Account created and logged in!</span>`;
                checkAuthState();
            } else {
                // Fallback
                document.getElementById('auth-message').innerHTML = `<span style="color: green;">Account created! You can now sign in.</span>`;
            }
            
            // Switch back to login form after a delay
            setTimeout(() => {
                document.getElementById('signup-form').style.display = 'none';
                document.getElementById('login-form').style.display = 'block';
            }, 3000);
        }
    }

    function showChatInterface(user) {
        // Remove login UI
        const loginContainer = document.getElementById('login-container');
        if (loginContainer) {
            loginContainer.remove();
        }

        // Remove profile UI
        const profileContainer = document.getElementById('profile-container');
        if (profileContainer) {
            profileContainer.remove();
        }

        // Store Supabase session for Chainlit to access (only if user exists)
        if (user) {
            supabase.auth.getSession().then(({ data: { session }, error }) => {
                if (session) {
                    // Store session data securely
                    const sessionData = {
                        access_token: session.access_token,
                        user_id: session.user.id,
                        user_email: session.user.email,
                        expires_at: session.expires_at
                    };
                    
                    localStorage.setItem('supabase_session', JSON.stringify(sessionData));
                    console.log('Stored Supabase session for Chainlit access');
                    console.log('Session data:', sessionData);
                    
                    // Immediately try to pass to Chainlit
                    setTimeout(() => {
                        console.log('Attempting to pass session to Chainlit...');
                        if (setChainlitSession(sessionData)) {
                            console.log('✅ Successfully set session in Chainlit');
                        } else {
                            console.log('❌ Failed to set session in Chainlit, will retry...');
                            waitForChainlitAndSetSession();
                        }
                    }, 1000);
                    
                    // Notify Chainlit about the authenticated user
                    if (window.chainlit && window.chainlit.socket) {
                        window.chainlit.socket.emit('auth_update', {
                            user_id: session.user.id,
                            user_email: session.user.email,
                            access_token: session.access_token
                        });
                    }
                }
            });
        }

        // Show chat interface
        const chatContainer = document.querySelector('#root');
        if (chatContainer) {
            chatContainer.style.display = 'block';
        }

        // Add appropriate button based on user status
        if (user) {
            // Add edit profile button for logged in users
            addEditProfileButton(user);
            console.log('Chat interface shown for user:', user.email);
        } else {
            // Add login button for anonymous users
            addLoginButton();
            console.log('Chat interface shown for anonymous user');
        }
    }

    function addEditProfileButton(user) {
        // Remove existing button if it exists
        const existingButton = document.getElementById('edit-profile-btn');
        if (existingButton) {
            existingButton.remove();
        }

        // Create edit profile button that integrates with Chainlit's UI
        const editButton = document.createElement('button');
        editButton.id = 'edit-profile-btn';
        editButton.innerHTML = '⚙️ Edit Profile';
        editButton.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            font-size: 0.875rem;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: background 0.2s;
        `;

        // Hover effect
        editButton.onmouseover = () => editButton.style.background = '#1d4ed8';
        editButton.onmouseout = () => editButton.style.background = '#2563eb';

        // Click handler
        editButton.onclick = () => showEditProfileModal(user);

        document.body.appendChild(editButton);
    }

    function addLoginButton() {
        // Remove existing buttons if they exist
        const existingButton = document.getElementById('edit-profile-btn');
        if (existingButton) {
            existingButton.remove();
        }
        const existingLoginButton = document.getElementById('login-btn-header');
        if (existingLoginButton) {
            existingLoginButton.remove();
        }

        // Create login button for anonymous users
        const loginButton = document.createElement('button');
        loginButton.id = 'login-btn-header';
        loginButton.innerHTML = '🔐 Sign In for Personalization';
        loginButton.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            font-size: 0.875rem;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: background 0.2s;
        `;

        // Hover effect
        loginButton.onmouseover = () => loginButton.style.background = '#059669';
        loginButton.onmouseout = () => loginButton.style.background = '#10b981';

        // Click handler - show login UI
        loginButton.onclick = () => {
            showLoginUI();
        };

        document.body.appendChild(loginButton);
    }

    async function showEditProfileModal(user) {
        // Get current profile data from Supabase
        let currentProfile = {};
        try {
            const { data, error } = await supabase
                .from('employee_profiles')
                .select('*')
                .eq('id', user.id)
                .single();

            if (data) {
                currentProfile = data;
            }
        } catch (err) {
            console.error('Error fetching profile:', err);
        }

        // Create modal overlay
        const modal = document.createElement('div');
        modal.id = 'edit-profile-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 2000;
            padding: 2rem;
            box-sizing: border-box;
        `;

        // Create modal content (reuse the profile form)
        modal.innerHTML = `
            <div style="background: white; border-radius: 8px; max-width: 600px; width: 100%; max-height: 80vh; overflow-y: auto; position: relative;">
                <div style="padding: 2rem; padding-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <h2 style="margin: 0; color: #333;">Edit Your Profile</h2>
                        <button id="close-modal" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #666;">×</button>
                    </div>
                    
                    <h3 style="color: #555; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #eee; font-size: 1rem;">👤 Basic Information</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Your Name *</label>
                        <input type="text" id="edit-display-name" placeholder="e.g., Alex Smith" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;" value="${currentProfile.name || ''}">
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Your Title *</label>
                        <select id="edit-title" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select your title</option>
                            <option value="Software Engineer" ${currentProfile.title === 'Software Engineer' ? 'selected' : ''}>Software Engineer</option>
                            <option value="Senior Software Engineer" ${currentProfile.title === 'Senior Software Engineer' ? 'selected' : ''}>Senior Software Engineer</option>
                            <option value="Staff Software Engineer" ${currentProfile.title === 'Staff Software Engineer' ? 'selected' : ''}>Staff Software Engineer</option>
                            <option value="Principal Engineer" ${currentProfile.title === 'Principal Engineer' ? 'selected' : ''}>Principal Engineer</option>
                            <option value="Tech Lead" ${currentProfile.title === 'Tech Lead' ? 'selected' : ''}>Tech Lead</option>
                            <option value="Frontend Engineer" ${currentProfile.title === 'Frontend Engineer' ? 'selected' : ''}>Frontend Engineer</option>
                            <option value="Backend Engineer" ${currentProfile.title === 'Backend Engineer' ? 'selected' : ''}>Backend Engineer</option>
                            <option value="Full Stack Engineer" ${currentProfile.title === 'Full Stack Engineer' ? 'selected' : ''}>Full Stack Engineer</option>
                            <option value="DevOps Engineer" ${currentProfile.title === 'DevOps Engineer' ? 'selected' : ''}>DevOps Engineer</option>
                            <option value="Other" ${currentProfile.title === 'Other' ? 'selected' : ''}>Other</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Specialization *</label>
                        <select id="edit-specialization" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select specialization</option>
                            <option value="Frontend" ${currentProfile.specialization === 'Frontend' ? 'selected' : ''}>Frontend</option>
                            <option value="Backend" ${currentProfile.specialization === 'Backend' ? 'selected' : ''}>Backend</option>
                            <option value="Full-stack" ${currentProfile.specialization === 'Full-stack' ? 'selected' : ''}>Full-stack</option>
                            <option value="DevOps" ${currentProfile.specialization === 'DevOps' ? 'selected' : ''}>DevOps/Infrastructure</option>
                            <option value="Mobile" ${currentProfile.specialization === 'Mobile' ? 'selected' : ''}>Mobile</option>
                            <option value="Data" ${currentProfile.specialization === 'Data' ? 'selected' : ''}>Data Engineering</option>
                            <option value="Machine Learning" ${currentProfile.specialization === 'Machine Learning' ? 'selected' : ''}>Machine Learning</option>
                            <option value="Security" ${currentProfile.specialization === 'Security' ? 'selected' : ''}>Security</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Level</label>
                        <select id="edit-level" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select level</option>
                            <option value="Junior" ${currentProfile.level === 'Junior' ? 'selected' : ''}>Junior</option>
                            <option value="Mid" ${currentProfile.level === 'Mid' ? 'selected' : ''}>Mid-level</option>
                            <option value="Senior" ${currentProfile.level === 'Senior' ? 'selected' : ''}>Senior</option>
                            <option value="Staff" ${currentProfile.level === 'Staff' ? 'selected' : ''}>Staff</option>
                            <option value="Principal" ${currentProfile.level === 'Principal' ? 'selected' : ''}>Principal</option>
                            <option value="Distinguished" ${currentProfile.level === 'Distinguished' ? 'selected' : ''}>Distinguished</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Years of Experience</label>
                        <select id="edit-years-experience" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select experience</option>
                            <option value="1" ${currentProfile.years_experience === 1 ? 'selected' : ''}>0-1 years</option>
                            <option value="2" ${currentProfile.years_experience === 2 ? 'selected' : ''}>2 years</option>
                            <option value="3" ${currentProfile.years_experience === 3 ? 'selected' : ''}>3 years</option>
                            <option value="4" ${currentProfile.years_experience === 4 ? 'selected' : ''}>4 years</option>
                            <option value="5" ${currentProfile.years_experience === 5 ? 'selected' : ''}>5 years</option>
                            <option value="7" ${currentProfile.years_experience === 7 ? 'selected' : ''}>6-7 years</option>
                            <option value="10" ${currentProfile.years_experience === 10 ? 'selected' : ''}>8-10 years</option>
                            <option value="15" ${currentProfile.years_experience === 15 ? 'selected' : ''}>10+ years</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Years at Company</label>
                        <select id="edit-years-at-company" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select years at company</option>
                            <option value="0" ${currentProfile.years_at_company === 0 ? 'selected' : ''}>Less than 1 year</option>
                            <option value="1" ${currentProfile.years_at_company === 1 ? 'selected' : ''}>1-2 years</option>
                            <option value="3" ${currentProfile.years_at_company === 3 ? 'selected' : ''}>3-4 years</option>
                            <option value="5" ${currentProfile.years_at_company === 5 ? 'selected' : ''}>5+ years</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Team Size</label>
                        <select id="edit-team-size" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select team size</option>
                            <option value="Solo" ${currentProfile.team === 'Solo' ? 'selected' : ''}>Solo contributor</option>
                            <option value="Small" ${currentProfile.team === 'Small' ? 'selected' : ''}>Small team (2-5)</option>
                            <option value="Medium" ${currentProfile.team === 'Medium' ? 'selected' : ''}>Medium team (6-10)</option>
                            <option value="Large" ${currentProfile.team === 'Large' ? 'selected' : ''}>Large team (10+)</option>
                        </select>
                    </div>
                    
                    <h3 style="color: #555; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #eee; font-size: 1rem;">🛠️ Skills & Experience</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Tech Skills</label>
                        <textarea id="edit-tech-skills" placeholder="e.g., Python, React, AWS, PostgreSQL, Docker..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;">${currentProfile.tech_skills ? currentProfile.tech_skills.join(', ') : ''}</textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Current Projects</label>
                        <textarea id="edit-current-projects" placeholder="e.g., User authentication system, Payment processing redesign..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;">${currentProfile.current_projects ? currentProfile.current_projects.join(', ') : ''}</textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <h3 style="color: #555; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #eee; font-size: 1rem;">🎯 Goals & Development</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Career Goals</label>
                        <textarea id="edit-career-goals" placeholder="e.g., Become tech lead, Learn machine learning, Move to product management..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;">${currentProfile.career_goals ? currentProfile.career_goals.join(', ') : ''}</textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Key Strengths</label>
                        <textarea id="edit-strengths" placeholder="e.g., Problem solving, Code reviews, Mentoring, System design..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;">${currentProfile.strengths ? currentProfile.strengths.join(', ') : ''}</textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Learning Goals</label>
                        <textarea id="edit-learning-goals" placeholder="e.g., System design, Leadership skills, New programming language..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 60px; resize: vertical;">${currentProfile.learning_goals ? currentProfile.learning_goals.join(', ') : ''}</textarea>
                        <small style="color: #666; font-size: 0.875rem;">Separate with commas</small>
                    </div>

                    <h3 style="color: #555; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #eee; font-size: 1rem;">🤝 Management Preferences</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Communication Style</label>
                        <select id="edit-communication-style" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select style</option>
                            <option value="Direct" ${currentProfile.communication_style === 'Direct' ? 'selected' : ''}>Direct & straightforward</option>
                            <option value="Supportive" ${currentProfile.communication_style === 'Supportive' ? 'selected' : ''}>Supportive & encouraging</option>
                            <option value="Data-driven" ${currentProfile.communication_style === 'Data-driven' ? 'selected' : ''}>Data-driven & analytical</option>
                            <option value="Collaborative" ${currentProfile.communication_style === 'Collaborative' ? 'selected' : ''}>Collaborative & team-focused</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Feedback Frequency</label>
                        <select id="edit-feedback-frequency" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select frequency</option>
                            <option value="Daily" ${currentProfile.feedback_frequency === 'Daily' ? 'selected' : ''}>Daily check-ins</option>
                            <option value="Weekly" ${currentProfile.feedback_frequency === 'Weekly' ? 'selected' : ''}>Weekly updates</option>
                            <option value="Bi-weekly" ${currentProfile.feedback_frequency === 'Bi-weekly' ? 'selected' : ''}>Bi-weekly reviews</option>
                            <option value="Monthly" ${currentProfile.feedback_frequency === 'Monthly' ? 'selected' : ''}>Monthly deep-dives</option>
                        </select>
                    </div>

                    <div style="margin-bottom: 1rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Meeting Style</label>
                        <select id="edit-meeting-style" style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px;">
                            <option value="">Select style</option>
                            <option value="Structured" ${currentProfile.meeting_style === 'Structured' ? 'selected' : ''}>Structured agenda</option>
                            <option value="Flexible" ${currentProfile.meeting_style === 'Flexible' ? 'selected' : ''}>Flexible conversation</option>
                            <option value="Problem-focused" ${currentProfile.meeting_style === 'Problem-focused' ? 'selected' : ''}>Problem-focused</option>
                            <option value="Goal-oriented" ${currentProfile.meeting_style === 'Goal-oriented' ? 'selected' : ''}>Goal-oriented</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 2rem;">
                        <label style="display: block; margin-bottom: 0.5rem; font-weight: 500;">Biggest Challenge Right Now</label>
                        <textarea id="edit-biggest-challenge" placeholder="e.g., Learning system design, improving code quality, work-life balance..." style="width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 4px; min-height: 80px; resize: vertical;">${currentProfile.biggest_challenges ? currentProfile.biggest_challenges.join(', ') : ''}</textarea>
                    </div>
                    
                    <div style="display: flex; gap: 1rem; margin-top: 2rem;">
                        <button id="save-edit-profile" style="flex: 1; padding: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem;">Save Changes</button>
                        <button id="cancel-edit" style="flex: 1; padding: 0.75rem; background: #6b7280; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem;">Cancel</button>
                    </div>
                    
                    <div id="edit-profile-message" style="margin-top: 1rem; text-align: center;"></div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Add event listeners
        document.getElementById('close-modal').onclick = () => modal.remove();
        document.getElementById('cancel-edit').onclick = () => modal.remove();
        document.getElementById('save-edit-profile').onclick = () => saveEditedProfile(user, modal);

        // Close modal when clicking outside
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        };
    }

    async function saveEditedProfile(user, modal) {
        // Helper function to split comma-separated values into array
        const splitToArray = (value) => {
            if (!value || !value.trim()) return null;
            return value.split(',').map(item => item.trim()).filter(item => item);
        };

        const profile = {
            id: user.id,
            email: user.email,
            name: document.getElementById('edit-display-name').value,
            title: document.getElementById('edit-title').value,
            specialization: document.getElementById('edit-specialization').value,
            level: document.getElementById('edit-level').value || null,
            years_experience: parseInt(document.getElementById('edit-years-experience').value) || null,
            years_at_company: parseInt(document.getElementById('edit-years-at-company').value) || null,
            team: document.getElementById('edit-team-size').value || null,
            tech_skills: splitToArray(document.getElementById('edit-tech-skills').value),
            current_projects: splitToArray(document.getElementById('edit-current-projects').value),
            career_goals: splitToArray(document.getElementById('edit-career-goals').value),
            strengths: splitToArray(document.getElementById('edit-strengths').value),
            learning_goals: splitToArray(document.getElementById('edit-learning-goals').value),
            biggest_challenges: splitToArray(document.getElementById('edit-biggest-challenge').value),
            communication_style: document.getElementById('edit-communication-style').value || null,
            feedback_frequency: document.getElementById('edit-feedback-frequency').value || null,
            meeting_style: document.getElementById('edit-meeting-style').value || null,
            profile_completed: true
        };

        // Validate required fields
        if (!profile.name || !profile.title || !profile.specialization) {
            document.getElementById('edit-profile-message').innerHTML = `<span style="color: red;">Please fill in all required fields</span>`;
            return;
        }

        console.log('Updating profile in Supabase:', profile);

        try {
            // Update in Supabase
            const { data, error } = await supabase
                .from('employee_profiles')
                .upsert(profile)
                .select();

            if (error) {
                console.error('Supabase error:', error);
                document.getElementById('edit-profile-message').innerHTML = `<span style="color: red;">Error updating profile: ${error.message}</span>`;
                return;
            }

            console.log('Profile updated successfully:', data);
            document.getElementById('edit-profile-message').innerHTML = `<span style="color: green;">Profile updated successfully!</span>`;

            // Also update localStorage for immediate access
            localStorage.setItem('currentUser', JSON.stringify(profile));

            // Close modal after a short delay
            setTimeout(() => {
                modal.remove();
            }, 1500);

        } catch (err) {
            console.error('Error updating profile:', err);
            document.getElementById('edit-profile-message').innerHTML = `<span style="color: red;">Error updating profile. Please try again.</span>`;
        }
    }

    // Function to set session data in Chainlit
    function setChainlitSession(sessionData) {
        console.log('setChainlitSession called with:', sessionData);
        console.log('window.chainlit exists:', !!window.chainlit);
        
        // Detect user's timezone
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        console.log('Detected user timezone:', userTimezone);
        
        // Try to set session data in Chainlit's user session
        if (window.chainlit && window.chainlit.setUserSession) {
            console.log('Chainlit setUserSession method exists, calling it...');
            window.chainlit.setUserSession({
                supabase_session: {
                    access_token: sessionData.access_token,
                    user_id: sessionData.user_id,
                    user_email: sessionData.user_email
                },
                user_timezone: userTimezone
            });
            console.log('✅ Set Chainlit session data with timezone:', userTimezone);
            return true;
        } else {
            console.log('❌ Chainlit setUserSession not available');
            if (window.chainlit) {
                console.log('Chainlit object methods:', Object.keys(window.chainlit));
            }
        }
        return false;
    }

    // Function to pass existing session to Chainlit
    function passSessionToChainlit() {
        const sessionData = localStorage.getItem('supabase_session');
        if (sessionData) {
            try {
                const session = JSON.parse(sessionData);
                
                // Check if session is still valid (not expired)
                const now = Math.floor(Date.now() / 1000);
                if (session.expires_at && session.expires_at > now) {
                    console.log('Found valid session, passing to Chainlit');
                    
                    // Try to set session data directly
                    if (setChainlitSession(session)) {
                        return true;
                    }
                    
                    // Detect user's timezone
                    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                    
                    // Fallback: dispatch custom event
                    const event = new CustomEvent('supabase_session_ready', {
                        detail: {
                            user_id: session.user_id,
                            user_email: session.user_email,
                            access_token: session.access_token,
                            user_timezone: userTimezone
                        }
                    });
                    window.dispatchEvent(event);
                    
                    return true;
                } else {
                    console.log('Session expired, clearing storage');
                    localStorage.removeItem('supabase_session');
                }
            } catch (e) {
                console.error('Error parsing session data:', e);
                localStorage.removeItem('supabase_session');
            }
        }
        return false;
    }

    // Enhanced function to wait for Chainlit to be ready
    function waitForChainlitAndSetSession() {
        const sessionData = localStorage.getItem('supabase_session');
        if (!sessionData) return;

        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max
        
        const checkChainlit = () => {
            attempts++;
            
            if (window.chainlit) {
                console.log('Chainlit loaded, setting session data');
                passSessionToChainlit();
                return;
            }
            
            if (attempts < maxAttempts) {
                setTimeout(checkChainlit, 100);
            } else {
                console.log('Chainlit not loaded after 5 seconds, proceeding anyway');
            }
        };
        
        checkChainlit();
    }

    // Check for existing session when page loads
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Page loaded, checking for existing session...');
        
        // Always detect and pass timezone to Chainlit
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        console.log('Detected user timezone:', userTimezone);
        
        // Set timezone in session storage for backend access
        sessionStorage.setItem('user_timezone', userTimezone);
        
        // Try to pass timezone to Chainlit immediately
        const passTimezoneToChainlit = () => {
            if (window.chainlit && window.chainlit.setUserSession) {
                window.chainlit.setUserSession({
                    user_timezone: userTimezone
                });
                console.log('✅ Set timezone in Chainlit session:', userTimezone);
                return true;
            }
            return false;
        };
        
        // Try immediately, then retry with delays
        if (!passTimezoneToChainlit()) {
            let attempts = 0;
            const maxAttempts = 50;
            
            const retryTimezone = () => {
                attempts++;
                if (passTimezoneToChainlit() || attempts >= maxAttempts) {
                    return;
                }
                setTimeout(retryTimezone, 100);
            };
            
            setTimeout(retryTimezone, 100);
        }
        
        // Wait for Chainlit to be ready, then set session
        waitForChainlitAndSetSession();
        
        // Also check auth state for new users
        setTimeout(() => {
            checkAuthState();
        }, 500);
    });
})(); 