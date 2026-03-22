# Offline AI Customer Support Chatbot

This project is a fully local Python chatbot that simulates an e-commerce customer support agent using Ollama and the Llama 3.2 3B model. It compares zero-shot and one-shot prompting across 20 realistic support queries and saves the generated responses to Markdown for review.

## Project Structure

```text
project/
|-- prompts/
|   |-- zero_shot_template.txt
|   `-- one_shot_template.txt
|-- eval/
|   `-- results.md
|-- chatbot.py
|-- setup.md
|-- report.md
`-- README.md
```

## Features

- Fully offline workflow with local Ollama inference
- Required Ollama endpoint: `http://localhost:11434/api/generate`
- Required model: `llama3.2:3b`
- Zero-shot vs one-shot prompt comparison
- 20 realistic e-commerce support queries
- Markdown export to `eval/results.md`
- Built-in timestamped logging
- Optional custom query file support
- Heuristic scoring for relevance, coherence, and helpfulness

## Tech Stack

- Python 3
- `requests`
- Ollama
- Llama 3.2 3B

## How To Run

1. Install Ollama and pull the model:

```bash
ollama pull llama3.2:3b
```

2. Make sure Ollama is running locally.

3. Create and activate a virtual environment, then install the dependency:

```bash
python -m venv .venv
pip install requests
```

4. Run the evaluation script:

```bash
python chatbot.py
```

5. Open `eval/results.md` to review the zero-shot and one-shot outputs.

## Sample Output

```text
## Query 1
Customer Query: How do I track my order?

Zero-shot Response:
You can track your order by opening the shipping confirmation email and selecting the tracking link. If you have not received the email yet, please sign in to your account and check the Orders section. If you still cannot find the tracking details, share your order number and we can help you look it up.

Zero-shot Scores: Relevance: 5/5 | Coherence: 5/5 | Helpfulness: 5/5 | Average: 5.0/5

One-shot Response:
I am happy to help you track your order. Please open your shipping confirmation email and click the tracking link, or sign in to your account and view the Orders section for the latest shipment status. If the tracking page is not updating, send your order number and email address so we can check it for you.

One-shot Scores: Relevance: 5/5 | Coherence: 5/5 | Helpfulness: 5/5 | Average: 5.0/5
```

## Custom Queries

You can run the chatbot with your own dataset:

```bash
python chatbot.py --queries-file custom_queries.txt
```

Use one customer query per line in the custom file.

## Notes

- This project does not call any external API
- All generation happens locally through Ollama
- The included scoring is heuristic and intended for quick comparison, not formal benchmarking

## Documentation

- Setup instructions: `setup.md`
- Prompt comparison report: `report.md`
- Generated evaluation file: `eval/results.md`
