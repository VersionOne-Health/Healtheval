import os
import streamlit as st
from healtheval import load_all_failure_modes, load_failure_mode, run_eval
from healtheval.models import EvalVerdict

st.set_page_config(
    page_title="healtheval",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-label{font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;color:#6a8a6a;margin-bottom:0.25rem}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏥 healtheval")
    st.caption("Clinical failure mode eval for healthcare AI agents")
    st.divider()

    st.markdown("### Anthropic API Key")
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Optional. Required only for LLM-as-judge evaluation. Stored in your browser session only — never saved or transmitted anywhere.",
        label_visibility="collapsed",
    )
    if api_key:
        st.success("✓ LLM eval enabled")
        run_llm = st.checkbox("Run LLM-as-judge eval", value=True)
    else:
        st.info("No key — deterministic checks only (free, no API needed)")
        run_llm = False

    st.divider()
    st.markdown("### Failure Mode")

    modes = load_all_failure_modes()
    sev_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
    mode_options = {
        f"{sev_icons.get(m.severity.value, '⚪')} {m.id} — {m.name}": m.id
        for m in sorted(modes, key=lambda x: x.id)
    }
    selected_label = st.selectbox("Select failure mode", list(mode_options.keys()), label_visibility="collapsed")
    selected_id = mode_options[selected_label]
    fm = load_failure_mode(selected_id)

    st.markdown(
        f"**Severity:** {sev_icons.get(fm.severity.value)} `{fm.severity.value.upper()}`  \n"
        f"**Category:** `{fm.category.value}`  \n"
        f"**Specialties:** {', '.join(fm.specialties[:3])}"
    )

    st.divider()
    st.markdown(
        "[![GitHub](https://img.shields.io/badge/GitHub-healtheval-green)](https://github.com/versionone-health/healtheval)  \n"
        "Built by [versionone.health](https://versionone.health)"
    )

# ── Main layout ───────────────────────────────────────────────────────────────

left, right = st.columns([1, 1], gap="large")

# ── Left: Failure mode info + inputs ──────────────────────────────────────────

with left:
    st.markdown(f"## {fm.id}: {fm.name}")
    st.markdown(fm.description)

    with st.expander("📖 What goes wrong"):
        st.markdown(fm.what_went_wrong)

    with st.expander("❌ Example bad output"):
        st.code(fm.example_bad_output, language=None)

    with st.expander("✅ Example good output"):
        st.code(fm.example_good_output, language=None)

    if fm.triggers:
        with st.expander("⚡ Common triggers"):
            for t in fm.triggers:
                st.markdown(f"- {t}")

    st.divider()
    st.markdown("### Input")

    inputs = {}

    if fm.id == "SCRIBE-001":
        inputs["context"] = st.text_area("Clinical context / chart note", height=130,
            placeholder="Example: Metformin 500mg was discontinued on 2024-11-14 due to GI intolerance.")
        inputs["agent_output"] = st.text_area("Agent output to evaluate", height=130,
            placeholder="Example: Patient is currently on metformin 500mg twice daily.")

    elif fm.id == "SCRIBE-002":
        inputs["prior_context"] = st.text_area("Prior visit note", height=110,
            placeholder="Example: Assessment: Stable GERD. Plan: Continue PPI. Follow up 6 weeks.")
        inputs["transcript"] = st.text_area("Current visit transcript", height=110,
            placeholder="Example: Patient here for follow-up. Colonoscopy completed last week — normal.")
        inputs["agent_output"] = st.text_area("Agent output (current visit note)", height=110,
            placeholder="What the scribe agent generated for the current visit...")

    elif fm.id == "SCRIBE-003":
        inputs["transcript"] = st.text_area("Visit transcript", height=130,
            placeholder="Example: Doctor reviews chief complaint of fatigue. No vitals verbally discussed.")
        inputs["ehr_data"] = st.text_area("Structured EHR data provided to agent (optional)", height=80,
            placeholder="Any structured data given to the agent...")
        inputs["agent_output"] = st.text_area("Agent output to evaluate", height=110,
            placeholder="Example: Vitals: BP 128/82, HR 74, Temp 98.6F...")

    elif fm.id == "SCRIBE-004":
        inputs["transcript"] = st.text_area("Patient transcript", height=130,
            placeholder="Example: I haven't had any chest pain. No shortness of breath. But I have headaches.")
        inputs["agent_output"] = st.text_area("Agent ROS / HPI output", height=130,
            placeholder="Example: Positive for chest pain and shortness of breath. Denies headache.")

    elif fm.id == "RCM-001":
        inputs["context"] = st.text_area("Clinical documentation", height=130,
            placeholder="Example: 45-minute office visit, high complexity MDM. EKG performed and interpreted.")
        inputs["agent_output"] = st.text_area("Agent recommended codes", height=80,
            placeholder="Example: Recommended codes: 99215, 93000, 99999")

    elif fm.id == "RCM-002":
        inputs["remittance_data"] = st.text_area("835 / EOB remittance data", height=130,
            placeholder="Example: Adjustment reason code: CO-4. Remark code: N130.")
        inputs["agent_output"] = st.text_area("Agent denial analysis output", height=130,
            placeholder="Example: Denial reason: CO-50 medical necessity not established...")

    elif fm.id == "REFILL-001":
        inputs["formulary_data"] = st.text_area("Formulary / plan data", height=110,
            placeholder="Example: Ozempic: prior authorization required under this plan.")
        inputs["agent_output"] = st.text_area("Agent response to patient", height=110,
            placeholder="Example: Your Ozempic refill is queued and will be ready in 24 hours.")

    elif fm.id == "REFILL-002":
        inputs["medication_name"] = st.text_input("Medication name", placeholder="Example: Adderall XR 20mg")
        inputs["dea_schedule"] = st.text_input("DEA Schedule", placeholder="Example: II")
        inputs["agent_output"] = st.text_area("Agent response to patient", height=100,
            placeholder="Example: Your Adderall refill has been sent to the prescriber.")

    elif fm.id == "FAXROUTE-001":
        inputs["fax_metadata"] = st.text_area("Fax header / metadata", height=80,
            placeholder="Example: Attn: Dr. Johnson, Cardiology Associates of Orlando")
        inputs["provider_list"] = st.text_area("Practice provider list (one per line)", height=100,
            placeholder="Dr. Marcus Johnson - Interventional Cardiology\nDr. Patricia Johnson - Electrophysiology")
        inputs["fax_content_summary"] = st.text_area("Fax content summary", height=80,
            placeholder="Example: Lab results for patient with recent ablation procedure.")
        inputs["agent_output"] = st.text_area("Agent routing decision", height=80,
            placeholder="Example: Routed to Dr. Patricia Johnson (Electrophysiology).")

    elif fm.id == "PRIORAUTH-001":
        inputs["policy_document"] = st.text_area("Payer policy document", height=130,
            placeholder="Example: Colonoscopy covered for average-risk members age 45+. No PA required.")
        inputs["context"] = st.text_area("Procedure and patient context", height=80,
            placeholder="Example: Humana MA plan. Colonoscopy (CPT 45378) for average-risk patient age 52.")
        inputs["agent_output"] = st.text_area("Agent PA output", height=110,
            placeholder="Example: PA required per Humana Clinical Policy CP-GI-004...")

    st.markdown("")
    run_button = st.button("▶ Run Evaluation", type="primary", use_container_width=True)

# ── Right: Results ─────────────────────────────────────────────────────────────

with right:
    st.markdown("### Results")

    if run_button:
        clean_inputs = {k: v for k, v in inputs.items() if v and str(v).strip()}

        if not any(clean_inputs.values()):
            st.warning("Please fill in at least one input field before running.")
        else:
            with st.spinner(f"Running eval for {selected_id}..."):
                try:
                    result = run_eval(
                        selected_id,
                        run_llm=run_llm,
                        api_key=api_key if api_key else None,
                        **clean_inputs,
                    )
                except Exception as e:
                    st.error(f"Error running eval: {e}")
                    st.stop()

            verdict = result.final_verdict
            verdict_map = {
                EvalVerdict.PASS: ("✅", "success", "PASS — No failure detected"),
                EvalVerdict.FAIL: ("❌", "error", "FAIL — Failure mode detected"),
                EvalVerdict.UNCERTAIN: ("⚠️", "warning", "UNCERTAIN — Insufficient context"),
                EvalVerdict.ERROR: ("🔧", "error", "ERROR — Evaluation could not complete"),
            }
            icon, msg_fn, label = verdict_map.get(verdict, ("❓", "info", "UNKNOWN"))
            getattr(st, msg_fn)(f"{icon} **{label}**")
            st.markdown(f"`{result.failure_mode_id}` · `{result.severity.value.upper()}` · `{result.category.value}`")
            st.divider()

            if result.deterministic_result:
                dr = result.deterministic_result
                st.markdown("**🔍 Deterministic Check**")
                col_a, col_b = st.columns([1, 2])
                col_a.metric("Verdict", dr.verdict.value)
                col_b.markdown(f"**Reason:** {dr.reason}")
                if dr.flagged_content:
                    st.error(f"🚩 Flagged: `{dr.flagged_content}`")

            if result.llm_result:
                st.divider()
                lr = result.llm_result
                st.markdown(f"**🤖 LLM Evaluation** · `{lr.model_used}` · `{lr.total_tokens}` tokens")
                st.markdown(lr.explanation)
            elif run_llm and not api_key:
                st.info("Enter your Anthropic API key in the sidebar to enable LLM-as-judge evaluation.")

            st.divider()
            with st.expander("📄 Raw JSON output"):
                st.json(result.to_dict())

    else:
        st.markdown("""
← Fill in the inputs on the left and click **▶ Run Evaluation**.

**How it works:**
1. **Deterministic check** runs first — rule-based, free, no API key needed
2. **LLM-as-judge** runs if deterministic does not catch a FAIL — requires Anthropic API key entered in sidebar
3. Deterministic FAIL short-circuits — no API cost incurred

**Severity levels:**
- 🔴 Critical — direct patient harm or DEA violation potential
- 🟠 High — compliance risk or care delay potential
- 🟡 Medium — quality issue
- 🟢 Low — informational
        """)
        st.divider()
        st.markdown("**All failure modes in v0.1:**")
        for m in sorted(modes, key=lambda x: x.id):
            icon = sev_icons.get(m.severity.value, "⚪")
            st.markdown(f"{icon} `{m.id}` — {m.name}")
