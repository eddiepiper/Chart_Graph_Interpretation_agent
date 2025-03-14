from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

models = client.models.list()
print("Available models:")
for model in models.data:
    print(f"- {model.id}") 