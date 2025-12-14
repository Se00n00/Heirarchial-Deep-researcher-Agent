class FinalAnswerTool:
    name = "final_answer"
    description = "Use this submit your task"
    inputs = {"answer":{"type":"string","description": "Exact result / feedback you want to give"}}
    inputs["citations"] = {
        "type":"list[str]",
        "description": "citations urls / source",
        "nullable": True
    }
    output_type = "any"
    
    def forward(self, answer, citations:None | list[str] = None):
        return answer