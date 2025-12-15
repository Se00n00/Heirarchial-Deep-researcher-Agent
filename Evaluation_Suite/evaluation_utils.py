from datasets import load_dataset
import subprocess

def _git(cmd: str) -> str:
    return subprocess.check_output(cmd.split()).decode().strip()


def get_git_metadata() -> dict:
    return {
        "branch": _git("git rev-parse --abbrev-ref HEAD"),
        "commit": _git("git rev-parse HEAD"),
        "dirty": bool(_git("git status --porcelain"))
    }

def build_dataset(dataset_path:str, subset:str | None = None, split:str | None = None):
    """
        Build your dataset
        
        :param dataset_path: Huggingface publically available dataset, ex- gaia-benchmark/GAIA
        :type dataset_path: str
        :param subset: Subset of dataset, ex- 2023-all
        :type subset: str | None
        :param split: Split of dataset, ex- validation
        :type split: str | None
    """
    if subset != None:
        data = load_dataset(dataset_path, subset)
    else:
        data = load_dataset(dataset_path)

    if split != None:
        data = data[split]
    
    metadata = {
        "num_rows": data.num_rows,
        "features": list(data.features.keys())
    }
    
    dataset_examples = []
    for row in range(data.num_rows):
        dataset_examples.append(data[row])

    return metadata, dataset_examples