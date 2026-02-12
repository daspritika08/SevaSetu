# Design Document: SevaSetu RAG Application

## Overview

SevaSetu is a multilingual voice-enabled web application that helps rural users access government scheme information through natural language queries. The system combines speech recognition, RAG-based information retrieval, and text-to-speech synthesis to provide an accessible interface for users with limited literacy or technical experience.

### Key Design Principles

1. **Accessibility First**: Voice-driven interface with minimal text interaction required
2. **Simplicity**: Clean, uncluttered UI with large interactive elements
3. **Accuracy**: RAG pipeline ensures responses are grounded in official documents
4. **Multilingual**: Native support for Hindi/Tamil/Telugu/Odia with translation fallback for dialects
5. **Resilience**: Graceful error handling and clear user feedback

### Technology Stack

- **Frontend**: Streamlit web application
- **Voice Capture**: WebRTC for browser-based audio recording
- **Speech-to-Text**: Amazon Transcribe or Bedrock Speech
- **LLM**: Amazon Bedrock (Claude 3.5 Sonnet)
- **RAG**: Amazon Bedrock Knowledge Bases
- **Document Storage**: Amazon S3
- **Translation**: IndicTrans2 for dialect support
- **Text-to-Speech**: Amazon Polly or Bedrock Speech

## Architecture

### System Architecture

```
──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Services Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Bedrock  │  │ Bedrock  │  │ ┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Web App                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Language   │  │    Voice     │  │   Response   │      │
│  │   Selector   │  │   Recorder   │  │   Display    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Query Processing Pipeline                  │   │
│  │  Audio → STT → Translation → RAG → LLM → TTS        │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────   S3    │  │  Polly   │   │
│  │   LLM    │  │    KB    │  │ Document │  │   TTS    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  IndicTrans2 Service                         │
│              (Dialect Translation Layer)                     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input Flow**:
   - User selects language (Hindi/Tamil)
   - User records voice query via WebRTC
   - Audio sent to Speech-to-Text service
   - Text query extracted in source language

2. **Query Processing Flow**:
   - Detect if language is natively supported by Bedrock
   - If dialect detected, translate to English via IndicTrans2
   - Query sent to Bedrock Knowledge Base for retrieval
   - Top-k relevant document chunks retrieved
   - Chunks + query sent to Claude 3.5 Sonnet for response generation

3. **Response Generation Flow**:
   - Claude generates simplified response with source citations
   - If translation was used, translate response back to source language
   - Convert text response to speech via TTS
   - Return both text and audio to frontend

4. **Display Flow**:
   - Display text response in UI
   - Auto-play audio response
   - Show source document references
   - Provide playback controls

## Components and Interfaces

### 1. Voice Interface Component

**Responsibilities**:
- Render Streamlit UI
- Capture audio via WebRTC
- Display responses (text + audio player)
- Handle language selection
- Show loading states and errors

**Key Functions**:
```python
class VoiceInterface:
    def render_language_selector() -> str:
        """Display language selection dropdown"""
        
    def render_voice_recorder() -> bytes:
        """Capture audio using WebRTC, return audio bytes"""
        
    def display_response(text: str, audio: bytes, sources: List[str]):
        """Show text response, play audio, display sources"""
        
    def show_loading_indicator(message: str):
        """Display processing status"""
        
    def show_error(error_message: str):
        """Display user-friendly error message"""
```

### 2. Speech-to-Text Service

**Responsibilities**:
- Convert audio bytes to text
- Detect language from audio
- Handle audio format conversion

**Key Functions**:
```python
class SpeechToTextService:
    def transcribe(audio_bytes: bytes, language_hint: str) -> TranscriptionResult:
        """
        Convert audio to text
        Returns: TranscriptionResult(text, detected_language, confidence)
        """
        
    def detect_language(audio_bytes: bytes) -> str:
        """Detect language from audio"""
