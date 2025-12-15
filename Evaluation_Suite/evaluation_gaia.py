import sys
from pathlib import Path 

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root)) 

CONFIG_PATH = project_root / "Evaluation/evaluation_config.yaml" 


from evaluation_utils import get_git_metadata, build_dataset
import yaml

def evaluate_simpleQA(evaluation_name:str):
    
    git_metadata = get_git_metadata()
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    config.setdefault("total_evaluation_runs", 0)
    config.setdefault("evaluation_runs", {})
    config["evaluation_runs"].setdefault("gaia", {})
    config["evaluation_runs"].setdefault("simpleQA", {})
    config["evaluation_runs"].setdefault("hle", {})

    runs = config["evaluation_runs"]["gaia"]

    if evaluation_name not in runs:
        config["total_evaluation_runs"] += 1
        runs[evaluation_name] = {
            "name": evaluation_name,
            "branch": git_metadata["branch"],
            "commit": git_metadata["commit"],
            "examples_evaluated": 0
        }
    
    examples_evaluated = runs[evaluation_name]["examples_evaluated"]

    # Continue Evaluation
    try:
        metadata, data = build_dataset(
            dataset_path= "basicv8vc/SimpleQA",
            split="test"
        )
        total_examples = metadata["num_rows"]

        if total_examples != examples_evaluated:

            nums = 0
            for i in data[examples_evaluated:]:
                nums += 1
            
                runs[evaluation_name]["examples_evaluated"] = nums
                
                # CRITICAL: As evaluation may results error in the middle keeping process
                with open(CONFIG_PATH, 'w') as f:
                    yaml.safe_dump(config, f)

                if nums == 150:
                    break

            print("----------------- EVALUATION COMPLEATED ---------------------")
        
        else:
            print("----------------- NO EXAMPLES TO EVALUATE ---------------------")
    except Exception as e:
        print(f"----------------------- EXCEPTION --------------------- \n {str(e)}")


evaluate_simpleQA(evaluation_name = "evaluation_trail_2")