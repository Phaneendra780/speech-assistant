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
    html_code = """
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
            .permission-status {
                margin-top: 15px;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
                font-size: 14px;
            }
            .permission-granted {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            .permission-denied {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body>
        <div class="voice-container">
            <button class="microphone" id="micButton">🎤</button>
            <div class="status" id="status">Click the microphone to start</div>
            <div class="wake-word-status wake-waiting" id="wakeStatus">Waiting for "Hey Bob"...</div>
            <div class="permission-status" id="permissionStatus" style="display: none;"></div>
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
            const permissionStatus = document.getElementById('permissionStatus');

            // Function to check and request microphone permission
            async function requestMicrophonePermission() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    // Permission granted
                    stream.getTracks().forEach(track => track.stop()); // Stop the stream
                    permissionGranted = true;
                    permissionStatus.style.display = 'block';
                    permissionStatus.className = 'permission-status permission-granted';
                    permissionStatus.textContent = '✅ Microphone access granted';
                    return true;
                } catch (error) {
                    // Permission denied
                    permissionStatus.style.display = 'block';
                    permissionStatus.className = 'permission-status permission-denied';
                    permissionStatus.textContent = '❌ Microphone access denied. Please allow microphone access and refresh the page.';
                    status.textContent = 'Microphone permission required';
                    return false;
                }
            }

            // Initialize speech recognition
            function initializeSpeechRecognition() {
                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    recognition = new SpeechRecognition();
                    
                    recognition.continuous = false;
                    recognition.interimResults = true;
                    recognition.lang = 'en-US';

                    recognition.onstart = function() {
                        isListening = true;
                        micButton.classList.add('listening');
                        if (!wakeWordDetected) {
                            status.textContent = 'Listening for "Hey Bob"...';
                        } else {
                            status.textContent = 'I\'m listening... What can I help you with?';
                        }
                    };

                    recognition.onresult = function(event) {
                        const text = event.results[0][0].transcript.toLowerCase();
                        console.log('Heard:', text);
                        
                        if (!wakeWordDetected) {
                            // Check for wake word
                            if (text.includes('hey bob') || text.includes('hi bob')) {
                                wakeWordDetected = true;
                                wakeStatus.textContent = '✅ Wake word detected! Ask your question...';
                                wakeStatus.className = 'wake-word-status wake-detected';
                                status.textContent = 'Great! Now ask me anything...';
                                
                                // Speak confirmation
                                const utterance = new SpeechSynthesisUtterance('Hello! What can I help you with?');
                                utterance.rate = 0.8;
                                speechSynthesis.speak(utterance);
                                
                                // Start listening for the actual query
                                setTimeout(() => {
                                    if (recognition && !isListening) {
                                        recognition.start();
                                    }
                                }, 2500);
                            } else {
                                status.textContent = 'I heard: "' + event.results[0][0].transcript + '" - Please say "Hey Bob"';
                                setTimeout(() => {
                                    status.textContent = 'Click the microphone and say "Hey Bob"';
                                }, 3000);
                            }
                        } else {
                            // Process the actual query
                            const query = event.results[0][0].transcript;
                            transcript.style.display = 'block';
                            transcript.innerHTML = '<strong>You said:</strong> ' + query;
                            
                            // Send query to Streamlit parent window
                            const message = {
                                type: 'streamlit:setComponentValue',
                                value: {
                                    type: 'voice_query',
                                    query: query,
                                    timestamp: Date.now()
                                }
                            };
                            window.parent.postMessage(message, '*');
                            
                            status.textContent = 'Processing your question...';
                            micButton.classList.remove('listening');
                            micButton.classList.add('processing');
                        }
                    };

                    recognition.onerror = function(event) {
                        console.error('Speech recognition error:', event.error);
                        let errorMessage = 'Please try again.';
                        
                        if (event.error === 'not-allowed' || event.error === 'permission-denied') {
                            errorMessage = 'Microphone permission denied. Please allow access and refresh.';
                            permissionStatus.style.display = 'block';
                            permissionStatus.className = 'permission-status permission-denied';
                            permissionStatus.textContent = '❌ Microphone access denied';
                        }
                        
                        status.textContent = 'Error: ' + event.error + '. ' + errorMessage;
                        micButton.classList.remove('listening', 'processing');
                        isListening = false;
                    };

                    recognition.onend = function() {
                        micButton.classList.remove('listening');
                        isListening = false;
                        
                        if (!wakeWordDetected) {
                            status.textContent = 'Click the microphone and say "Hey Bob"';
                        }
                    };

                } else {
                    status.textContent = 'Speech recognition not supported in this browser. Please use Chrome, Edge, or Safari.';
                    micButton.disabled = true;
                }
            }

            // Microphone button click handler
            micButton.addEventListener('click', async function() {
                if (!permissionGranted) {
                    status.textContent = 'Requesting microphone permission...';
                    const granted = await requestMicrophonePermission();
                    if (!granted) {
                        return;
                    }
                    initializeSpeechRecognition();
                    setTimeout(() => {
                        status.textContent = 'Click the microphone and say "Hey Bob"';
                    }, 2000);
                } else if (!isListening && recognition) {
                    recognition.start();
                }
            });

            // Listen for responses from Streamlit
            window.addEventListener('message', function(event) {
                if (event.data.type === 'bot_response') {
                    status.textContent = 'Bob is speaking...';
                    
                    // Clean the response for speech
                    let responseText = event.data.response;
                    responseText = responseText.replace(/[*#`]/g, ''); // Remove markdown
                    responseText = responseText.replace(/\n/g, ' '); // Replace newlines with spaces
                    
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
                    };
                    
                    speechSynthesis.speak(utterance);
                }
            });

            // Initialize on page load
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Voice interface loaded');
            });
        </script>
    </body>
    </html>
    """
    return html_code

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'voice_query' not in st.session_state:
        st.session_state.voice_query = None

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
    components.html(voice_html, height=400)
    
    # Handle voice queries from JavaScript
    query = st.query_params.get("voice_query")
    if query and query != st.session_state.voice_query:
        st.session_state.voice_query = query
        
        # Get AI response
        ai_response = get_ai_response(query)
        
        # Add to conversation history
        st.session_state.conversation_history.append({
            "user": query,
            "bob": ai_response,
            "timestamp": time.strftime("%H:%M:%S")
        })
        
        # Send response back to JavaScript for speech synthesis
        st.components.v1.html(f"""
        <script>
        window.parent.postMessage({{
            type: 'bot_response',
            response: `{ai_response.replace('`', '\\`').replace('$', '\\$')}`
        }}, '*');
        </script>
        """, height=0)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.subheader("💬 Recent Conversations")
        
        # Show last 5 conversations
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:])):
            with st.expander(f"Conversation {len(st.session_state.conversation_history) - i} - {conv['timestamp']}"):
                st.write(f"**You:** {conv['user']}")
                st.write(f"**Bob:** {conv['bob']}")
    
    # Instructions
    st.markdown("---")
    st.markdown("""
    ### 📝 How to use Bob:
    
    1. **Click the microphone** 🎤 
    2. **Say "Hey Bob"** to wake up the assistant
    3. **Wait** for Bob to acknowledge you
    4. **Ask your question** clearly
    5. **Listen** to Bob's response
    
    **Example questions:**
    - "What's the weather like today?"
    - "Tell me about aspirin"
    - "What's 25 times 47?"
    - "Latest news about technology"
    
    **Note:** This uses your browser's built-in speech recognition and text-to-speech.
    """)
    
    # Clear history button
    if st.session_state.conversation_history:
        if st.button("🗑️ Clear Conversation History"):
            st.session_state.conversation_history = []
            st.rerun()

if __name__ == "__main__":
    main()
