import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import time
import streamlit.components.v1 as components

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

def create_voice_interface():
    """Create the web-based voice interface using HTML5 Speech Recognition."""
    html_code = '''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .voice-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
                font-family: Arial, sans-serif;
            }
            .microphone {
                font-size: 120px;
                cursor: pointer;
                transition: all 0.3s ease;
                border: none;
                background: none;
                color: #4A90E2;
                padding: 20px;
                border-radius: 50%;
                box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
            }
            .microphone:hover {
                transform: scale(1.1);
                color: #357ABD;
                box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
            }
            .microphone:disabled {
                color: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            .microphone.listening {
                color: #E74C3C;
                animation: pulse 1.5s infinite;
                box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
            }
            .microphone.processing {
                color: #F39C12;
                box-shadow: 0 6px 20px rgba(243, 156, 18, 0.4);
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); }
            }
            .status {
                margin-top: 20px;
                font-size: 18px;
                text-align: center;
                min-height: 25px;
                color: #333;
            }
            .transcript {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
                max-width: 500px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .wake-word-status {
                margin-top: 10px;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            .wake-detected {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .wake-waiting {
                background: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
            }
            .debug-info {
                margin-top: 15px;
                padding: 10px;
                background: #f1f1f1;
                border-radius: 5px;
                font-size: 12px;
                color: #666;
                max-width: 500px;
                word-wrap: break-word;
            }
            .error-info {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .success-info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
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

            function updateDebugInfo(message, isError) {
                console.log('Debug:', message);
                const timestamp = new Date().toLocaleTimeString();
                debugInfo.textContent = timestamp + ': ' + message;
                if (isError) {
                    debugInfo.className = 'debug-info error-info';
                } else {
                    debugInfo.className = 'debug-info success-info';
                }
            }

            // Check browser compatibility
            function checkBrowserSupport() {
                const userAgent = navigator.userAgent;
                let browserInfo = '';
                
                if (userAgent.includes('Chrome')) {
                    browserInfo = 'Chrome detected - Good!';
                } else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
                    browserInfo = 'Safari detected - Should work';
                } else if (userAgent.includes('Edge')) {
                    browserInfo = 'Edge detected - Should work';
                } else if (userAgent.includes('Firefox')) {
                    browserInfo = 'Firefox detected - NOT SUPPORTED';
                } else {
                    browserInfo = 'Unknown browser - May not work';
                }
                
                const isSecure = window.location.protocol === 'https:' || 
                               window.location.hostname === 'localhost' || 
                               window.location.hostname === '127.0.0.1';
                const protocolInfo = isSecure ? 'Secure connection - Good!' : 'HTTPS required for microphone';
                
                updateDebugInfo(browserInfo + ', ' + protocolInfo, !isSecure);
                
                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                    updateDebugInfo('Speech Recognition API available');
                    return true;
                } else {
                    updateDebugInfo('Speech Recognition API NOT available', true);
                    status.textContent = 'Speech recognition not supported. Use Chrome, Edge, or Safari with HTTPS.';
                    micButton.disabled = true;
                    return false;
                }
            }

            // Function to check and request microphone permission
            async function requestMicrophonePermission() {
                updateDebugInfo('Requesting microphone permission...');
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    stream.getTracks().forEach(track => track.stop());
                    permissionGranted = true;
                    updateDebugInfo('Microphone permission GRANTED');
                    return true;
                } catch (error) {
                    updateDebugInfo('Microphone permission DENIED: ' + error.message, true);
                    status.textContent = 'Microphone access denied. Please allow access and refresh.';
                    return false;
                }
            }

            // Initialize speech recognition
            function initializeSpeechRecognition() {
                try {
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    recognition = new SpeechRecognition();
                    
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.lang = 'en-US';

                    recognition.onstart = function() {
                        isListening = true;
                        micButton.classList.add('listening');
                        updateDebugInfo('Speech recognition STARTED successfully');
                        
                        if (!wakeWordDetected) {
                            status.textContent = 'Listening for "Hey Bob"...';
                            wakeStatus.textContent = 'Say "Hey Bob" now...';
                        } else {
                            status.textContent = 'I am listening... What can I help you with?';
                        }
                    };

                    recognition.onresult = function(event) {
                        const result = event.results[0];
                        const text = result[0].transcript.toLowerCase().trim();
                        const confidence = result[0].confidence || 0;
                        
                        updateDebugInfo('Heard: "' + text + '" (confidence: ' + confidence.toFixed(2) + ')');
                        
                        if (!wakeWordDetected) {
                            // Check for wake word
                            if (text.includes('hey bob') || text.includes('hi bob') || text.includes('hello bob')) {
                                wakeWordDetected = true;
                                wakeStatus.textContent = 'Wake word detected! Ask your question...';
                                wakeStatus.className = 'wake-word-status wake-detected';
                                status.textContent = 'Great! Now ask me anything...';
                                
                                updateDebugInfo('Wake word DETECTED, preparing for query...');
                                
                                // Speak confirmation
                                const utterance = new SpeechSynthesisUtterance('Hello! What can I help you with?');
                                utterance.rate = 0.8;
                                speechSynthesis.speak(utterance);
                                
                                // Start listening for the actual query after confirmation
                                setTimeout(function() {
                                    if (recognition && !isListening) {
                                        try {
                                            recognition.start();
                                        } catch (error) {
                                            updateDebugInfo('Error restarting recognition: ' + error.message, true);
                                        }
                                    }
                                }, 2500);
                            } else {
                                status.textContent = 'I heard: "' + result[0].transcript + '" - Please say "Hey Bob"';
                                setTimeout(function() {
                                    status.textContent = 'Click the microphone and say "Hey Bob"';
                                }, 3000);
                            }
                        } else {
                            // Process the actual query
                            const query = result[0].transcript;
                            transcript.style.display = 'block';
                            transcript.innerHTML = '<strong>You said:</strong> ' + query;
                            
                            updateDebugInfo('Processing query: "' + query + '"');
                            
                            // Store in window for Streamlit to access
                            window.currentVoiceQuery = query;
                            window.queryTimestamp = Date.now();
                            
                            // Trigger Streamlit rerun by modifying a query parameter
                            const url = new URL(window.location);
                            url.searchParams.set('voice_query', encodeURIComponent(query));
                            url.searchParams.set('voice_timestamp', Date.now().toString());
                            window.location.href = url.toString();
                        }
                    };

                    recognition.onerror = function(event) {
                        console.error('Speech recognition error:', event.error);
                        updateDebugInfo('Speech ERROR: ' + event.error, true);
                        
                        let errorMessage = 'Please try again.';
                        
                        switch(event.error) {
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
                        }
                        
                        status.textContent = 'Error: ' + event.error + '. ' + errorMessage;
                        micButton.classList.remove('listening', 'processing');
                        isListening = false;
                    };

                    recognition.onend = function() {
                        micButton.classList.remove('listening');
                        isListening = false;
                        updateDebugInfo('Speech recognition ENDED');
                        
                        if (!wakeWordDetected) {
                            status.textContent = 'Click the microphone and say "Hey Bob"';
                        }
                    };

                    updateDebugInfo('Speech recognition INITIALIZED successfully');
                } catch (error) {
                    updateDebugInfo('Error initializing speech recognition: ' + error.message, true);
                }
            }

            // Microphone button click handler
            micButton.addEventListener('click', async function() {
                updateDebugInfo('Microphone button CLICKED');
                
                if (!permissionGranted) {
                    status.textContent = 'Requesting microphone permission...';
                    const granted = await requestMicrophonePermission();
                    if (!granted) {
                        return;
                    }
                    initializeSpeechRecognition();
                    setTimeout(function() {
                        status.textContent = 'Click the microphone and say "Hey Bob"';
                        wakeStatus.textContent = 'Waiting for "Hey Bob"...';
                    }, 1000);
                } else if (!isListening && recognition) {
                    try {
                        recognition.start();
                    } catch (error) {
                        updateDebugInfo('Error starting recognition: ' + error.message, true);
                        status.textContent = 'Error starting microphone. Please refresh and try again.';
                    }
                } else {
                    updateDebugInfo('Button clicked but already listening or no recognition object');
                }
            });

            // Listen for responses from Streamlit
            window.addEventListener('message', function(event) {
                if (event.data && event.data.type === 'bot_response') {
                    status.textContent = 'Bob is speaking...';
                    updateDebugInfo('Received response from Streamlit');
                    
                    // Clean the response for speech
                    let responseText = event.data.response;
                    responseText = responseText.replace(/[*#`]/g, ''); // Remove markdown
                    responseText = responseText.replace(/\\n/g, ' '); // Replace newlines with spaces
                    responseText = responseText.replace(/\\s+/g, ' '); // Clean whitespace
                    responseText = responseText.trim();
                    
                    // Speak the response
                    const utterance = new SpeechSynthesisUtterance(responseText);
                    utterance.rate = 0.8;
                    utterance.pitch = 1;
                    utterance.volume = 0.8;
                    
                    utterance.onend = function() {
                        // Reset for next interaction
                        wakeWordDetected = false;
                        wakeStatus.textContent = 'Waiting for "Hey Bob"...';
                        wakeStatus.className = 'wake-word-status wake-waiting';
                        status.textContent = 'Click the microphone and say "Hey Bob"';
                        micButton.classList.remove('processing');
                        transcript.style.display = 'none';
                        updateDebugInfo('Ready for next interaction');
                    };
                    
                    speechSynthesis.speak(utterance);
                }
            });

            // Initialize on page load
            document.addEventListener('DOMContentLoaded', function() {
                updateDebugInfo('Page loaded, checking browser support...');
                
                if (checkBrowserSupport()) {
                    status.textContent = 'Click the microphone to start';
                    wakeStatus.textContent = 'Ready - Click microphone first';
                    wakeStatus.className = 'wake-word-status wake-waiting';
                } else {
                    wakeStatus.textContent = 'Browser not supported';
                    wakeStatus.className = 'wake-word-status error-info';
                }
            });
        </script>
    </body>
    </html>
    '''
    return html_code

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'processed_queries' not in st.session_state:
        st.session_state.processed_queries = set()

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
    
    # Voice interface
    voice_html = create_voice_interface()
    components.html(voice_html, height=450, key="voice_interface")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle voice queries from URL parameters
    voice_query = st.query_params.get("voice_query")
    voice_timestamp = st.query_params.get("voice_timestamp")
    
    if voice_query and voice_timestamp:
        # Decode the query
        import urllib.parse
        decoded_query = urllib.parse.unquote(voice_query)
        
        # Check if this is a new query
        query_id = f"{decoded_query}_{voice_timestamp}"
        if query_id not in st.session_state.processed_queries:
            # Mark as processed
            st.session_state.processed_queries.add(query_id)
            
            # Show what we're processing
            st.info(f"🎙️ Processing voice query: '{decoded_query}'")
            
            # Get AI response
            ai_response = get_ai_response(decoded_query)
            
            # Add to conversation history
            st.session_state.conversation_history.append({
                "user": decoded_query,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            # Clean response for JavaScript
            clean_response = ai_response.replace('"', '\\"').replace("'", "\\'").replace('\n', ' ').replace('\r', '')
            
            # Send response back to JavaScript for speech synthesis
            response_js = f'''
            <script>
            console.log('Sending response to iframe...');
            const iframe = document.querySelector('iframe[title="voice_interface"]');
            if (iframe && iframe.contentWindow) {{
                iframe.contentWindow.postMessage({{
                    type: 'bot_response',
                    response: "{clean_response}"
                }}, '*');
                console.log('Response sent to iframe');
            }} else {{
                console.error('Could not find iframe or iframe content window');
            }}
            
            // Clear URL parameters after processing
            setTimeout(function() {{
                const url = new URL(window.location);
                url.searchParams.delete('voice_query');
                url.searchParams.delete('voice_timestamp');
                history.replaceState(null, '', url.toString());
            }}, 100);
            </script>
            '''
            components.html(response_js, height=0)
    
    # Simple text input as backup for testing
    st.markdown("---")
    st.markdown("### 💬 Alternative: Text Input (for testing)")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        text_query = st.text_input("Type your question here:", placeholder="What can Bob help you with?", key="text_input")
    
    with col2:
        ask_button = st.button("Ask Bob", type="primary")
    
    if ask_button and text_query:
        ai_response = get_ai_response(text_query)
        st.session_state.conversation_history.append({
            "user": text_query,
            "bob": ai_response,
            "timestamp": time.strftime("%H:%M:%S")
        })
        st.success(f"**Bob:** {ai_response}")
        
        # Clear the text input
        st.rerun()
    
    # Troubleshooting section
    st.markdown("---")
    st.markdown("### 🔧 Troubleshooting Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Common Issues:**
        1. **Wrong Browser** - Firefox doesn't work, use Chrome
        2. **Permission Blocked** - Allow microphone when prompted
        3. **HTTP Connection** - Must use HTTPS or localhost
        4. **No Microphone** - Check device has working microphone
        5. **Pop-up Blocked** - Allow pop-ups for permission requests
        """)
    
    with col2:
        st.markdown("""
        **What to Check:**
        - 🔍 Look at debug info in voice interface
        - 🎙️ Click "Test Microphone" button below
        - 🔧 Open browser console (F12) for errors
        - 💬 Try text input to test Bob's responses
        - 🔄 Refresh page if microphone gets stuck
        """)
    
    # Test microphone button
    if st.button("🎙️ Test Microphone Access Now"):
        test_js = '''
        <script>
        console.log('Testing microphone access...');
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                stream.getTracks().forEach(track => track.stop());
                alert('✅ SUCCESS: Microphone access works!');
                console.log('Microphone test successful');
            })
            .catch(function(error) {
                alert('❌ FAILED: ' + error.message);
                console.error('Microphone test failed:', error);
            });
        </script>
        '''
        components.html(test_js, height=0)
    
    # Show current environment info
    st.markdown("---")
    st.markdown("### 📊 Environment Info")
    env_info_js = '''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const envInfo = {
            userAgent: navigator.userAgent,
            protocol: window.location.protocol,
            hostname: window.location.hostname,
            speechRecognition: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
            mediaDevices: 'mediaDevices' in navigator,
            getUserMedia: 'getUserMedia' in (navigator.mediaDevices || {})
        };
        
        console.log('Environment Info:', envInfo);
        
        let infoHtml = '<div style="background: #f0f0f0; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px;">';
        infoHtml += '<strong>Browser Environment:</strong><br>';
        infoHtml += 'User Agent: ' + envInfo.userAgent + '<br>';
        infoHtml += 'Protocol: ' + envInfo.protocol + '<br>';
        infoHtml += 'Hostname: ' + envInfo.hostname + '<br>';
        infoHtml += 'Speech Recognition: ' + (envInfo.speechRecognition ? '✅ Available' : '❌ Not Available') + '<br>';
        infoHtml += 'Media Devices: ' + (envInfo.mediaDevices ? '✅ Available' : '❌ Not Available') + '<br>';
        infoHtml += 'getUserMedia: ' + (envInfo.getUserMedia ? '✅ Available' : '❌ Not Available');
        infoHtml += '</div>';
        
        // Try to find a container to display this info
        const containers = document.querySelectorAll('div');
        if (containers.length > 0) {
            const lastContainer = containers[containers.length - 1];
            lastContainer.innerHTML = infoHtml;
        }
    });
    </script>
    '''
    components.html(env_info_js, height=100)
    
    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.subheader("💬 Recent Conversations")
        
        # Show last 3 conversations
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-3:])):
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
