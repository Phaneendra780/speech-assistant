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
        return f"Sorry, I encountered an error: {str(e)}"

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'voice_input' not in st.session_state:
        st.session_state.voice_input = ""
    if 'last_processed' not in st.session_state:
        st.session_state.last_processed = ""

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

    # Header
    st.markdown("# 🤖 Bob - Voice Assistant")
    st.markdown("### Talk to Bob or type your questions")

    # Step 1: Quick API Test
    st.markdown("---")
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

    # Step 2: Voice Interface with Session State
    st.markdown("---")
    st.markdown("**🎙️ Step 2: Voice Interface**")

    # Display any pending voice input that needs processing
    if st.session_state.voice_input and st.session_state.voice_input != st.session_state.last_processed:
        st.markdown(f'<div class="voice-input">🎙️ <strong>You said:</strong> "{st.session_state.voice_input}"</div>', unsafe_allow_html=True)
        
        # Process the voice input
        with st.spinner("🤖 Bob is thinking..."):
            try:
                ai_response = get_ai_response(st.session_state.voice_input)
                
                # Display response
                st.markdown(f'<div class="voice-response">🤖 <strong>Bob says:</strong><br><br>{ai_response}</div>', unsafe_allow_html=True)
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "user": st.session_state.voice_input,
                    "bob": ai_response,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "type": "voice"
                })
                
                # Mark as processed
                st.session_state.last_processed = st.session_state.voice_input
                
                # Text-to-Speech
                import streamlit.components.v1 as components
                clean_text = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '')
                
                tts_html = f"""
                <div style="text-align: center; margin: 15px 0;">
                    <button onclick="playResponse()" style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                        🔊 Play Bob's Voice
                    </button>
                    <div id="playStatus" style="margin-top: 8px; font-size: 14px;"></div>
                </div>
                
                <script>
                function playResponse() {{
                    const text = `{clean_text}`;
                    if ('speechSynthesis' in window) {{
                        speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.rate = 0.85;
                        utterance.pitch = 1.0;
                        
                        utterance.onstart = () => document.getElementById('playStatus').innerHTML = '🔊 Playing...';
                        utterance.onend = () => {{
                            document.getElementById('playStatus').innerHTML = '✅ Finished';
                            setTimeout(() => document.getElementById('playStatus').innerHTML = '', 2000);
                        }};
                        
                        speechSynthesis.speak(utterance);
                    }}
                }}
                
                // Auto-play after a short delay
                setTimeout(playResponse, 800);
                </script>
                """
                
                components.html(tts_html, height=70)
                
            except Exception as e:
                st.error(f"❌ Error getting Bob's response: {e}")

    # Voice input interface - COMPLETELY NEW APPROACH
    import streamlit.components.v1 as components
    
    voice_component = f"""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #74b9ff, #0984e3); border-radius: 15px; margin: 20px 0;">
        <div style="color: white; font-size: 18px; margin-bottom: 20px;">
            🎙️ Click and speak to Bob
        </div>
        
        <button id="micBtn" style="
            font-size: 70px; 
            background: rgba(255,255,255,0.2); 
            border: 3px solid white; 
            border-radius: 50%; 
            cursor: pointer; 
            padding: 20px;
            transition: all 0.3s;
            color: white;
        ">🎤</button>
        
        <div id="micStatus" style="color: white; margin-top: 15px; font-size: 16px; min-height: 25px;">
            Ready to listen
        </div>
        
        <div id="transcript" style="
            background: rgba(255,255,255,0.9); 
            color: #333; 
            padding: 15px; 
            border-radius: 10px; 
            margin-top: 15px; 
            display: none;
            font-style: italic;
        "></div>
    </div>

    <script>
    let recognition;
    let listening = false;

    document.getElementById('micBtn').addEventListener('click', function() {{
        const btn = this;
        const status = document.getElementById('micStatus');
        const transcript = document.getElementById('transcript');
        
        if (listening) return;
        
        // Check browser support
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
            status.innerHTML = '❌ Speech not supported. Use Chrome!';
            return;
        }}

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = function() {{
            listening = true;
            btn.style.background = 'rgba(255,0,0,0.3)';
            btn.style.transform = 'scale(1.1)';
            status.innerHTML = '🎤 Listening... Speak now!';
            transcript.style.display = 'none';
        }};

        recognition.onresult = function(event) {{
            const spokenText = event.results[0][0].transcript.trim();
            
            transcript.innerHTML = `You said: "${{spokenText}}"`;
            transcript.style.display = 'block';
            status.innerHTML = '✅ Got it! Sending to Bob...';
            
            // Send to Streamlit using query params
            setTimeout(() => {{
                const url = new URL(window.location);
                url.searchParams.set('voice_query', spokenText);
                url.searchParams.set('ts', Date.now());
                window.location.href = url.toString();
            }}, 1500);
        }};

        recognition.onerror = function(event) {{
            status.innerHTML = `❌ Error: ${{event.error}}`;
            btn.style.background = 'rgba(255,255,255,0.2)';
            btn.style.transform = 'scale(1)';
            listening = false;
            
            // Show helpful error messages
            setTimeout(() => {{
                if (event.error === 'not-allowed') {{
                    status.innerHTML = '🔒 Please allow microphone access';
                }} else if (event.error === 'no-speech') {{
                    status.innerHTML = '🔇 No speech detected. Try again!';
                }} else {{
                    status.innerHTML = '⚠️ Try again or use text input';
                }}
            }}, 2000);
        }};

        recognition.onend = function() {{
            btn.style.background = 'rgba(255,255,255,0.2)';
            btn.style.transform = 'scale(1)';
            listening = false;
            
            if (status.innerHTML.includes('Listening')) {{
                status.innerHTML = '🔇 No speech heard. Try again!';
            }}
        }};

        try {{
            recognition.start();
        }} catch (error) {{
            status.innerHTML = '❌ Cannot start: ' + error.message;
        }}
    }});
    </script>
    """
    
    components.html(voice_component, height=250)

    # Process voice query from URL parameters - FIXED
    voice_query = st.query_params.get("voice_query")
    if voice_query:
        # Clear the URL parameter immediately to prevent reprocessing
        st.query_params.clear()
        
        st.markdown(f'<div class="voice-input">🎙️ <strong>Voice Input:</strong> "{voice_query}"</div>', unsafe_allow_html=True)
        
        # Process the query
        with st.spinner("🤖 Bob is processing your voice input..."):
            try:
                ai_response = get_ai_response(voice_query)
                
                # Show response
                st.markdown(f'<div class="voice-response">🤖 <strong>Bob responds:</strong><br><br>{ai_response}</div>', unsafe_allow_html=True)
                
                # Add to history
                st.session_state.conversation_history.append({
                    "user": voice_query,
                    "bob": ai_response,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "type": "voice"
                })
                
                # Auto-play response
                clean_response = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '')[:200]  # Limit length
                
                tts_html = f"""
                <div style="text-align: center; margin: 20px 0;">
                    <button onclick="speak()" style="padding: 15px 30px; background: #28a745; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 18px;">
                        🔊 Hear Bob's Response
                    </button>
                    <div id="ttsStatus" style="margin-top: 10px; font-size: 14px;"></div>
                </div>
                
                <script>
                function speak() {{
                    const text = `{clean_response}`;
                    if ('speechSynthesis' in window) {{
                        speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.rate = 0.9;
                        utterance.onstart = () => document.getElementById('ttsStatus').innerHTML = '🔊 Speaking...';
                        utterance.onend = () => document.getElementById('ttsStatus').innerHTML = '✅ Done';
                        speechSynthesis.speak(utterance);
                    }}
                }}
                
                // Auto-play
                setTimeout(speak, 1000);
                </script>
                """
                
                components.html(tts_html, height=80)
                
            except Exception as e:
                st.error(f"❌ Error processing voice input: {e}")
                st.write(f"Debug - Voice query was: {voice_query}")

    # Manual text input
    st.markdown("---")
    st.markdown("### 💬 Text Input (Always Works)")
    
    text_input = st.text_input("Type your question to Bob:", placeholder="Ask anything...")
    
    if st.button("Ask Bob", type="primary") and text_input:
        with st.spinner("🤖 Bob is thinking..."):
            ai_response = get_ai_response(text_input)
            st.session_state.conversation_history.append({
                "user": text_input,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S"),
                "type": "text"
            })
            st.success(f"**Bob:** {ai_response}")

    # Emergency test section
    st.markdown("---")
    st.markdown("### 🚨 Emergency Test Section")
    st.markdown("If voice isn't working, test these one by one:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧠 Test Bob's Brain", help="Test if AI agent works"):
            try:
                response = get_ai_response("Say the word 'hello' and nothing else")
                st.write(f"✅ **Response:** {response}")
            except Exception as e:
                st.error(f"❌ **AI Error:** {e}")
    
    with col2:
        if st.button("🎯 Test Simple Query", help="Test a basic question"):
            response = get_ai_response("What is 1 plus 1?")
            st.write(f"✅ **Bob:** {response}")

    # Show what's happening behind the scenes
    st.markdown("---")
    st.markdown("### 🔍 What's Happening")
    
    # Real-time status
    status_container = st.container()
    with status_container:
        st.write("**Current Status:**")
        
        # Check for voice input in URL
        current_voice = st.query_params.get("voice_query")
        if current_voice:
            st.info(f"🎙️ Found voice input: '{current_voice}'")
        else:
            st.info("🔍 Waiting for voice input...")
        
        # Show session state
        st.write("**Session Info:**")
        st.write(f"- Last voice input: {st.session_state.voice_input or 'None'}")
        st.write(f"- Last processed: {st.session_state.last_processed or 'None'}")
        st.write(f"- Total conversations: {len(st.session_state.conversation_history)}")

    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.markdown("### 💬 Recent Conversations")
        
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-3:])):
            icon = "🎙️" if conv.get('type') == 'voice' else "⌨️"
            with st.expander(f"{icon} {conv['timestamp']} - {conv['user'][:30]}..."):
                st.write(f"**You:** {conv['user']}")
                st.write(f"**Bob:** {conv['bob']}")
        
        if st.button("🗑️ Clear All History"):
            st.session_state.conversation_history = []
            st.session_state.voice_input = ""
            st.session_state.last_processed = ""
            st.rerun()

    # Troubleshooting guide
    st.markdown("---")
    st.markdown("### 🛠️ Troubleshooting")
    
    with st.expander("Voice not working? Try these steps:"):
        st.markdown("""
        **1. Browser Check:**
        - ✅ Use Chrome (best support)
        - ✅ Use Edge (good support)
        - ⚠️ Safari (limited support)
        - ❌ Firefox (not supported)
        
        **2. Permissions:**
        - Allow microphone access when prompted
        - Check browser settings for microphone permissions
        
        **3. Environment:**
        - Must be HTTPS or localhost
        - Good internet connection required
        
        **4. Speaking Tips:**
        - Speak clearly and loudly
        - Wait for the red microphone before speaking
        - Keep sentences short and clear
        
        **5. If still not working:**
        - Refresh the page
        - Try incognito/private window
        - Use text input as backup
        """)

if __name__ == "__main__":
    main()
