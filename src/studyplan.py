import os
import streamlit as st
import requests
from groq import Groq


# Set your Groq API key
os.environ['GROQ_API_KEY'] = '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'
# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

QUIZ_DATA_URL = "https://free-ap-south-1.cosmocloud.io/development/api/quiz_data"  
USER_DATA_URL = "https://free-ap-south-1.cosmocloud.io/development/api/user_data"
STUDY_PLAN_URL= "https://free-ap-south-1.cosmocloud.io/development/api/study_plan"

ENV_ID = "66dabc906f12fff792820bb0"
PROJECT_ID = "66dabc906f12fff792820baf"

def get_study_plan_id(user_id):
    # CosmoCloud API endpoint for retrieving study plan data based on user_id
    url = f"{STUDY_PLAN_URL}?user_id={user_id}&limit=10&offset=0"
    
    headers = {
        "Content-Type": "application/json",
        "projectId": PROJECT_ID,
        "environmentId": ENV_ID
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        study_plan_data = response.json()
        #st.write(f"study plan data:{study_plan_data}")
        if 'data' in study_plan_data and len(study_plan_data['data']) > 0:
            return study_plan_data['data'][0]['_id']  # Return the _id of the first record
        else:
            print("No study plan data found for the specified user ID.")
            return None
    else:
        print(f"Error retrieving study plan data. Status code: {response.status_code}")
        return None
def get_quiz_data_id(user_id):
    # CosmoCloud API endpoint for retrieving quiz data based on user_id
    url = f"{QUIZ_DATA_URL}?user_id={user_id}&limit=1&offset=0"
    
    headers = {
        "Content-Type": "application/json",
        "projectId": PROJECT_ID,
        "environmentId": ENV_ID
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        quiz_data = response.json()
        return quiz_data['data'][0]['_id']
    else:
        print(f"Error retrieving quiz data. Status code: {response.status_code}")
        return None
      
def fetch_quiz_data(user_id):
    # CosmoCloud API endpoint for fetching quiz data
    url = f"{QUIZ_DATA_URL}/{user_id}"
    headers = {
        "Content-Type": "application/json",
        "projectId": PROJECT_ID,
        "environmentId": ENV_ID
    }
    try:
        # Sending GET request to fetch quiz data
        response = requests.get(url,headers=headers)
        
        if response.status_code == 200:
            quiz_record = response.json()
            return quiz_record
        else:
            print(f"Error fetching quiz data. Status code: {response.status_code}")
            print(f"Response content: {response.text}") 
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def fetch_study_plan_data(user_id):
    url = f"{STUDY_PLAN_URL}/{user_id}"
    headers = {
        "Content-Type": "application/json",
        "projectId": PROJECT_ID,
        "environmentId": ENV_ID
    }
    try:
        response = requests.get(url, headers=headers)
        #st.write(f"Status code: {response.status_code}")
        #st.write(f"Response content: {response.text}")
        
        response.raise_for_status()  # Raise an error for bad responses
        study_plan_record = response.json()
        return study_plan_record
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching study plan data: {e}")
        return None

def study_plan_creator(certification_goal,deadline,revision,study_plan_record):

    query_template = f"""You are a Learning Path Creator for {certification_goal} exam. 
    The user has {deadline} no.of.days to prepare for {certification_goal} exam.
    User is a {study_plan_record.get('proficiency_level')} and lacks proficiency in {study_plan_record.get('weak_areas')}.
    He wants to revise {revision} topics as well.
    Generate a comprehensive study plan that includes key topics, resources, and recommendations 
    based on proficiency and time constraints"""
    
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": query_template}],
        model="gemma2-9b-it"
    )
    try:
        response_content = chat_completion.choices[0].message.content
        st.write("Study Plan:", response_content)  # Debug line
        return response_content
    except Exception as e:
        st.error(f"Error querying LLM: {str(e)}")
        return None

#streamlit app-main function
def user_study_plan():
    # CSS for styling the UI
    st.markdown("""
        <style>
            .stButton>button {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                margin: 10px 0;
            }
            .stTextInput, .stNumberInput, .stSelectbox, .stMultiselect {
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
            .stNumberInput>div>input, .stTextInput>div>input {
                border: 1px solid #ddd;
                padding: 5px;
                border-radius: 5px;
            }
            .stMarkdown h1 {
                color: #4CAF50;
                font-weight: bold;
                text-align: center;
            }
            .custom-container {
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 15px rgba(0,0,0,0.1);
                max-width: 800px;
                margin: auto;
            }
            .stMultiselect {
                background-color: #f0f0f0;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("Study Plan Recommendation Assistant")
    st.markdown(
        """
        - :bulb: **Custom Study Plans:** Dynamic plans that evolve based on your progress.
        - :chart_with_upwards_trend: **Progress Tracking:** Monitor your journey toward certification mastery.
        """
    )
    # Fetch the user_id from session state
    user_id = st.session_state.get('user_id')
    
    if not user_id:
        st.error("No user is logged in. Please log in first.")
        return

    # Retrieve study plan record and quiz record for the user
    st.write(f"Fetching study plan data for user: {user_id}")
    study_plan_id=get_study_plan_id(user_id)
    study_plan_record = fetch_study_plan_data(study_plan_id)
    quiz_id=get_quiz_data_id(user_id)
    quiz_data_record = fetch_quiz_data(quiz_id)

    if not study_plan_record:
        st.error("Failed to fetch study plan data.")
        return

    if quiz_data_record is None:
        st.error("Failed to fetch quiz data or received null response.")
        return
    
    certification_goal = quiz_data_record.get('certification_type')  # Use .get() to avoid KeyError
    if not certification_goal:
        st.error("Certification goal is not available in the quiz data.")
        return
    
    # Select deadline for certification
    deadline = st.number_input("Enter the Number of Days left for preparation (in days):", min_value=1, step=1)
    revision = st.multiselect(
        "Topics in which you might need extra help",
        ["Security, Identity and Compliance", "Storage and Databases", "Cloud Concepts", 
         "Core Architectural Concepts", "Compute and Networking", "All"]
    )

    # Check if revision topics are selected
    if not revision:
        st.warning("Please select at least one revision topic.")
        return
    
    # Pass data to study_plan_creator
    data = study_plan_creator(certification_goal, deadline, revision, study_plan_record)
    return data
