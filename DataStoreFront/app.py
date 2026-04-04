import streamlit as st
import requests
import os

st.set_page_config(page_title="Students DataStore", page_icon="📚", layout="wide")

st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

API_URL = os.environ.get("API_URL", "http://localhost:8081")

st.title("Student DataStore")

tab1, tab2, tab3 = st.tabs(["Add Student", "Search Student", "List Students"])

with tab1:
    st.header("Add a new student")
    with st.form("add_student_form"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=1, max_value=100, value=18)
        submit_button = st.form_submit_button("Add Student")
        if submit_button:
            if name:
                try:
                    response = requests.post(f"{API_URL}/student/post", json={"name": name, "age": age})
                    if response.status_code == 200:
                        st.success(f"Student {name} added successfully!")
                    else:
                        st.error(f"Error adding student: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")
            else:
                st.warning("Please fill in all required fields.")

with tab2:
    st.header("Search for a student")
    search_name = st.text_input("Enter student name to search")
    if st.button("Search") and search_name:
        try:
            response = requests.get(f"{API_URL}/student/get/{search_name}")
            if response.status_code == 200:
                student = response.json()
                st.subheader("Student Information")
                st.write(f"**Name:** {student.get('name', 'N/A')}")
                st.write(f"**Age:** {student.get('age', 'N/A')}")
            else:
                st.warning(f"Student with name '{search_name}' not found.")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")

with tab3:
    st.header("List of all students")
    st.button("Refresh List")
    try:
        response = requests.get(f"{API_URL}/student/all")
        if response.status_code == 200:
            students = response.json()
            if students:
                student_data = [{"Name": s.get("name", "N/A"), "Age": s.get("age", "N/A")} for s in students]
                st.table(student_data)
            else:
                st.info("No students found in the database.")
        else:
            st.error("Failed to retrieve student list.")
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")