import sys
import yaml
import time
import traceback
import uuid
import os
from pathlib import Path 
from datasets import Dataset, load_from_disk, concatenate_datasets

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root)) 

CONFIG_PATH = project_root / "Evaluation_Suite/evaluation_config.yaml" 
RESULT_PATH = project_root / "Evaluation_Suite/Evaluation_results/" 


from evaluation_utils import get_git_metadata, build_dataset, ArgsParser
from src.agent import create_agent

def agent_inference(message: str):
    Outputs = []
    try:
        agent = create_agent()
        for log in agent.forward(message):
            if isinstance(log, dict):
                Outputs.append(log)
            
            print(f"\n---------------------------------------------------\n{log}")
    except Exception as e:
        Outputs.append({
            "type": "ERROR",
            "content": str(e)
        })
    
    final_answer = None
    for item in Outputs:
        if item.get("type") == "FINAL_ANSWER":
            final_answer = item["content"]
            break

    if final_answer is None:
        final_answer = ""
    
    return final_answer, Outputs

def write_to_dataset(new_list, dataset_id):
    available_dataset = os.listdir(RESULT_PATH)
    if dataset_id not in available_dataset:
        ds = Dataset.from_list([])
    else:
        ds = load_from_disk(f"{RESULT_PATH}/{dataset_id}")
    
    new_example = Dataset.from_list(new_list)
    combined_dataset = concatenate_datasets([ds, new_example])
    combined_dataset.save_to_disk(f"{RESULT_PATH}/{dataset_id}")

def evaluate_simpleQA(evaluation_name:str, sleep_time:float | int = 0):
    
    git_metadata = get_git_metadata()
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    config.setdefault("total_evaluation_runs", 0)
    config.setdefault("evaluation_runs", {})
    config["evaluation_runs"].setdefault("gaia", {})
    config["evaluation_runs"].setdefault("simpleQA", {})
    config["evaluation_runs"].setdefault("hle", {})

    runs = config["evaluation_runs"]["simpleQA"]

    if evaluation_name not in runs:
        config["total_evaluation_runs"] += 1
        runs[evaluation_name] = {
            "name": evaluation_name,
            "eval_id": str(uuid.uuid4()),
            "branch": git_metadata["branch"],
            "commit": git_metadata["commit"],
            "examples_evaluated": 0
        }
    
    examples_evaluated = runs[evaluation_name]["examples_evaluated"]
    eval_id = runs[evaluation_name]["eval_id"]

    # Continue Evaluation
    try:
        metadata, data = build_dataset(
            dataset_path= "basicv8vc/SimpleQA",
            split="test"
        )
        total_examples = metadata["num_rows"]

        if total_examples != examples_evaluated:
            for example in data[examples_evaluated:]:
                
                # Dump It in config to insure agent dont repeat any bound to fail examples (Ignore if agent isn't capable to solve)
                examples_evaluated += 1
                runs[evaluation_name]["examples_evaluated"] = examples_evaluated

                # CRITICAL: As evaluation may results error in the middle keeping process
                with open(CONFIG_PATH, 'w') as f:
                    yaml.safe_dump(config, f)

                # ----------------------------------------------- #
                #               GET ANSWER FROM AGENT             #
                # ----------------------------------------------- #
                final, output = agent_inference(example['problem'])
                example['answer_from_agent'] , example['Output_observation'] = final, str(output)
                new_list = [example]
                write_to_dataset(new_list, eval_id)
                print(f"----------------- EVALUATED [{examples_evaluated}] ---------------------")

                # TODO: REMOVE BEFORE ACTUAL EVALUATION
                # if examples_evaluated == 2:
                #     break
                if sleep_time != None:
                    time.sleep(sleep_time)
            

            print("----------------- EVALUATION COMPLEATED ---------------------")
        
        else:
            print("----------------- NO EXAMPLES TO EVALUATE ---------------------")
    except Exception as e:
        print(f"----------------------- EXCEPTION --------------------- \n {str(e)} \n {traceback.format_exc()}")


if __name__ == "__main__":
    parser = ArgsParser()
    args = parser.parse_args()
    evaluate_simpleQA(
        evaluation_name = args.evaluation_name,
        sleep_time=args.time
    )