from state import Action

import yaml
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class PlanningAgent:
    def __init__(
            self,
            model_config,
            config,
            template_path,
            tools: list[Any]
        ):
        self.llm = ChatOpenAI(
            model = model_config['Planning_agent']['llm'],
            api_key = model_config['API_KEY'],
            base_url = model_config['BASE_URL'],
            streaming = model_config['Planning_agent']['stream']
        )

        self.agent = self.llm.with_structured_output(Action)
        with open(template_path, "r") as f:
            self.prompt_templates = yaml.safe_load(f)
        
        self.prompt_template = ChatPromptTemplate()
    
    def __call__(self, query):
        try:
            return self.agent.invoke(
                ChatPromptTemplate
            )
        except Exception as e:
            return {"Error":str(e)}