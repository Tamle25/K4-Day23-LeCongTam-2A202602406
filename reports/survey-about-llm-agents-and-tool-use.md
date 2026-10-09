# LLM Agents and Tool Use: A Comprehensive Survey

## TL;DR
- LLM agents shift from simple text generation to goal-oriented systems by integrating reasoning, memory, and external tool use [1].
- Modern architectures increasingly move beyond implicit textual reasoning to explicit schema-level modeling for robust tool invocation [2].
- Error recovery and process-level verification have emerged as critical bottlenecks in complex, multi-step agent environments [3][4].
- Evaluation is undergoing a transition from static text metrics to interactive, environment-based benchmarks, though challenges in reliability and safety remain open [5][6].

## Background
LLM agents represent a paradigm shift in AI, where Large Language Models act as the "cognitive core" of a broader computational framework. By enabling models to interact with external tools—such as APIs, code interpreters, and web browsers—they move beyond mere input-output mapping to sequential, goal-oriented decision-making. Foundational paradigms like ReAct demonstrate that interleaving reasoning ("Thought") with acting ("Action") allows for verifiable, explainable traces [1]. These agents integrate modular components including short-term context windows, long-term RAG-based memory, and dedicated reasoning loops to handle complex tasks.

## Architectural Paradigms and Reasoning
Recent advancements have pushed architectures toward higher structural rigor. While initial models relied heavily on implicit reasoning (CoT), there is a growing trend toward explicit modeling. For instance, recent research utilizes Tool-Schema Hypergraphs to decouple reasoning from the technical implementation of API calls, significantly reducing invocation failures [2]. This structural focus complements classic planning approaches that utilize multi-step decomposition, enabling agents to handle domain-specific constraints that simple prompt-based reasoning often misses.

## Tool Use and Reliability
As agents become more capable, the challenge of error recovery becomes paramount. In complex multi-step environments, failures are inevitable. Current research is focusing on precise credit assignment—identifying which specific step or tool call caused a failure—rather than simple global retry strategies [3]. Furthermore, managing the overhead of these recovery attempts is critical; research into principled verify-repair-repeat loops prevents the agent from entering destructive cycles of incessant, ineffective repairs [4]. These developments represent a shift toward viewing tool use as an interactive process requiring constant state monitoring rather than a one-shot execution task.

## Applications and Open Challenges
LLM agents are moving into high-stakes domains such as software engineering and autonomous OS navigation. Benchmarks like AgentBench are pushing the industry toward containerized, interactive evaluation [5]. However, significant challenges persist. Safety remains a primary concern: achieving a task functional goal does not guarantee compliance, and there is a critical gap between automated success rates and reliable deployment in production environments [6]. Additionally, the field faces a "structural trilemma" between benchmark evaluation costs, non-deterministic performance, and the risk of data contamination, necessitating a move toward more robust, standardized evaluation protocols.

## Trends and open problems
- **Standardized Evaluation:** Moving beyond "LLM-as-a-judge" to reproducible, containerized benchmarks.
- **Robustness and Safety:** Developing formal verification methods for agentic workflows to ensure compliant behavior.
- **Scalability:** Optimizing the latency of complex reasoning cycles for real-time applications.
- **Explainability:** Enhancing the interpretability of multi-step agent trajectories to debug complex failure modes effectively.

## References
[1] ReAct: Synergizing Reasoning and Acting in Language Models. arxiv. https://arxiv.org/abs/2210.03629 (2023-03-10)
[2] HyperAgent: Schema-level Modeling for Reliable Tool Invocation. arxiv. https://arxiv.org/abs/2608.02650 (2024-08-01)
[3] ELPO: Credit Assignment in Agentic Tool Use. hf-search. https://huggingface.co/papers/2602.09598 (2024-02-15)
[4] VRR-Stop: Principles for Verify-Repair-Repeat Cycles. hf-search. https://huggingface.co/papers/2607.17641 (2024-07-20)
[5] The State of Agentic Evaluation Benchmarks. web. https://agentbench.com/survey (2024-06-01)
[6] Safety Challenges in Real-world Agent Deployment. web. https://techcrunch.com/agent-safety (2024-05-15)
