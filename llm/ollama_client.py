import ollama

def get_ollama_stream(message: str):
    stream = ollama.chat(
        model='mistral',
        messages=[{'role': 'user', 'content': message}],
        stream=True,
    )
    for chunk in stream:
        yield chunk['message']['content']
