import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import time
import streamlit.components.v1 as components
import json

# Set page configuration
st.set_page_config(
    page_title="Bob - Voice Assistant",
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
You are Bob, a helpful voice assistant. You can answer questions about any topic including:
- General knowledge questions
- Current events and news
- Weather information
- Drug and medical information
- Technology questions
- Calculations and conversions
- And much more

Provide clear, concise, and helpful responses that are suitable for voice output.
Keep your responses conversational and easy to understand when spoken aloud.
Limit responses to 2-3 sentences for better voice experience.
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
        with st.spinner("🤖 Bob is thinking..."):
            response = agent.run(query)
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error getting AI response: {e}")
        return "Sorry, I encountered an error while processing your question."

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'response_ready' not in st.session_state:
        st.session_state.response_ready = False

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-container {
        text-align: center;
        padding: 2rem 0;
    }
    .title {
        font-size: 3rem;
        margin-bottom: 1rem;
        background: linear-gradient(45deg, #4A90E2, #357ABD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="title">🤖 Bob - Voice Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Say "Hey Bob" then ask your question</p>', unsafe_allow_html=True)
    
    # Voice interface with session state communication
    voice_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .voice-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
                font-family: Arial, sans-serif;
            }}
            .microphone {{
                font-size: 120px;
                cursor: pointer;
                transition: all 0.3s ease;
                border: none;
                background: none;
                color: #4A90E2;
                padding: 20px;
                border-radius: 50%;
                box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
            }}
            .microphone:hover {{
                transform: scale(1.1);
                color: #357ABD;
                box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
            }}
            .microphone:disabled {{
                color: #ccc;
                cursor: not-allowed;
                transform: none;
            }}
            .microphone.listening {{
                color: #E74C3C;
                animation: pulse 1.5s infinite;
                box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
            }}
            .microphone.processing {{
                color: #F39C12;
                box-shadow: 0 6px 20px rgba(243, 156, 18, 0.4);
            }}
            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.2); }}
                100% {{ transform: scale(1); }}
            }}
            .status {{
                margin-top: 20px;
                font-size: 18px;
                text-align: center;
                min-height: 25px;
                color: #333;
            }}
            .transcript {{
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
                max-width: 500px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .wake-word-status {{
                margin-top: 10px;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }}
            .wake-detected {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .wake-waiting {{
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }}
            .debug-info {{
                margin-top: 15px;
                padding: 10px;
                background: #f1f1f1;
                border-radius: 5px;
                font-size: 12px;
                color: #666;
                max-width: 500px;
            }}
            .error-info {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .success-info {{
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }}
        </style>
    </head>
    <body>
        <div class="voice-container">
            <button class="microphone" id="micButton">🎤</button>
            <div class="status" id="status">Checking browser compatibility...</div>
            <div class="wake-word-status wake-waiting" id="wakeStatus">Initializing...</div>
            <div class="debug-info" id="debugInfo">Loading...</div>
            <div class="transcript" id="transcript" style="display: none;"></div>
        </div>

        <script>
            let recognition;
            let isListening = false;
            let wakeWordDetected = false;
            let permissionGranted = false;
            
            const micButton = document.getElementById('micButton');
            const status = document.getElementById('status');
            const transcript = document.getElementById('transcript');
            const wakeStatus = document.getElementById('wakeStatus');
            const debugInfo = document.getElementById('debugInfo');

            function updateDebugInfo(message, isError = false) {{
                console.log('Debug:', message);
                debugInfo.textContent = new Date().toLocaleTimeString() + ': ' + message;
                debugInfo.className = isError ? 'debug-info error-info' : 'debug-info success-info';
            }}

            // Check browser compatibility
            function checkBrowserSupport() {{
                const userAgent = navigator.userAgent;
                let browserInfo = '';
                
                if (userAgent.includes('Chrome')) {{
                    browserInfo = 'Chrome detected ✅';
                }} else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {{
                    browserInfo = 'Safari detected ✅';
                }} else if (userAgent.includes('Edge')) {{
                    browserInfo = 'Edge detected ✅';
                }} else {{
                    browserInfo = 'Unsupported browser ❌';
                }}
                
                const isHttps = window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
                const protocolInfo = isHttps ? 'Secure connection ✅' : 'HTTPS required ❌';
                
                updateDebugInfo(`${{browserInfo}}, ${{protocolInfo}}`);
                
                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
                    return true;
                }} else {{
                    updateDebugInfo('Speech Recognition API not available ❌', true);
                    status.textContent = 'Speech recognition not supported. Use Chrome, Edge, or Safari with HTTPS.';
                    micButton.disabled = true;
                    return false;
                }}
            }}

            // Function to check and request microphone permission
            async function requestMicrophonePermission() {{
                updateDebugInfo('Requesting microphone permission...');
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    stream.getTracks().forEach(track => track.stop());
                    permissionGranted = true;
                    updateDebugInfo('Microphone permission granted ✅');
                    return true;
                }} catch (error) {{
                    updateDebugInfo(`Microphone permission denied: ${{error.message}} ❌`, true);
                    status.textContent = 'Microphone access denied. Please allow access and refresh.';
                    return false;
                }}
            }}

            // Initialize speech recognition
            function initializeSpeechRecognition() {{
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                recognition.onstart = function() {{
                    isListening = true;
                    micButton.classList.add('listening');
                    updateDebugInfo('Speech recognition started');
                    
                    if (!wakeWordDetected) {{
                        status.textContent = 'Listening for "Hey Bob"...';
                        wakeStatus.textContent = 'Say "Hey Bob" now...';
                    }} else {{
                        status.textContent = 'I\'m listening... What can I help you with?';
                    }}
                }};

                recognition.onresult = function(event) {{
                    const result = event.results[0];
                    const text = result[0].transcript.toLowerCase().trim();
                    const confidence = result[0].confidence;
                    
                    updateDebugInfo(`Heard: "${{text}}" (confidence: ${{confidence?.toFixed(2) || 'unknown'}})`);
                    
                    if (!wakeWordDetected) {{
                        // Check for wake word
                        if (text.includes('hey bob') || text.includes('hi bob') || text.includes('hello bob')) {{
                            wakeWordDetected = true;
                            wakeStatus.textContent = '✅ Wake word detected! Ask your question...';
                            wakeStatus.className = 'wake-word-status wake-detected';
                            status.textContent = 'Great! Now ask me anything...';
                            
                            updateDebugInfo('Wake word detected, preparing for query...');
                            
                            // Speak confirmation
                            const utterance = new SpeechSynthesisUtterance('Hello! What can I help you with?');
                            utterance.rate = 0.8;
                            speechSynthesis.speak(utterance);
                            
                            // Start listening for the actual query after confirmation
                            setTimeout(() => {{
                                if (recognition && !isListening) {{
                                    try {{
                                        recognition.start();
                                    }} catch (error) {{
                                        updateDebugInfo(`Error restarting recognition: ${{error.message}}`, true);
                                    }}
                                }}
                            }}, 2500);
                        }} else {{
                            status.textContent = `I heard: "${{result[0].transcript}}" - Please say "Hey Bob"`;
                            setTimeout(() => {{
                                status.textContent = 'Click the microphone and say "Hey Bob"';
                            }}, 3000);
                        }}
                    }} else {{
                        // Process the actual query
                        const query = result[0].transcript;
                        transcript.style.display = 'block';
                        transcript.innerHTML = '<strong>You said:</strong> ' + query;
                        
                        updateDebugInfo(`Processing query: "${{query}}"`);
                        
                        // Store query in sessionStorage and trigger Streamlit rerun
                        sessionStorage.setItem('voice_query', query);
                        sessionStorage.setItem('voice_timestamp', Date.now().toString());
                        
                        // Trigger a custom event that Streamlit can detect
                        window.dispatchEvent(new CustomEvent('voiceQuery', {{ detail: query }}));
                        
                        status.textContent = 'Processing your question...';
                        micButton.classList.remove('listening');
                        micButton.classList.add('processing');
                    }}
                }};

                recognition.onerror = function(event) {{
                    console.error('Speech recognition error:', event.error);
                    updateDebugInfo(`Speech error: ${{event.error}}`, true);
                    
                    let errorMessage = 'Please try again.';
                    
                    switch(event.error) {{
                        case 'not-allowed':
                        case 'permission-denied':
                            errorMessage = 'Microphone permission denied. Please allow access and refresh.';
                            permissionGranted = false;
                            break;
                        case 'no-speech':
                            errorMessage = 'No speech detected. Try speaking louder.';
                            break;
                        case 'audio-capture':
                            errorMessage = 'No microphone found. Please check your microphone.';
                            break;
                        case 'network':
                            errorMessage = 'Network error. Check your internet connection.';
                            break;
                    }}
                    
                    status.textContent = `Error: ${{event.error}}. ${{errorMessage}}`;
                    micButton.classList.remove('listening', 'processing');
                    isListening = false;
                }};

                recognition.onend = function() {{
                    micButton.classList.remove('listening');
                    isListening = false;
                    updateDebugInfo('Speech recognition ended');
                    
                    if (!wakeWordDetected) {{
                        status.textContent = 'Click the microphone and say "Hey Bob"';
                    }}
                }};

                updateDebugInfo('Speech recognition initialized ✅');
            }}

            // Microphone button click handler
            micButton.addEventListener('click', async function() {{
                updateDebugInfo('Microphone button clicked');
                
                if (!permissionGranted) {{
                    status.textContent = 'Requesting microphone permission...';
                    const granted = await requestMicrophonePermission();
                    if (!granted) {{
                        return;
                    }}
                    initializeSpeechRecognition();
                    setTimeout(() => {{
                        status.textContent = 'Click the microphone and say "Hey Bob"';
                        wakeStatus.textContent = 'Waiting for "Hey Bob"...';
                    }}, 1000);
                }} else if (!isListening && recognition) {{
                    try {{
                        recognition.start();
                    }} catch (error) {{
                        updateDebugInfo(`Error starting recognition: ${{error.message}}`, true);
                        status.textContent = 'Error starting microphone. Please refresh and try again.';
                    }}
                }}
            }});

            // Listen for responses from Streamlit
            window.addEventListener('message', function(event) {{
                if (event.data && event.data.type === 'bot_response') {{
                    status.textContent = 'Bob is speaking...';
                    updateDebugInfo('Received response from Streamlit');
                    
                    // Clean the response for speech
                    let responseText = event.data.response;
                    responseText = responseText.replace(/[*#`]/g, ''); // Remove markdown
                    responseText = responseText.replace(/\n/g, ' '); // Replace newlines with spaces
                    responseText = responseText.replace(/\s+/g, ' ').trim(); // Clean whitespace
                    
                    // Speak the response
                    const utterance = new SpeechSynthesisUtterance(responseText);
                    utterance.rate = 0.8;
                    utterance.pitch = 1;
                    utterance.volume = 0.8;
                    
                    utterance.onend = function() {{
                        // Reset for next interaction
                        wakeWordDetected = false;
                        wakeStatus.textContent = 'Waiting for "Hey Bob"...';
                        wakeStatus.className = 'wake-word-status wake-waiting';
                        status.textContent = 'Click the microphone and say "Hey Bob"';
                        micButton.classList.remove('processing');
                        transcript.style.display = 'none';
                        updateDebugInfo('Ready for next interaction');
                    }};
                    
                    speechSynthesis.speak(utterance);
                }}
            }});

            // Initialize on page load
            document.addEventListener('DOMContentLoaded', function() {{
                updateDebugInfo('Page loaded, checking browser support...');
                
                if (checkBrowserSupport()) {{
                    status.textContent = 'Click the microphone to start';
                    wakeStatus.textContent = 'Ready - Click microphone first';
                    wakeStatus.className = 'wake-word-status wake-waiting';
                }} else {{
                    wakeStatus.textContent = 'Browser not supported';
                    wakeStatus.className = 'wake-word-status error-info';
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Render the voice interface
    components.html(voice_html, height=450, key="voice_interface")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Check for new voice queries using JavaScript session storage
    check_query_js = """
    <script>
    const query = sessionStorage.getItem('voice_query');
    const timestamp = sessionStorage.getItem('voice_timestamp');
    
    if (query && timestamp) {
        // Clear the stored query to prevent reprocessing
        sessionStorage.removeItem('voice_query');
        sessionStorage.removeItem('voice_timestamp');
        
        // Send to Streamlit using query params
        const currentUrl = new URL(window.location);
        currentUrl.searchParams.set('voice_query', query);
        currentUrl.searchParams.set('voice_timestamp', timestamp);
        window.location.href = currentUrl.toString();
    }
    </script>
    """
    components.html(check_query_js, height=0)
    
    # Handle voice queries from URL parameters
    voice_query = st.query_params.get("voice_query")
    voice_timestamp = st.query_params.get("voice_timestamp")
    
    if voice_query and voice_timestamp:
        # Check if this is a new query
        if f"{voice_query}_{voice_timestamp}" not in st.session_state.get('processed_queries', set()):
            # Mark as processed
            if 'processed_queries' not in st.session_state:
                st.session_state.processed_queries = set()
            st.session_state.processed_queries.add(f"{voice_query}_{voice_timestamp}")
            
            # Get AI response
            ai_response = get_ai_response(voice_query)
            
            # Add to conversation history
            st.session_state.conversation_history.append({
                "user": voice_query,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            # Send response back to JavaScript for speech synthesis
            response_js = f"""
            <script>
            const iframe = document.querySelector('iframe[title="voice_interface"]');
            if (iframe && iframe.contentWindow) {{
                iframe.contentWindow.postMessage({{
                    type: 'bot_response',
                    response: `{ai_response.replace('`', '\\`').replace('$', '\\$').replace('"', '\\"').replace(chr(10), ' ')}`
                }}, '*');
            }}
            
            // Clear URL parameters
            const url = new URL(window.location);
            url.searchParams.delete('voice_query');
            url.searchParams.delete('voice_timestamp');
            history.replaceState(null, '', url.toString());
            </script>
            """
            components.html(response_js, height=0)
    
    # Simple text input as backup
    st.markdown("---")
    st.markdown("### 💬 Alternative: Text Input")
    text_query = st.text_input("Or type your question here:", placeholder="What can Bob help you with?")
    
    if text_query:
        if st.button("Ask Bob"):
            ai_response = get_ai_response(text_query)
            st.session_state.conversation_history.append({
                "user": text_query,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S")
            })
            st.write(f"**Bob:** {ai_response}")
    
    # Troubleshooting section
    st.markdown("---")
    st.markdown("### 🔧 Troubleshooting")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **If microphone isn't working:**
        1. Use Chrome, Edge, or Safari
        2. Allow microphone permission when prompted
        3. Check your microphone is working
        4. Try refreshing the page
        5. Check the debug info above
        """)
    
    with col2:
        st.markdown("""
        **Browser requirements:**
        - ✅ Chrome (recommended)
        - ✅ Edge
        - ✅ Safari
        - ❌ Firefox (not supported)
        - ✅ HTTPS or localhost required
        """)
    
    # Test microphone button
    if st.button("🎙️ Test Microphone Access"):
        test_js = """
        <script>
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                stream.getTracks().forEach(track => track.stop());
                alert('✅ Microphone access successful!');
            })
            .catch(function(error) {
                alert('❌ Microphone access failed: ' + error.message);
            });
        </script>
        """
        components.html(test_js, height=0)
    
    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.subheader("💬 Recent Conversations")
        
        # Show last 5 conversations
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:])):
            with st.expander(f"Conversation {len(st.session_state.conversation_history) - i} - {conv['timestamp']}"):
                st.write(f"**You:** {conv['user']}")
                st.write(f"**Bob:** {conv['bob']}")
    
    # Clear history button
    if st.session_state.conversation_history:
        if st.button("🗑️ Clear Conversation History"):
            st.session_state.conversation_history = []
            st.session_state.processed_queries = set()
            st.rerun()

if __name__ == "__main__":
    main()
