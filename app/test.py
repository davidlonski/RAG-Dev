import chromadb
import streamlit as st
from dotenv import load_dotenv
import os
import json

st.title("ChromaDB Test")

def init_session_state():
    if "app_stage" not in st.session_state:
        st.session_state.app_stage = "dashboard"
    if "collections" not in st.session_state:
        st.session_state.collections = []


def load_chroma_db():
    load_dotenv()
    HOST=os.getenv("CHROMA_SERVER_HOST")
    PORT=os.getenv("CHROMA_SERVER_HTTP_PORT")

    return chromadb.HttpClient(host=HOST, port=PORT)


init_session_state()

client = load_chroma_db()
collection_names = client.list_collections()

st.header("ChromaDB Collections")

# --- CREATE Collection ---
with st.expander("Create New Collection"):
    new_collection_name = st.text_input("Collection Name", key="new_collection_name")
    if st.button("Create Collection"):
        if new_collection_name:
            try:
                client.create_collection(new_collection_name)
                st.success(f"Collection '{new_collection_name}' created.")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating collection: {e}")
        else:
            st.warning("Please enter a collection name.")

# --- LIST, SHOW, DELETE ---
for col in collection_names:
    name = col.name if hasattr(col, "name") else col
    with st.expander(f"Collection: {name}", expanded=False):
        st.markdown(f"**Collection Name:** `{name}`")
        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("Show", key=f"show_{name}"):
                st.session_state.selected_collection = name
        with cols[1]:
            if st.button("Delete", key=f"delete_{name}"):
                try:
                    client.delete_collection(name)
                    st.success(f"Deleted collection: {name}")
                    if st.session_state.get("selected_collection") == name:
                        del st.session_state["selected_collection"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting collection '{name}': {e}")

# --- DELETE ALL COLLECTIONS ---
if st.button("Delete All Collections"):
    for col in collection_names:
        client.delete_collection(col.name)
    st.success("All collections deleted")
    st.rerun()

# --- READ/UPDATE: Show and add documents to a collection ---
if "selected_collection" in st.session_state:
    st.subheader(f"Contents of Collection: {st.session_state.selected_collection}")
    try:
        collection = client.get_collection(st.session_state.selected_collection)
        data = collection.get()
        st.write("Documents:", data["documents"])
        st.write("Metadatas:", data["metadatas"])
        st.write("Ids:", data["ids"])

        # --- UPDATE: Add document to collection ---
        with st.expander("Add Document to Collection"):
            new_doc = st.text_area("Document Text", key="new_doc")
            new_metadata = st.text_area("Metadata (JSON)", key="new_metadata")
            new_id = st.text_input("Document ID (unique)", key="new_id")
            if st.button("Add Document"):
                if new_doc and new_id:
                    try:
                        metadata = json.loads(new_metadata) if new_metadata else None
                        collection.add(
                            documents=[new_doc],
                            metadatas=[metadata] if metadata else None,
                            ids=[new_id],
                        )
                        st.success("Document added.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding document: {e}")
                else:
                    st.warning("Please provide both Document Text and Document ID.")
    except Exception as e:
        st.write(f"Error loading collection '{st.session_state.selected_collection}': {e}")