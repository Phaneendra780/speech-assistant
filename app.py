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

    // Send command to Streamlit - Fixed version
    function sendToStreamlit(command) {{
        console.log('Sending command to Streamlit:', command);
        
        // Method 1: URL parameters (most reliable for Streamlit Cloud)
        const url = new URL(window.location);
        url.searchParams.set('voice_query', encodeURIComponent(command));
        url.searchParams.set('timestamp', Date.now());
        
        // Navigate to trigger Streamlit rerun
        window.location.href = url.toString();
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

    # Voice Response Output Section - This is where Bob's response will appear
    if not st.query_params.get("voice_query"):
        st.markdown("---")
        st.markdown("### 🎙️ Voice Command Output")
        st.info("👆 Use the voice interface above, then Bob's response will appear here!")

    voice_query = st.query_params.get("voice_query")
    
    # Process voice command immediately and display output below voice input
    if voice_query and not st.session_state.get('last_processed_query') == voice_query:
        st.session_state.last_processed_query = voice_query
        
        # Display the voice command result section
        st.markdown("---")
        st.markdown("### 🎙️ Voice Command Results")
        
        # Display what user said
        st.markdown(f'<div class="conversation-bubble">🎙️ <strong>You said:</strong> "Hey Bob, {voice_query}"</div>', unsafe_allow_html=True)
        
        # Get and display Bob's response
        with st.spinner("🤖 Bob is thinking..."):
            try:
                ai_response = get_ai_response(voice_query)
                
                # Display Bob's text response
                st.markdown(f'<div class="bob-response">🤖 <strong>Bob responds:</strong><br><br>{ai_response}</div>', unsafe_allow_html=True)
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "user": f"Hey Bob, {voice_query}",
                    "bob": ai_response,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "type": "voice"
                })
                
                # Clean response for speech synthesis
                clean_response = ai_response.replace('"', '\\"').replace('\n', ' ').replace('`', '').replace('*', '').replace('#', '').replace('\\', '\\\\')
                
                # Voice response controls
                voice_controls_html = f"""
                <div style="text-align: center; margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #e8f5e8, #d4edda); border-radius: 15px; border: 2px solid #28a745;">
                    <h3 style="color: #28a745; margin-bottom: 20px;">🔊 Bob's Voice Response</h3>
                    
                    <div style="margin: 20px 0;">
                        <button onclick="playBobResponse()" id="playBtn" style="
                            padding: 15px 30px; 
                            background: #28a745; 
                            color: white; 
                            border: none; 
                            border-radius: 10px; 
                            cursor: pointer; 
                            font-size: 18px;
                            margin: 10px;
                            box-shadow: 0 3px 6px rgba(0,0,0,0.2);
                            transition: all 0.3s;
                        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                            🎙️ Play Bob's Response
                        </button>
                        
                        <button onclick="askAnother()" style="
                            padding: 15px 30px; 
                            background: #007bff; 
                            color: white; 
                            border: none; 
                            border-radius: 10px; 
                            cursor: pointer; 
                            font-size: 18px;
                            margin: 10px;
                            box-shadow: 0 3px 6px rgba(0,0,0,0.2);
                            transition: all 0.3s;
                        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                            🎤 Ask Another Question
                        </button>
                    </div>
                    
                    <div id="voicePlayStatus" style="margin-top: 15px; font-size: 16px; color: #666; min-height: 25px;"></div>
                </div>

                <script>
                const bobResponseText = "{clean_response}";
                let currentUtterance = null;
                
                function playBobResponse() {{
                    const statusDiv = document.getElementById('voicePlayStatus');
                    const playBtn = document.getElementById('playBtn');
                    
                    if ('speechSynthesis' in window) {{
                        // Stop any ongoing speech
                        speechSynthesis.cancel();
                        
                        statusDiv.innerHTML = '🔄 Preparing voice...';
                        playBtn.disabled = true;
                        playBtn.innerHTML = '⏳ Loading...';
                        
                        currentUtterance = new SpeechSynthesisUtterance(bobResponseText);
                        currentUtterance.rate = 0.85;
                        currentUtterance.pitch = 1.0;
                        currentUtterance.volume = 1.0;
                        
                        // Set voice when available
                        function setupVoice() {{
                            const voices = speechSynthesis.getVoices();
                            console.log('Available voices:', voices.length);
                            
                            const preferredVoice = voices.find(voice => 
                                voice.lang.startsWith('en') && (
                                    voice.name.includes('Google') || 
                                    voice.name.includes('Natural') ||
                                    voice.name.includes('Enhanced') ||
                                    voice.localService === false
                                )
                            ) || voices.find(voice => voice.lang.startsWith('en'));
                            
                            if (preferredVoice) {{
                                currentUtterance.voice = preferredVoice;
                                console.log('Using voice:', preferredVoice.name);
                            }}
                        }}
                        
                        if (speechSynthesis.getVoices().length === 0) {{
                            speechSynthesis.onvoiceschanged = setupVoice;
                        }} else {{
                            setupVoice();
                        }}
                        
                        currentUtterance.onstart = () => {{
                            statusDiv.innerHTML = '🔊 Bob is speaking...';
                            playBtn.innerHTML = '⏸️ Speaking...';
                        }};
                        
                        currentUtterance.onend = () => {{
                            statusDiv.innerHTML = '✅ Response complete! Ready for next question.';
                            playBtn.disabled = false;
                            playBtn.innerHTML = '🎙️ Play Again';
                            setTimeout(() => {{
                                statusDiv.innerHTML = '';
                            }}, 4000);
                        }};
                        
                        currentUtterance.onerror = (event) => {{
                            statusDiv.innerHTML = '❌ Voice error: ' + event.error;
                            playBtn.disabled = false;
                            playBtn.innerHTML = '🎙️ Try Again';
                            console.error('Speech error:', event.error);
                        }};
                        
                        // Start speaking
                        setTimeout(() => {{
                            speechSynthesis.speak(currentUtterance);
                        }}, 500);
                        
                    }} else {{
                        statusDiv.innerHTML = '❌ Text-to-speech not supported in this browser';
                        playBtn.disabled = false;
                    }}
                }}
                
                function askAnother() {{
                    // Clear the current query and reload page for new voice input
                    const url = new URL(window.location);
                    url.search = '';
                    url.hash = '';
                    window.location.href = url.toString();
                }}
                
                // Auto-play Bob's response
                setTimeout(() => {{
                    playBobResponse();
                }}, 1000);
                </script>
                """
                
                components.html(voice_controls_html, height=300)
                
            except Exception as e:
                st.error(f"❌ Error getting Bob's response: {e}")
                
        # Clear URL parameters after processing to prevent reprocessing
        if st.button("🔄 Clear and Start Fresh"):
            st.query_params.clear()
            st.session_state.last_processed_query = None
            st.rerun()

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
