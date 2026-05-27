## **Step-by-Step Developer Guide: ADK Agent Evaluation**

Moving an AI agent from a proof-of-concept to a production-ready system requires a robust, automated evaluation framework. Unlike standard generative models where only the final output matters, evaluating agents requires assessing both **what** they output and **how** they arrived at that conclusion.

### ---

**Step 1: Understand the Core Evaluation Types**

The ADK breaks agent evaluation down into two distinct categories. You must configure expected thresholds for both to determine if a test passes or fails.

| Evaluation Type | What It Measures | How It Works | Configuration & Scoring |
| :---- | :---- | :---- | :---- |
| **Final Response** | The quality, relevance, and correctness of the final output. | Compares the agent's final natural language response to a reference response in your dataset using the **ROUGE** metric. | Set response\_match\_score. Defaults to **0.8**, allowing a small margin of error for natural language. |
| **Trajectory & Tool Use** | The decision-making process, tool choice, strategies, and efficiency. | Compares the actual trajectory (steps taken, such as *Determine intent, Use tool, Review results, Report generation*) against the expected\_tool\_use. | Set tool\_trajectory\_avg\_score. Defaults to **1.0**, requiring a 100% match. (Matches score 1, mismatches score 0; the final score is the average). |

#### **Trajectory Evaluation Methods**

Depending on how strict your agent's process needs to be (e.g., high-stakes environments vs. flexible tasks), you can evaluate trajectories using several ground-truth-based methods:

* **Exact match:** Requires a perfect match to the ideal trajectory.  
* **In-order match:** Requires the correct actions in the correct order but allows for extra actions.  
* **Any-order match:** Requires the correct actions in any order and allows for extra actions.  
* **Precision:** Measures the relevance or correctness of the predicted actions.  
* **Recall:** Measures how many essential actions are captured in the prediction.  
* **Single-tool use:** Checks only for the inclusion of one specific action.

### ---

**Step 2: Choose Your Evaluation Data Approach**

The ADK provides two methods for structuring your evaluation data, depending on the stage of development and the complexity of the test.

#### **Approach A: Test Files (Unit Testing)**

Best used during active development for rapid execution and simple session complexity.

* **Structure:** Each file represents a single agent-model interaction (one session), which may contain multiple turns (user-agent interactions).  
* **Contents:** Includes queries, expected tool use, and reference responses.  
* **Naming Convention:** The framework only checks for the \*.test.json suffix (e.g., evaluation.test.json).

#### **Approach B: Evalsets (Integration Testing)**

Best used for simulating complex, multi-turn conversations and testing heavier integrations. Run these less frequently than test files.

* **Structure:** A single dataset file containing multiple "evals" (distinct sessions).  
* **Contents:** Each eval contains a unique name, an associated initial session state, and one or more turns (user query, expected tool use, expected intermediate responses, and reference response).  
* **Creation:** Because building these manually is complex, you can use the ADK Web UI to capture real sessions and save them directly as evals.

### ---

**Step 3: Execute Your Evaluations**

As a developer, you have three primary ways to run these evaluations depending on your workflow:

1. **Web-Based UI (Interactive)**  
   * Navigate to the **Eval** tab in the Web UI.  
   * Create an evaluation set file.  
   * Load past saved sessions or use your current session and add them as eval cases.  
   * Run evaluations interactively against new versions of your agent.  
2. **Programmatically (CI/CD pipelines)**  
   * Integrate evaluation into your testing pipeline or larger test suites using **pytest**.  
   * Use the AgentEvaluator.evaluate() method to run your test files.  
   * *Note:* If you need to specify an initial session state, store the session details in a file and pass that file into the .evaluate() method.  
3. **Command Line Interface (CLI)**  
   * Run evaluations on an existing evaluation set file directly from your terminal.

### ---

**Step 4: Enable Tracing (Optional but Recommended)**

To get deeper visibility into your agent's operations during evaluation and runtime, enable cloud tracing.

* Open your project's .env file.  
* Add the following configuration: AF\_Trace\_to\_Cloud=1