```

### 3. Translation Service

**Responsibilities**:
- Translate queries from dialects to English
- Translate responses from English back to source language
- Determine if translation is needed

**Key Functions**:
```python
class TranslationService:
    def needs_translation(text: str, language: str) -> bool:
        """Check if Bedrock natively supports this language/dialect"""
        
    def translate_to_english(text: str, source_language: str) -> str:
        """Translate query to English using IndicTrans2"""
        
    def translate_from_english(text: str, target_language: str) -> str:
        """Translate response back to user's language"""
```

### 4. RAG Pipeline Component

**Responsibilities**:
- Query Bedrock Knowledge Base
- Retrieve relevant document chunks
- Rank and filter results
- Format context for LLM

**Key Functions**:
```python
class RAGPipeline:
    def retrieve(query: str, top_k: int = 5) -> List[DocumentChunk]:
        """
        Retrieve relevant chunks from Knowledge Base
        Returns: List of DocumentChunk(text, source, score)
        """
        
    def format_context(chunks: List[DocumentChunk]) -> str:
        """Format retrieved chunks as context for LLM"""
```

### 5. Response Generator

**Responsibilities**:
- Call Bedrock Claude 3.5 Sonnet
- Generate simplified responses
- Extract source citations
- Handle multi-scheme responses

**Key Functions**:
```python
class ResponseGenerator:
    def generate(query: str, context: str, language: str) -> Response:
        """
        Generate simplified response using Claude
        Returns: Response(text, sources, confidence)
        """
        
    def simplify_language(text: str) -> str:
        """Ensure response uses simple vocabulary"""
        
    def extract_sources(response: str, chunks: List[DocumentChunk]) -> List[str]:
        """Extract which sources were used in response"""
```

### 6. Text-to-Speech Service

**Responsibilities**:
- Convert text to speech
- Support Hindi/Tamil voices
- Generate audio in appropriate format

**Key Functions**:
```python
class TextToSpeechService:
    def synthesize(text: str, language: str) -> bytes:
        """
        Convert text to speech audio
        Returns: Audio bytes in MP3 format
        """
        
    def get_voice_for_language(language: str) -> str:
        """Select appropriate voice ID for language"""
```

### 7. Document Manager

**Responsibilities**:
- Upload PDFs to S3
- Trigger Knowledge Base indexing
- Manage document metadata
- Handle document versioning

**Key Functions**:
```python
class DocumentManager:
    def upload_document(pdf_path: str, metadata: dict) -> str:
        """Upload PDF to S3, return document ID"""
        
    def trigger_kb_sync() -> bool:
        """Trigger Knowledge Base to re-index documents"""
        
    def list_documents() -> List[DocumentMetadata]:
        """List all documents in Knowledge Base"""
```

### 8. Query Orchestrator

**Responsibilities**:
- Coordinate the entire query processing pipeline
- Handle errors at each stage
- Manage conversation context
- Track processing time

**Key Functions**:
```python
class QueryOrchestrator:
    def process_query(audio: bytes, language: str, session_id: str) -> QueryResult:
        """
        Main orchestration function
        Steps:
        1. Speech-to-text
        2. Translation (if needed)
        3. RAG retrieval
        4. Response generation
        5. Translation back (if needed)
        6. Text-to-speech
        Returns: QueryResult(text, audio, sources, processing_time)
        """
        
    def handle_error(error: Exception, stage: str) -> ErrorResponse:
        """Convert technical errors to user-friendly messages"""
```

## Data Models

### TranscriptionResult
```python
@dataclass
class TranscriptionResult:
    text: str
    detected_language: str
    confidence: float
```

### DocumentChunk
```python
@dataclass
class DocumentChunk:
    text: str
    source_document: str
    scheme_name: str
    relevance_score: float
    metadata: dict
```

### Response
```python
@dataclass
class Response:
    text: str
    sources: List[str]
    confidence: float
    scheme_names: List[str]
```

### QueryResult
```python
@dataclass
class QueryResult:
    text_response: str
    audio_response: bytes
    sources: List[str]
    processing_time: float
    error: Optional[str] = None
```

### DocumentMetadata
```python
@dataclass
class DocumentMetadata:
    document_id: str
    filename: str
    scheme_name: str
    language: str
    upload_date: datetime
    version: str
