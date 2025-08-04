
# Local LLM Chat App

This is a real-time chat application using Streamlit, FastAPI, and Ollama's local LLMs.

## Project Structure

- `backend/`: The FastAPI backend that serves the LLM.
- `frontend/`: The Streamlit frontend for the user interface.
- `llm/`: Contains the LLM logic (in this case, handled by the `ollama` library).

## Setup and Usage

### Prerequisites

- Python 3.7+
- Ollama installed and running with the `mistral` model.

### Backend Setup

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the FastAPI server:
    ```bash
    uvicorn main:app --reload
    ```

### Frontend Setup

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the Streamlit app:
    ```bash
    streamlit run app.py
    ```

Now, open your browser to the Streamlit URL (usually `http://localhost:8501`) to use the chat application.
