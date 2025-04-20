from typing import Dict, Optional
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.callbacks.manager import CallbackManager
import re

class GrowthAdvisorTool(BaseTool):
    name: str = "growth_advisor"
    description: str = "Provides personalized growth advice based on evaluation results"
    llm: Optional[ChatOpenAI] = None
    prompt: Optional[ChatPromptTemplate] = None
    
    def __init__(self, callback_manager: Optional[CallbackManager] = None):
        super().__init__()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7, callback_manager=callback_manager)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert engineering career advisor.
            Based on the evaluation, provide actionable growth advice.
            Return a JSON with:
            - next_level: target level to aim for
            - key_focus_areas: 2-3 specific areas to focus on
            - action_items: 3-5 concrete action items
            - resources: relevant learning resources
            - timeline: suggested timeline for growth"""),
            ("user", """Evaluation Results:
            {evaluation}
            
            Provide growth advice:""")
        ])
    
    def _run(self, evaluation: Dict) -> Dict:
        """Generate growth advice based on evaluation."""
        chain = self.prompt | self.llm
        response = chain.invoke({
            "evaluation": evaluation
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
    
    async def _arun(self, evaluation: Dict) -> Dict:
        """Async implementation of the tool."""
        return self._run(evaluation) 