```

### SessionContext
```python
@dataclass
class SessionContext:
    session_id: str
    language: str
    conversation_history: List[dict]
    last_query_time: datetime
```


## AWS Bedrock Knowledge Base Configuration

### Knowledge Base Setup

1. **Vector Store**: Use Amazon OpenSearch Serverless or Amazon Aurora PostgreSQL with pgvector
2. **Embedding Model**: Amazon Titan Embeddings G1 - Text
3. **Chunking Strategy**:
   - Chunk size: 500 tokens
   - Overlap: 50 tokens
   - Preserve sentence boundaries
4. **Metadata Fields**:
   - scheme_name
   - document_type (eligibility, benefits, application_process)
   - language
   - last_updated

### S3 Document Structure

```
s3://sevasetu-documents/
├── pm-kisan/
│   ├── hindi/
│   │   ├── eligibility.pdf
│   │   ├── benefits.pdf
│   │   └── application.pdf
│   └── english/
│       ├── eligibility.pdf
│       ├── benefits.pdf
│       └── application.pdf
├── mgnrega/
│   ├── hindi/
│   │   └── ...
│   └── english/
│       └── ...
└── metadata.json
```

### Retrieval Configuration

- **Top-k**: 5 chunks per query
- **Minimum relevance score**: 0.6
- **Re-ranking**: Enable Bedrock re-ranking for better results
- **Filters**: Apply scheme-specific filters when mentioned in query

## Prompt Engineering

### System Prompt for Claude

```
You are SevaSetu, an assistant helping rural Indian users understand government schemes.

Your role:
1. Provide accurate information based ONLY on the provided context documents
2. Use simple, clear language appropriate for users with limited education
3. Structure responses with bullet points for eligibility criteria
4. Always cite which government document your answer comes from
5. If information is not in the context, say "I don't have information about that"
6. Be encouraging and supportive in tone

Context documents:
{retrieved_chunks}

User question: {query}

Provide a helpful, simplified response in {language}.
```

### Response Simplification Guidelines

- Use common words instead of technical jargon
- Keep sentences short (max 15 words)
- Use active voice
- Provide examples when explaining eligibility
- Break complex processes into numbered steps
- Use analogies familiar to rural contexts

## IndicTrans2 Integration

### When to Use Translation

Translation is needed when:
- User speaks a regional dialect not natively supported by Claude
- Query contains code-mixed language (Hindi + English)
- User's language preference is set to a dialect variant

### Translation Pipeline

```python
def should_translate(language: str, text: str) -> bool:
    """
    Check if translation needed
    Bedrock natively supports: Hindi, Tamil (standard)
    Translate for: Bhojpuri, Awadhi, regional Tamil variants
    """
    native_languages = ["hi", "ta", "en"]
    return language not in native_languages

def translate_query_pipeline(text: str, source_lang: str) -> str:
    """
    1. Detect if dialect or standard language
    2. If dialect, use IndicTrans2 to translate to English
    3. Return translated text
    """
    
def translate_response_pipeline(text: str, target_lang: str) -> str:
    """
    1. Translate English response to target language
    2. Ensure cultural appropriateness
    3. Return translated text
    """
