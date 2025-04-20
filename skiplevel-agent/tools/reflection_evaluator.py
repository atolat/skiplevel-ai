from typing import Dict, List, Optional
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks.manager import CallbackManager
import re

class ReflectionEvaluatorTool(BaseTool):
    name: str = "reflection_evaluator"
    description: str = "Evaluates a reflection against provided rubric chunks using an LLM"
    llm: Optional[ChatOpenAI] = None
    prompt: Optional[ChatPromptTemplate] = None
    
    def __init__(self, callback_manager: Optional[CallbackManager] = None):
        super().__init__()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0, callback_manager=callback_manager)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert engineering career evaluator. 
            Evaluate the reflection against the provided rubric chunks.
            Return a JSON with:
            - level: estimated level (L3-L7)
            - score: 0-100
            - reasoning: detailed explanation
            - strengths: list of key strengths
            - areas_for_improvement: list of areas to focus on"""),
            ("user", """Reflection: {reflection}
            
            Rubric Chunks:
            {rubrics}
            
            Provide your evaluation:""")
        ])
    
    def _run(self, reflection: str, rubrics: List[Dict]) -> Dict:
        """Evaluate reflection against rubric chunks."""
        rubric_text = "\n\n".join([f"Chunk {i+1}: {r['text']}" for i, r in enumerate(rubrics)])
        
        chain = self.prompt | self.llm
        response = chain.invoke({
            "reflection": reflection,
            "rubrics": rubric_text
        })
        
        response_content = response.content.strip('`')
        # Extract JSON content using regex
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            response_content = json_match.group(0)
        else:
            response_content = "{}"  # Default to empty JSON if no match

        print("Debug: Extracted JSON Content:", response_content)  # Debugging line
        
        return response_content
    
    async def _arun(self, reflection: str, rubrics: List[Dict]) -> Dict:
        """Async implementation of the tool."""
        return self._run(reflection, rubrics) 