#!/usr/bin/env python3
"""
SevaSetu - Multilingual Government Scheme Assistant
Streamlit Web Application
"""

import streamlit as st
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from rag_system import RAGSystem, LANGUAGE_NAMES

# Page configuration
st.set_page_config(
    page_title="SevaSetu - Government Scheme Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .response-box {
        background-color: #f0f8ff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #FF6B35;
        margin: 1rem 0;
    }
    .source-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF6B35;
        color: white;
        font-size: 1.1rem;
        padding: 0.75rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_system' not in st.session_state:
    with st.spinner("🔄 Loading SevaSetu system..."):
        try:
            st.session_state.rag_system = RAGSystem()
            st.session_state.initialized = True
        except Exception as e:
            st.error(f"❌ Failed to initialize system: {e}")
            st.info("Please run: `python scripts/ingest_to_vectorstore.py`")
            st.session_state.initialized = False

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'query_count' not in st.session_state:
    st.session_state.query_count = 0

# Header
st.markdown('<h1 class="main-header">🏛️ SevaSetu</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">सरकारी योजना सहायक | Government Scheme Assistant</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Language selection
    language = st.selectbox(
        "🌐 Select Language / भाषा चुनें",
        options=list(LANGUAGE_NAMES.keys()),
        format_func=lambda x: f"{LANGUAGE_NAMES[x]} ({x.upper()})",
        index=0  # Default to Hindi
    )
    
    st.markdown("---")
    
    # Information
    st.header("ℹ️ About")
    st.info("""
    **SevaSetu** helps you understand government schemes:
    
    📋 **Available Schemes:**
    - PM-KISAN
    - MGNREGA
    - PMAY-G (Housing)
    - Ayushman Bharat
    
    🎯 **Ask about:**
    - Eligibility criteria
    - Financial benefits
    - Application process
    - Required documents
    """)
    
    st.markdown("---")
    
    # Statistics
    if st.session_state.initialized:
        st.header("📊 Statistics")
        st.metric("Queries Asked", st.session_state.query_count)
        st.metric("Documents Loaded", len(st.session_state.rag_system.vector_store.documents))
    
    st.markdown("---")
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation"):
        st.session_state.conversation_history = []
        st.session_state.query_count = 0
        st.rerun()

# Main content
if not st.session_state.initialized:
    st.error("❌ System not initialized. Please check the error message above.")
    st.stop()

# Example questions
st.subheader("💡 Example Questions")
col1, col2 = st.columns(2)

with col1:
    if st.button("📝 PM-KISAN eligibility?"):
        st.session_state.example_query = "What is the eligibility criteria for PM-KISAN scheme?"
    if st.button("🏠 PMAY-G housing benefit?"):
        st.session_state.example_query = "What is the financial assistance under PMAY-G?"

with col2:
    if st.button("💼 MGNREGA employment days?"):
        st.session_state.example_query = "How many days of employment does MGNREGA provide?"
    if st.button("🏥 Ayushman Bharat coverage?"):
        st.session_state.example_query = "What is the health cover amount in Ayushman Bharat?"

st.markdown("---")

# Query input
st.subheader("❓ Ask Your Question")

# Use example query if set
default_query = st.session_state.get('example_query', '')
if default_query:
    query = st.text_area(
        "Type your question here:",
        value=default_query,
        height=100,
        placeholder="Example: What are the benefits of PM-KISAN scheme?"
    )
    st.session_state.example_query = None  # Clear after use
else:
    query = st.text_area(
        "Type your question here:",
        height=100,
        placeholder="Example: What are the benefits of PM-KISAN scheme?"
    )

# Submit button
if st.button("🔍 Get Answer"):
    if not query.strip():
        st.warning("⚠️ Please enter a question.")
    else:
        with st.spinner("🤔 Thinking..."):
            try:
                # Query the RAG system
                result = st.session_state.rag_system.query(
                    question=query,
                    language=language,
                    conversation_history=st.session_state.conversation_history
                )
                
                # Update conversation history
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": query
                })
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": result['response']
                })
                
                # Increment query count
                st.session_state.query_count += 1
                
                # Display response
                st.markdown("### 💬 Response")
                st.markdown(f'<div class="response-box">{result["response"]}</div>', unsafe_allow_html=True)
                
                # Display sources
                if result['sources']:
                    st.markdown("### 📚 Sources")
                    sources_text = " • ".join(result['sources'])
                    st.markdown(f'<div class="source-box">📋 {sources_text}</div>', unsafe_allow_html=True)
                
                # Display metadata
                with st.expander("🔍 View Details"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Documents Retrieved", result['retrieved_docs'])
                    with col2:
                        st.metric("Language", LANGUAGE_NAMES[result['language']])
                    with col3:
                        st.metric("Model", "Claude 3.5 Sonnet")
                    
                    # Show retrieved documents
                    if result.get('documents'):
                        st.markdown("**Retrieved Document Chunks:**")
                        for i, doc in enumerate(result['documents'][:3], 1):
                            st.markdown(f"**{i}. {doc['metadata']['scheme_name']}** (Similarity: {doc['similarity']:.2%})")
                            st.text(doc['text'][:200] + "...")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("Please ensure the vector store is initialized and AWS credentials are configured.")

# Conversation history
if st.session_state.conversation_history:
    st.markdown("---")
    st.subheader("💬 Conversation History")
    
    for i in range(0, len(st.session_state.conversation_history), 2):
        if i + 1 < len(st.session_state.conversation_history):
            user_msg = st.session_state.conversation_history[i]
            assistant_msg = st.session_state.conversation_history[i + 1]
            
            with st.expander(f"Q: {user_msg['content'][:50]}..."):
                st.markdown(f"**You:** {user_msg['content']}")
                st.markdown(f"**SevaSetu:** {assistant_msg['content']}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏛️ SevaSetu - Empowering Rural India with Government Scheme Information</p>
    <p style='font-size: 0.9rem;'>Built with ❤️ for AI for Bharat Hackathon 2026</p>
</div>
""", unsafe_allow_html=True)
