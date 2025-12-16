from jinja2 import Template

def extract_completion_metadata(completion_obj):
  usage = getattr(completion_obj, "usage", None)
  choice = completion_obj.choices[0] if completion_obj.choices else None
  message = getattr(choice, "message", None)

  completion_details = getattr(usage, "completion_tokens_details", None)
  prompt_details = getattr(usage, "prompt_tokens_details", None)

  return {
    "id": getattr(completion_obj, "id", None),
    "model": getattr(completion_obj, "model", None),
    "created": getattr(completion_obj, "created", None),
    "object": getattr(completion_obj, "object", None),
    "service_tier": getattr(completion_obj, "service_tier", None),
    "system_fingerprint": getattr(completion_obj, "system_fingerprint", None),

    # ---------------- Token Usage ----------------
    "completion_tokens": getattr(usage, "completion_tokens", None),
    "prompt_tokens": getattr(usage, "prompt_tokens", None),
    "total_tokens": getattr(usage, "total_tokens", None),

    "reasoning_tokens": (
        getattr(completion_details, "reasoning_tokens", None)
        if completion_details is not None
        else None
    ),

    "prompt_cached_tokens": (
        getattr(prompt_details, "cached_tokens", None)
        if prompt_details is not None
        else None
    ),

    # ---------------- Timing ----------------
    "completion_time": getattr(usage, "completion_time", None),
    "prompt_time": getattr(usage, "prompt_time", None),
    "queue_time": getattr(usage, "queue_time", None),
    "total_time": getattr(usage, "total_time", None),

    # ---------------- Reasoning / Provider ----------------
    "reasoning": getattr(message, "reasoning", None),
    "x_groq_id": getattr(getattr(completion_obj, "x_groq", None), "id", None),
  }


def render_yaml_template(file_path, var):
    with open(file_path, "r") as f:
      file_content = f.read()
    template = Template(file_content)
    rendered = template.render(**var)
    return rendered