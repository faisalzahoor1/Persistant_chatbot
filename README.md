# Persistent Chatbot

A ChatGPT-style chatbot with a web UI, built with **Streamlit**, **LangGraph** and **Google Gemini**. It streams replies token by token, supports multiple conversations in a sidebar, and (in the database version) remembers every conversation across app restarts using SQLite.

## Features

- Chat UI with streaming responses
- Multiple conversation threads — start a **New Chat** or switch between old ones from the sidebar
- Automatic chat titles taken from the first message of each conversation
- Two versions:
  - **In-memory** (`frontend.py` + `backend.py`) — history lasts only while the app is running
  - **Persistent** (`frontend_with_database.py` + `backend_with_database.py`) — history and titles are saved to SQLite and reloaded on restart

## Technologies Used

| Technology | Purpose |
| --- | --- |
| [Python](https://www.python.org/) | Programming language |
| [Streamlit](https://streamlit.io/) | Web UI (`st.chat_input`, `st.chat_message`, `st.write_stream`, sidebar) |
| [LangGraph](https://langchain-ai.github.io/langgraph/) | Builds the chatbot as a state graph (`StateGraph`) and manages conversation memory via checkpointers |
| [LangChain Core](https://python.langchain.com/) | Message types (`HumanMessage`, `BaseMessage`) |
| [LangChain Google GenAI](https://pypi.org/project/langchain-google-genai/) | Connects to the Google Gemini model (`gemini-3.5-flash-lite`) |
| `InMemorySaver` | LangGraph checkpointer that keeps chats in RAM (in-memory version) |
| `SqliteSaver` (`langgraph-checkpoint-sqlite`) | LangGraph checkpointer that stores chats in `chatbot.db` (persistent version) |
| SQLite (`sqlite3`) | Stores conversation checkpoints and chat titles (`chat_titles.db`) |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Loads the API key from a `.env` file |
| `uuid` | Generates a unique ID for each conversation thread |

## How It Works

```
User ──► Streamlit UI ──► LangGraph graph ──► Gemini LLM
              ▲               │
              │               ▼
        streamed reply   Checkpointer (memory / SQLite)
```

1. **State** — `ChatState` holds a list of messages. The `add_messages` reducer appends new messages instead of overwriting them.
2. **Graph** — a single node, `chat_node`, sends the full message history to Gemini and returns the reply. The graph is `START → chat_node → END`.
3. **Memory** — the graph is compiled with a checkpointer. Each conversation has its own `thread_id`, so LangGraph saves and restores the history per thread.
4. **Streaming** — the frontend calls `chatbot.stream(..., stream_mode="messages")` and passes the chunks to `st.write_stream` so the reply appears as it is generated.
5. **Threads in the sidebar** — every new chat gets a UUID. Clicking a conversation loads its messages with `chatbot.get_state(config)`.
6. **Persistence** — in the database version, `retrieve_all_threads()` lists all saved threads from `chatbot.db`, and titles are stored in a `chat_titles` table in `chat_titles.db`.

## Project Structure

```
.
├── backend.py                  # LangGraph chatbot with in-memory checkpointer
├── frontend.py                 # Streamlit UI for the in-memory version
├── backend_with_database.py    # LangGraph chatbot with SQLite checkpointer
├── frontend_with_database.py   # Streamlit UI with persistent threads and titles
├── requirements.txt            # Python dependencies
└── .env                        # Your Google API key (not committed)
```

## Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/faisalzahoor1/Persistant_chatbot.git
   cd Persistant_chatbot
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your Gemini API key** — get one from [Google AI Studio](https://aistudio.google.com/apikey) and create a `.env` file:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

5. **Run the app**
   ```bash
   # Persistent version (recommended)
   streamlit run frontend_with_database.py

   # In-memory version
   streamlit run frontend.py
   ```

6. Open the URL Streamlit prints (usually http://localhost:8501) and start chatting.

## Build Steps (how this bot was made)

1. Defined a `ChatState` `TypedDict` with a `messages` list using the `add_messages` reducer.
2. Created the Gemini LLM with `ChatGoogleGenerativeAI`.
3. Wrote `chat_node`, which calls the LLM with the conversation so far.
4. Built a LangGraph `StateGraph` with one node and compiled it with `InMemorySaver` for memory.
5. Built a Streamlit chat UI using `st.chat_input` and `st.chat_message`, keeping message history in `st.session_state`.
6. Switched from `invoke` to `stream` with `st.write_stream` for live, token-by-token replies.
7. Added multiple conversations: UUID thread IDs, a **New Chat** button, and a sidebar list to reload old chats.
8. Added chat titles generated from the first user message.
9. Replaced `InMemorySaver` with `SqliteSaver` so conversations survive restarts, and added `retrieve_all_threads()` to list them.
10. Stored chat titles in a separate SQLite table so they persist as well.
