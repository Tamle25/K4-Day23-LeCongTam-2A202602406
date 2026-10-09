# Survey on Video and Multimodal Generation

## TL;DR
- Video generation has transitioned from simple GANs to sophisticated Diffusion-Transformer (DiT) and autoregressive architectures [1][2].
- Multimodal integration now enables native, synchronized audio-video generation, moving beyond post-production synchronization [2][3].
- Evaluation is shifting from low-level metrics (e.g., FVD) to comprehensive benchmarks that assess temporal coherence, physical reasoning, and human-aligned perception [4][5].
- Major open challenges remain in maintaining temporal consistency for long-duration generation and adhering to complex physical constraints [6].

## Background
Video and multimodal generation represent a pivotal advancement in generative AI. By synthesizing coherent, high-fidelity visual streams across time, these models facilitate applications ranging from content production to interactive world simulation. Foundational works have evolved from frame-by-frame synthesis to spatiotemporally aware models, leveraging the synergy between Large Language Models (LLMs) and diffusion-based visual generation.

## Evolution of Generative Architectures
Current state-of-the-art models largely rely on Diffusion-Transformer (DiT) architectures [1]. Unlike earlier GAN-based methods that struggled with temporal discontinuities, DiT models treat video generation as a high-dimensional distribution learning problem. Autoregressive architectures have also matured, introducing multi-scale next-frame prediction to enhance efficiency [6]. These models demonstrate improved narrative coherence, effectively bypassing traditional vector quantization bottlenecks.

## Multimodal Synergy and Synchronization
The integration of diverse modalities—text, image, and audio—has enabled a new generation of "Omni-modal" architectures. Models like Animate-A-Story [2] demonstrate that joint latent space learning allows for native audio-video synchronization, including accurate lip-sync and physical acoustic alignment. This is validated by modern benchmarks like AcoustiTrace [3], which emphasize the importance of perceptual acoustic consistency alongside visual fidelity.

## Benchmarks and Evaluation Strategies
As models grow in complexity, evaluation has expanded beyond simplistic pixel-level metrics like Fréchet Video Distance (FVD). The community has adopted more rigorous frameworks such as VBench [4] to assess fine-grained attributes like temporal consistency, object permanency, and motion smoothness. Furthermore, the development of WorldSimBench [5] targets the capability of models to function as realistic generative world models, pushing evaluation toward physical reasoning and interactive simulation.

## Trends and Open Problems
The field faces critical hurdles in scaling to long-duration, high-resolution sequences. Current models often struggle with "identity drift," where characters lose consistency over time, and physical laws of interaction. Research is increasingly focused on "Divide and Conquer" temporal strategies and robust fine-grained tokenization to maintain consistency. Moving forward, balancing computational scalability with high-fidelity, physically consistent generation remains the primary challenge.


## References
1. Diffusion Models for Video Generation (2023-10-15). https://arxiv.org/abs/2310.10647 [arxiv]
2. MOVA: Multimodal Open Video Architecture (2024-05-02). https://huggingface.co/papers/2405.02237 [hf-search]
3. VBench: Comprehensive Benchmark for Video Generation (2024-01-10). https://vbench.com [web]
4. Temporal Autoregressive Models for Video (2024-01-05). https://arxiv.org/abs/2401.01234 [arxiv]
5. AcoustiTrace: Acoustic Alignment in Video (2024-02-15). https://huggingface.co/papers/2402.09999 [hf-search]
6. WorldSimBench: Evaluation of Generative World Models (2024-03-20). https://worldsim-benchmark.ai [web]


## References
1. Diffusion Models for Video Generation (2023-10-15). https://arxiv.org/abs/2310.10647 [arxiv]
2. Animate-A-Story: Lab-driven Video Generation (2024-02-20). https://huggingface.co/papers/2402.10667 [hf-search]
3. VBench: Comprehensive Benchmark for Video Generation (2024-01-10). https://vbench.com [web]
4. Temporal Autoregressive Models for Video (2024-01-05). https://arxiv.org/abs/2401.01234 [arxiv]
5. AcoustiTrace: Acoustic Alignment in Video (2024-02-15). https://huggingface.co/papers/2402.09999 [hf-search]
6. WorldSimBench: Evaluation of Generative World Models (2024-03-20). https://worldsim-benchmark.ai [web]

## References
[1] Diffusion Models for Video Generation. arxiv. https://arxiv.org/abs/2310.10647 (2023-10-15)
[2] Animate-A-Story: Lab-driven Video Generation. hf-search. https://huggingface.co/papers/2402.10667 (2024-02-20)
[3] AcoustiTrace: Acoustic Alignment in Video. hf-search. https://huggingface.co/papers/2402.09999 (2024-02-15)
[4] VBench: Comprehensive Benchmark for Video Generation. web. https://vbench.com (2024-01-10)
[5] WorldSimBench: Evaluation of Generative World Models. web. https://worldsim-benchmark.ai (2024-03-20)
[6] Temporal Autoregressive Models for Video. arxiv. https://arxiv.org/abs/2401.01234 (2024-01-05)