```

### IndicTrans2 Model Selection

- **Model**: IndicTrans2 (1B parameter model)
- **Deployment**: Host on AWS SageMaker or EC2
- **Supported Languages**: 
  - Hindi and dialects (Bhojpuri, Awadhi, Magahi)
  - Tamil and dialects
  - Telugu, Odia (future expansion)

## Error Handling

### Error Categories and Responses

1. **Audio Capture Errors**:
   - Microphone permission denied → "कृपया माइक्रोफ़ोन की अनुमति दें" (Please allow microphone access)
   - No audio detected → "कोई आवाज़ नहीं सुनाई दी, कृपया फिर से बोलें" (No voice detected, please speak again)

2. **Speech Recognition Errors**:
   - Low confidence → "मैं आपकी बात समझ नहीं पाया, कृपया स्पष्ट रूप से बोलें" (I couldn't understand, please speak clearly)
   - Unsupported language → "यह भाषा अभी समर्थित नहीं है" (This language is not supported yet)

3. **RAG Pipeline Errors**:
   - No relevant documents → "मुझे इस बारे में जानकारी नहीं मिली, कृपया अपना सवाल दूसरे तरीके से पूछें" (I couldn't find information, please rephrase)
   - Knowledge Base unavailable → "सेवा अभी उपलब्ध नहीं है, कृपया बाद में प्रयास करें" (Service unavailable, please try later)

4. **LLM Errors**:
   - Bedrock timeout → "प्रतिक्रिया में समय लग रहा है, कृपया फिर से प्रयास करें" (Response taking time, please retry)
   - Rate limit exceeded → "बहुत सारे अनुरोध हैं, कृपया थोड़ी देर प्रतीक्षा करें" (Too many requests, please wait)

5. **Translation Errors**:
   - Translation service down → Fallback to processing in original language
   - Unsupported dialect → Attempt direct processing with Bedrock

### Retry Logic

- **Speech-to-Text**: 2 retries with exponential backoff
- **Bedrock calls**: 3 retries with exponential backoff
- **Translation**: 2 retries, then fallback to original language
- **TTS**: 2 retries, if fails show text-only response

### Logging and Monitoring

```python
@dataclass
class QueryLog:
    session_id: str
    timestamp: datetime
    language: str
    query_text: str
    translation_used: bool
    retrieval_score: float
    response_time: float
    error: Optional[str]
    user_feedback: Optional[str]
