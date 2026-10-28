import streamlit as st
from backend_with_database import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid
import sqlite3

DB_PATH = "chat_titles.db"



def init_title_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_titles (
                thread_id TEXT PRIMARY KEY,
                title TEXT NOT NULL
            )
        """)


def save_chat_title(thread_id, title):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO chat_titles (thread_id, title)
            VALUES (?, ?)
            ON CONFLICT(thread_id)
            DO UPDATE SET title = excluded.title
            """,
            (str(thread_id), title)
        )


def get_chat_titles():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT thread_id, title FROM chat_titles"
        ).fetchall()

    return dict(rows)


init_title_db()





def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_threads(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_threads(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    config = {
        'configurable': {
            'thread_id': str(thread_id)
            }
    }
    state = chatbot.get_state(config)
    if not state.values:
        return []
    return state.values.get('messages', [])

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if 'chat_titles' not in st.session_state:
    st.session_state['chat_titles'] = get_chat_titles()

add_threads(st.session_state['thread_id'])

CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

st.sidebar.title("Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads']:
    title = st.session_state['chat_titles'].get(
        str(thread_id), "New Chat"
    )
    if st.sidebar.button(title, key=str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            content = msg.content

            if isinstance(content, list):
                content = ''.join(
                    block.get('text', '')
                    for block in content
                    if isinstance(block, dict)
                    and block.get('type') == 'text'
                )
            temp_messages.append({'role': role, 'content': content})

        st.session_state['message_history'] = temp_messages



for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:

    thread_key = str(st.session_state['thread_id'])

    if thread_key not in st.session_state['chat_titles']:
        title = ' '.join(user_input.split())

        # Keep the sidebar title short
        if len(title) > 35:
            title = title[:32] + '...'

        save_chat_title(thread_key, title)

        st.session_state['chat_titles'][thread_key] = title



    st.session_state['message_history'].append({'role':'user', 'content':user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]}, config=CONFIG)
    # ai_message = response['messages'][-1].content[0]["text"]
    with st.chat_message('assistant'):

        def stream_text():
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config = CONFIG,
                stream_mode = 'messages'
            ):
                content = message_chunk.content
                print(content)

                # Case 1: Content is already a string
                if isinstance(content, str):
                    text = content

                # Case 2: Content is a list of blocks
                elif isinstance(content, list):
                    text = ''.join(
                        block.get('text', '')
                        for block in content
                        if isinstance(block, dict)
                        and block.get('type') == 'text'
                        and isinstance(block.get('text'), str)
                    )

                # Case 3: Unknown content format
                else:
                    text = ''

                # Skip empty chunks
                if text:
                    yield text

        ai_message = st.write_stream(stream_text())
    st.session_state['message_history'].append({'role':'assistant', 'content':ai_message})
        # st.text(ai_message)
