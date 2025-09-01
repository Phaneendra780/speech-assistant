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

def process_query(query, input_type="manual"):
    """Unified function to process both voice and manual queries."""
    # Display the query
    icon = "🎙️" if input_type == "voice" else "⌨️"
    prefix = "You said:" if input_type == "voice" else "You asked:"
    
    st.markdown(f'<div class="conversation-bubble">{icon} <strong>{prefix}</strong> "{query}"</div>', unsafe_allow_html=True)
    
    # Get Bob's response
    with st.spinner("🤖 Bob is thinking..."):
        try:
            ai_response = get_ai_response(query)
            
            # Display Bob's response
            st.markdown(f'<div class="bob-response">🤖 <strong>Bob responds:</strong><br><br>{ai_response}</div>', unsafe_allow_html=True)
            
            # Add to conversation history
            st.session_state.conversation_history.append({
                "user": query,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S"),
                "type": input_type
            })
            
            # For voice input, add text-to-speech
            if input_type == "voice":
                add_voice_response(ai_response)
                
            return ai_response
            
        except Exception as e:
            error_msg = f"❌ Error getting Bob's response: {e}"
            st.error(error_msg)
            return error_msg

def add_voice_response(response_text):
    """Add text-to-speech functionality for voice responses."""
    import streamlit.components.v1 as components
    
    # Clean response for speech synthesis
    clean_response = response_text.replace('"', '\\"').replace('\n', ' ').replace('`', '').replace('*', '').replace('#', '').replace('\\', '\\\\')
    
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
    
    function playBobResponse() {{
        const statusDiv = document.getElementById('voicePlayStatus');
        const playBtn = document.getElementById('playBtn');
        
        if ('speechSynthesis' in window) {{
            speechSynthesis.cancel();
            
            statusDiv.innerHTML = '🔄 Preparing voice...';
            playBtn.disabled = true;
            playBtn.innerHTML = '⏳ Loading...';
            
            const utterance = new SpeechSynthesisUtterance(bobResponseText);
            utterance.rate = 0.85;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            function setupVoice() {{
                const voices = speechSynthesis.getVoices();
                const preferredVoice = voices.find(voice => 
                    voice.lang.startsWith('en') && !voice.localService
                ) || voices.find(voice => voice.lang.startsWith('en'));
                
                if (preferredVoice) {{
                    utterance.voice = preferredVoice;
                }}
            }}
            
            if (speechSynthesis.getVoices().length === 0) {{
                speechSynthesis.onvoiceschanged = setupVoice;
            }} else {{
                setupVoice();
            }}
            
            utterance.onstart = () => {{
                statusDiv.innerHTML = '🔊 Bob is speaking...';
                playBtn.innerHTML = '⏸️ Speaking...';
            }};
            
            utterance.onend = () => {{
                statusDiv.innerHTML = '✅ Response complete!';
                playBtn.disabled = false;
                playBtn.innerHTML = '🎙️ Play Again';
                setTimeout(() => {{
                    statusDiv.innerHTML = '';
                }}, 4000);
            }};
            
            utterance.onerror = (event) => {{
                statusDiv.innerHTML = '❌ Voice error: ' + event.error;
                playBtn.disabled = false;
                playBtn.innerHTML = '🎙️ Try Again';
            }};
            
            setTimeout(() => {{
                speechSynthesis.speak(utterance);
            }}, 500);
            
        }} else {{
            statusDiv.innerHTML = '❌ Text-to-speech not supported';
        }}
    }}
    
    function askAnother() {{
        const url = new URL(window.location);
        url.search = '';
        url.hash = '';
        window.location.href = url.toString();
    }}
    
    // Auto-play response
    setTimeout(() => {{
        playBobResponse();
    }}, 1000);
    </script>
    """
    
    components.html(voice_controls_html, height=300)

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

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
    
    # Voice interface with simplified communication
    voice_assistant_html = """
    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #74b9ff, #0984e3); border-radius: 20px; margin: 20px 0; color: white;">
        
        <!-- Assistant Status -->
        <div id="assistantStatus" style="font-size: 24px; margin-bottom: 20px; font-weight: bold;">
            🎤 Click to Start Listening
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
            Say "Hey Bob" followed by your question
        </div>
        
        <!-- Live Transcript Display -->
        <div id="transcriptDisplay" style="
            background: rgba(255,255,255,0.9); 
            color: #333; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 15px 0; 
            min-height: 50px;
            display: none;
            font-family: monospace;
            font-size: 14px;
        ">
            Listening...
        </div>
        
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

    const mainBtn = document.getElementById('mainBtn');
    const status = document.getElementById('listeningStatus');
    const assistantStatus = document.getElementById('assistantStatus');
    const transcript = document.getElementById('transcriptDisplay');
    const stopBtn = document.getElementById('stopBtn');

    // Check for wake word and extract command
    function checkWakeWord(text) {
        const lowerText = text.toLowerCase().trim();
        const wakePatterns = [
            /hey\\s+bob/i,
            /hi\\s+bob/i,
            /hello\\s+bob/i
        ];
        
        for (let pattern of wakePatterns) {
            const match = lowerText.match(pattern);
            if (match) {
                const command = text.substring(match.index + match[0].length).trim();
                return command || "Hello";
            }
        }
        return null;
    }

    // Send voice command to Streamlit
    function sendVoiceCommand(command) {
        console.log('Detected command:', command);
        
        // Send to Streamlit via URL parameter
        const url = new URL(window.location);
        url.searchParams.set('voice_query', encodeURIComponent(command));
        url.searchParams.set('t', Date.now());
        window.location.href = url.toString();
    }

    // Initialize speech recognition
    function startListening() {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            status.innerHTML = '❌ Speech recognition not supported. Use Chrome/Edge!';
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = function() {
            isListening = true;
            mainBtn.style.background = 'rgba(255,0,0,0.4)';
            mainBtn.style.transform = 'scale(1.1)';
            assistantStatus.innerHTML = '👂 Listening for "Hey Bob"...';
            status.innerHTML = 'Speak now: "Hey Bob, [your question]"';
            stopBtn.style.display = 'inline-block';
            transcript.style.display = 'block';
            transcript.innerHTML = '🎧 Listening...';
        };

        recognition.onresult = function(event) {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcriptPart = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcriptPart;
                } else {
                    interimTranscript += transcriptPart;
                }
            }
            
            // Show live transcript
            const currentText = finalTranscript + interimTranscript;
            if (currentText.trim()) {
                transcript.innerHTML = `🎧 Hearing: "${currentText}"`;
                
                // Check for wake word in final transcript
                if (finalTranscript) {
                    const command = checkWakeWord(finalTranscript);
                    if (command) {
                        transcript.innerHTML = `🎯 Command detected: "${command}"`;
                        assistantStatus.innerHTML = '✅ Processing command...';
                        recognition.stop();
                        setTimeout(() => {
                            sendVoiceCommand(command);
                        }, 1000);
                        return;
                    }
                }
            }
        };

        recognition.onerror = function(event) {
            console.error('Speech error:', event.error);
            if (event.error === 'not-allowed') {
                status.innerHTML = '🔒 Please allow microphone access!';
            } else if (event.error === 'no-speech') {
                status.innerHTML = '🔇 No speech detected. Try again.';
            } else {
                status.innerHTML = `❌ Error: ${event.error}`;
            }
            assistantStatus.innerHTML = '❌ Error occurred';
        };

        recognition.onend = function() {
            isListening = false;
            mainBtn.style.background = 'rgba(255,255,255,0.2)';
            mainBtn.style.transform = 'scale(1)';
            stopBtn.style.display = 'none';
            
            if (!transcript.innerHTML.includes('Command detected')) {
                assistantStatus.innerHTML = '🎤 Click to Start Listening';
                status.innerHTML = 'Say "Hey Bob" followed by your question';
                transcript.style.display = 'none';
            }
        };

        recognition.start();
    }

    // Stop listening function
    function stopListening() {
        if (recognition) {
            recognition.stop();
        }
        isListening = false;
        mainBtn.style.background = 'rgba(255,255,255,0.2)';
        mainBtn.style.transform = 'scale(1)';
        assistantStatus.innerHTML = '🎤 Click to Start Listening';
        status.innerHTML = 'Say "Hey Bob" followed by your question';
        stopBtn.style.display = 'none';
        transcript.style.display = 'none';
    }

    // Event listeners
    mainBtn.addEventListener('click', startListening);
    stopBtn.addEventListener('click', stopListening);
    </script>
    """

    components.html(voice_assistant_html, height=450)

    # UNIFIED PROCESSING - Both voice and manual input use the same path
    # Check for voice input from URL parameters
    voice_query = st.query_params.get("voice_query")
    if voice_query:
        # Clear URL parameters immediately
        st.query_params.clear()
        # Set the voice query in text input for unified processing
        st.session_state.current_query = voice_query
        st.session_state.input_type = "voice"

    # Manual text input - this becomes the unified input method
    st.markdown("---")
    st.markdown("### 💬 Query Input")
    
    # Pre-fill with voice query if it exists
    default_value = st.session_state.get('current_query', '')
    
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(
            "Ask Bob anything (or use voice above):", 
            value=default_value,
            placeholder="What's the weather like today?",
            key="unified_input"
        )
    with col2:
        process_button = st.button("Ask Bob", type="primary")

    # UNIFIED PROCESSING PATH - handles both voice and manual input
    if (process_button and user_input) or (st.session_state.get('current_query') and st.session_state.get('input_type') == "voice"):
        query_to_process = user_input or st.session_state.get('current_query', '')
        input_type = st.session_state.get('input_type', 'manual')
        
        # Clear session state
        if 'current_query' in st.session_state:
            del st.session_state.current_query
        if 'input_type' in st.session_state:
            del st.session_state.input_type
        
        # Process the query using unified function
        process_query(query_to_process, input_type)

    # Quick test buttons
    st.markdown("---")
    st.markdown("### 🧪 Quick Tests")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Math"):
            process_query("What is 15 times 7?", "manual")
    
    with col2:
        if st.button("🌍 Knowledge"):
            process_query("What is the capital of Japan?", "manual")
    
    with col3:
        if st.button("📰 News"):
            process_query("What's in the news today?", "manual")
    
    with col4:
        if st.button("🌤️ Weather"):
            process_query("What's the weather like in New York?", "manual")

    # Instructions
    st.markdown("---")
    st.markdown("### 📋 How to Use Hey Bob")
    
    st.markdown("""
    **🎯 Step-by-Step:**
    1. **Click the microphone** to start listening
    2. **Say "Hey Bob"** followed by your question (e.g., "Hey Bob, what's 2+2?")
    3. **Wait for processing** - your voice will be converted to text
    4. **See Bob's response** - appears below with optional voice playback
    5. **Ask another question** - use voice or type manually

    **🎙️ Example Commands:**
    - *"Hey Bob, what's the weather today?"*
    - *"Hey Bob, what is 25 times 4?"*
    - *"Hey Bob, tell me about artificial intelligence"*
    - *"Hey Bob, what's happening in the news?"*
    
    **⚠️ Important Notes:**
    - Use **Chrome or Edge** browser for speech recognition
    - Allow **microphone permissions** when prompted
    - Speak **clearly** after saying "Hey Bob"
    - Both voice and manual input use the same processing
    
    **🔧 Troubleshooting:**
    - Try the manual text input if voice isn't working
    - Check browser console (F12) for error details
    - Refresh page if stuck
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
            st.write(f"- Current Query: {st.session_state.get('current_query', 'None')}")
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
                response = get_ai_response("Say exactly: 'Agent working perfectly'")
                st.success(f"✅ Agent Response: {response}")
            except Exception as e:
                st.error(f"❌ Agent test failed: {e}")

if __name__ == "__main__":
    main()
