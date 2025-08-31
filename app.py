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
    if 'processing_voice' not in st.session_state:
        st.session_state.processing_voice = False

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

    # FIXED: Process voice query from URL parameters FIRST
    voice_query = st.query_params.get("voice_query")
    timestamp = st.query_params.get("ts")
    
    # Create a unique key for this voice input to prevent reprocessing
    voice_key = f"{voice_query}_{timestamp}" if voice_query and timestamp else None
    
    if voice_query and voice_key and voice_key not in st.session_state.get('processed_queries', set()):
        # Mark as processing to prevent duplicates
        if 'processed_queries' not in st.session_state:
            st.session_state.processed_queries = set()
        st.session_state.processed_queries.add(voice_key)
        
        # Clear URL parameters immediately
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
                
                # Auto-play TTS
                import streamlit.components.v1 as components
                clean_text = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '')[:300]
                
                tts_html = f"""
                <div style="text-align: center; margin: 20px 0;">
                    <button onclick="playResponse()" style="padding: 15px 30px; background: #28a745; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 18px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                        🔊 Play Bob's Response
                    </button>
                    <div id="playStatus" style="margin-top: 10px; font-size: 14px;"></div>
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
                    }} else {{
                        document.getElementById('playStatus').innerHTML = '❌ TTS not supported';
                    }}
                }}
                
                // Auto-play after delay
                setTimeout(playResponse, 1000);
                </script>
                """
                
                components.html(tts_html, height=100)
                
            except Exception as e:
                st.error(f"❌ Error processing voice input: {e}")

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

    # Step 2: FIXED Voice Interface
    st.markdown("---")
    st.markdown("**🎙️ Step 2: Voice Interface**")
    
    # Import components first
    import streamlit.components.v1 as components
    
    # Check HTTPS status and show warning if needed
    https_check = """
    <script>
    if (location.protocol !== 'https:' && !location.hostname.includes('localhost')) {
        document.write('<div style="background: #ff6b6b; color: white; padding: 15px; border-radius: 10px; margin: 20px 0; text-align: center;"><strong>⚠️ HTTPS Required!</strong><br>Voice input needs HTTPS to work. Deploy to Streamlit Cloud or use localhost for testing.</div>');
    } else {
        document.write('<div style="background: #51cf66; color: white; padding: 10px; border-radius: 8px; margin: 10px 0; text-align: center;">✅ HTTPS Enabled - Voice should work!</div>');
    }
    </script>
    """
    components.html(https_check, height=80)

    # Display voice conversation area FIRST
    voice_container = st.container()
    
    # FIXED: Better voice component with proper error handling
    voice_component = f"""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #74b9ff, #0984e3); border-radius: 15px; margin: 20px 0;">
        <div style="color: white; font-size: 18px; margin-bottom: 20px;">
            🎙️ Click the microphone and speak clearly
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
            outline: none;
        ">🎤</button>
        
        <div id="micStatus" style="color: white; margin-top: 15px; font-size: 16px; min-height: 25px;">
            Click microphone to start
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
    let processed = new Set();

    document.getElementById('micBtn').addEventListener('click', function() {{
        const btn = this;
        const status = document.getElementById('micStatus');
        const transcript = document.getElementById('transcript');
        
        if (listening) {{
            status.innerHTML = '⏸️ Already listening...';
            return;
        }}
        
        // Check browser support
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
            status.innerHTML = '❌ Speech recognition not supported. Please use Chrome or Edge.';
            return;
        }}

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        // Configure recognition
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onstart = function() {{
            listening = true;
            btn.style.background = 'rgba(255,0,0,0.4)';
            btn.style.transform = 'scale(1.15)';
            btn.style.boxShadow = '0 0 20px rgba(255,0,0,0.5)';
            status.innerHTML = '🎤 LISTENING... Speak now!';
            transcript.style.display = 'none';
        }};

        recognition.onresult = function(event) {{
            const spokenText = event.results[0][0].transcript.trim();
            const confidence = event.results[0][0].confidence;
            
            console.log('Speech result:', spokenText, 'Confidence:', confidence);
            
            if (spokenText.length > 0) {{
                transcript.innerHTML = `You said: "${{spokenText}}" (confidence: ${{(confidence * 100).toFixed(0)}}%)`;
                transcript.style.display = 'block';
                status.innerHTML = '✅ Got it! Sending to Bob...';
                
                // Generate unique timestamp
                const timestamp = Date.now();
                const queryKey = `${{spokenText}}_${{timestamp}}`;
                
                // Avoid duplicate processing
                if (!processed.has(queryKey)) {{
                    processed.add(queryKey);
                    
                    // Send to Streamlit with unique timestamp
                    setTimeout(() => {{
                        const url = new URL(window.location);
                        url.searchParams.set('voice_query', spokenText);
                        url.searchParams.set('ts', timestamp);
                        window.location.href = url.toString();
                    }}, 1000);
                }} else {{
                    status.innerHTML = '⚠️ Already processing this input...';
                }}
            }} else {{
                status.innerHTML = '🔇 No text detected. Try again!';
            }}
        }};

        recognition.onerror = function(event) {{
            console.error('Speech recognition error:', event.error);
            
            btn.style.background = 'rgba(255,255,255,0.2)';
            btn.style.transform = 'scale(1)';
            btn.style.boxShadow = 'none';
            listening = false;
            
            let errorMsg = '❌ ';
            switch(event.error) {{
                case 'not-allowed':
                    errorMsg += 'Microphone access denied. Please allow microphone access and try again.';
                    break;
                case 'no-speech':
                    errorMsg += 'No speech detected. Click again and speak clearly.';
                    break;
                case 'audio-capture':
                    errorMsg += 'No microphone found. Check your microphone connection.';
                    break;
                case 'network':
                    errorMsg += 'Network error. Check your internet connection.';
                    break;
                case 'aborted':
                    errorMsg += 'Speech recognition aborted.';
                    break;
                default:
                    errorMsg += `Error (${{event.error}}). Try again or use text input.`;
            }}
            
            status.innerHTML = errorMsg;
            
            // Reset status after delay
            setTimeout(() => {{
                status.innerHTML = 'Click microphone to try again';
            }}, 4000);
        }};

        recognition.onend = function() {{
            btn.style.background = 'rgba(255,255,255,0.2)';
            btn.style.transform = 'scale(1)';
            btn.style.boxShadow = 'none';
            listening = false;
            
            // Only show "no speech" if we didn't get a result
            if (status.innerHTML.includes('LISTENING')) {{
                status.innerHTML = '🔇 No speech detected. Try again!';
                setTimeout(() => {{
                    status.innerHTML = 'Click microphone to try again';
                }}, 3000);
            }}
        }};

        try {{
            recognition.start();
        }} catch (error) {{
            console.error('Failed to start recognition:', error);
            status.innerHTML = '❌ Cannot start speech recognition: ' + error.message;
            listening = false;
        }}
    }});

    // Add keyboard shortcut (spacebar to start recording)
    document.addEventListener('keydown', function(event) {{
        if (event.code === 'Space' && !listening && event.target.tagName !== 'INPUT') {{
            event.preventDefault();
            document.getElementById('micBtn').click();
        }}
    }});
    </script>
    """
    
    components.html(voice_component, height=280)

    # VOICE OUTPUT DISPLAY SECTION
    st.markdown("### 🎯 Voice Conversation")
    
    # Show the latest voice conversation if any
    if st.session_state.conversation_history:
        latest_voice_convs = [conv for conv in reversed(st.session_state.conversation_history) 
                             if conv.get('type') in ['voice', 'manual_voice']][:1]
        
        if latest_voice_convs:
            conv = latest_voice_convs[0]
            st.markdown(f'<div class="voice-input">🎙️ <strong>You said:</strong> "{conv["user"]}"</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="voice-response">🤖 <strong>Bob replied:</strong><br><br>{conv["bob"]}</div>', unsafe_allow_html=True)
            
            # Add TTS for the latest voice response
            clean_text = conv["bob"].replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '')[:300]
            
            tts_html = f"""
            <div style="text-align: center; margin: 20px 0;">
                <button onclick="playLatestResponse()" style="padding: 15px 30px; background: #28a745; color: white; border: none; border-radius: 10px; cursor: pointer; font-size: 18px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    🔊 Play Bob's Latest Response
                </button>
                <div id="playLatestStatus" style="margin-top: 10px; font-size: 14px;"></div>
            </div>
            
            <script>
            function playLatestResponse() {{
                const text = `{clean_text}`;
                if ('speechSynthesis' in window) {{
                    speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.rate = 0.85;
                    utterance.pitch = 1.0;
                    
                    utterance.onstart = () => document.getElementById('playLatestStatus').innerHTML = '🔊 Playing...';
                    utterance.onend = () => {{
                        document.getElementById('playLatestStatus').innerHTML = '✅ Finished';
                        setTimeout(() => document.getElementById('playLatestStatus').innerHTML = '', 2000);
                    }};
                    
                    speechSynthesis.speak(utterance);
                }} else {{
                    document.getElementById('playLatestStatus').innerHTML = '❌ TTS not supported';
                }}
            }}
            </script>
            """
            
            components.html(tts_html, height=100)
        else:
            st.info("🎙️ No voice conversations yet. Click the microphone above to start!")
    else:
        st.info("💬 Start a conversation with Bob using voice or text input above!")

    # Manual text input
    st.markdown("---")
    st.markdown("### 💬 Text Input (Always Works)")
    
    text_input = st.text_input("Type your question to Bob:", placeholder="Ask anything...", key="text_input")
    
    if st.button("Ask Bob", type="primary") and text_input:
        with st.spinner("🤖 Bob is thinking..."):
            ai_response = get_ai_response(text_input)
            st.session_state.conversation_history.append({
                "user": text_input,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S"),
                "type": "text"
            })
            
            # Show response with TTS option
            st.markdown(f'<div class="voice-response">🤖 <strong>Bob:</strong><br><br>{ai_response}</div>', unsafe_allow_html=True)
            
            # Add TTS for text responses too
            clean_text = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '')[:300]
            
            tts_html = f"""
            <div style="text-align: center; margin: 15px 0;">
                <button onclick="speakText()" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    🔊 Hear Bob's Response
                </button>
                <div id="ttsTextStatus" style="margin-top: 8px; font-size: 12px;"></div>
            </div>
            
            <script>
            function speakText() {{
                const text = `{clean_text}`;
                if ('speechSynthesis' in window) {{
                    speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.rate = 0.9;
                    utterance.onstart = () => document.getElementById('ttsTextStatus').innerHTML = '🔊 Speaking...';
                    utterance.onend = () => document.getElementById('ttsTextStatus').innerHTML = '✅ Done';
                    speechSynthesis.speak(utterance);
                }}
            }}
            </script>
            """
            
            components.html(tts_html, height=60)

    # Emergency test section
    st.markdown("---")
    st.markdown("### 🚨 Emergency Test Section")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧠 Test Bob's Brain", key="test_brain"):
            try:
                response = get_ai_response("Say 'Hello, I am working perfectly!' and nothing else")
                st.success(f"✅ **Bob:** {response}")
            except Exception as e:
                st.error(f"❌ **AI Error:** {e}")
    
    with col2:
        if st.button("🎯 Test Simple Query", key="test_simple"):
            response = get_ai_response("What is 5 times 5?")
            st.success(f"✅ **Bob:** {response}")

    # Debug information
    st.markdown("---")
    st.markdown("### 🔍 Debug Information")
    
    with st.expander("Current Status & Debug Info"):
        st.write("**URL Parameters:**")
        if st.query_params:
            for key, value in st.query_params.items():
                st.write(f"- {key}: {value}")
        else:
            st.write("- No URL parameters")
        
        st.write("**Session State:**")
        st.write(f"- Processed queries: {len(st.session_state.get('processed_queries', set()))}")
        st.write(f"- Total conversations: {len(st.session_state.conversation_history)}")
        
        st.write("**Browser Info:**")
        check_browser = """
        <script>
        document.write('<p>User Agent: ' + navigator.userAgent + '</p>');
        document.write('<p>HTTPS: ' + (location.protocol === 'https:') + '</p>');
        document.write('<p>Speech Recognition: ' + ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) + '</p>');
        </script>
        """
        components.html(check_browser, height=100)

    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.markdown("### 💬 Recent Conversations")
        
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:])):
            icon = "🎙️" if conv.get('type') == 'voice' else "⌨️"
            with st.expander(f"{icon} {conv['timestamp']} - {conv['user'][:40]}..."):
                st.write(f"**You:** {conv['user']}")
                st.write(f"**Bob:** {conv['bob']}")
        
        if st.button("🗑️ Clear All History", key="clear_history"):
            st.session_state.conversation_history = []
            if 'processed_queries' in st.session_state:
                st.session_state.processed_queries.clear()
            st.rerun()

    # Enhanced troubleshooting guide
    st.markdown("---")
    st.markdown("### 🛠️ Troubleshooting")
    
    with st.expander("Voice not working? Try these solutions:"):
        st.markdown("""
        **🔧 Common Issues & Fixes:**
        
        **1. Browser Compatibility:**
        - ✅ **Chrome** (Recommended - best support)
        - ✅ **Edge** (Good support) 
        - ⚠️ **Safari** (Limited support, may not work)
        - ❌ **Firefox** (No support for Web Speech API)
        
        **2. Streamlit Cloud Specific Issues:**
        - Voice input requires **HTTPS** (Streamlit Cloud provides this)
        - Check that your deployed app URL starts with `https://`
        - Clear browser cache if voice was working before
        
        **3. Microphone Permissions:**
        - Browser will ask for microphone permission - click "Allow"
        - If denied, click the lock/microphone icon in address bar
        - In Chrome: Settings > Privacy > Site Settings > Microphone
        
        **4. Environment Requirements:**
        - Must be HTTPS (✅ Streamlit Cloud)
        - Stable internet connection required
        - No ad blockers blocking microphone access
        
        **5. Speaking Guidelines:**
        - Wait for "LISTENING..." message before speaking
        - Speak clearly and at normal volume
        - Keep sentences under 10 seconds
        - Avoid background noise
        
        **6. If Voice Still Fails:**
        - Try refreshing the page
        - Test in incognito/private window
        - Check browser console for errors (F12)
        - Use text input as reliable backup
        - Try a different browser
        """)

    # Manual voice test
    st.markdown("---")
    st.markdown("### 🎯 Manual Voice Test")
    
    manual_voice = st.text_input("Simulate voice input (for testing):", placeholder="Type what you would say...")
    if st.button("Process as Voice Input", key="manual_voice") and manual_voice:
        # Simulate voice processing
        st.markdown(f'<div class="voice-input">🎙️ <strong>Simulated Voice:</strong> "{manual_voice}"</div>', unsafe_allow_html=True)
        
        with st.spinner("🤖 Bob is responding..."):
            ai_response = get_ai_response(manual_voice)
            st.markdown(f'<div class="voice-response">🤖 <strong>Bob:</strong><br><br>{ai_response}</div>', unsafe_allow_html=True)
            
            st.session_state.conversation_history.append({
                "user": manual_voice,
                "bob": ai_response,
                "timestamp": time.strftime("%H:%M:%S"),
                "type": "manual_voice"
            })

if __name__ == "__main__":
    main()
