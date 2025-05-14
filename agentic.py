# Install necessary libraries
# !pip install langgraph langchain langchain_community sentence-transformers faiss-cpu pandas "ipykernel>=6.27.1"

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import TypedDict, Annotated, List, Optional, Dict
import operator

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver # For persistence if needed

# --- 0. Configuration ---
# For HuggingFaceEmbeddings, especially on systems with limited RAM or specific tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_STORE_PATH = "ticket_vector_store.faiss" # Optional: for saving/loading FAISS index
NUM_SIMILAR_TICKETS = 5

# --- 1. Simulate Historical Ticket Data ---
def generate_dummy_ticket_data(num_records=2000):
    """Generates dummy ticket data for 2 years."""
    data = []
    base_time = datetime.now() - timedelta(days=365 * 2)
    ticket_id_counter = 1

    # Define some common issue patterns
    issue_templates = [
        "User {user_id} is unable to login to the {service} portal. Error message: {error_code}.",
        "The {feature} feature is not working as expected on {platform}.",
        "Request for access to {resource} for user {user_id}.",
        "Password reset required for account {account_id}.",
        "System experiencing slow performance when accessing {module}.",
        "Error {error_code} encountered during payment processing for order {order_id}.",
        "Cannot connect to the {network_component} server.",
        "Software installation failed for {software_name} on {os_version}.",
        "Data discrepancy found in {report_name} report.",
        "How do I configure the {setting_name} setting in {application}?"
    ]
    services = ["CRM", "Billing", "Support", "Payment", "API"]
    features = ["dashboard", "reporting", "user management", "export", "search"]
    platforms = ["Web App", "Mobile App (iOS)", "Mobile App (Android)", "Desktop Client"]
    resources = ["SharedFolderX", "DatabaseY", "AdminPanelZ"]
    error_codes = ["ERR-401", "TIMEOUT-504", "DB-CONN-FAIL", "AUTH-003", "NULL-PTR-EX"]

    for i in range(num_records):
        template = random.choice(issue_templates)
        description = template.format(
            user_id=f"user{random.randint(100, 999)}",
            service=random.choice(services),
            error_code=random.choice(error_codes),
            feature=random.choice(features),
            platform=random.choice(platforms),
            resource=random.choice(resources),
            account_id=f"acc{random.randint(1000, 9999)}",
            module=random.choice(services),
            order_id=f"ord{random.randint(10000, 99999)}",
            network_component=random.choice(["VPN", "Database", "Application"]),
            software_name=random.choice(["Office Suite", "IDE Pro", "GraphicTool"]),
            os_version=random.choice(["Windows 11", "macOS Sonoma", "Ubuntu 22.04"]),
            report_name=random.choice(["Sales_Q3", "UserActivity_Monthly", "Inventory_Daily"]),
            setting_name=random.choice(["notification", "privacy", "API key"]),
            application=random.choice(services)
        )
        
        # Add some more realistic variations
        if "login" in description:
            description += f" Tried on {random.choice(['Chrome', 'Firefox', 'Edge'])}."
        if "password reset" in description:
            description += f" Security question answer was '{random.choice(['mother_maiden_name', 'first_pet'])}'."

        create_time = base_time + timedelta(days=random.randint(0, 365 * 2 -1),
                                            seconds=random.randint(0, 86399))
        
        data.append({
            "ticket_id": f"TICKET-{ticket_id_counter:05d}",
            "description": description,
            "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        ticket_id_counter += 1
    return pd.DataFrame(data)

# --- 2. Define Agent State ---
class TicketSimilarityState(TypedDict):
    historical_tickets_df: Optional[pd.DataFrame]
    vector_store: Optional[FAISS]
    embeddings_model: Optional[HuggingFaceEmbeddings]
    
    # Input for a new query
    query_ticket_id: Optional[str]
    query_ticket_description: str
    
    # Output
    similar_tickets: Optional[List[Dict]]
    error_message: Optional[str]

# --- 3. Define Nodes (Agent's Tools/Actions) ---

def load_historical_data_node(state: TicketSimilarityState) -> TicketSimilarityState:
    print("--- Node: Loading Historical Data ---")
    try:
        # In a real scenario, you might load from a DB or CSV files
        # For this example, we generate it or load from a pre-generated CSV
        csv_path = "historical_tickets.csv"
        if os.path.exists(csv_path):
            print(f"Loading from {csv_path}")
            df = pd.read_csv(csv_path)
        else:
            print("Generating new dummy historical ticket data...")
            df = generate_dummy_ticket_data(2000) # Generate 2000 tickets
            df.to_csv(csv_path, index=False)
            print(f"Saved dummy data to {csv_path}")
        
        state['historical_tickets_df'] = df
        print(f"Loaded {len(df)} historical tickets.")
    except Exception as e:
        print(f"Error loading historical data: {e}")
        state['error_message'] = f"Failed to load historical data: {str(e)}"
    return state

def initialize_vector_store_node(state: TicketSimilarityState) -> TicketSimilarityState:
    print("--- Node: Initializing Vector Store ---")
    if state.get('error_message'): return state # Skip if previous error

    df = state.get('historical_tickets_df')
    if df is None or df.empty:
        state['error_message'] = "Historical data is not loaded. Cannot initialize vector store."
        return state

    try:
        embeddings_model = state.get('embeddings_model')
        if not embeddings_model:
            print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}")
            embeddings_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
            state['embeddings_model'] = embeddings_model

        # Check if a pre-built FAISS index exists and can be loaded
        # This is a simple check; a more robust one would involve checking model compatibility
        if os.path.exists(VECTOR_STORE_PATH) and os.path.exists(VECTOR_STORE_PATH + ".pkl"): # Langchain FAISS saves two files
            try:
                print(f"Attempting to load vector store from {VECTOR_STORE_PATH}...")
                vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings_model, allow_dangerous_deserialization=True)
                # Quick check: ensure it has documents (this doesn't guarantee it's the *correct* store)
                if vector_store.index.ntotal > 0:
                    print(f"Successfully loaded vector store with {vector_store.index.ntotal} embeddings.")
                    state['vector_store'] = vector_store
                    return state
                else:
                    print("Loaded vector store is empty. Rebuilding.")
            except Exception as e:
                print(f"Failed to load vector store from {VECTOR_STORE_PATH}: {e}. Rebuilding.")

        print("Building new vector store from historical ticket descriptions...")
        texts = df['description'].tolist()
        # Create LangChain Document objects, including metadata
        documents = []
        for i, row in df.iterrows():
            doc = Document(
                page_content=row['description'],
                metadata={
                    "ticket_id": row['ticket_id'],
                    "create_time": row['create_time'],
                    "original_description": row['description'] # Keep original desc in metadata
                }
            )
            documents.append(doc)

        vector_store = FAISS.from_documents(documents, embeddings_model)
        state['vector_store'] = vector_store
        print(f"Vector store initialized with {len(documents)} documents.")
        
        # Optional: Save the FAISS index
        try:
            vector_store.save_local(VECTOR_STORE_PATH)
            print(f"Saved vector store to {VECTOR_STORE_PATH}")
        except Exception as e:
            print(f"Warning: Could not save vector store: {e}")
            
    except Exception as e:
        print(f"Error initializing vector store: {e}")
        state['error_message'] = f"Failed to initialize vector store: {str(e)}"
    return state

