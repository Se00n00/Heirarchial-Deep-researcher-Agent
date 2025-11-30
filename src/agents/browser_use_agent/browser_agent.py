from state import Action

import yaml
from typing import Any
from jinja2 import Environment, FileSystemLoader

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class BrowserAgent:
    def __init__(
            self,
            model_config,
            config,
            template_path,
            tools: list[Any]
        ):
        env = Environment(loader=FileSystemLoader('.'))
        self.llm = ChatOpenAI(
            model = model_config['Planning_agent']['llm'],
            api_key = model_config['API_KEY'],
            base_url = model_config['BASE_URL'],
            streaming = model_config['Planning_agent']['stream']
        )

        self.config = config
        self.agent = self.llm.with_structured_output(Action)
        self.prompt_template = env.get_template(template_path)
       
    
    def __call__(self, query):
        rendered_yaml = self.prompt_template.render(self.config)
        with open(rendered_yaml, "r") as f:
            prompt_templates = yaml.safe_load(f)
        
        # self.prompt_template = ChatPromptTemplate()
        try:
            return self.agent.invoke(
                prompt_templates
            )
        except Exception as e:
            return {"Error":str(e)}