```

Log all queries for:
- Performance monitoring
- Error analysis
- Quality improvement
- Usage analytics


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Speech-to-Text Conversion Completeness
*For any* valid audio input in a supported language, the system should produce a non-empty text transcription.
**Validates: Requirements 1.5**

### Property 2: Direct Processing for Supported Languages
*For any* query in Hindi or Tamil (supported languages), the system should process it directly without invoking the translation service.
**Validates: Requirements 2.3**

### Property 3: Translation Round-Trip for Dialects
*For any* query in an unsupported dialect, if the system translates the query to English for processing, then the response must be translated back to the original dialect language.
**Validates: Requirements 2.4, 2.5, 6.4**

### Property 4: Document Upload Persistence
*For any* PDF document uploaded to the system, the document should be retrievable from the Document_Store with the same content.
**Validates: Requirements 3.2**

### Property 5: Document Metadata Preservation
*For any* document stored in the Document_Store, the system should maintain complete metadata including scheme name, version, language, and upload date.
**Validates: Requirements 3.3, 11.5**

### Property 6: Knowledge Base Index Synchronization
*For any* document update in the Document_Store, the Knowledge_Base index should reflect the changes after synchronization is triggered.
**Validates: Requirements 3.5**

### Property 7: Relevant Chunk Retrieval
*For any* user query, the RAG_Pipeline should retrieve at least one document chunk when relevant documents exist in the Knowledge_Base.
**Validates: Requirements 4.2**

### Property 8: Relevance-Based Ranking
*For any* set of retrieved document chunks, they should be ordered such that chunk[i].relevance_score >= chunk[i+1].relevance_score for all i.
**Validates: Requirements 4.3**

### Property 9: Response Source Attribution
*For any* response generated by the system, the response should include citations to specific source documents from the Knowledge_Base, and these sources should be displayed in the UI.
**Validates: Requirements 4.5, 12.2, 12.5**

### Property 10: Response Language Simplification
*For any* response generated from policy documents, the vocabulary complexity of the response should be lower than the vocabulary complexity of the source document chunks (measured by average word frequency rank or readability score).
**Validates: Requirements 5.2, 5.3**

### Property 11: Eligibility Criteria Formatting
*For any* response about a scheme that contains eligibility criteria, the response text should include structured formatting (bullet points or numbered lists) for the criteria.
**Validates: Requirements 5.5**

### Property 12: Text-to-Speech Generation
*For any* text response generated by the system, an audio version should be produced in the same language as the response text.
**Validates: Requirements 6.1, 6.5**

### Property 13: UI Language Consistency
*For any* language selected by the user, all UI text elements should be displayed in that language throughout the session.
**Validates: Requirements 7.4, 10.3**

### Property 14: Query Processing Time Bound
*For any* user query, the total processing time from audio input to response delivery should not exceed 10 seconds under normal operating conditions.
**Validates: Requirements 8.1**

### Property 15: Pipeline Stage Ordering
*For any* query processed by the system, the pipeline stages should execute in this order: speech-to-text → translation (if needed) → RAG retrieval → response generation → translation (if needed) → text-to-speech.
**Validates: Requirements 8.2**

### Property 16: No-Results Handling
*For any* query where the Knowledge_Base returns zero relevant chunks (relevance score below threshold), the system should return a message indicating that information is not available rather than generating an unsupported response.
**Validates: Requirements 8.3**

### Property 17: Multi-Scheme Response Completeness
*For any* query that matches multiple schemes in the Knowledge_Base (based on retrieved chunks from different schemes), the response should mention all applicable schemes.
**Validates: Requirements 8.4**

### Property 18: Conversation Context Persistence
*For any* follow-up query within the same session, the system should have access to previous queries and responses from that session.
**Validates: Requirements 8.5**

### Property 19: Language Preference Persistence
*For any* language selected by a user, that preference should remain consistent for all subsequent queries within the same session.
**Validates: Requirements 10.4**

### Property 20: Scheme Query Response Completeness
*For any* query about a specific government scheme, if information exists in the Knowledge_Base, the response should address at least two of the three aspects: eligibility, benefits, or application process.
**Validates: Requirements 11.3**

### Property 21: Response Grounding in Knowledge Base
*For any* response generated by the Bedrock_Engine, all factual claims in the response should be traceable to specific chunks retrieved from the Knowledge_Base (no hallucinated information).
**Validates: Requirements 12.1, 12.3**

### Property 22: Low-Confidence Uncertainty Indication
*For any* response where the maximum relevance score of retrieved chunks is below a confidence threshold (e.g., 0.7), the response should include explicit language indicating uncertainty.
**Validates: Requirements 12.4**


## Testing Strategy

### Overview

The testing strategy employs a dual approach combining unit tests for specific examples and edge cases with property-based tests for universal correctness properties. This ensures both concrete functionality and general correctness across all inputs.

### Property-Based Testing

**Framework**: Use `hypothesis` for Python-based property testing

**Configuration**:
- Minimum 100 iterations per property test
- Each test must reference its design document property
- Tag format: `# Feature: sevasetu-rag-app, Property {number}: {property_text}`

**Property Test Coverage**:

Each of the 22 correctness properties defined above must be implemented as a property-based test. Property tests will:
- Generate random valid inputs (queries, documents, audio samples)
- Verify universal properties hold across all generated inputs
- Catch edge cases that manual test cases might miss

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=500))
def test_property_1_speech_to_text_completeness(audio_text):
    """
    Feature: sevasetu-rag-app, Property 1: Speech-to-Text Conversion Completeness
    For any valid audio input, system produces non-empty transcription
    """
    # Generate synthetic audio from text
    audio_bytes = generate_test_audio(audio_text, language="hi")
    
    # Process through STT
    result = speech_to_text_service.transcribe(audio_bytes, language_hint="hi")
    
    # Verify non-empty output
    assert result.text is not None
    assert len(result.text.strip()) > 0