def find_similar_tickets_node(state: TicketSimilarityState) -> TicketSimilarityState:
    print("--- Node: Finding Similar Tickets ---")
    if state.get('error_message'): return state

    vector_store = state.get('vector_store')
    query_description = state.get('query_ticket_description')
    
    if not vector_store:
        state['error_message'] = "Vector store is not initialized."
        return state
    if not query_description:
        state['error_message'] = "Query ticket description is missing."
        return state

    try:
        print(f"Searching for tickets similar to: '{query_description[:100]}...'")
        # The vector store uses the same embedding model it was created with
        # FAISS `similarity_search` takes text directly, it will embed it using its stored embedder
        similar_docs_with_scores = vector_store.similarity_search_with_score(
            query_description, 
            k=NUM_SIMILAR_TICKETS
        )
        
        similar_tickets_result = []
        for doc, score in similar_docs_with_scores:
            similar_tickets_result.append({
                "ticket_id": doc.metadata.get("ticket_id"),
                "description": doc.metadata.get("original_description"), # Get original from metadata
                "create_time": doc.metadata.get("create_time"),
                "similarity_score": float(score) # FAISS score is L2 distance, lower is better
            })
        
        state['similar_tickets'] = similar_tickets_result
        print(f"Found {len(similar_tickets_result)} similar tickets.")
    except Exception as e:
        print(f"Error finding similar tickets: {e}")
        state['error_message'] = f"Failed to find similar tickets: {str(e)}"
    return state

