# Agent Factory Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Core Components](#core-components)
4. [Class Diagrams](#class-diagrams)
5. [Data Flow Architecture](#data-flow-architecture)
6. [Profile Personalization System](#profile-personalization-system)
7. [Memory Management System](#memory-management-system)
8. [Tool System Architecture](#tool-system-architecture)
9. [Configuration Management](#configuration-management)
10. [Web Interface Architecture](#web-interface-architecture)
11. [Database Integration](#database-integration)
12. [Deployment Architecture](#deployment-architecture)
13. [Technical Implementation Details](#technical-implementation-details)

## System Overview

Agent Factory is a sophisticated AI agent platform that has been transformed into **Emreq** - a personalized AI Engineering Manager. The system provides:

- **Personalized AI Interactions** using Supabase profile integration
- **Memory Management** with intelligent LLM-based extraction
- **Tool Integration** including web search and calendar scheduling
- **Modern Web Interface** using Chainlit with real-time streaming
- **Configuration-Driven Architecture** for flexible agent customization

### Key Technologies
- **Backend**: Python 3.11+, Pydantic, OpenAI GPT-4-turbo
- **Database**: Supabase (PostgreSQL) with Row Level Security
- **Web Interface**: Chainlit (FastAPI-based) with WebSocket streaming
- **Authentication**: Supabase Auth with JavaScript bridge
- **Configuration**: YAML-based with validation
- **Tools**: Extensible plugin architecture

### System Capabilities
- **Phase 1 Personalization**: Profile-based personalized welcome messages and context
- **Intelligent Memory**: LLM-powered extraction of user information with confidence scoring
- **Tool Ecosystem**: Calculator, file reader, web search, calendar scheduling
- **Streaming Responses**: Real-time chat with WebSocket streaming
- **Enterprise Ready**: Security, error handling, and scalable architecture

## High-Level Architecture

The system follows a layered architecture pattern with clear separation of concerns:

**Frontend Layer**: Chainlit web interface with JavaScript authentication bridge
**Application Layer**: Core agent logic, memory management, and tool orchestration  
**Core Layer**: Configuration, LLM abstraction, and registry systems
**Data Layer**: Supabase database, YAML configs, and environment variables
**External Services**: OpenAI API, web search, and email services

This architecture enables:
- **Modularity**: Each layer can be modified independently
- **Scalability**: Components can be scaled horizontally
- **Testability**: Clear interfaces enable comprehensive testing
- **Maintainability**: Well-defined responsibilities reduce complexity

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Chainlit Web Interface]
        JS[JavaScript Auth Bridge]
        CSS[Custom Styling]
    end
    
    subgraph "Application Layer"
        APP[app.py - Main Application]
        AGENT[BaseAgent]
        MEMORY[MemoryManager]
        TOOLS[Tool System]
    end
    
    subgraph "Core Layer"
        CONFIG[Configuration System]
        LLM[LLM Abstraction]
        TRAITS[Traits Registry]
        MODELS[Models Registry]
    end
    
    subgraph "Data Layer"
        SUPABASE[(Supabase Database)]
        FILES[YAML Configs]
        ENV[Environment Variables]
    end
    
    subgraph "External Services"
        OPENAI[OpenAI API]
        WEB[Web Search APIs]
        EMAIL[SMTP Services]
    end
    
    UI --> APP
    JS --> APP
    APP --> AGENT
    AGENT --> MEMORY
    AGENT --> TOOLS
    AGENT --> CONFIG
    AGENT --> LLM
    CONFIG --> TRAITS
    CONFIG --> MODELS
    AGENT --> SUPABASE
    LLM --> OPENAI
    TOOLS --> WEB
    TOOLS --> EMAIL
    CONFIG --> FILES
    CONFIG --> ENV
```

## Core Components

### 1. BaseAgent (`agent_factory/agent.py`)
The central orchestrator that manages all agent interactions, memory, and tools.

**Key Responsibilities:**
- Chat message processing with streaming support
- Memory management integration
- Tool execution and coordination
- Profile personalization injection
- LLM interaction management

### 2. MemoryManager (`agent_factory/agent.py`)
Intelligent memory system that tracks user profiles, goals, and conversation history.

**Key Features:**
- LLM-based information extraction with confidence scoring
- Profile data injection from Supabase
- Conversation summarization
- Goal tracking and management

### 3. SupabaseProfileClient (`agent_factory/supabase_client.py`)
Handles all database interactions for user profile management.

**Key Features:**
- Row Level Security (RLS) bypass using service role
- Profile data formatting for agent consumption
- Session token validation
- Personalized context generation

### 4. Configuration System (`agent_factory/config.py`)
YAML-based configuration with comprehensive validation.

**Key Features:**
- Pydantic model validation
- API key availability checking
- Traits and models registry integration
- Environment variable management

## Class Diagrams

### Core Agent Architecture

```mermaid
classDiagram
    class BaseAgent {
        -config: AgentConfig
        -llm: BaseLLM
        -user_profile: Dict[str, Any]
        -memory_manager: MemoryManager
        -available_tools: Dict[str, BaseTool]
        +__init__(config, llm, user_profile)
        +chat(message: str): str
        +chat_stream(message: str): Iterator
        +use_tool(tool_name, input_data): str
        +get_personalized_context(): str
        -_inject_profile_data(user_profile)
    }
    
    class MemoryManager {
        -config: MemoryConfig
        -llm: BaseLLM
        -user_profile: UserProfile
        -goals: List[Goal]
        -conversation_history: List[Dict]
        -profile_confidence: Dict[str, float]
        +update_profile(user_message)
        +add_goal(user_message)
        +add_message(role, content)
        +get_memory_context(): str
        -_extract_user_info(message): dict
        -_fallback_extraction(message): dict
        -_summarize_conversation()
    }
    
    class AgentConfig {
        +agent_id: str
        +name: str
        +description: str
        +max_tokens: int
        +temperature: float
        +tools: List[str]
        +llm: LLMConfig
        +cognitive_core: CognitiveCoreConfig
        +traits: List[str]
        +memory: MemoryConfig
        +validate_temperature(v): float
    }
    
    class SupabaseProfileClient {
        -url: str
        -anon_key: str
        -service_key: str
        -client: Client
        +get_user_profile(user_id): Dict
        +get_user_profile_by_email(email): Dict
        +format_profile_for_agent(profile): Dict
        +generate_personalized_context(profile): str
        +validate_session_token(token): Dict
    }
    
    BaseAgent --> MemoryManager
    BaseAgent --> AgentConfig
    BaseAgent --> SupabaseProfileClient
    MemoryManager --> UserProfile
    MemoryManager --> Goal
```

### Tool System Architecture

```mermaid
classDiagram
    class BaseTool {
        <<abstract>>
        +name: str
        +description: str
        +execute(input_data: str): str
    }
    
    class CalculatorTool {
        +name: "calculator"
        +description: "Mathematical calculations"
        +execute(expression): str
        -_safe_eval(expression): float
    }
    
    class WebSearchTool {
        -llm: BaseLLM
        +name: "web_search"
        +description: "Web search with AI synthesis"
        +execute(query): str
        -_search_web(query): List[Dict]
        -_synthesize_results(results): str
    }
    
    class OneOnOneScheduler {
        +name: "one_on_one_scheduler"
        +description: "Meeting scheduling with ICS"
        +execute(request): str
        -_parse_schedule_request(request): Dict
        -_generate_ics_file(details): str
        -_send_email_invite(details): bool
    }
    
    class FileReaderTool {
        +name: "file_reader"
        +description: "Read file contents"
        +execute(file_path): str
        -_validate_file_path(path): bool
    }
    
    BaseTool <|-- CalculatorTool
    BaseTool <|-- WebSearchTool
    BaseTool <|-- OneOnOneScheduler
    BaseTool <|-- FileReaderTool
    
    BaseAgent --> BaseTool : uses
```

### Configuration System

```mermaid
classDiagram
    class AgentConfig {
        +agent_id: str
        +name: str
        +description: str
        +max_tokens: int
        +temperature: float
        +tools: List[str]
        +llm: LLMConfig
        +cognitive_core: CognitiveCoreConfig
        +traits: List[str]
        +memory: MemoryConfig
    }
    
    class LLMConfig {
        +provider: str
        +model_name: str
        +api_key: str
    }
    
    class CognitiveCoreConfig {
        +model: str
        +system_prompt: str
    }
    
    class MemoryConfig {
        +enabled: bool
        +conversation_max_messages: int
        +summarize_after: int
        +user_profile_enabled: bool
        +goals_tracking_enabled: bool
        +max_goals: int
    }
    
    class TraitsRegistry {
        -traits_data: Dict
        +get_trait_instruction(name): str
        +build_traits_prompt(names): str
        +list_available_traits(): Dict
        +validate_traits(names): Tuple
        -_load_traits()
        -_find_trait_instruction(name): str
    }
    
    class ModelsRegistry {
        -models_data: Dict
        +get_available_models(): List
        +validate_model(name): Tuple
        +get_model_info(name): Dict
        -_load_models()
        -_check_api_key_availability(model): bool
    }
    
    AgentConfig --> LLMConfig
    AgentConfig --> CognitiveCoreConfig
    AgentConfig --> MemoryConfig
    AgentConfig --> TraitsRegistry : validates
    AgentConfig --> ModelsRegistry : validates
```

## Data Flow Architecture

### Chat Message Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Chainlit
    participant BaseAgent
    participant MemoryManager
    participant LLM
    participant Tools
    participant Supabase
    
    User->>Chainlit: Send message
    Chainlit->>BaseAgent: chat(message)
    
    BaseAgent->>MemoryManager: add_message("user", message)
    MemoryManager->>MemoryManager: update_profile(message)
    MemoryManager->>MemoryManager: add_goal(message)
    
    BaseAgent->>MemoryManager: get_memory_context()
    MemoryManager-->>BaseAgent: formatted context
    
    BaseAgent->>BaseAgent: get_personalized_context()
    BaseAgent->>Supabase: get user profile data
    Supabase-->>BaseAgent: profile data
    
    BaseAgent->>LLM: generate(prompt + context)
    LLM-->>BaseAgent: response
    
    alt Tool usage detected
        BaseAgent->>Tools: use_tool(name, input)
        Tools-->>BaseAgent: tool result
        BaseAgent->>BaseAgent: append tool result
    end
    
    BaseAgent->>MemoryManager: add_message("assistant", response)
    BaseAgent-->>Chainlit: final response
    Chainlit-->>User: Display response
```

### Profile Loading and Personalization Flow

```mermaid
sequenceDiagram
    participant Browser
    participant JavaScript
    participant Chainlit
    participant SupabaseClient
    participant Database
    participant BaseAgent
    
    Browser->>JavaScript: Page load
    JavaScript->>JavaScript: Check Supabase session
    JavaScript->>Chainlit: Send session data
    
    Chainlit->>SupabaseClient: validate_session_token()
    SupabaseClient->>Database: Validate token
    Database-->>SupabaseClient: User info
    
    SupabaseClient->>Database: get_user_profile(user_id)
    Database-->>SupabaseClient: Raw profile data
    
    SupabaseClient->>SupabaseClient: format_profile_for_agent()
    SupabaseClient->>SupabaseClient: generate_personalized_context()
    
    Chainlit->>BaseAgent: Initialize with user_profile
    BaseAgent->>BaseAgent: _inject_profile_data()
    BaseAgent->>MemoryManager: Populate profile data
    
    BaseAgent-->>Chainlit: Personalized welcome message
    Chainlit-->>Browser: Display personalized UI
```

## Profile Personalization System

### Architecture Overview

The profile personalization system enables **Phase 1 Personalization** where loaded profiles provide personalized first chat messages and context throughout conversations.

```mermaid
graph TD
    subgraph "Authentication Layer"
        AUTH[Supabase Auth]
        JS_BRIDGE[JavaScript Bridge]
        SESSION[Session Management]
    end
    
    subgraph "Profile Loading"
        PROFILE_CLIENT[SupabaseProfileClient]
        RLS[Row Level Security Bypass]
        FORMATTER[Profile Formatter]
    end
    
    subgraph "Agent Integration"
        CONTEXT_GEN[Context Generator]
        MEMORY_INJECT[Memory Injection]
        PERSONALIZED_PROMPT[Personalized Prompts]
    end
    
    subgraph "Database Schema"
        EMPLOYEES[(employee_profiles)]
        FIELDS[name, title, level, specialization, etc.]
        COMPLETED[profile_completed flag]
    end
    
    AUTH --> JS_BRIDGE
    JS_BRIDGE --> SESSION
    SESSION --> PROFILE_CLIENT
    PROFILE_CLIENT --> RLS
    PROFILE_CLIENT --> EMPLOYEES
    EMPLOYEES --> FORMATTER
    FORMATTER --> CONTEXT_GEN
    CONTEXT_GEN --> MEMORY_INJECT
    MEMORY_INJECT --> PERSONALIZED_PROMPT
```

### Key Features

1. **Seamless Authentication Bridge**: JavaScript Supabase auth communicates with Python backend
2. **RLS Bypass**: Service role key bypasses Row Level Security for backend operations
3. **Profile Context Injection**: User data flows into memory system and chat prompts
4. **Personalized Welcome Messages**: Dynamic greetings based on user profile data
5. **Continuous Personalization**: Profile data available throughout conversation

### Database Schema

```sql
CREATE TABLE employee_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT NOT NULL,
    name TEXT,
    title TEXT,
    level TEXT,
    team TEXT,
    years_experience INTEGER,
    years_at_company INTEGER,
    specialization TEXT,
    tech_skills TEXT[],
    current_projects TEXT[],
    career_goals TEXT[],
    biggest_challenges TEXT[],
    strengths TEXT[],
    learning_goals TEXT[],
    communication_style TEXT,
    feedback_frequency TEXT,
    meeting_style TEXT,
    profile_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Memory Management System

### Architecture Overview

The V1 Memory System provides intelligent user profile extraction, goal tracking, and conversation management.

```mermaid
graph TD
    subgraph "Memory Components"
        MANAGER[MemoryManager]
        PROFILE[UserProfile]
        GOALS[Goals List]
        HISTORY[Conversation History]
    end
    
    subgraph "Extraction Engine"
        LLM_EXTRACT[LLM-based Extraction]
        CONFIDENCE[Confidence Scoring]
        FALLBACK[Fallback Heuristics]
    end
    
    subgraph "Context Generation"
        CONTEXT_BUILD[Context Builder]
        SUMMARIZER[Conversation Summarizer]
        MEMORY_PROMPT[Memory-Enhanced Prompts]
    end
    
    MANAGER --> PROFILE
    MANAGER --> GOALS
    MANAGER --> HISTORY
    MANAGER --> LLM_EXTRACT
    LLM_EXTRACT --> CONFIDENCE
    LLM_EXTRACT --> FALLBACK
    MANAGER --> CONTEXT_BUILD
    CONTEXT_BUILD --> SUMMARIZER
    CONTEXT_BUILD --> MEMORY_PROMPT
```

### Key Features

1. **Intelligent Extraction**: Uses GPT-4-turbo for extracting names, roles, communication styles
2. **Confidence Scoring**: 0.0-1.0 confidence scores prevent overwriting high-quality data
3. **Goal Tracking**: Automatically detects and tracks user goals with deduplication
4. **Conversation Summarization**: Maintains context while staying within token limits
5. **Profile Injection**: Seamlessly integrates Supabase profile data

## Tool System Architecture

### Plugin Architecture

```mermaid
graph TD
    subgraph "Tool Registry"
        REGISTRY[Tool Registry]
        DISCOVERY[Tool Discovery]
        VALIDATION[Tool Validation]
    end
    
    subgraph "Base Tools"
        CALC[Calculator Tool]
        FILE[File Reader Tool]
        WEB[Web Search Tool]
        CALENDAR[Calendar Tool]
    end
    
    subgraph "Advanced Tools"
        WEB_SEARCH[WebSearchTool with LLM]
        SCHEDULER[OneOnOneScheduler]
        CUSTOM[Custom Tools]
    end
    
    subgraph "Tool Execution"
        EXECUTOR[Tool Executor]
        ERROR_HANDLER[Error Handling]
        RESULT_FORMATTER[Result Formatting]
    end
    
    REGISTRY --> DISCOVERY
    REGISTRY --> CALC
    REGISTRY --> FILE
    REGISTRY --> WEB
    REGISTRY --> CALENDAR
    WEB --> WEB_SEARCH
    CALENDAR --> SCHEDULER
    REGISTRY --> EXECUTOR
    EXECUTOR --> ERROR_HANDLER
    EXECUTOR --> RESULT_FORMATTER
```

### Tool Integration Pattern

```python
# Tool Registration Pattern
_TOOLS: Dict[str, BaseTool] = {
    "calculator": CalculatorTool(),
    "file_reader": FileReaderTool(),
    "web_search": WebSearchTool(),  # Re-initialized with LLM
    "one_on_one_scheduler": OneOnOneScheduler()
}

# LLM-Enhanced Tool Pattern
class WebSearchTool(BaseTool):
    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm
    
    def execute(self, query: str) -> str:
        # Use LLM for intelligent query processing
        # and result synthesis
```

## Configuration Management

### YAML-Based Configuration

```mermaid
graph TD
    subgraph "Configuration Files"
        AGENT_CONFIG[engineering_manager_emreq.yaml]
        TRAITS_REG[traits_registry.yaml]
        MODELS_REG[models_registry.yaml]
    end
    
    subgraph "Validation Layer"
        PYDANTIC[Pydantic Models]
        API_CHECK[API Key Validation]
        TRAIT_CHECK[Traits Validation]
        MODEL_CHECK[Model Availability]
    end
    
    subgraph "Runtime Configuration"
        CONFIG_OBJ[AgentConfig Object]
        MEMORY_CONFIG[MemoryConfig]
        LLM_CONFIG[LLMConfig]
        CORE_CONFIG[CognitiveCoreConfig]
    end
    
    AGENT_CONFIG --> PYDANTIC
    TRAITS_REG --> TRAIT_CHECK
    MODELS_REG --> MODEL_CHECK
    PYDANTIC --> API_CHECK
    PYDANTIC --> CONFIG_OBJ
    CONFIG_OBJ --> MEMORY_CONFIG
    CONFIG_OBJ --> LLM_CONFIG
    CONFIG_OBJ --> CORE_CONFIG
```

### Configuration Structure

```yaml
# engineering_manager_emreq.yaml
agent_id: "emreq"
name: "Emreq"
description: "AI Engineering Manager"

cognitive_core:
  model: "gpt-4-turbo"
  system_prompt: |
    You are Emreq, a ruthless AI engineering manager...

tools:
  - web_search
  - one_on_one_scheduler

traits:
  - sarcasm
  - ruthless_efficiency
  - tough_love
  - results_focused

memory:
  enabled: true
  conversation_max_messages: 50
  user_profile_enabled: true
  goals_tracking_enabled: true
```

## Web Interface Architecture

### Chainlit Integration

```mermaid
graph TD
    subgraph "Frontend Components"
        UI[Chainlit UI]
        STREAMING[WebSocket Streaming]
        ACTIONS[Action Buttons]
        STYLING[Custom CSS]
    end
    
    subgraph "Application Layer"
        APP_PY[app.py]
        SESSION_MGR[Session Manager]
        MESSAGE_HANDLER[Message Handler]
        WELCOME_GEN[Welcome Generator]
    end
    
    subgraph "Authentication Bridge"
        JS_AUTH[supabase-auth.js]
        SESSION_BRIDGE[Session Bridge]
        STORAGE[Browser Storage]
    end
    
    subgraph "Backend Integration"
        AGENT_LOADER[Agent Loader]
        PROFILE_LOADER[Profile Loader]
        STREAM_HANDLER[Stream Handler]
    end
    
    UI --> APP_PY
    UI --> STREAMING
    UI --> ACTIONS
    JS_AUTH --> SESSION_BRIDGE
    SESSION_BRIDGE --> STORAGE
    APP_PY --> SESSION_MGR
    APP_PY --> MESSAGE_HANDLER
    APP_PY --> WELCOME_GEN
    APP_PY --> AGENT_LOADER
    APP_PY --> PROFILE_LOADER
    APP_PY --> STREAM_HANDLER
```

### Key Features

1. **Real-time Streaming**: WebSocket-based streaming for responsive interactions
2. **Custom Styling**: Dark theme with JetBrains Mono fonts and green accents
3. **Action Buttons**: Quick access to common engineering manager functions
4. **Session Management**: Seamless Supabase auth integration
5. **Responsive Design**: Modern, professional interface

## Database Integration

### Supabase Architecture

```mermaid
graph TD
    subgraph "Supabase Services"
        AUTH[Supabase Auth]
        DB[PostgreSQL Database]
        RLS[Row Level Security]
        API[REST API]
    end
    
    subgraph "Authentication Flow"
        JS_CLIENT[JavaScript Client]
        AUTH_TOKEN[Access Token]
        SESSION_VALIDATION[Session Validation]
    end
    
    subgraph "Data Access"
        ANON_KEY[Anonymous Key - RLS Subject]
        SERVICE_KEY[Service Role Key - RLS Bypass]
        PROFILE_ACCESS[Profile Access]
    end
    
    subgraph "Security Model"
        USER_POLICIES[User Policies]
        ADMIN_BYPASS[Admin Bypass]
        DATA_ISOLATION[Data Isolation]
    end
    
    JS_CLIENT --> AUTH
    AUTH --> AUTH_TOKEN
    AUTH_TOKEN --> SESSION_VALIDATION
    SERVICE_KEY --> PROFILE_ACCESS
    ANON_KEY --> RLS
    SERVICE_KEY --> ADMIN_BYPASS
    RLS --> USER_POLICIES
    DB --> API
    API --> PROFILE_ACCESS
```

### Security Model

1. **Row Level Security (RLS)**: Protects user data at the database level
2. **Service Role Key**: Backend uses service role to bypass RLS for system operations
3. **Session Validation**: Tokens validated against Supabase auth
4. **Data Isolation**: Users can only access their own profile data

## Deployment Architecture

### Development Environment

```mermaid
graph TD
    subgraph "Local Development"
        DEV_ENV[Development Environment]
        ENV_VARS[Environment Variables]
        LOCAL_DB[Local Supabase]
        HOT_RELOAD[Hot Reload]
    end
    
    subgraph "External Services"
        SUPABASE_CLOUD[Supabase Cloud]
        OPENAI_API[OpenAI API]
        SEARCH_API[Search APIs]
    end
    
    subgraph "Development Tools"
        CHAINLIT_DEV[Chainlit Dev Server]
        DEBUG_LOGS[Debug Logging]
        PROFILE_TESTING[Profile Testing]
    end
    
    DEV_ENV --> ENV_VARS
    DEV_ENV --> CHAINLIT_DEV
    DEV_ENV --> DEBUG_LOGS
    CHAINLIT_DEV --> SUPABASE_CLOUD
    CHAINLIT_DEV --> OPENAI_API
    DEBUG_LOGS --> PROFILE_TESTING
```

### Production Considerations

1. **Environment Variables**: Secure API key management
2. **Database Connection Pooling**: Efficient Supabase connections
3. **Error Handling**: Comprehensive error logging and recovery
4. **Performance Monitoring**: Response time and token usage tracking
5. **Security**: HTTPS, secure session management, data encryption

## Technical Implementation Details

### Key Design Patterns

1. **Factory Pattern**: Agent creation through configuration
2. **Strategy Pattern**: Multiple LLM providers support
3. **Observer Pattern**: Memory system updates
4. **Plugin Architecture**: Extensible tool system
5. **Singleton Pattern**: Registry management

### Performance Optimizations

1. **Lazy Loading**: Tools and registries loaded on demand
2. **Connection Pooling**: Efficient database connections
3. **Caching**: Configuration and profile data caching
4. **Streaming**: Real-time response streaming
5. **Token Management**: Efficient prompt construction

### Error Handling Strategy

1. **Graceful Degradation**: Fallback to basic functionality
2. **Comprehensive Logging**: Debug information at all levels
3. **User-Friendly Messages**: Clear error communication
4. **Recovery Mechanisms**: Automatic retry and fallback
5. **Monitoring**: Error tracking and alerting

## Future Architecture Considerations

### Phase 2: Dynamic Profile Updates
- Real-time profile updates based on conversation insights
- ML-based preference learning
- Behavioral pattern recognition

### Phase 3: Advanced Personalization
- Adaptive communication style matching
- Context-aware response generation
- Multi-modal interaction support

### Phase 4: Enterprise Features
- Multi-tenant architecture
- Advanced analytics and reporting
- Integration with enterprise tools
- Scalable deployment options

---

This architecture document provides a comprehensive overview of the Agent Factory system transformed into Emreq. The modular design, comprehensive error handling, and extensible architecture make it suitable for both current personalization features and future enterprise enhancements. 