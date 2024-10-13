# main.py
import streamlit as st
from login import user_authentication
from quiz import quiz_page
from studyplan import user_study_plan
from PIL import Image
import base64
from io import BytesIO

# --- PAGE SETUP ---
st.set_page_config(
    page_title="QuizSphere",
    page_icon=":books:",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Define navigation pages
login = st.Page(
    "login.py",
    title="Login/signup",
    icon=":material/account_circle:",
    default=True,
)

project_1_page = st.Page(
    "quiz.py",
    title="Quizzes",
    icon=":material/question_answer:",
)

project_2_page = st.Page(
    "studyplan.py",
    title="Studyplan",
    icon=":material/assignment:",
)

pg = st.navigation(
    {
        "Info": [login],
        "Home": [project_1_page, project_2_page],
    }
)

# Load the background image and convert it to base64
def get_base64_background(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# CSS to style the logo and bottom-right image
def add_bg_with_logo_style(background_image_base64):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/avif;base64,{background_image_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .sub-pages {{
            position: relative;
        }}
        .circular-logo {{
            width: 200px;  /* Adjust size of the circular logo */
            height: 200px;
            border-radius: 50%;  /* Makes the logo circular */
            border: 10px solid rgba(255, 255, 255, 0.8);  /* White border blending with the background */
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);  /* Soft shadow for better blending */
            object-fit: cover;  /* Ensures the image covers the circular area */
            position: relative;
            top: 20px;  /* Position above the login section */
            left: 50%;
            transform: translateX(-50%);
            z-index: 1;  /* Ensure the image stays on top */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Convert an image to base64 format
def convert_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def main():
    # Load and set the background image
    background_image_base64 = get_base64_background("background.jpg")
    
    # Apply CSS for the background, logo, and corner image
    add_bg_with_logo_style(background_image_base64)

    # Load and display the logo
    logo = Image.open("logo2.png")
    logo_base64 = convert_image_to_base64(logo)
    
    if pg == login:
        st.markdown('<div class="sub-pages">', unsafe_allow_html=True) 
        st.markdown(
            f"""
            <div>
                <img src="data:image/png;base64,{logo_base64}" class="circular-logo"/>
            </div>
            """,
            unsafe_allow_html=True
        )
        user = user_authentication()
        
        # Assuming user authentication returns user details including user_id
        if user:
            st.session_state['user_id'] = user['_id']

        st.markdown('</div>', unsafe_allow_html=True)

    # Render other pages if user is logged in
    if st.session_state.get('user_id'):
        if pg == project_1_page:
            data = quiz_page()  # Now the quiz page can access the user_id from session state
        if pg == project_2_page:
            study = user_study_plan()

if __name__ == '__main__':
    main()