# --- 4. Define Conditional Edges ---

def should_initialize_data_and_store(state: TicketSimilarityState) -> str:
    """
    Determines if the historical data and vector store need initialization.
    This logic ensures we only do this once per agent "session" or if explicitly reset.
    """
    if state.get('vector_store') and state.get('historical_tickets_df') is not None:
        print("<<< Condition: Data and Vector Store already initialized. Skipping. >>>")
        return "skip_initialization"
    print("<<< Condition: Data and Vector Store need initialization. >>>")
    return "needs_initialization"

def check_for_errors(state: TicketSimilarityState) -> str:
    if state.get('error_message'):
        print(f"<<< Condition: Error detected: {state['error_message']} >>>")
        return "error_detected"
    return "continue_processing"

# --- 5. Build the Graph ---
# Initialize the graph
workflow = StateGraph(TicketSimilarityState)

# Add nodes
workflow.add_node("load_historical_data", load_historical_data_node)
workflow.add_node("initialize_vector_store", initialize_vector_store_node)
workflow.add_node("find_similar_tickets", find_similar_tickets_node)
workflow.add_node("handle_error", lambda state: print(f"ERROR STATE: {state.get('error_message')}") or state) # Simple error handler

# Define edges
workflow.set_entry_point("load_historical_data") # Start by ensuring data is loaded

# Conditional edge after loading data: check if vector store needs init or if there was an error
workflow.add_conditional_edges(
    "load_historical_data",
    check_for_errors,
    {
        "error_detected": "handle_error",
        "continue_processing": "initialize_vector_store" 
    }
)

# Conditional edge after initializing vector store
workflow.add_conditional_edges(
    "initialize_vector_store",
    check_for_errors,
    {
        "error_detected": "handle_error",
        "continue_processing": "find_similar_tickets" # If successful, proceed to find tickets
    }
)

# After finding tickets, either end or handle error
workflow.add_conditional_edges(
    "find_similar_tickets",
    check_for_errors,
    {
        "error_detected": "handle_error",
        "continue_processing": END
    }
)

workflow.add_edge("handle_error", END) # End after handling an error

# Compile the graph
# memory = SqliteSaver.from_conn_string(":memory:") # For persisting state across runs (optional)
app = workflow.compile() # checkpoint_saver=memory

