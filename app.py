import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import time
import json

# Set page configuration
st.set_page_config(
    page_title="Hey Bob - Voice Assistant",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🎤"
)

# API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 API keys are missing. Please check your configuration.")
    st.stop()

SYSTEM_PROMPT = """
You are Bob, a friendly and helpful voice assistant activated by the wake word "Hey Bob".

Your personality:
- Conversational and natural, like talking to a friend
- Concise but informative (2-4 sentences max for voice)
- Helpful and knowledgeable about any topic
- Always respond as if you're speaking out loud

You can help with:
- General knowledge and trivia
- Current events and news (use web search)
- Weather information  
- Technology questions
- Calculations and conversions
- Medical and health information
- Travel and local information
- And much more

Always provide responses that sound natural when spoken aloud. Avoid overly technical language unless specifically asked.
"""

@st.cache_resource
def get_agent():
    """Initialize and cache the AI agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=SYSTEM_PROMPT,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return None

def get_ai_response(query):
    """Get response from AI agent."""
    agent = get_agent()
    if agent is None:
        return "Sorry, I'm having trouble connecting to my knowledge base right now."
    
    try:
        response = agent.run(query)
        return response.content.strip()
    except Exception as e:
        return f"Sorry, I encountered an error while processing your question: {str(e)}"

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'voice_query' not in st.session_state:
        st.session_state.voice_query = None
    if 'processing_voice' not in st.session_state:
        st.session_state.processing_voice = False

    # Custom CSS for a modern voice assistant look
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    .voice-status {
        font-size: 1.5rem;
        margin: 1rem 0;
    }
    .conversation-bubble {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        border-left: 4px solid #007bff;
    }
    .bob-response {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .wake-word {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Hey Bob</h1>
        <p>Your Voice-Activated AI Assistant</p>
        <p style="font-size: 0.9rem; opacity: 0.8;">Say <span class="wake-word">"Hey Bob"</span> followed by your question</p>
    </div>
    """, unsafe_allow_html=True)

    # Voice Assistant Interface
    import streamlit.components.v1 as components
    
    # Fixed voice interface with proper communication
    voice_assistant_html = f"""
    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #74b9ff, #0984e3); border-radius: 20px; margin: 20px 0; color: white;">
        
        <!-- Assistant Status -->
        <div id="assistantStatus" style="font-size: 24px; margin-bottom: 20px; font-weight: bold;">
            🎤 Assistant Ready
        </div>
        
        <!-- Main Control Button -->
        <button id="mainBtn" style="
            font-size: 80px; 
            background: rgba(255,255,255,0.2); 
            border: 3px solid white; 
            border-radius: 50%; 
            cursor: pointer; 
            padding: 25px;
            transition: all 0.3s;
            color: white;
            margin-bottom: 20px;
        ">🎤</button>
        
        <!-- Status Messages -->
        <div id="listeningStatus" style="font-size: 18px; margin: 15px 0; min-height: 30px;">
            Click to start listening for "Hey Bob"
        </div>
        
        <!-- Transcript Display -->
        <div id="transcriptDisplay" style="
            background: rgba(255,255,255,0.9); 
            color: #333; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 15px 0; 
            min-height: 50px;
            display: none;
            font-family: monospace;
        ">
            Transcript will appear here...
        </div>
        
        <!-- Hidden form for communication with Streamlit -->
        <form id="voiceForm" style="display: none;">
            <input type="text" id="voiceInput" name="voice_query" />
        </form>
        
        <!-- Controls -->
        <div style="margin-top: 20px;">
            <button id="stopBtn" style="
                padding: 10px 20px; 
                background: #dc3545; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer;
                margin: 5px;
                display: none;
            ">⏹️ Stop Listening</button>
        </div>
    </div>

    <script>
    let recognition;
    let isListening = false;
    let continuousMode = false;
    let restartTimeout;

    const mainBtn = document.getElementById('mainBtn');
    const status = document.getElementById('listeningStatus');
    const assistantStatus = document.getElementById('assistantStatus');
    const transcript = document.getElementById('transcriptDisplay');
    const stopBtn = document.getElementById('stopBtn');

    // Check for wake word
    function checkWakeWord(text) {{
        const lowerText = text.toLowerCase().trim();
        const wakePatterns = [
            /hey\\s+bob/,
            /hi\\s+bob/,
            /hello\\s+bob/,
            /ok\\s+bob/
        ];
        
        for (let pattern of wakePatterns) {{
            const match = lowerText.match(pattern);
            if (match) {{
                // Extract command after wake word
                const command = text.substring(match.index + match[0].length).trim();
                return command || "Hello"; // Return command or default greeting
            }}
        }}
        return null;
    }}

    // Send command to Streamlit using session state callback
    function sendToStreamlit(command) {{
        // Use Streamlit's session state communication
        const data = {{
            query: command,
            timestamp: Date.now()
        }};
        
        // Store in session storage temporarily
        try {{
            sessionStorage.setItem('hey_bob_query', JSON.stringify(data));
            // Trigger Streamlit rerun by changing URL hash
            window.location.hash = 'voice_command_' + Date.now();
            
            // Alternative: Use postMessage to parent window
            window.parent.postMessage({{
                type: 'hey_bob_command',
                command: command
            }}, '*');
            
        }} catch (e) {{
            console.log('Storage method failed, trying direct method');
            // Fallback: Use URL parameters
            const url = new URL(window.location);
            url.searchParams.set('voice_query', encodeURIComponent(command));
            url.searchParams.set('t', Date.now());
            window.location.href = url.toString();
        }}
    }}

    // Process voice command
    function processCommand(command) {{
        transcript.innerHTML = `🎙️ <strong>You said:</strong> "Hey Bob, ${{command}}"`;
        transcript.style.display = 'block';
        status.innerHTML = '🤖 Sending to Bob...';
        assistantStatus.innerHTML = '📡 Processing...';
        
        // Stop recognition
        if (recognition) {{
            continuousMode = false;
            recognition.stop();
        }}
        
        // Send to Streamlit
        sendToStreamlit(command);
    }}

    // Initialize speech recognition
    function initSpeechRecognition() {{
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
            status.innerHTML = '❌ Speech recognition not supported. Use Chrome/Edge!';
            return false;
        }}

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;  // Process one phrase at a time
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onstart = function() {{
            isListening = true;
            mainBtn.style.background = 'rgba(255,0,0,0.4)';
            mainBtn.style.transform = 'scale(1.1)';
            mainBtn.style.boxShadow = '0 0 20px rgba(255,0,0,0.5)';
            assistantStatus.innerHTML = '👂 Listening for "Hey Bob"...';
            status.innerHTML = 'Listening... Say <strong>"Hey Bob"</strong> + your question';
            stopBtn.style.display = 'inline-block';
            transcript.style.display = 'block';
            transcript.innerHTML = '🎧 Listening for wake word...';
        }};

        recognition.onresult = function(event) {{
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {{
                const transcriptPart = event.results[i][0].transcript;
                if (event.results[i].isFinal) {{
                    finalTranscript += transcriptPart + ' ';
                }} else {{
                    interimTranscript += transcriptPart;
                }}
            }}
            
            // Show live transcript
            const currentText = finalTranscript + interimTranscript;
            if (currentText.trim()) {{
                transcript.innerHTML = `🎧 Hearing: "${{currentText.trim()}}"`;
                
                // Check for wake word in real-time
                const command = checkWakeWord(currentText);
                if (command) {{
                    transcript.innerHTML = `🎯 Wake word detected! Command: "${{command}}"`;
                    assistantStatus.innerHTML = '🎯 Wake word found!';
                    setTimeout(() => processCommand(command), 500);
                    return;
                }}
            }}
        }};

        recognition.onerror = function(event) {{
            console.error('Speech recognition error:', event.error);
            
            if (event.error === 'not-allowed') {{
                status.innerHTML = '🔒 Microphone access denied. Please allow and refresh!';
                assistantStatus.innerHTML = '❌ No mic access';
            }} else if (event.error === 'network') {{
                status.innerHTML = '🌐 Network error. Check connection.';
                assistantStatus.innerHTML = '❌ Network issue';
            }} else if (event.error === 'no-speech') {{
                status.innerHTML = '🔇 No speech detected. Try again.';
                // Auto-restart after no speech
                if (continuousMode) {{
                    setTimeout(startListening, 1000);
                }}
            }} else {{
                status.innerHTML = `❌ Error: ${{event.error}}`;
                assistantStatus.innerHTML = '❌ Recognition error';
            }}
        }};

        recognition.onend = function() {{
            isListening = false;
            mainBtn.style.background = 'rgba(255,255,255,0.2)';
            mainBtn.style.transform = 'scale(1)';
            mainBtn.style.boxShadow = 'none';
            
            if (continuousMode) {{
                // Restart listening after a short delay
                clearTimeout(restartTimeout);
                restartTimeout = setTimeout(() => {{
                    if (continuousMode && !isListening) {{
                        startListening();
                    }}
                }}, 500);
            }} else {{
                assistantStatus.innerHTML = '🎤 Assistant Ready';
                status.innerHTML = 'Click to start listening for "Hey Bob"';
                stopBtn.style.display = 'none';
                transcript.style.display = 'none';
            }}
        }};

        return true;
    }}

    // Start listening function
    function startListening() {{
        if (!recognition && !initSpeechRecognition()) {{
            return;
        }}
        
        if (isListening) {{
            return; // Already listening
        }}
        
        try {{
            continuousMode = true;
            recognition.start();
        }} catch (e) {{
            console.error('Failed to start recognition:', e);
            status.innerHTML = '❌ Failed to start listening. Try again.';
            setTimeout(() => {{
                if (continuousMode) startListening();
            }}, 2000);
        }}
    }}

    // Stop listening
    function stopListening() {{
        continuousMode = false;
        isListening = false;
        clearTimeout(restartTimeout);
        
        if (recognition) {{
            recognition.stop();
        }}
        
        mainBtn.style.background = 'rgba(255,255,255,0.2)';
        mainBtn.style.transform = 'scale(1)';
        mainBtn.style.boxShadow = 'none';
        assistantStatus.innerHTML = '🎤 Assistant Ready';
        status.innerHTML = 'Click to start listening for "Hey Bob"';
        stopBtn.style.display = 'none';
        transcript.style.display = 'none';
    }}

    // Event listeners
    mainBtn.addEventListener('click', function() {{
        if (!isListening && !continuousMode) {{
            startListening();
        }}
    }});

    stopBtn.addEventListener('click', stopListening);

    // Initialize recognition on load
    initSpeechRecognition();

    // Listen for Streamlit communication
    window.addEventListener('message', function(event) {{
        if (event.data && event.data.type === 'streamlit_response') {{
            assistantStatus.innerHTML = '✅ Response received!';
            status.innerHTML = 'Click to ask another question';
        }}
    }});

    // Check for stored queries
    try {{
        const storedQuery = sessionStorage.getItem('hey_bob_query');
        if (storedQuery) {{
            const data = JSON.parse(storedQuery);
            sessionStorage.removeItem('hey_bob_query');
            // This would be processed by Streamlit
        }}
    }} catch (e) {{
        console.log('No stored query found');
    }}
    </script>
    """

    components.html(voice_assistant_html, height=450)

    # Enhanced URL parameter processing
    voice_query = st.query_params.get("voice_query")
    
    # Also check session state for voice queries
    if not voice_query and hasattr(st.session_state, 'voice_query') and st.session_state.voice_query:
        voice_query = st.session_state.voice_query
        st.session_state.voice_query = None

    # Process voice command
    if voice_query and not st.session_state.processing_voice:
        st.session_state.processing_voice = True
        
        # Display the command
        st.markdown(f'<div class="conversation-bubble">🎙️ <strong>You said:</strong> "Hey Bob, {voice_query}"</div>', unsafe_allow_html=True)
        
        # Get Bob's response
        with st.spinner("🤖 Bob is analyzing and preparing response..."):
            try:
                ai_response = get_ai_response(voice_query)
                
                # Display Bob's response
                st.markdown(f'<div class="bob-response">🤖 <strong>Bob responds:</strong><br><br>{ai_response}</div>', unsafe_allow_html=True)
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "user": f"Hey Bob, {voice_query}",
                    "bob": ai_response,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "type": "voice"
                })
                
                # Clean response for speech
                clean_response = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '').replace('#', '').replace('\\', '')
                
                # Voice response component
                voice_response_html = f"""
                <div style="text-align: center; margin: 20px 0; padding: 20px; background: #e8f5e8; border-radius: 15px;">
                    <h3 style="color: #28a745; margin-bottom: 15px;">🔊 Bob's Voice Response</h3>
                    
                    <div style="margin: 20px 0;">
                        <button onclick="speakBobResponse()" style="
                            padding: 15px 30px; 
                            background: #28a745; 
                            color: white; 
                            border: none; 
                            border-radius: 10px; 
                            cursor: pointer; 
                            font-size: 18px;
                            margin: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        ">🎙️ Play Response</button>
                        
                        <button onclick="restartListening()" style="
                            padding: 15px 30px; 
                            background: #007bff; 
                            color: white; 
                            border: none; 
                            border-radius: 10px; 
                            cursor: pointer; 
                            font-size: 18px;
                            margin: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        ">🎤 Ask Another Question</button>
                    </div>
                    
                    <div id="voiceStatus" style="margin-top: 15px; font-size: 16px; color: #666;"></div>
                </div>

                <script>
                const bobResponse = `{clean_response}`;
                
                function speakBobResponse() {{
                    if ('speechSynthesis' in window) {{
                        // Cancel any ongoing speech
                        speechSynthesis.cancel();
                        
                        const utterance = new SpeechSynthesisUtterance(bobResponse);
                        utterance.rate = 0.9;
                        utterance.pitch = 1.0;
                        utterance.volume = 1.0;
                        
                        // Wait for voices to load
                        function setVoice() {{
                            const voices = speechSynthesis.getVoices();
                            const preferredVoice = voices.find(voice => 
                                voice.lang.startsWith('en') && (
                                    voice.name.includes('Google') || 
                                    voice.name.includes('Natural') ||
                                    voice.name.includes('Enhanced') ||
                                    voice.default
                                )
                            );
                            if (preferredVoice) {{
                                utterance.voice = preferredVoice;
                            }}
                        }}
                        
                        if (speechSynthesis.getVoices().length === 0) {{
                            speechSynthesis.onvoiceschanged = setVoice;
                        }} else {{
                            setVoice();
                        }}
                        
                        utterance.onstart = () => {{
                            document.getElementById('voiceStatus').innerHTML = '🔊 Bob is speaking...';
                        }};
                        
                        utterance.onend = () => {{
                            document.getElementById('voiceStatus').innerHTML = '✅ Response complete!';
                            setTimeout(() => {{
                                document.getElementById('voiceStatus').innerHTML = '';
                            }}, 3000);
                        }};
                        
                        utterance.onerror = (event) => {{
                            document.getElementById('voiceStatus').innerHTML = '❌ Voice error: ' + event.error;
                        }};
                        
                        speechSynthesis.speak(utterance);
                    }} else {{
                        document.getElementById('voiceStatus').innerHTML = '❌ Text-to-speech not available';
                    }}
                }}
                
                function restartListening() {{
                    // Clear parameters and reload
                    const url = new URL(window.location);
                    url.search = '';
                    url.hash = '';
                    window.location.href = url.toString();
                }}
                
                // Auto-play Bob's response after a short delay
                setTimeout(() => {{
                    speakBobResponse();
                }}, 1500);
                </script>
                """
                
                components.html(voice_response_html, height=250)
                
                # Clear URL parameters to prevent reprocessing
                st.query_params.clear()
                st.session_state.processing_voice = False
                
            except Exception as e:
                st.error(f"❌ Error getting Bob's response: {e}")
                st.session_state.processing_voice = False

    # Reset processing flag if no voice query
    elif not voice_query:
        st.session_state.processing_voice = False

    # Manual text input for testing
    st.markdown("---")
    st.markdown("### 💬 Text Mode (For Testing)")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        manual_input = st.text_input(
            "Type to test Bob's responses:", 
            placeholder="What's the weather like today?",
            key="manual_test"
        )
    with col2:
        if st.button("Test", type="primary"):
            if manual_input:
                with st.spinner("Testing Bob..."):
                    response = get_ai_response(manual_input)
                    st.success(f"**Bob:** {response}")

    # Quick test buttons
    st.markdown("**Quick Tests:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Math Test"):
            response = get_ai_response("What is 15 times 7?")
            st.write(f"Bob: {response}")
    
    with col2:
        if st.button("🌍 Knowledge Test"):
            response = get_ai_response("What is the capital of Japan?")
            st.write(f"Bob: {response}")
    
    with col3:
        if st.button("📰 News Test"):
            response = get_ai_response("What's in the news today?")
            st.write(f"Bob: {response}")
    
    with col4:
        if st.button("🌤️ Weather Test"):
            response = get_ai_response("What's the weather like in New York?")
            st.write(f"Bob: {response}")

    # Instructions
    st.markdown("---")
    st.markdown("### 📋 How to Use Hey Bob")
    
    st.markdown("""
    **🎯 Step-by-Step:**
    1. **Click the microphone** to start listening
    2. **Say "Hey Bob"** followed by your question (e.g., "Hey Bob, what's 2+2?")
    3. **Wait for processing** - Bob will show your command
    4. **Listen to Bob's response** - it will auto-play
    5. **Click "Ask Another Question"** to continue

    **🎙️ Example Commands:**
    - *"Hey Bob, what's the weather today?"*
    - *"Hey Bob, what is 25 times 4?"*
    - *"Hey Bob, tell me about artificial intelligence"*
    - *"Hey Bob, what's happening in the news?"*
    
    **⚠️ Important Notes:**
    - Use **Chrome or Edge** browser for best speech recognition
    - Allow **microphone permissions** when prompted
    - Speak **clearly** and **wait** for the wake word detection
    - Make sure your connection is stable
    
    **🔧 Troubleshooting:**
    - If stuck, click "Ask Another Question" to reset
    - Check browser console (F12) for detailed error messages
    - Try the text mode below if voice isn't working
    """)

    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.subheader("💬 Recent Conversations with Bob")
        
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:])):
            icon = "🎙️" if conv.get('type') == 'voice' else "⌨️"
            with st.expander(f"{icon} [{conv['timestamp']}] {conv['user'][:50]}..."):
                st.markdown(f"**You:** {conv['user']}")
                st.markdown(f"**Bob:** {conv['bob']}")
        
        # Clear history
        if st.button("🗑️ Clear Conversation History"):
            st.session_state.conversation_history = []
            st.rerun()

    # System status
    st.markdown("---")
    st.markdown("### ⚙️ System Status")
    
    with st.expander("Show System Information"):
        # API Status
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Keys:**")
            st.write(f"- Tavily: {'✅ Configured' if TAVILY_API_KEY else '❌ Missing'}")
            st.write(f"- Google: {'✅ Configured' if GOOGLE_API_KEY else '❌ Missing'}")
        
        with col2:
            st.write("**Session State:**")
            st.write(f"- Processing: {st.session_state.processing_voice}")
            st.write(f"- Conversations: {len(st.session_state.conversation_history)}")
        
        # Current URL info
        st.write("**Current URL Parameters:**")
        if st.query_params:
            for key, value in st.query_params.items():
                st.write(f"- {key}: {value[:50]}...")
        else:
            st.write("- None")
        
        # Agent test
        if st.button("🧪 Test AI Agent Connection"):
            try:
                agent = get_agent()
                if agent:
                    test_response = get_ai_response("Say exactly: 'Agent working perfectly'")
                    st.success(f"✅ Agent Response: {test_response}")
                else:
                    st.error("❌ Agent initialization failed")
            except Exception as e:
                st.error(f"❌ Agent test failed: {e}")

    # Debug section for development
    if st.checkbox("🔍 Show Debug Info"):
        st.write("**Debug Information:**")
        st.write(f"- Current URL: {st.experimental_get_query_params()}")
        st.write(f"- Session State Keys: {list(st.session_state.keys())}")
        st.write(f"- Processing Voice: {st.session_state.processing_voice}")

if __name__ == "__main__":
    main()
