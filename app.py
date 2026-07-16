import streamlit as st
import os
import json
import shutil
import chromadb
from src.document_loader import load_documents
from src.text_splitter import split_documents
from src.vector_store import create_vector_store
from src.chatbot import ask_question
from utils.helpers import register_user, authenticate_user


st.set_page_config(page_title="Enterprise AI Document Assistant", layout="wide")


# --- Session state setup ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- LOGIN / REGISTER SCREEN ---
def show_login_screen():
    st.title("📄 Enterprise AI Document Assistant")
    st.caption("Please log in or create an account to continue.")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Log In"):
            success, message = authenticate_user(login_username.strip(), login_password)
            if success:
                st.session_state.username = login_username.strip()
            if success:
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with tab2:
        st.subheader("Create Account")
        reg_username = st.text_input("Choose a username", key="reg_username")
        reg_password = st.text_input("Choose a password", type="password", key="reg_password")

        if st.button("Register"):
            success, message = register_user(reg_username, reg_password)
            if success:
                st.success(message + " You can now log in.")
            else:
                st.error(message)


# --- MAIN APP (only shown after login) ---
def show_main_app():
    username = st.session_state.username
    upload_folder = f"data/users/{username}/uploaded_documents"
    chroma_folder = f"data/users/{username}/chroma_db"
    history_file = f"data/users/{username}/chat_history.json"

    os.makedirs(upload_folder, exist_ok=True)

    # Load this user's saved chat history the first time they log in this session
    if not st.session_state.get("history_loaded_for") == username:
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                st.session_state.chat_history = json.load(f)
        else:
            st.session_state.chat_history = []
        st.session_state.history_loaded_for = username

    # --- Top bar ---
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title("📄 Enterprise AI Document Assistant")
        st.caption(f"Logged in as: **{username}**")
    with col2:
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.chat_history = []
            st.rerun()

    def get_uploaded_filenames():
        if not os.path.exists(upload_folder):
            return []
        return os.listdir(upload_folder)

    def rebuild_database_from_all_files():
        chromadb.api.client.SharedSystemClient.clear_system_cache()
        if os.path.exists(chroma_folder):
            shutil.rmtree(chroma_folder, ignore_errors=True)

        docs = load_documents(upload_folder)
        chunks = split_documents(docs)

        if chunks:
            create_vector_store(chunks, username)
            return len(chunks)
        return 0

    # --- Sidebar: Upload & manage documents ---
    with st.sidebar:
        st.header("📁 Document Management")

        st.subheader("Upload New Documents")
        new_files = st.file_uploader(
            "Upload PDF or Word files",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key="uploader"
        )

        if st.button("Add Documents"):
            if new_files:
                for file in new_files:
                    file_path = os.path.join(upload_folder, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())

                with st.spinner("Processing documents..."):
                    num_chunks = rebuild_database_from_all_files()

                st.success(f"Added {len(new_files)} file(s)! Database now has {num_chunks} chunks.")
                st.rerun()
            else:
                st.warning("Please select at least one file first.")

        st.divider()
        st.subheader("Your Uploaded Files")
        current_files = get_uploaded_filenames()

        if current_files:
            file_to_delete = None

            for filename in current_files:
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.text(filename)
                with c2:
                    if st.button("✏️", key=f"rename_{filename}", help="Rename"):
                        st.session_state[f"renaming_{filename}"] = True
                with c3:
                    if st.button("🗑️", key=f"delete_{filename}"):
                        file_to_delete = filename

                # Show rename input if this file's rename button was clicked
                if st.session_state.get(f"renaming_{filename}", False):
                    new_name = st.text_input(
                        "New filename (keep the extension, e.g. .pdf or .docx)",
                        value=filename,
                        key=f"newname_{filename}"
                    )
                    rc1, rc2 = st.columns([1, 1])
                    with rc1:
                        if st.button("Save", key=f"save_rename_{filename}"):
                            old_path = os.path.join(upload_folder, filename)
                            new_path = os.path.join(upload_folder, new_name)
                            if new_name != filename and not os.path.exists(new_path):
                                os.rename(old_path, new_path)
                                with st.spinner("Updating database..."):
                                    rebuild_database_from_all_files()
                                st.session_state[f"renaming_{filename}"] = False
                                st.success(f"Renamed to {new_name}")
                                st.rerun()
                            elif os.path.exists(new_path):
                                st.error("A file with that name already exists.")
                    with rc2:
                        if st.button("Cancel", key=f"cancel_rename_{filename}"):
                            st.session_state[f"renaming_{filename}"] = False
                            st.rerun()

            if file_to_delete:
                os.remove(os.path.join(upload_folder, file_to_delete))
                with st.spinner("Updating database..."):
                    rebuild_database_from_all_files()
                st.success(f"Deleted {file_to_delete}")
                st.rerun()

            st.divider()
            st.subheader("Replace a Document")
            file_to_replace = st.selectbox("Choose file to replace:", current_files, key="replace_select")
            replacement_file = st.file_uploader(
                "Upload the new version (same or different name)",
                type=["pdf", "docx"],
                key="replace_uploader"
            )
            if st.button("Replace"):
                if replacement_file:
                    old_path = os.path.join(upload_folder, file_to_replace)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                    new_path = os.path.join(upload_folder, replacement_file.name)
                    with open(new_path, "wb") as f:
                        f.write(replacement_file.getbuffer())

                    with st.spinner("Updating database..."):
                        rebuild_database_from_all_files()

                    st.success(f"Replaced {file_to_replace} with {replacement_file.name}")
                    st.rerun()
                else:
                    st.warning("Please upload a replacement file first.")
        else:
            st.text("No files uploaded yet.")
        st.header("Quick Document Actions")

    current_files_for_actions = get_uploaded_filenames()
    if current_files_for_actions:
        action_file = st.selectbox(
            "Choose a document (or select 'All documents'):",
            ["All documents"] + current_files_for_actions,
            key="action_file_select"
        )
        action_filename_filter = None if action_file == "All documents" else os.path.join(upload_folder, action_file)

        col1, col2, col3, col4 = st.columns(4)

        from src.chatbot import summarize_document, generate_key_points, generate_faqs, extract_action_items

        with col1:
            if st.button("📝 Summarize"):
                with st.spinner("Summarizing..."):
                    result = summarize_document(username, action_filename_filter)
                st.session_state.chat_history.append({
                    "question": f"Summarize {action_file}",
                    "answer": result,
                    "sources": []
                })
                with open(history_file, "w") as f:
                    json.dump(st.session_state.chat_history, f, indent=2)
                st.rerun()

        with col2:
            if st.button("🔑 Key Points"):
                with st.spinner("Extracting key points..."):
                    result = generate_key_points(username, action_filename_filter)
                st.session_state.chat_history.append({
                    "question": f"Key points from {action_file}",
                    "answer": result,
                    "sources": []
                })
                with open(history_file, "w") as f:
                    json.dump(st.session_state.chat_history, f, indent=2)
                st.rerun()

        with col3:
            if st.button("❓ Generate FAQs"):
                with st.spinner("Generating FAQs..."):
                    result = generate_faqs(username, action_filename_filter)
                st.session_state.chat_history.append({
                    "question": f"FAQs for {action_file}",
                    "answer": result,
                    "sources": []
                })
                with open(history_file, "w") as f:
                    json.dump(st.session_state.chat_history, f, indent=2)
                st.rerun()

        with col4:
            if st.button("✅ Action Items"):
                with st.spinner("Extracting action items..."):
                    result = extract_action_items(username, action_filename_filter)
                st.session_state.chat_history.append({
                    "question": f"Action items in {action_file}",
                    "answer": result,
                    "sources": []
                })
                with open(history_file, "w") as f:
                    json.dump(st.session_state.chat_history, f, indent=2)
                st.rerun()

    st.divider()

    # --- Main area: Chat interface ---
    st.header("Ask a Question")

    current_files = get_uploaded_filenames()
    file_options = ["All documents"] + current_files
    selected_file = st.selectbox("Search within:", file_options)

    question = st.text_input("Type your question here:", key="question_input")

    if st.button("Ask"):
        if not current_files:
            st.warning("Please upload at least one document first.")
        elif question:
            filename_filter = None if selected_file == "All documents" else os.path.join(upload_folder, selected_file)

            with st.spinner("Thinking..."):
                result = ask_question(
                    question,
                    username=username,
                    chat_history=st.session_state.chat_history,
                    filename_filter=filename_filter
                )

            st.session_state.chat_history.append({
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"]
            })
            with open(history_file, "w") as f:
                json.dump(st.session_state.chat_history, f, indent=2)
        else:
            st.warning("Please type a question first.")

    for chat in reversed(st.session_state.chat_history):
        st.markdown(f"**🧑 Question:** {chat['question']}")
        st.markdown(f"**🤖 Answer:** {chat['answer']}")

        with st.expander("View sources"):
            for i, source in enumerate(chat["sources"]):
                st.markdown(f"**📄 {source['filename']} — Page {source['page']}**")
                st.text(source['text'][:300])
                st.divider()

        st.divider()


# --- Router ---
if st.session_state.logged_in:
    show_main_app()
else:
    show_login_screen()