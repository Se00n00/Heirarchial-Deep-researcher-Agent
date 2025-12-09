# Dataset Descriptions

This document includes three datasets used for evaluating the agent: **SIMPLE-QA**, **HLE**, and **GAIA**.
Each subsection provides dataset statistics, modality information, metadata schema, and other relevant characteristics.

---

##  **1. SIMPLE-QA Dataset**

### **Overview**

The SIMPLE-QA dataset consists of short, factual question–answer pairs. It is strictly text-based and designed to assess basic language understanding and retrieval capabilities.

### **Statistics**

* **Split evaluated:** `test`
* **Total samples:** **4,326**
* **Multimodal:** **False**
* **Metadata sources:** `Urls`

### **Schema**

Each entry contains:

| Field                  | Type          | Description                         |
| ---------------------- | ------------- | ----------------------------------- |
| `problem`              | `str`         | The question or prompt.             |
| `answer`               | `str`         | The ground-truth answer.            |
| `metadata.topic`       | `str`         | Topic associated with the question. |
| `metadata.urls`        | `List[str]`   | List of referenced URLs.            |
| `metadata.answer_type` | *type varies* | Type/category of the answer.        |

---

##  **2. HLE Dataset**

### **Overview**

The HLE (Humanity's Last Exam) dataset is a **multimodal benchmark** containing complex reasoning questions across a wide range of domains. Although images are included, the majority of questions are text-only.

### **Statistics**

* **Split evaluated:** `test`
* **Total samples:** **2,500**
* **Multimodal:** **True**
* **Text-only questions:** **2,158** (≈ **86.32%**)
* **Metadata sources:** `image`

### **Schema**

Each entry includes:

| Field             | Type                                                                                                                               | Description                                                                                                                |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `id`              | `string`                                                                                                                           | Unique item identifier.                                                                                                    |
| `question`        | `string`                                                                                                                           | Natural-language question.                                                                                                 |
| `image`           | `string`                                                                                                                           | Image file path or ID.                                                                                                     |
| `image_preview`   | *varies*                                                                                                                           | Preview or pointer to image content.                                                                                       |
| `answer`          | `string`                                                                                                                           | Ground-truth answer.                                                                                                       |
| `answer_type`     | `['multipleChoice', 'exactMatch']`                                                                                                 | Answer format classification.                                                                                              |
| `author_name`     | `string`                                                                                                                           | Source author or annotator.                                                                                                |
| `rationale`       | `string`                                                                                                                           | Explanation supporting the answer.                                                                                         |
| `rationale_image` | *varies*                                                                                                                           | Image-based rationale, if provided.                                                                                        |
| `raw_subject`     | `List[str]`                                                                                                                        | Fine-grained subject labels (extensive; spanning sciences, humanities, arts, engineering, logic, games, literature, etc.). |
| `category`        | `['Computer Science/AI', 'Biology/Medicine', 'Math', 'Physics', 'Chemistry', 'Other', 'Engineering', 'Humanities/Social Science']` | High-level subject category.                                                                                               |
| `canary`          | `string`                                                                                                                           | Canary string for safety or detection purposes.                                                                            |

The dataset spans a wide interdisciplinary range, including scientific, mathematical, humanities, artistic, and domain-specific topics.

---

##  **3. GAIA Dataset**

### **Overview**

The GAIA dataset evaluates complex reasoning and tool-use capabilities. It is **highly multimodal**, including text, images, documents, audio, structured files, and archive formats.

### **Statistics**

* **Split evaluated:** `validation`
* **Total samples:** **165**
* **Multimodal:** **True**
* **Non-file examples:** **127** (≈ **76.96%**)
* **Metadata sources:**
  `['txt', 'jpg', 'docx', 'mp3', 'png', 'pdf', 'csv', 'jsonld', 'zip', 'pptx', 'xlsx', 'py', 'pdb']`

### **Schema**

| Field          | Type      | Description                           |
| -------------- | --------- | ------------------------------------- |
| `task_id`      | `string`  | Unique task identifier.               |
| `question`     | `string`  | The problem description or question.  |
| `level`        | `integer` | Difficulty level.                     |
| `final_answer` | `string`  | The final ground-truth answer.        |
| `file_name`    | `string`  | Name of the associated file (if any). |
| `file_path`    | `string`  | Path to the provided external file.   |

### **Annotator Metadata**

Each example may include structured annotation metadata, such as:

```json
{
  "steps": "...",
  "number_of_steps": "...",
  "tools": "...",
  "time_taken": "..."
}
```

This metadata supports interpretability and provides insight into human reasoning traces during annotation.

---
