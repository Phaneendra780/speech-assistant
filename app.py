import streamlit as st
import speech_recognition as sr
import pyttsx3
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import threading
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

@st.cache_resource
def get_tts_engine():
    """Initialize text-to-speech engine."""
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        return engine
    except Exception as e:
        st.error(f"❌ Error initializing TTS engine: {e}")
        return None

def listen_for_wake_word():
    """Listen for the wake word 'Hey Bob'."""
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        
        with microphone as source:
            st.info("🎤 Listening for 'Hey Bob'...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
        
        text = recognizer.recognize_google(audio).lower()
        return "hey bob" in text or "hi bob" in text
    except sr.WaitTimeoutError:
        return False
    except sr.UnknownValueError:
        return False
    except sr.RequestError as e:
        st.error(f"❌ Speech recognition error: {e}")
        return False

def listen_for_query():
    """Listen for user query after wake word is detected."""
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        with microphone as source:
            st.info("🎤 I'm listening... What can I help you with?")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
        
        text = recognizer.recognize_google(audio)
        return text
    except sr.WaitTimeoutError:
        st.warning("⏰ Timeout - I didn't hear anything.")
        return None
    except sr.UnknownValueError:
        st.warning("🤷 Sorry, I couldn't understand what you said.")
        return None
    except sr.RequestError as e:
        st.error(f"❌ Speech recognition error: {e}")
        return None

def speak_response(text):
    """Convert text to speech."""
    try:
        engine = get_tts_engine()
        if engine:
            # Clean the text for better speech
            clean_text = text.replace('*', '').replace('#', '').replace('`', '')
            engine.say(clean_text)
            engine.runAndWait()
    except Exception as e:
        st.error(f"❌ Error with text-to-speech: {e}")

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
    if 'is_listening' not in st.session_state:
        st.session_state.is_listening = False
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'wake_word_detected' not in st.session_state:
        st.session_state.wake_word_detected = False

    # Custom CSS for styling
    st.markdown("""
    <style>
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
    }
    .microphone-button {
        font-size: 120px;
        border: none;
        background: none;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .microphone-button:hover {
        transform: scale(1.1);
    }
    .listening {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    st.title("🎤 Bob - Voice Assistant")
    st.markdown("*Say 'Hey Bob' to wake me up, then ask your question*")
    
    # Microphone button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Create a large microphone icon
        if st.session_state.is_listening:
            st.markdown("🎤", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: red;'>🔴 Listening...</p>", unsafe_allow_html=True)
        else:
            if st.button("🎤", help="Click to start listening for 'Hey Bob'"):
                st.session_state.is_listening = True
                st.rerun()
    
    # Voice interaction logic
    if st.session_state.is_listening:
        # Listen for wake word
        if not st.session_state.wake_word_detected:
            if listen_for_wake_word():
                st.session_state.wake_word_detected = True
                st.success("👋 Hello! I heard you say 'Hey Bob'. What can I help you with?")
                speak_response("Hello! What can I help you with?")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.is_listening = False
                st.info("💭 I didn't hear 'Hey Bob'. Click the microphone to try again.")
                st.rerun()
        
        # Listen for query after wake word
        elif st.session_state.wake_word_detected:
            user_query = listen_for_query()
            
            if user_query:
                st.write(f"**You said:** {user_query}")
                
                # Get AI response
                ai_response = get_ai_response(user_query)
                
                # Display and speak response
                st.write(f"**Bob says:** {ai_response}")
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "user": user_query,
                    "bob": ai_response,
                    "timestamp": time.strftime("%H:%M:%S")
                })
                
                # Speak the response
                speak_response(ai_response)
                
                # Reset for next interaction
                st.session_state.is_listening = False
                st.session_state.wake_word_detected = False
                
                st.info("💭 Say 'Hey Bob' again or click the microphone for another question.")
                
            else:
                st.session_state.is_listening = False
                st.session_state.wake_word_detected = False
                st.info("💭 Ready for next interaction. Say 'Hey Bob' or click the microphone.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
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
    
    1. **Click the microphone** 🎤 or say **"Hey Bob"**
    2. **Wait** for Bob to acknowledge you
    3. **Ask your question** clearly
    4. **Listen** to Bob's response
    
    **Example questions:**
    - "What's the weather like today?"
    - "Tell me about aspirin"
    - "What's 25 times 47?"
    - "Latest news about technology"
    """)
    
    # Clear history button
    if st.session_state.conversation_history:
        if st.button("🗑️ Clear Conversation History"):
            st.session_state.conversation_history = []
            st.rerun()

if __name__ == "__main__":
    main()
