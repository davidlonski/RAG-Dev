import streamlit as st


def init_auth_state() -> None:
    ss = st.session_state
    if "user_role" not in ss:
        ss.user_role = None
    if "user_id" not in ss:
        ss.user_id = None
    if "user_name" not in ss:
        ss.user_name = None


def login_form(expected_role: str) -> bool:
    """Render a minimal login form for the expected role. Returns True once logged in."""
    init_auth_state()
    ss = st.session_state

    st.subheader(f"Login as {expected_role.title()}")
    with st.form(key=f"login_form_{expected_role}"):
        user_id = st.text_input("User ID", value=ss.get("user_id") or "")
        user_name = st.text_input("Name (optional)", value=ss.get("user_name") or "")
        submitted = st.form_submit_button("Login")
        if submitted:
            if not user_id.strip():
                st.error("Please enter a User ID")
            else:
                ss.user_role = expected_role
                ss.user_id = user_id.strip()
                ss.user_name = user_name.strip() or None
                return True
    return False


essential_role_to_stage = {
    "teacher": "dashboard",
    "student": "dashboard",
}


def require_login(expected_role: str) -> bool:
    """Ensure a user is logged in with the expected role. Returns True if allowed to proceed."""
    init_auth_state()
    ss = st.session_state
    if ss.user_role == expected_role and ss.user_id:
        return True
    return login_form(expected_role)


def logout() -> None:
    init_auth_state()
    ss = st.session_state
    ss.user_role = None
    ss.user_id = None
    ss.user_name = None