from transformers import pipeline
import gradio as gr

# Load the sentiment analysis pipeline from Hugging Face
classifier = pipeline("sentiment-analysis")

# Define a function to classify sentiment
def classify_sentiment(text):
    result = classifier(text)[0]
    return f"Sentiment: {result['label']}, with score: {result['score']:.4f}"

# Set up a simple Gradio interface for input and output
demo = gr.Interface(fn=classify_sentiment, inputs="text", outputs="text", live=True)

# Launch the app
demo.launch()
 