# ==========================================
# 6. Execution
# ==========================================
if __name__ == "__main__":
    app = build_triage_graph()
    
    # Typhoid-like Patient Input:
    # Prolonged high fever + GI symptoms + Recent travel = Infectious Disease Red Flag
    typhoid_patient_input = (
        "I've had a fever that keeps going up for the last five days; it hit 103.5°F last night. "
        "I have a terrible headache, my stomach really hurts, and I'm so exhausted I can barely get out of bed. "
        "I haven't had an appetite at all. I just got back from a backpacking trip in Southeast Asia last week, "
        "so maybe I ate some bad street food. I think I just need a prescription for some strong nausea meds."
    )
    
    initial_state = {
        "patient_narrative": typhoid_patient_input,
        "clinical_summary": "",
        "recommended_pathway": "",
        "safety_critique": "",
        "is_safe_and_approved": False,
        "revision_number": 0
    }
    
    print("\nStarting UHG Patient Triage Workflow...\n" + "="*40)
    final_state = app.invoke(initial_state)
    
    print("\n" + "="*40 + "\nFINAL OUTPUT:")
    print(f"Clinical Summary:\n{final_state['clinical_summary']}\n")
    print(f"Recommended Pathway:\n{final_state['recommended_pathway']}")