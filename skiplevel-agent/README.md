# SkipLevel Agent

An AI-powered growth system for engineers that provides personalized career evaluations and growth advice.

## Features

- 🔍 Semantic search for relevant career rubrics
- 📊 AI-powered reflection evaluation
- 🎯 Personalized growth advice and action items
- 💬 Interactive Chainlit interface
- 📈 LangSmith tracing for monitoring and debugging

## Setup

1. Clone the repository
2. Install dependencies using `uv` (recommended) or `pip`:

   Using `uv` (faster):
   ```bash
   # Install uv if you don't have it
   pip install uv
   
   # Create a virtual environment and install dependencies
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

   Using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   
   Required environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   LANGCHAIN_API_KEY=your_langsmith_api_key_here
   LANGCHAIN_PROJECT=skiplevel-agent
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   ```

4. Run the Chainlit app:
   ```bash
   chainlit run chainlit_app.py
   ```

## Project Structure

- `tools/` - LangChain tools for rubric retrieval, evaluation, and advice
- `graph/` - LangGraph workflow setup
- `chainlit_app.py` - Web interface
- `main.py` - CLI interface

## Usage

1. Start the Chainlit app
2. Enter your career reflection in the chat
3. Receive:
   - Level estimate
   - Detailed evaluation
   - Growth advice
   - Action items
   - Recommended resources

## Development

To run the agent independently:
```bash
python main.py
```

## License

MIT License 