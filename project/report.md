# Prompting Comparison Report

## Objective

This project compares two prompting strategies for an offline e-commerce customer support chatbot powered by Ollama and Llama 3.2 3B:

- Zero-shot prompting
- One-shot prompting

The goal is to measure how much a single worked example improves the quality of customer support responses.

## Evaluation Criteria

Each response is scored with a lightweight 1-5 heuristic for:

- Relevance: Does the answer address the customer issue directly?
- Coherence: Is the answer clear, organized, and easy to follow?
- Helpfulness: Does the answer include useful next steps?

## Zero-shot Observations

Strengths:

- Fast to design because it needs only an instruction and the user query
- Usually acceptable for simple questions such as shipping times or order tracking
- Good baseline for comparison

Limitations:

- Can sound generic or inconsistent
- May skip empathy or resolution steps on more complex issues
- Often needs stronger prompting to maintain the same tone across many queries

## One-shot Observations

Strengths:

- More consistent tone because the example demonstrates the desired support style
- Often produces better step-by-step guidance
- More likely to ask for missing details when they are needed

Limitations:

- Slightly longer prompt on every request
- Quality depends on the example being representative
- Can bias the model toward one response pattern

## Which Performs Better?

One-shot prompting is the stronger default choice for this project.

Why it usually performs better:

- The example anchors the model in a customer support tone
- It improves consistency across different query types
- It encourages practical next steps instead of vague replies
- It often increases helpfulness more than zero-shot prompting

Zero-shot is still useful as a simple baseline, but one-shot is generally better for realistic support simulation.

## Final Conclusion

If your goal is to simulate an e-commerce support assistant that feels more reliable and more action-oriented, one-shot prompting is the better strategy. Zero-shot remains valuable for baseline evaluation, but one-shot will usually produce stronger relevance, coherence, and helpfulness across the 20 sample queries.