# --- 6. Run the Agent ---
if __name__ == "__main__":
    print("--- Agent Run 1: Initializing data and vector store, then finding similar tickets ---")
    
    # Example new ticket
    new_ticket = {
        "ticket_id": "NEW-001",
        "description": "I cannot log in to the payment gateway. It shows an authentication failure."
    }

    # Initial state for the first run.
    # Vector store and historical_tickets_df will be populated by the graph.
    initial_state_run1 = {
        "query_ticket_id": new_ticket["ticket_id"],
        "query_ticket_description": new_ticket["description"],
    }
    
    # Stream events to see the flow
    config = {"configurable": {"thread_id": "ticket-similarity-thread-1"}}
    print(f"\nInvoking agent for: '{new_ticket['description']}'")
    final_state_run1 = None
    for event in app.stream(initial_state_run1, config=config):
        for key, value in event.items():
            print(f"Event: {key}")
            # print(f"  State: {value}") # Can be very verbose
            if key == "__end__":
                final_state_run1 = value
                print("--- Agent Run 1 Finished ---")

    if final_state_run1 and final_state_run1.get("similar_tickets"):
        print("\nMost Similar Tickets Found:")
        for ticket in final_state_run1["similar_tickets"]:
            print(f"  ID: {ticket['ticket_id']}, Score: {ticket['similarity_score']:.4f}")
            print(f"  Desc: {ticket['description'][:150]}...") # Print first 150 chars
            print(f"  Created: {ticket['create_time']}")
            print("-" * 20)
    elif final_state_run1 and final_state_run1.get("error_message"):
        print(f"\nError during agent execution: {final_state_run1['error_message']}")

    print("\n" + "="*50 + "\n")

    # --- Agent Run 2: Using existing initialized data (if successful before) ---
    print("--- Agent Run 2: Finding similar tickets for a different query (should reuse existing vector store) ---")
    
    another_new_ticket = {
        "ticket_id": "NEW-002",
        "description": "The main dashboard is very slow to load reports this morning."
    }

    # For the second run, we want to reuse the vector_store and historical_df
    # The graph is designed to load/initialize if they are not present in the input state.
    # If the first run was successful and `app` holds the state (e.g. with memory),
    # subsequent calls might pick it up.
    # To explicitly show reuse, we'd pass the `vector_store` and `historical_tickets_df`
    # from `final_state_run1` if we were NOT using a persistent checkpointer.
    # With SqliteSaver and the same thread_id, it *should* resume.
    # However, the current graph structure re-evaluates `load_historical_data` and `initialize_vector_store`
    # but `initialize_vector_store` has logic to load from disk if available.
    
    # To demonstrate re-use more explicitly without relying on checkpointing state carrying over perfectly,
    # let's simulate that the vector store and df are "globally" available after the first run
    # (which they would be if `app` was a long-lived service object).
    
    # If run 1 was successful, its `final_state_run1` would contain these.
    # For this script, we just re-run. The FAISS loading logic in `initialize_vector_store_node` will kick in.

    initial_state_run2 = {
        "query_ticket_id": another_new_ticket["ticket_id"],
        "query_ticket_description": another_new_ticket["description"],
        # If first run was successful, these would be populated.
        # If using persistent memory and same thread_id, LangGraph handles this.
        # "vector_store": final_state_run1.get("vector_store") if final_state_run1 else None, 
        # "historical_tickets_df": final_state_run1.get("historical_tickets_df") if final_state_run1 else None,
        # "embeddings_model": final_state_run1.get("embeddings_model") if final_state_run1 else None,
    }

    config_run2 = {"configurable": {"thread_id": "ticket-similarity-thread-2"}} # Use a new thread_id or manage state
    print(f"\nInvoking agent for: '{another_new_ticket['description']}'")
    final_state_run2 = None
    for event in app.stream(initial_state_run2, config=config_run2):
        for key, value in event.items():
            print(f"Event: {key}")
            if key == "__end__":
                final_state_run2 = value
                print("--- Agent Run 2 Finished ---")

    if final_state_run2 and final_state_run2.get("similar_tickets"):
        print("\nMost Similar Tickets Found (Run 2):")
        for ticket in final_state_run2["similar_tickets"]:
            print(f"  ID: {ticket['ticket_id']}, Score: {ticket['similarity_score']:.4f}")
            print(f"  Desc: {ticket['description'][:150]}...")
            print(f"  Created: {ticket['create_time']}")
            print("-" * 20)
    elif final_state_run2 and final_state_run2.get("error_message"):
        print(f"\nError during agent execution (Run 2): {final_state_run2['error_message']}")