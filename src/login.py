from datetime import datetime
import streamlit as st
import requests

#CosmoCloud URL's for connecting to database
COSMO_API_URL = "https://free-ap-south-1.cosmocloud.io/development/api/user_data"
QUIZ_DATA_URL = "https://free-ap-south-1.cosmocloud.io/development/api/quiz_data"  
STUDY_PLAN_URL= "https://free-ap-south-1.cosmocloud.io/development/api/study_plan"

ENV_ID = "66dabc906f12fff792820bb0"
PROJECT_ID = "66dabc906f12fff792820baf"

def check_quiz_record_exists(user_id):
    response = requests.get(
        f"{QUIZ_DATA_URL}?user_id={user_id}&limit=1&offset=0",
        headers={
            "Content-Type": "application/json",
            "projectId": PROJECT_ID,
            "environmentId": ENV_ID
        }
    )
    if response.status_code == 200:
        quiz_data = response.json()
        return len(quiz_data['data']) > 0  # Check if any records exist
    else:
        st.error(f"Failed to check quiz records. Error: {response.text}")
        return False

def create_quiz_record(user_id, certification_goal):
    quiz_data = {
        "user_id": user_id,
        "certification_type": "",
        "quiz_generated_date": datetime.utcnow().isoformat() + "Z",
        "difficulty_level": "Beginner",  # Default difficulty level
        "questions": [],
        "score": {}  # Assuming the score object should be empty initially
    }
    response = requests.post(
        QUIZ_DATA_URL,
        json=quiz_data,
        headers={
            "Content-Type": "application/json",
            "projectId": PROJECT_ID,
            "environmentId": ENV_ID
        }
    )
    if response.status_code == 201:
        st.success("Quiz record created successfully!")
    else:
        st.error(f"Failed to create quiz record. Error: {response.text}")
# New function to create study plan record
def create_study_plan(user_id, proficiency_level="beginner", weak_areas=None, study_recommendations=None, deadline=30):
    if weak_areas is None:
        weak_areas = []  # Default to empty list if None
    if study_recommendations is None:
        study_recommendations = []  # Default to empty list if None

    study_plan_data = {
        "user_id": user_id,
        "deadline": deadline,
        "proficiency_level": proficiency_level,
        "weak_areas": weak_areas,
        "links": [],  # Placeholder for any links you might add later
        "study_recommendations": study_recommendations
    }

    try:
        # Log the data being sent for debugging
        st.write("Sending the following study plan data:", study_plan_data)

        response = requests.post(
            STUDY_PLAN_URL,
            json=study_plan_data,
            headers={
                "Content-Type": "application/json",
                "projectId": PROJECT_ID,
                "environmentId": ENV_ID
            }
        )
        response.raise_for_status()  # Raise an error for HTTP error responses

        # Check for specific response codes or messages
        if response.status_code == 201:
            st.success("Study plan created successfully!")
        else:
            st.error(f"Unexpected response status: {response.status_code}. Response: {response.text}")

    except requests.exceptions.HTTPError as e:
        # Log the full error response for more details
        st.error(f"Failed to create study plan. Error: {e.response.text}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

def add_button_hover_style():
    st.markdown(
        """
        <style>
        .stButton>button {
            background-color: black;  /* Default button color */
            color: white;
            border-radius: 5px;
            outline: none;  /* Remove outline */
            border: none;  /* Remove border */
        }

        .stButton>button:hover {
            background-color: green;  /* Hover color */
            color: white;
        }

        .stButton>button:focus, .stButton>button:active {
            outline: none;  /* Remove focus/active outline */
            border: none;  /* Remove focus/active border */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def user_authentication():

    # Apply button hover style
    add_button_hover_style()

    option = st.selectbox("Login or Signup", ("Login", "Signup"))

    if option == "Signup":
        username = st.text_input("Enter username")
        email = st.text_input("Enter email")
        password = st.text_input("Enter password", type="password")
        #certification_goal = st.text_input("Enter your certification goal (e.g., AWS/Azure Certification)")

        if st.button("Signup"):
            user_data = {
                "username": username,
                "email": email,
                "password": password,
                "certification_goal": "",
                "study_plan": {
                    "plan_created_date": None,
                    "modules": []
                },
                "progress": {
                    "completed_modules": [],
                    "quizzes_taken": []
                }
            }
            st.write("Sending the following data to the API:", user_data)
            response = requests.post(
                COSMO_API_URL,
                json=user_data,
                headers={
                    "Content-Type": "application/json",
                    "projectId": PROJECT_ID,
                    "environmentId": ENV_ID
                }
            )

            if response.status_code == 201:
                st.success("Signup successful!")
                user_id = response.json().get('id')
                st.session_state['user_id'] = user_id  # Store user_id in session state
                st.write(f"User ID: {user_id}")
                if not check_quiz_record_exists(user_id):
                    create_quiz_record(user_id, "")
                    # Create study plan for the user
                    create_study_plan(user_id, "Beginner", [], [])
                    #st.write("study plan created")
                else:
                    st.info("Quiz record already exists for this user.")
            else:
                st.error(f"Signup failed. Error: {response.text}")

    else:  # Login
        email = st.text_input("Enter email")
        password = st.text_input("Enter password", type="password")

        if st.button("Login"):
            # Include limit and offset parameters
            limit = 20  # Set your desired limit
            offset = 0  # Start offset

            response = requests.get(
                f"{COSMO_API_URL}?email={email}&password={password}&limit={limit}&offset={offset}",
                headers={
                    "Content-Type": "application/json",
                    "projectId": PROJECT_ID,
                    "environmentId": ENV_ID
                }
            )

            if response.status_code == 200:
                user_data = response.json()
                if user_data['data']:
                    user = user_data['data'][0]
                    if 'username' in user and user['username'] is not None:
                        st.success(f"Welcome back, {user['username']}!")
                        st.session_state['user_id'] = user['_id']  # Store user_id in session state
                        return user
                    else:
                        st.error("Username not found in user data.")
                else:
                    st.error("No user data returned.")
            else:
                if response.status_code == 404:
                    st.error("User not found. Please check your credentials.")
                else:
                    st.error(f"Login failed. Error: {response.text}")

    return None  # Return None if user is not authenticated

