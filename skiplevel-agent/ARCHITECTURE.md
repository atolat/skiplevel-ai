# SkipLevel AI Agent Architecture

## Overview
SkipLevel AI is a LangGraph-based agent system designed to evaluate engineering reflections and provide personalized growth advice. The system uses a combination of vector search, LLM-based evaluation, and structured advice generation to help engineers understand their current level and plan their career growth.

## System Components

### 1. Data Layer
- **Qdrant Vector Database**: Stores engineering rubrics and level descriptions
- **Synthetic Data**: Pre-loaded engineering level descriptions and evaluation criteria
- Location: `load_data.py`

### 2. Core Tools

#### a. RubricRetrieverTool (`tools/rubric_retriever.py`)
- Purpose: Retrieves relevant rubric chunks based on engineer's reflection
- Process:
  1. Takes engineer's reflection as input
  2. Uses Qdrant to perform semantic search
  3. Returns most relevant rubric chunks with similarity scores
- Key Features:
  - Semantic search using embeddings
  - Configurable number of results
  - Similarity score thresholding

#### b. ReflectionEvaluatorTool (`tools/reflection_evaluator.py`)
- Purpose: Evaluates engineer's reflection against retrieved rubrics
- Process:
  1. Takes reflection and rubric chunks as input
  2. Uses LLM to analyze alignment with rubrics
  3. Returns structured evaluation with:
     - Level assessment
     - Numerical score
     - Reasoning
     - Strengths
     - Areas for improvement

#### c. GrowthAdvisorTool (`tools/growth_advisor.py`)
- Purpose: Generates personalized growth advice
- Process:
  1. Takes evaluation results as input
  2. Uses LLM to generate targeted advice
  3. Returns structured advice with:
     - Next level target
     - Key focus areas
     - Action items
     - Recommended resources
     - Timeline

### 3. Graph Architecture (`graph/agent.py`)

#### State Management
```python
class AgentState(TypedDict):
    reflection: str
    rubrics: List[Dict]
    evaluation: Dict
    advice: Dict
```

#### Workflow Steps
1. **Retrieve Rubrics**
   - Entry point of the workflow
   - Calls RubricRetrieverTool
   - Updates state with relevant rubrics

2. **Evaluate Reflection**
   - Takes reflection and rubrics
   - Calls ReflectionEvaluatorTool
   - Updates state with evaluation

3. **Generate Growth Advice**
   - Takes evaluation
   - Calls GrowthAdvisorTool
   - Updates state with advice

#### Graph Structure
```
[Retrieve Rubrics] -> [Evaluate Reflection] -> [Generate Growth Advice]
```

### 4. Testing (`test.py`)
- Comprehensive testing of all tools
- Sample reflection testing
- Output validation
- Integration testing

## Data Flow

1. **Input**: Engineer's reflection text
2. **Rubric Retrieval**:
   - Reflection → Qdrant → Relevant Rubrics
3. **Evaluation**:
   - Reflection + Rubrics → LLM → Structured Evaluation
4. **Advice Generation**:
   - Evaluation → LLM → Growth Advice
5. **Output**: Structured JSON with complete evaluation and advice

## Environment Setup
- Required environment variables in `.env`:
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
  - `OPENAI_API_KEY`
  - `LANGCHAIN_API_KEY`
  - `LANGCHAIN_PROJECT`

## Dependencies
- LangGraph: Graph-based workflow management
- LangChain: LLM integration and tool management
- Qdrant: Vector database for semantic search
- OpenAI: LLM provider
- Python 3.9+

## Usage Flow
1. Load environment variables
2. Initialize Qdrant client
3. Create agent instance
4. Process engineer's reflection
5. Receive evaluation and growth advice

## Testing
The system includes a comprehensive test suite that:
1. Loads synthetic data
2. Tests each tool independently
3. Validates the complete workflow
4. Provides sample outputs for verification

## Future Improvements
- Persistent Qdrant storage
- Additional rubric categories
- Enhanced evaluation metrics
- Customizable advice generation
- Integration with career development platforms 