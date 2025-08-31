import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import time

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
    if 'processing_voice' not in st.session_state:
        st.session_state.processing_voice = False

    # Custom CSS
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
    .voice-response {
        background: #e8f5e8;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background: #f8d7da;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="title">🤖 Bob - Voice Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Talk to Bob or type your questions</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Voice Interface - COMPLETELY REWRITTEN
    st.markdown("### 🎙️ Voice Interface")
    
    import streamlit.components.v1 as components
    
    # Simple voice interface that uses session state
    voice_html = f"""
    <div style="text-align: center; padding: 20px; border: 2px dashed #ccc; border-radius: 10px; margin: 20px 0;">
        <div style="font-size: 60px; margin-bottom: 10px;">
            <button id="voiceBtn" style="background: none; border: none; cursor: pointer; font-size: 60px;">
                🎤
            </button>
        </div>
        <div id="status" style="font-size: 16px; margin: 10px 0; min-height: 25px;">
            Click microphone to talk to Bob
        </div>
        <div id="transcript" style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin: 10px 0; min-height: 40px; display: none;">
        </div>
    </div>

    <script>
    let isListening = false;
    const voiceBtn = document.getElementById('voiceBtn');
    const status = document.getElementById('status');
    const transcript = document.getElementById('transcript');

    voiceBtn.addEventListener('click', function() {{
        if (isListening) return;
        
        // Check if speech recognition is available
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
            status.innerHTML = '❌ Speech recognition not supported. Try Chrome browser.';
            return;
        }}

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();

        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = function() {{
            isListening = true;
            voiceBtn.style.color = '#ff4444';
            status.innerHTML = '🎤 Listening... Speak clearly!';
            transcript.style.display = 'none';
        }};

        recognition.onresult = function(event) {{
            const spokenText = event.results[0][0].transcript;
            transcript.innerHTML = 'You said: "' + spokenText + '"';
            transcript.style.display = 'block';
            status.innerHTML = '✅ Got it! Processing...';
            
            // Send to Streamlit using query params - FIXED METHOD
            setTimeout(() => {{
                const params = new URLSearchParams(window.location.search);
                params.set('voice_input', encodeURIComponent(spokenText));
                params.set('timestamp', Date.now());
                window.location.search = params.toString();
            }}, 1000);
        }};

        recognition.onerror = function(event) {{
            status.innerHTML = '❌ Error: ' + event.error + ' - Try again!';
            voiceBtn.style.color = '#4A90E2';
            isListening = false;
        }};

        recognition.onend = function() {{
            voiceBtn.style.color = '#4A90E2';
            isListening = false;
            if (status.innerHTML.includes('Listening')) {{
                status.innerHTML = '⚠️ No speech detected. Try again.';
            }}
        }};

        recognition.start();
    }});
    </script>
    """
    
    components.html(voice_html, height=200)

    # Process voice input from URL parameters - SIMPLIFIED
    voice_input = st.query_params.get("voice_input")
    timestamp = st.query_params.get("timestamp")
    
    if voice_input and timestamp:
        try:
            decoded_input = voice_input
            st.info(f"🎙️ **Voice Input:** {decoded_input}")
            
            # Get AI response
            with st.spinner("🤖 Bob is thinking..."):
                ai_response = get_ai_response(decoded_input)
            
            # Display response
            st.markdown(f'<div class="voice-response"><strong>🤖 Bob says:</strong><br>{ai_response}</div>', unsafe_allow_html=True)
            
            # Add to history
            st.session_state.conversation_history.append({
                "user": decoded_input,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S"),
                "type": "voice"
            })
            
            # Text-to-speech
            clean_response = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '')
            
            tts_html = f"""
            <div style="text-align: center; margin: 20px 0;">
                <button onclick="speakResponse()" style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">
                    🔊 Hear Bob's Response
                </button>
                <div id="speakStatus" style="margin-top: 10px;"></div>
            </div>
            
            <script>
            function speakResponse() {{
                const text = `{clean_response}`;
                if ('speechSynthesis' in window) {{
                    speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.rate = 0.9;
                    utterance.pitch = 1.0;
                    
                    utterance.onstart = () => document.getElementById('speakStatus').innerHTML = '🔊 Speaking...';
                    utterance.onend = () => {{
                        document.getElementById('speakStatus').innerHTML = '✅ Done';
                        setTimeout(() => document.getElementById('speakStatus').innerHTML = '', 2000);
                    }};
                    
                    speechSynthesis.speak(utterance);
                }} else {{
                    document.getElementById('speakStatus').innerHTML = '❌ Text-to-speech not available';
                }}
            }}
            
            // Auto-play response
            setTimeout(() => {{
                speakResponse();
            }}, 500);
            </script>
            """
            
            components.html(tts_html, height=80)
            
            # Clear URL params after processing
            if st.button("🔄 Ready for next question"):
                st.query_params.clear()
                st.rerun()
                
        except Exception as e:
            st.markdown(f'<div class="error-box"><strong>❌ Error processing voice:</strong><br>{str(e)}</div>', unsafe_allow_html=True)

    # Text input as backup
    st.markdown("---")
    st.markdown("### 💬 Text Input")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        text_query = st.text_input("Type your question:", placeholder="Ask Bob anything...")
    with col2:
        text_button = st.button("Ask", type="primary")
    
    if text_button and text_query:
        with st.spinner("🤖 Bob is thinking..."):
            ai_response = get_ai_response(text_query)
            st.session_state.conversation_history.append({
                "user": text_query,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S"),
                "type": "text"
            })
            st.success(f"**Bob:** {ai_response}")

    # Quick test section
    st.markdown("---")
    st.markdown("### ⚡ Quick Test")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Test: What's 5+5?"):
            response = get_ai_response("What is 5 plus 5?")
            st.write(f"**Bob:** {response}")
    
    with col2:
        if st.button("Test: Tell me a joke"):
            response = get_ai_response("Tell me a short joke")
            st.write(f"**Bob:** {response}")
            
    with col3:
        if st.button("Test: Current time"):
            response = get_ai_response("What time is it?")
            st.write(f"**Bob:** {response}")

    # Debug section
    st.markdown("---")
    st.markdown("### 🔍 Debug Info")
    
    with st.expander("Show Debug Information"):
        st.write("**URL Parameters:**", dict(st.query_params))
        st.write("**Session State Keys:**", list(st.session_state.keys()))
        st.write("**Processing Status:**", st.session_state.get('processing_voice', 'Not set'))
        
        # API Status
        if st.button("Test API Connection"):
            try:
                test_response = get_ai_response("Say hello")
                st.success(f"✅ API Working: {test_response}")
            except Exception as e:
                st.error(f"❌ API Error: {e}")

    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.subheader("💬 Conversation History")
        
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-3:])):
            icon = "🎙️" if conv.get('type') == 'voice' else "⌨️"
            st.write(f"{icon} **[{conv['timestamp']}] You:** {conv['user']}")
            st.write(f"🤖 **Bob:** {conv['bob']}")
            st.markdown("---")
        
        if st.button("Clear History"):
            st.session_state.conversation_history = []
            st.rerun()

if __name__ == "__main__":
    main()
