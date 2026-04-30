import os
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# Load environment variables (ensure GOOGLE_API_KEY is set)
load_dotenv()

# ==========================================
# 1. State Definition
# ==========================================
class PatientTriageState(TypedDict):
    patient_narrative: str
    clinical_summary: str
    recommended_pathway: str
    safety_critique: str
    is_safe_and_approved: bool
    revision_number: int

# ==========================================
# 2. Pydantic Models for Structured Output
# ==========================================
class IntakeDraftOutput(BaseModel):
    """Output structure for the Intake Coordinator (Generator)"""
    clinical_summary: str = Field(description="Structured medical summary of the patient's narrative.")
    recommended_pathway: str = Field(description="Suggested care pathway (e.g., ER, Urgent Care, Primary Care, Telehealth).")

class ClinicalReviewOutput(BaseModel):
    """Output structure for the Clinical Safety Reviewer (Reflector)"""
    is_safe_and_approved: bool = Field(description="True if the triage is clinically safe and catches all red flags. False otherwise.")
    safety_critique: str = Field(description="Actionable feedback if not approved. Empty if approved.")

# ==========================================
# 3. Node Functions (The Agents)
# ==========================================
def intake_coordinator_node(state: PatientTriageState):
    """Drafts or revises the clinical summary and pathway."""
    print(f"--- [Generator] Drafting Triage (Iteration {state.get('revision_number', 0) + 1}) ---")
    
    # Initialize Gemini model (Flash is fast and good for generation)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
    structured_llm = llm.with_structured_output(IntakeDraftOutput)
    
    # Dynamic prompt based on whether this is a first draft or a revision
    if state.get("safety_critique"):
        sys_prompt = (
            "You are an Intake Coordinator. Revise the clinical summary and care pathway based on "
            "the Clinical Reviewer's safety critique.\n"
            "Critique to address: {critique}"
        )
    else:
        sys_prompt = (
            "You are an Intake Coordinator. Read the patient's narrative, summarize the clinical presentation, "
            "and suggest a care pathway (e.g., Routine, Telehealth, Urgent Care, Emergency Room)."
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_prompt),
        ("human", "Patient Narrative: {narrative}")
    ])
    
    chain = prompt | structured_llm
    
    response = chain.invoke({
        "narrative": state["patient_narrative"],
        "critique": state.get("safety_critique", "")
    })
    
    return {
        "clinical_summary": response.clinical_summary,
        "recommended_pathway": response.recommended_pathway,
        "revision_number": state.get("revision_number", 0) + 1
    }

def clinical_safety_reviewer_node(state: PatientTriageState):
    """Reviews the draft for medical safety and red flags."""
    print("--- [Reflector] Reviewing for Clinical Safety ---")
    
    # Initialize Gemini model (Pro is better for complex reasoning and safety constraints)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.0)
    structured_llm = llm.with_structured_output(ClinicalReviewOutput)
    
    sys_prompt = (
        "You are an expert Chief Medical Officer and Triage Nurse. Your job is to review the Intake Coordinator's "
        "summary and pathway for patient safety.\n"
        "Look for 'red flag' symptoms (e.g., chest pain, sudden weakness, shortness of breath) that might be "
        "hidden in the narrative and ensure the pathway is appropriately urgent.\n"
        "If the triage is unsafe (under-triaged), output is_safe_and_approved=False and provide a strict critique.\n"
        "If it is safe, output is_safe_and_approved=True."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_prompt),
        ("human", "Patient Narrative: {narrative}\n\nDraft Summary: {summary}\nDraft Pathway: {pathway}")
    ])
    
    chain = prompt | structured_llm
    
    response = chain.invoke({
        "narrative": state["patient_narrative"],
        "summary": state["clinical_summary"],
        "pathway": state["recommended_pathway"]
    })
    
    print(f"    -> Approved: {response.is_safe_and_approved}")
    if not response.is_safe_and_approved:
        print(f"    -> Critique: {response.safety_critique}")
        
    return {
        "is_safe_and_approved": response.is_safe_and_approved,
        "safety_critique": response.safety_critique
    }

# ==========================================
# 4. Routing Logic
# ==========================================
def route_to_next_step(state: PatientTriageState):
    """Determines whether to loop back or end the graph."""
    if state["is_safe_and_approved"]:
        return END
    if state["revision_number"] >= 3: # Max retries to prevent infinite loops
        print("--- [Router] Max revisions reached. Flagging for human review. ---")
        return END
    return "intake_coordinator"

# ==========================================
# 5. Graph Construction
# ==========================================
def build_triage_graph():
    workflow = StateGraph(PatientTriageState)
    
    # Add nodes
    workflow.add_node("intake_coordinator", intake_coordinator_node)
    workflow.add_node("clinical_reviewer", clinical_safety_reviewer_node)
    
    # Define edges
    workflow.set_entry_point("intake_coordinator")
    workflow.add_edge("intake_coordinator", "clinical_reviewer")
    workflow.add_conditional_edges(
        "clinical_reviewer",
        route_to_next_step,
        {
            "intake_coordinator": "intake_coordinator",
            END: END
        }
    )
    
    return workflow.compile()

# ==========================================
# 6. Execution / Test Scenario
# ==========================================
if __name__ == "__main__":
    app = build_triage_graph()
    
    # A tricky scenario: The patient thinks it's a stomach issue, but it's likely cardiac.
    # A naive LLM will route to Gastroenterology/Primary care. The Reflector should catch the cardiac red flag.
    tricky_patient_input = (
        "I've been having really bad heartburn since this morning after eating breakfast. "
        "Tums aren't helping at all. I also feel a bit sweaty and my left jaw aches, probably "
        "because I'm clenching my teeth from the stomach pain. I'd like to see a stomach doctor."
    )
    
    initial_state = {
        "patient_narrative": tricky_patient_input,
        "clinical_summary": "",
        "recommended_pathway": "",
        "safety_critique": "",
        "is_safe_and_approved": False,
        "revision_number": 0
    }
    
    print("\nStarting Patient Triage Workflow...\n" + "="*40)
    final_state = app.invoke(initial_state)
    
    print("\n" + "="*40 + "\nFINAL OUTPUT:")
    print(f"Clinical Summary:\n{final_state['clinical_summary']}\n")
    print(f"Recommended Pathway:\n{final_state['recommended_pathway']}")