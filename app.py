import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import streamlit.components.v1 as components
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
        return f"Sorry, I encountered an error: {str(e)}"

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    # PROCESS VOICE INPUT FIRST - BEFORE ANYTHING ELSE
    voice_query = st.query_params.get("voice_query")
    
    if voice_query:
        # Clear query params immediately
        st.query_params.clear()
        
        # Big header for voice response
        st.markdown("# 🎤 VOICE CONVERSATION")
        
        # Show what user said
        st.markdown(f"""
        <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #2196f3;">
            <h3 style="margin: 0; color: #1976d2;">🎙️ You said:</h3>
            <p style="font-size: 18px; margin: 10px 0 0 0; font-style: italic;">"{voice_query}"</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get Bob's response
        with st.spinner("🤖 Bob is thinking..."):
            ai_response = get_ai_response(voice_query)
        
        # Show Bob's response
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 15px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h3 style="margin: 0 0 15px 0;">🤖 Bob says:</h3>
            <p style="font-size: 18px; line-height: 1.5; margin: 0;">{ai_response}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add to conversation history
        st.session_state.conversation_history.append({
            "user": voice_query,
            "bob": ai_response,
            "timestamp": time.strftime("%H:%M:%S"),
            "type": "voice"
        })
        
        # TTS Response
        clean_text = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '')
        
        tts_component = f"""
        <div style="text-align: center; margin: 30px 0;">
            <button onclick="speakBob()" style="
                padding: 20px 40px; 
                background: #4CAF50; 
                color: white; 
                border: none; 
                border-radius: 12px; 
                cursor: pointer; 
                font-size: 20px; 
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                transition: all 0.3s;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                🔊 PLAY BOB'S RESPONSE
            </button>
            <div id="speechStatus" style="margin-top: 15px; font-size: 16px; color: #666;"></div>
        </div>
        
        <script>
        function speakBob() {{
            const text = `{clean_text}`;
            const status = document.getElementById('speechStatus');
            
            if ('speechSynthesis' in window) {{
                speechSynthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.8;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;
                
                utterance.onstart = () => {{
                    status.innerHTML = '🔊 Bob is speaking...';
                    status.style.color = '#4CAF50';
                }};
                
                utterance.onend = () => {{
                    status.innerHTML = '✅ Bob finished speaking';
                    status.style.color = '#2196F3';
                    setTimeout(() => {{
                        status.innerHTML = '';
                    }}, 3000);
                }};
                
                utterance.onerror = (e) => {{
                    status.innerHTML = '❌ Speech error: ' + e.error;
                    status.style.color = '#f44336';
                }};
                
                speechSynthesis.speak(utterance);
            }} else {{
                status.innerHTML = '❌ Text-to-speech not supported in this browser';
                status.style.color = '#f44336';
            }}
        }}
        
        // Auto-play Bob's response after 1 second
        setTimeout(() => {{
            speakBob();
        }}, 1000);
        </script>
        """
        
        components.html(tts_component, height=120)
        
        # Success message
        st.success("🎉 Voice conversation completed! Try speaking again below.")
        
        st.markdown("---")

    # Main App Header
    st.markdown("# 🤖 Bob - Voice Assistant")
    st.markdown("### Talk to Bob or type your questions")

    # Custom CSS
    st.markdown("""
    <style>
    .voice-response {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .voice-input {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Step 1: Quick API Test
    st.markdown("**🧪 Step 1: Test Bob's Brain**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What's 2+2?", key="test1"):
            response = get_ai_response("What is 2 plus 2?")
            st.success(f"Bob: {response}")
    
    with col2:
        if st.button("Tell a joke", key="test2"):
            response = get_ai_response("Tell me a short joke")
            st.success(f"Bob: {response}")
    
    with col3:
        if st.button("Say hello", key="test3"):
            response = get_ai_response("Just say hello")
            st.success(f"Bob: {response}")

    # Step 2: Voice Interface
    st.markdown("---")
    st.markdown("**🎙️ Step 2: Voice Interface**")
    
    # Streamlit Cloud HTTPS check
    st.info("ℹ️ Voice input works on Streamlit Cloud (HTTPS) and Chrome/Edge browsers")
    
    # Voice Interface Component
    voice_html = f"""
    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #74b9ff, #0984e3); border-radius: 20px; margin: 20px 0;">
        <div style="color: white; font-size: 20px; margin-bottom: 25px; font-weight: bold;">
            🎙️ Click the microphone and speak to Bob
        </div>
        
        <button id="voiceBtn" style="
            font-size: 80px; 
            background: rgba(255,255,255,0.2); 
            border: 4px solid white; 
            border-radius: 50%; 
            cursor: pointer; 
            padding: 25px;
            transition: all 0.3s ease;
            color: white;
            outline: none;
            width: 150px;
            height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
        ">🎤</button>
        
        <div id="voiceStatus" style="color: white; margin-top: 20px; font-size: 18px; min-height: 30px; font-weight: bold;">
            Ready to listen - Click microphone!
        </div>
        
        <div id="voiceTranscript" style="
            background: rgba(255,255,255,0.9); 
            color: #333; 
            padding: 20px; 
            border-radius: 12px; 
            margin-top: 20px; 
            display: none;
            font-size: 16px;
            font-weight: bold;
        "></div>
    </div>

    <script>
    let voiceRecognition;
    let isListening = false;

    document.getElementById('voiceBtn').addEventListener('click', function() {{
        const btn = this;
        const status = document.getElementById('voiceStatus');
        const transcript = document.getElementById('voiceTranscript');
        
        if (isListening) {{
            status.innerHTML = '⏸️ Already listening, please wait...';
            return;
        }}
        
        // Check for speech recognition support
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
            status.innerHTML = '❌ Speech not supported. Use Chrome or Edge browser!';
            return;
        }}

        // Create recognition instance
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        voiceRecognition = new SpeechRecognition();
        
        // Configure recognition
        voiceRecognition.continuous = false;
        voiceRecognition.interimResults = false;
        voiceRecognition.lang = 'en-US';

        voiceRecognition.onstart = function() {{
            isListening = true;
            btn.style.background = 'rgba(255,50,50,0.5)';
            btn.style.transform = 'scale(1.1)';
            btn.style.boxShadow = '0 0 30px rgba(255,50,50,0.6)';
            status.innerHTML = '🎤 LISTENING... Speak now!';
            transcript.style.display = 'none';
        }};

        voiceRecognition.onresult = function(event) {{
            const spokenText = event.results[0][0].transcript.trim();
            const confidence = event.results[0][0].confidence || 0;
            
            console.log('Speech result:', spokenText, 'Confidence:', confidence);
            
            if (spokenText && spokenText.length > 0) {{
                transcript.innerHTML = `✅ Captured: "${{spokenText}}"`;
                transcript.style.display = 'block';
                status.innerHTML = '📤 Sending to Bob... Please wait!';
                
                // Create unique URL to send voice input
                const timestamp = Date.now();
                console.log('Redirecting with voice query:', spokenText);
                
                setTimeout(() => {{
                    const currentUrl = new URL(window.location);
                    currentUrl.searchParams.set('voice_input', spokenText);
                    currentUrl.searchParams.set('voice_ts', timestamp);
                    window.location.href = currentUrl.toString();
                }}, 2000);
            }} else {{
                status.innerHTML = '🔇 No speech detected. Try again!';
            }}
        }};

        voiceRecognition.onerror = function(event) {{
            console.error('Speech recognition error:', event.error);
            
            btn.style.background = 'rgba(255,255,255,0.2)';
            btn.style.transform = 'scale(1)';
            btn.style.boxShadow = 'none';
            isListening = false;
            
            switch(event.error) {{
                case 'not-allowed':
                    status.innerHTML = '🚫 Microphone access denied! Please allow and refresh.';
                    break;
                case 'no-speech':
                    status.innerHTML = '🔇 No speech heard. Click and try again!';
                    break;
                case 'audio-capture':
                    status.innerHTML = '🎤 No microphone found. Check connection.';
                    break;
                case 'network':
                    status.innerHTML = '🌐 Network error. Check internet connection.';
                    break;
                default:
                    status.innerHTML = `❌ Error: ${{event.error}}. Try again!`;
            }}
        }};

        voiceRecognition.onend = function() {{
            btn.style.background = 'rgba(255,255,255,0.2)';
            btn.style.transform = 'scale(1)';
            btn.style.boxShadow = 'none';
            isListening = false;
            
            if (status.innerHTML.includes('LISTENING')) {{
                status.innerHTML = '🔇 Finished listening. Click to try again!';
            }}
        }};

        // Start recognition
        try {{
            voiceRecognition.start();
        }} catch (error) {{
            console.error('Failed to start recognition:', error);
            status.innerHTML = '❌ Cannot start: ' + error.message;
            isListening = false;
        }}
    }});
    </script>
    """
    
    components.html(voice_html, height=350)

    # HANDLE VOICE INPUT FROM URL PARAMETERS
    voice_input = st.query_params.get("voice_input")
    voice_ts = st.query_params.get("voice_ts")
    
    if voice_input and voice_ts:
        # Clear parameters immediately
        st.query_params.clear()
        
        # BIG VOICE CONVERSATION DISPLAY
        st.markdown("## 🗣️ VOICE CONVERSATION RESULT")
        
        # User input display
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 25px; border-radius: 15px; margin: 20px 0;">
            <h2 style="margin: 0 0 10px 0;">🎙️ You said:</h2>
            <h3 style="margin: 0; font-style: italic;">"{voice_input}"</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Get AI response
        with st.spinner("🤖 Bob is generating response..."):
            bot_response = get_ai_response(voice_input)
        
        # Bot response display
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FF6B6B, #FF5722); color: white; padding: 25px; border-radius: 15px; margin: 20px 0;">
            <h2 style="margin: 0 0 15px 0;">🤖 Bob responds:</h2>
            <h3 style="margin: 0; line-height: 1.4;">{bot_response}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # TTS Playback
        clean_speech = bot_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '')
        
        tts_html = f"""
        <div style="text-align: center; margin: 30px 0;">
            <button onclick="playBobResponse()" style="
                padding: 20px 50px; 
                background: #9C27B0; 
                color: white; 
                border: none; 
                border-radius: 15px; 
                cursor: pointer; 
                font-size: 22px; 
                font-weight: bold;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                transition: all 0.3s;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                🔊 HEAR BOB'S VOICE
            </button>
            <div id="ttsStatus" style="margin-top: 15px; font-size: 18px; font-weight: bold;"></div>
        </div>
        
        <script>
        function playBobResponse() {{
            const text = `{clean_speech}`;
            const status = document.getElementById('ttsStatus');
            
            if ('speechSynthesis' in window) {{
                speechSynthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.85;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;
                
                utterance.onstart = () => {{
                    status.innerHTML = '🔊 Bob is speaking...';
                    status.style.color = '#9C27B0';
                }};
                
                utterance.onend = () => {{
                    status.innerHTML = '✅ Bob finished speaking!';
                    status.style.color = '#4CAF50';
                    setTimeout(() => status.innerHTML = '', 3000);
                }};
                
                speechSynthesis.speak(utterance);
            }} else {{
                status.innerHTML = '❌ Text-to-speech not available';
                status.style.color = '#f44336';
            }}
        }}
        
        // Auto-play after 1.5 seconds
        setTimeout(() => {{
            playBobResponse();
        }}, 1500);
        </script>
        """
        
        components.html(tts_html, height=120)
        
        # Add to session history
        st.session_state.conversation_history.append({
            "user": voice_input,
            "bot": bot_response,
            "timestamp": time.strftime("%H:%M:%S"),
            "type": "voice"
        })
        
        st.success("🎉 Voice conversation completed! Scroll down to speak again.")
        st.markdown("---")

    # Text Input Section
    st.markdown("### 💬 Text Input (Backup Method)")
    
    text_question = st.text_input("Type your question:", placeholder="Ask Bob anything...")
    if st.button("Ask Bob") and text_question:
        with st.spinner("🤖 Bob is thinking..."):
            response = get_ai_response(text_question)
            st.success(f"**Bob:** {response}")
            
            # Add to history
            st.session_state.conversation_history.append({
                "user": text_question,
                "bot": response,
                "timestamp": time.strftime("%H:%M:%S"),
                "type": "text"
            })

    # Quick Test Buttons
    st.markdown("---")
    st.markdown("### 🚨 Quick Tests")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧠 Test AI", key="test_ai"):
            response = get_ai_response("Say hello and that you are working")
            st.success(f"✅ {response}")
    
    with col2:
        if st.button("🎯 Test Math", key="test_math"):
            response = get_ai_response("What is 3 times 4?")
            st.success(f"✅ {response}")

    # Conversation History
    if st.session_state.conversation_history:
        st.markdown("---")
        st.markdown("### 💬 Recent Conversations")
        
        for conv in reversed(st.session_state.conversation_history[-3:]):
            icon = "🎙️" if conv.get('type') == 'voice' else "⌨️"
            with st.expander(f"{icon} {conv['timestamp']} - {conv['user'][:30]}..."):
                st.write(f"**You:** {conv['user']}")
                st.write(f"**Bob:** {conv.get('bot', conv.get('bob', 'No response'))}")

    # Debug Section
    st.markdown("---")
    with st.expander("🔍 Debug Info"):
        st.write("**Current URL Parameters:**")
        if st.query_params:
            for key, value in st.query_params.items():
                st.write(f"- {key}: {value}")
        else:
            st.write("- No URL parameters")
        
        st.write(f"**Total conversations:** {len(st.session_state.conversation_history)}")
        
        # Browser compatibility check
        browser_check = """
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <script>
            document.write('<p><strong>Protocol:</strong> ' + location.protocol + '</p>');
            document.write('<p><strong>Browser:</strong> ' + navigator.userAgent.split(')')[0] + ')</p>');
            document.write('<p><strong>Speech Recognition:</strong> ' + ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) + '</p>');
            document.write('<p><strong>Text-to-Speech:</strong> ' + ('speechSynthesis' in window) + '</p>');
            </script>
        </div>
        """
        components.html(browser_check, height=150)

if __name__ == "__main__":
    main()
