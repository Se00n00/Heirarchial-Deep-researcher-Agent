# test_smoke.py
import asyncio
import json
from deep_researcher import DeepResearcherTool
from models import model_manager

async def run_test():
    # Use the explicit gemini model registered in models.py
    if 'gemini-pro' not in model_manager.registered_models:
        print("gemini-pro is not registered in model_manager.registered_models.")
        print("Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment and re-run.")
        return
    model_id = 'gemini-pro'
    print(f"Using registered model: {model_id}")

    tool = DeepResearcherTool(model_id=model_id, time_limit_seconds=30)
    print('Starting model.forward() call...')
    import asyncio
    try:
        # add an explicit outer timeout in case the inner call blocks
        result = await asyncio.wait_for(tool.forward("design me a attack drone"), timeout=35)
    except asyncio.TimeoutError:
        print('Outer timeout: tool.forward did not complete within 35s')
        return
    except Exception as e:
        print('Exception during tool.forward():', type(e).__name__, e)
        return
    print('Model call completed, examining result...')
    if result.error:
        print("Error:", result.error)
    else:
        print("=== OUTPUT ===")
        print(result.output)

if __name__ == "__main__":
    asyncio.run(run_test())