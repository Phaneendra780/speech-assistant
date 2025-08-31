import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import time
import urllib.parse

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
    if 'voice_processed' not in st.session_state:
        st.session_state.voice_processed = False

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
    .voice-response {
        background: #e8f5e8;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #28a745;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="title">🤖 Bob - Voice Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Voice-enabled AI Assistant</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Handle voice query from URL params - FIXED VERSION
    voice_query = st.query_params.get("voice_query")
    if voice_query and not st.session_state.voice_processed:
        # Decode the voice query properly
        try:
            decoded_query = urllib.parse.unquote(voice_query)
            st.info(f"🎙️ Voice Input: **{decoded_query}**")
            
            # Process the voice query
            ai_response = get_ai_response(decoded_query)
            
            # Add to conversation history
            st.session_state.conversation_history.append({
                "user": decoded_query,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S"),
                "type": "voice"
            })
            
            # Display response with special styling
            st.markdown(f'<div class="voice-response"><strong>🤖 Bob:</strong> {ai_response}</div>', unsafe_allow_html=True)
            
            # Mark as processed to prevent reprocessing
            st.session_state.voice_processed = True
            
            # Text-to-speech - IMPROVED VERSION
            import streamlit.components.v1 as components
            
            # Clean the response for TTS
            clean_response = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '')
            
            tts_html = f"""
            <div style="text-align: center; margin: 10px 0;">
                <button id="playTTS" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    🔊 Play Bob's Response
                </button>
                <div id="ttsStatus" style="margin-top: 10px; font-size: 14px;"></div>
            </div>
            
            <script>
            const response = `{clean_response}`;
            
            document.getElementById('playTTS').addEventListener('click', function() {{
                if ('speechSynthesis' in window) {{
                    // Stop any ongoing speech
                    speechSynthesis.cancel();
                    
                    const utterance = new SpeechSynthesisUtterance(response);
                    utterance.rate = 0.8;
                    utterance.pitch = 1.0;
                    utterance.volume = 1.0;
                    
                    utterance.onstart = function() {{
                        document.getElementById('ttsStatus').innerHTML = '🔊 Speaking...';
                    }};
                    
                    utterance.onend = function() {{
                        document.getElementById('ttsStatus').innerHTML = '✅ Finished';
                        setTimeout(() => {{
                            document.getElementById('ttsStatus').innerHTML = '';
                        }}, 2000);
                    }};
                    
                    utterance.onerror = function(event) {{
                        document.getElementById('ttsStatus').innerHTML = '❌ TTS Error: ' + event.error;
                    }};
                    
                    speechSynthesis.speak(utterance);
                }} else {{
                    document.getElementById('ttsStatus').innerHTML = '❌ Text-to-speech not supported';
                }}
            }});
            
            // Auto-play the response
            if ('speechSynthesis' in window) {{
                setTimeout(() => {{
                    const utterance = new SpeechSynthesisUtterance(response);
                    utterance.rate = 0.8;
                    speechSynthesis.speak(utterance);
                }}, 500);
            }}
            </script>
            """
            
            components.html(tts_html, height=80)
            
        except Exception as e:
            st.error(f"❌ Error processing voice query: {e}")
            st.write(f"Raw voice query: {voice_query}")
    
    # Reset the voice processed flag when URL params are cleared
    if not voice_query and st.session_state.voice_processed:
        st.session_state.voice_processed = False

    # Step 1: Test Bob with text input first
    st.markdown("### 🧪 Test Bob's AI Response")
    st.markdown("First, let's make sure Bob can answer questions:")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        test_query = st.text_input(
            "Ask Bob a simple question:", 
            placeholder="What is 2 + 2?",
            key="test_query"
        )
    
    with col2:
        test_button = st.button("Test Bob", type="primary")
    
    if test_button and test_query:
        with st.spinner("Testing Bob's response..."):
            try:
                ai_response = get_ai_response(test_query)
                st.success(f"✅ **Bob:** {ai_response}")
                st.markdown("Great! Bob's AI is working. Now try voice...")
            except Exception as e:
                st.error(f"❌ Bob's AI failed: {e}")
                st.stop()
    
    # Step 2: Browser compatibility check
    st.markdown("---")
    st.markdown("### 🌐 Browser Compatibility Check")
    
    import streamlit.components.v1 as components
    
    # Improved browser check
    browser_check_html = """
    <div style="padding: 20px; font-family: Arial, sans-serif;">
        <div id="browserInfo" style="padding: 15px; background: #f0f0f0; border-radius: 5px; margin: 10px 0;">
            Checking browser compatibility...
        </div>
        <button id="testMic" style="padding: 10px 20px; background: #4A90E2; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px;">
            Test Microphone Permission
        </button>
        <button id="testSpeech" style="padding: 10px 20px; background: #E74C3C; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px;">
            Test Speech Recognition
        </button>
        <div id="testResults" style="padding: 15px; margin-top: 10px; background: #fff; border: 1px solid #ddd; border-radius: 5px;">
            Click buttons above to test functionality
        </div>
    </div>

    <script>
    const browserInfo = document.getElementById('browserInfo');
    const testResults = document.getElementById('testResults');
    const testMic = document.getElementById('testMic');
    const testSpeech = document.getElementById('testSpeech');

    // Check browser compatibility
    function checkBrowser() {
        const ua = navigator.userAgent;
        let browser = 'Unknown';
        let supported = false;
        
        if (ua.includes('Chrome') && !ua.includes('Edge')) {
            browser = 'Chrome';
            supported = true;
        } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
            browser = 'Safari';
            supported = true;
        } else if (ua.includes('Edge')) {
            browser = 'Edge';
            supported = true;
        } else if (ua.includes('Firefox')) {
            browser = 'Firefox';
            supported = false;
        }
        
        const isSecure = location.protocol === 'https:' || location.hostname === 'localhost';
        const hasAPI = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
        
        let status = supported ? '✅' : '❌';
        browserInfo.innerHTML = `
            ${status} <strong>${browser}</strong> | 
            ${isSecure ? '✅' : '❌'} ${location.protocol} | 
            ${hasAPI ? '✅' : '❌'} Speech API
        `;
        browserInfo.style.background = supported && isSecure && hasAPI ? '#d4edda' : '#f8d7da';
        
        return supported && isSecure && hasAPI;
    }

    // Test microphone permission
    testMic.addEventListener('click', async function() {
        testResults.innerHTML = 'Testing microphone permission...';
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            testResults.innerHTML = '✅ <strong>SUCCESS:</strong> Microphone permission granted!';
            testResults.style.background = '#d4edda';
        } catch (error) {
            testResults.innerHTML = `❌ <strong>FAILED:</strong> ${error.message}<br><small>Try: Allow microphone in browser settings</small>`;
            testResults.style.background = '#f8d7da';
        }
    });

    // Test speech recognition
    testSpeech.addEventListener('click', function() {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            testResults.innerHTML = '❌ <strong>FAILED:</strong> Speech Recognition API not available';
            testResults.style.background = '#f8d7da';
            return;
        }
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        testResults.innerHTML = '🎤 <strong>LISTENING:</strong> Say something...';
        testResults.style.background = '#fff3cd';
        
        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            testResults.innerHTML = `✅ <strong>SUCCESS:</strong> I heard "${text}"`;
            testResults.style.background = '#d4edda';
        };
        
        recognition.onerror = function(event) {
            testResults.innerHTML = `❌ <strong>ERROR:</strong> ${event.error}<br><small>Common fixes: Check microphone permissions, speak louder, use Chrome browser</small>`;
            testResults.style.background = '#f8d7da';
        };
        
        recognition.onend = function() {
            if (testResults.innerHTML.includes('LISTENING')) {
                testResults.innerHTML = '⚠️ <strong>NO SPEECH:</strong> Try speaking louder or closer to microphone';
                testResults.style.background = '#fff3cd';
            }
        };
        
        try {
            recognition.start();
        } catch (error) {
            testResults.innerHTML = `❌ <strong>START ERROR:</strong> ${error.message}`;
            testResults.style.background = '#f8d7da';
        }
    });

    // Initialize
    checkBrowser();
    </script>
    """
    
    components.html(browser_check_html, height=220)
    
    # Step 3: Voice Interface - FIXED VERSION
    st.markdown("---")
    st.markdown("### 🎙️ Voice Interface")
    
    # Improved voice input with better error handling
    voice_interface_html = """
    <div style="text-align: center; padding: 20px;">
        <button id="voiceBtn" style="font-size: 80px; background: none; border: none; cursor: pointer; color: #4A90E2; transition: all 0.3s;">
            🎤
        </button>
        <div id="voiceStatus" style="margin-top: 15px; font-size: 16px; min-height: 20px;">
            Click microphone to ask Bob something
        </div>
        <div id="voiceResult" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; display: none; font-style: italic;">
        </div>
        <div id="debugInfo" style="margin-top: 10px; font-size: 12px; color: #666; display: none;">
        </div>
    </div>

    <script>
    let recognition;
    let isListening = false;

    document.getElementById('voiceBtn').addEventListener('click', function() {
        // Debug info
        const debugDiv = document.getElementById('debugInfo');
        debugDiv.style.display = 'block';
        debugDiv.innerHTML = 'Debug: Button clicked, checking compatibility...';
        
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            document.getElementById('voiceStatus').innerHTML = '❌ Speech recognition not supported in this browser';
            debugDiv.innerHTML = 'Debug: Speech API not found';
            return;
        }

        if (isListening) {
            debugDiv.innerHTML = 'Debug: Already listening, ignoring click';
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onstart = function() {
            isListening = true;
            document.getElementById('voiceBtn').style.color = '#E74C3C';
            document.getElementById('voiceBtn').style.transform = 'scale(1.1)';
            document.getElementById('voiceStatus').innerHTML = '🎤 Listening... Speak now!';
            document.getElementById('voiceResult').style.display = 'none';
            debugDiv.innerHTML = 'Debug: Recognition started successfully';
        };

        recognition.onresult = function(event) {
            const query = event.results[0][0].transcript.trim();
            const confidence = event.results[0][0].confidence;
            
            debugDiv.innerHTML = `Debug: Got result "${query}" (confidence: ${confidence})`;
            
            document.getElementById('voiceResult').style.display = 'block';
            document.getElementById('voiceResult').innerHTML = `You said: "${query}"`;
            document.getElementById('voiceStatus').innerHTML = '✅ Processing your question...';
            
            // Small delay to show the recognized text
            setTimeout(() => {
                // Properly encode the query for URL
                const encodedQuery = encodeURIComponent(query);
                const url = new URL(window.location);
                url.searchParams.set('voice_query', encodedQuery);
                
                debugDiv.innerHTML = `Debug: Redirecting with query: ${encodedQuery}`;
                
                // Force page reload with new parameters
                window.location.href = url.toString();
            }, 1000);
        };

        recognition.onerror = function(event) {
            const errorMsg = event.error;
            document.getElementById('voiceStatus').innerHTML = `❌ Speech Error: ${errorMsg}`;
            document.getElementById('voiceBtn').style.color = '#4A90E2';
            document.getElementById('voiceBtn').style.transform = 'scale(1)';
            isListening = false;
            
            debugDiv.innerHTML = `Debug: Speech error - ${errorMsg}`;
            
            // Provide helpful error messages
            let helpText = '';
            switch(errorMsg) {
                case 'not-allowed':
                    helpText = 'Please allow microphone access in your browser';
                    break;
                case 'no-speech':
                    helpText = 'No speech detected. Try speaking louder or closer to mic';
                    break;
                case 'network':
                    helpText = 'Network error. Check your internet connection';
                    break;
                case 'audio-capture':
                    helpText = 'Microphone not working. Check device settings';
                    break;
                default:
                    helpText = 'Try again or use text input below';
            }
            
            setTimeout(() => {
                document.getElementById('voiceStatus').innerHTML = helpText;
            }, 2000);
        };

        recognition.onend = function() {
            document.getElementById('voiceBtn').style.color = '#4A90E2';
            document.getElementById('voiceBtn').style.transform = 'scale(1)';
            isListening = false;
            
            if (document.getElementById('voiceStatus').innerHTML.includes('Listening')) {
                document.getElementById('voiceStatus').innerHTML = '⚠️ No speech detected. Try again.';
                debugDiv.innerHTML = 'Debug: Recognition ended without result';
            }
        };

        try {
            debugDiv.innerHTML = 'Debug: Starting recognition...';
            recognition.start();
        } catch (error) {
            document.getElementById('voiceStatus').innerHTML = '❌ Could not start: ' + error.message;
            debugDiv.innerHTML = `Debug: Start error - ${error.message}`;
        }
    });
    </script>
    """
    
    components.html(voice_interface_html, height=200)
    
    # Regular text input for comparison
    st.markdown("---")
    st.markdown("### 💬 Text Input (Backup)")
    
    text_query = st.text_input("Type your question:", placeholder="What can Bob help you with?")
    
    if st.button("Ask Bob") and text_query:
        ai_response = get_ai_response(text_query)
        st.session_state.conversation_history.append({
            "user": text_query,
            "bob": ai_response,
            "timestamp": time.strftime("%H:%M:%S"),
            "type": "text"
        })
        st.write(f"**Bob:** {ai_response}")
    
    # Debugging info
    st.markdown("---")
    st.markdown("### 🔍 Debug Information")
    
    # Show current URL params for debugging
    if st.query_params:
        st.write("**Current URL Parameters:**")
        for key, value in st.query_params.items():
            st.write(f"- {key}: {value}")
            if key == "voice_query":
                decoded = urllib.parse.unquote(value)
                st.write(f"  - Decoded: {decoded}")
    else:
        st.write("**No URL parameters found**")
    
    # Session state info
    st.write(f"**Voice Processed:** {st.session_state.voice_processed}")
    
    # Environment check
    st.markdown("**Browser Requirements:**")
    st.markdown("- ✅ Chrome (best support)")
    st.markdown("- ✅ Edge (good support)")  
    st.markdown("- ✅ Safari (basic support)")
    st.markdown("- ❌ Firefox (not supported)")
    st.markdown("- ✅ HTTPS or localhost required")
    
    # Conversation history with type indicators
    if st.session_state.conversation_history:
        st.markdown("---")
        st.subheader("💬 Recent Conversations")
        
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:])):
            voice_icon = "🎙️" if conv.get('type') == 'voice' else "⌨️"
            with st.expander(f"{voice_icon} Conversation {len(st.session_state.conversation_history) - i} - {conv['timestamp']}"):
                st.write(f"**You:** {conv['user']}")
                st.write(f"**Bob:** {conv['bob']}")
    
    # Clear history button
    if st.session_state.conversation_history:
        if st.button("🗑️ Clear History"):
            st.session_state.conversation_history = []
            st.session_state.voice_processed = False
            st.rerun()

if __name__ == "__main__":
    main()
