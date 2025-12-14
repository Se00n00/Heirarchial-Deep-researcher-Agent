from jinja2 import Template

def extract_completion_metadata(completion_obj):
    usage = completion_obj.usage

    return {
      "id": completion_obj.id,
      "model": completion_obj.model,
      "created": completion_obj.created,
      "object": completion_obj.object,
      "service_tier": completion_obj.service_tier,
      "system_fingerprint": completion_obj.system_fingerprint,
      "completion_tokens": usage.completion_tokens,
      "prompt_tokens": usage.prompt_tokens,
      "total_tokens": usage.total_tokens,
      "reasoning_tokens": usage.completion_tokens_details.reasoning_tokens,
      "prompt_tokens_details": usage.prompt_tokens_details if usage.prompt_tokens_details == None else usage.prompt_tokens_details.cached_tokens,
      "completion_time": usage.completion_time,
      "prompt_time": usage.prompt_time,
      "queue_time": usage.queue_time,
      "total_time": usage.total_time,
      "resoning": completion_obj.choices[0].message.reasoning,
      "x_groq": completion_obj.x_groq.id,
    }

def render_yaml_template(file_path, var):
    with open(file_path, "r") as f:
      file_content = f.read()
    template = Template(file_content)
    rendered = template.render(**var)
    return rendered