```

### Unit Testing

**Framework**: Use `pytest` for Python unit tests

**Unit Test Focus Areas**:

1. **Component Integration Tests**:
   - Test interactions between QueryOrchestrator and individual services
   - Verify error propagation between components
   - Test session state management

2. **Edge Cases**:
   - Empty audio input
   - Very long queries (>1000 words)
   - Queries with no relevant documents
   - Mixed language queries
   - Special characters in queries
   - Concurrent requests from same session

3. **Error Handling**:
   - Microphone permission denied
   - Network timeouts to AWS services
   - Invalid audio formats
   - Bedrock rate limiting
   - S3 access errors
   - Translation service failures

4. **Specific Examples**:
   - Test with actual PM-Kisan eligibility query in Hindi
   - Test with MGNREGA wage query in Tamil
   - Test language switching mid-session
   - Test follow-up question handling

**Example Unit Test**:
```python
def test_pm_kisan_eligibility_query_hindi():
    """Test specific PM-Kisan eligibility query in Hindi"""
    query = "मैं पीएम किसान योजना के लिए पात्र हूं क्या?"
    
    orchestrator = QueryOrchestrator()
    result = orchestrator.process_query(
        audio=generate_test_audio(query, "hi"),
        language="hi",
        session_id="test-session-1"
    )
    
    assert result.error is None
    assert "पीएम किसान" in result.text_response or "PM-Kisan" in result.text_response
    assert len(result.sources) > 0
    assert "pm-kisan" in result.sources[0].lower()
```

### Integration Testing

**Scope**: Test complete end-to-end flows

**Key Integration Tests**:
1. Full query pipeline: Audio → STT → RAG → LLM → TTS → Response
2. Document upload → Knowledge Base sync → Query retrieval
3. Language selection → Query in that language → Response in same language
4. Translation flow: Dialect query → English translation → Response → Dialect translation
5. Error recovery: Service failure → Retry → Success

### Mock Services for Testing

**AWS Service Mocks**:
- Mock Bedrock Knowledge Base with in-memory document store
- Mock Bedrock LLM with predefined responses for test queries
- Mock S3 with local file system
- Mock Polly TTS with silent audio generation

**Benefits**:
- Fast test execution
- No AWS costs during testing
- Deterministic test results
- Ability to simulate failures

### Performance Testing

**Metrics to Track**:
- Query processing time (target: <10 seconds)
- STT latency
- RAG retrieval time
- LLM response time
- TTS generation time
- End-to-end latency

**Load Testing**:
- Simulate 10 concurrent users
- Test with 100 queries per minute
- Verify no degradation in response quality
- Check error rates under load

### Test Data

**Document Corpus**:
- 5 PM-Kisan documents (Hindi + English)
- 5 MGNREGA documents (Hindi + English)
- 3 documents with eligibility criteria
- 3 documents with application processes
- 2 documents with benefit details

**Audio Test Samples**:
- 20 Hindi voice samples (male/female, different accents)
- 20 Tamil voice samples (male/female, different accents)
- 10 samples with background noise
- 5 samples with unclear speech

**Query Test Set**:
- 50 common queries about PM-Kisan
- 50 common queries about MGNREGA
- 20 multi-scheme queries
- 20 follow-up questions
- 10 unanswerable queries

### Continuous Testing

**Pre-commit Hooks**:
- Run unit tests
- Run linting and type checking
- Verify no hardcoded credentials

**CI/CD Pipeline**:
- Run all unit tests
- Run property tests (100 iterations each)
- Run integration tests with mocked services
- Generate coverage report (target: >80%)
- Run security scans

**Monitoring in Production**:
- Log all query processing times
- Track error rates by error type
- Monitor user feedback/ratings
- Alert on response time >10 seconds
- Alert on error rate >5%

### Test Coverage Goals

- **Unit Test Coverage**: >80% of code
- **Property Test Coverage**: 100% of correctness properties (all 22 properties)
- **Integration Test Coverage**: All critical user flows
- **Edge Case Coverage**: All error handling paths

### Testing Priorities

**Priority 1 (Must Have)**:
- Property tests for response grounding (Property 21)
- Property tests for source attribution (Property 9)
- Unit tests for error handling
- Integration test for full query pipeline

**Priority 2 (Should Have)**:
- Property tests for language consistency (Properties 3, 13)
- Property tests for RAG retrieval (Properties 7, 8)
- Unit tests for edge cases
- Performance tests

**Priority 3 (Nice to Have)**:
- Property tests for UI behavior
- Load testing
- Stress testing
- Chaos engineering tests

