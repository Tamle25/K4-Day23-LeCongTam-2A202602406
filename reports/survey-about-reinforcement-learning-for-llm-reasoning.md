# Survey of Reinforcement Learning for LLM Reasoning

## TL;DR
- Reinforcement Learning (RL) has become central to training Large Language Models (LLMs) for complex reasoning tasks by directly optimizing for process and outcome success [1][2].
- Modern reasoning models (e.g., DeepSeek-R1) leverage RL to incentivize chain-of-thought (CoT) generation, bypassing the limitations of supervised fine-tuning [3].
- Process-based Reward Models (PRMs) improve credit assignment by evaluating reasoning trajectories token-by-token rather than just the final answer [2].
- Open challenges include sample inefficiency, reward hacking during self-play, and the emergence of redundant "overthinking" in large reasoning models [3][4].

## Background
Reasoning in LLMs refers to the ability to decompose complex problems into logical sequences, often represented as Chain-of-Thought (CoT). Traditional LLMs were primarily trained via supervised learning on massive datasets, but RL methods—rooted in foundational policy gradient approaches [1]—have significantly improved performance. By utilizing Reinforcement Learning from Human Feedback (RLHF) [4] and increasingly, automated verifiers, researchers can train models to perform multi-step reasoning tasks such as mathematical problem-solving or code generation.

## Foundational RL for Reasoning
Foundational advancements in policy gradient methods [1] provide the mathematical underpinning for optimizing LLMs. The transition from outcome-supervised reward models (ORMs) to process-supervised reward models (PRMs) [2] represents a major leap in reasoning capability. PRMs allow for finer-grained reward signals at each reasoning step, which helps the model learn to backtrack when it reaches an invalid logical intermediate state. This paradigm has been foundational for the current generation of reasoning-centric RL frameworks.

## Modern Architectures and RL Post-Training
Current state-of-the-art architectures, such as DeepSeek-R1 [3], demonstrate the efficacy of RL post-training on massive scale. Rather than relying heavily on pre-labelled reasoning traces, these models use group-based policy optimization and verifiable feedback loops to elicit reasoning autonomously. However, these models face the "overthinking" problem, where they may generate redundant CoT traces even after identifying the final answer. Current mitigation strategies involve structural steering vectors and training objectives that penalize excessive token usage once a solution path is clear [3].

## Applications and Benchmarking
RL-based LLM reasoning is extensively benchmarked on mathematical datasets like MATH and GSM8K, as well as code generation benchmarks like HumanEval [5]. Empirical studies suggest that training on synthetic, rule-verifiable logical puzzles significantly generalizes to harder, unseen mathematical problems. Furthermore, frameworks integrating offline RL with value-function learning have shown success in enabling guided test-time search, allowing models to evaluate multiple potential reasoning paths before committing to an final output [5][6].

## Trends and Open Problems
The current landscape focuses on improving sample efficiency through adaptive reasoning budgets and robust reward shaping [3]. While PRMs reduce the need for sparse outcome rewards, they remain susceptible to reward hacking where models generate "gibberish" logical steps that happen to arrive at a correct final token [2]. Future research trends emphasize transparent reasoning, ensuring that the model's intermediate logic is interpretable, and developing training objectives that prevent "model collapse" in iterative self-play [3].

## References
1. Policy Gradient Methods for Reinforcement Learning with Function Approximation - https://papers.nips.cc/paper/1713-policy-gradient-methods-for-reinforcement-learning-with-function-approximation (arxiv)
2. Let's Verify Step by Step - https://arxiv.org/abs/2305.20050 (arxiv)
3. DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning - https://huggingface.co/papers/2501.12948 (hf-search)
4. Training language models to follow instructions with human feedback - https://arxiv.org/abs/2203.02155 (arxiv)
5. LLM Reasoning and RL: A Survey - https://lilianweng.github.io/posts/2023-12-07-llm-reasoning/ (web)
6. Introduction to RLHF - https://huggingface.co/blog/rlhf (hf-search)

## References
[1] Policy Gradient Methods for Reinforcement Learning with Function Approximation. arxiv. https://papers.nips.cc/paper/1713-policy-gradient-methods-for-reinforcement-learning-with-function-approximation (1999-01-01)
[2] Let's Verify Step by Step. arxiv. https://arxiv.org/abs/2305.20050 (2023-05-30)
[3] DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. hf-search. https://huggingface.co/papers/2501.12948 (2025-01-22)
[4] Training language models to follow instructions with human feedback. arxiv. https://arxiv.org/abs/2203.02155 (2022-03-04)
[5] LLM Reasoning and RL: A Survey. web. https://lilianweng.github.io/posts/2023-12-07-llm-reasoning/ (2023-12-07)
[6] Introduction to RLHF. hf-search. https://huggingface.co/blog/rlhf (2023-01-01)
