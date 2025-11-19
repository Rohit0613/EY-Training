import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge import Rouge
from sentence_transformers import SentenceTransformer, util

# ---------------------------
# 1. Load environment vars
# ---------------------------
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in .env")

# ---------------------------
# 2. Define two models
# ---------------------------
model_1 = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    temperature=0.7,
    max_tokens=256,
    api_key=api_key,
    base_url=base_url,
)

model_2 = ChatOpenAI(
    model="mistralai/mixtral-8x7b-instruct",
    temperature=0.7,
    max_tokens=256,
    api_key=api_key,
    base_url=base_url,
)

# ---------------------------
# 3. Define prompt
# ---------------------------
messages = [
    SystemMessage(content="You are a helpful and concise AI assistant."),
    HumanMessage(content="<s>[INST] Explain in simple terms what reinforcement learning is. [/INST]")
]

# ---------------------------
# 4. Get responses
# ---------------------------
response_1 = model_1.invoke(messages).content.strip()
response_2 = model_2.invoke(messages).content.strip()

print("\n--- MODEL 1: Mistral 7B ---")
print(response_1)
print("\n--- MODEL 2: Mixtral 8x7B ---")
print(response_2)

# ---------------------------
# 5. Evaluate responses
# ---------------------------

# BLEU
smooth_fn = SmoothingFunction().method1
bleu_score = sentence_bleu(
    [response_1.split()],
    response_2.split(),
    smoothing_function=smooth_fn
)

# ROUGE
rouge = Rouge()
rouge_scores = rouge.get_scores(response_1, response_2)[0]

# Cosine similarity using embeddings
embedder = SentenceTransformer("all-MiniLM-L6-v2")
emb1 = embedder.encode(response_1, convert_to_tensor=True)
emb2 = embedder.encode(response_2, convert_to_tensor=True)
cosine_sim = float(util.cos_sim(emb1, emb2))

# ---------------------------
# 6. Display results
# ---------------------------
print("\n--- Evaluation Metrics ---")
print(f"BLEU Score:  {bleu_score:.4f}")
print(f"ROUGE-1:     {rouge_scores['rouge-1']['f']:.4f}")
print(f"ROUGE-L:     {rouge_scores['rouge-l']['f']:.4f}")
print(f"Cosine Sim:  {cosine_sim:.4f}")
