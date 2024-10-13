import json
import os
import uuid
import boto3
import requests
import streamlit as st
from io import BytesIO
import tempfile
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from langchain_community.document_loaders import PyPDFLoader
import urllib.parse
from groq import Groq
from datetime import datetime
from login import add_button_hover_style
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Set your Groq API key
os.environ['GROQ_API_KEY'] = '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'

QUIZ_DATA_URL = "https://free-ap-south-1.cosmocloud.io/development/api/quiz_data"  # URL for quiz_data
USER_DATA_URL = "https://free-ap-south-1.cosmocloud.io/development/api/user_data"
STUDY_PLAN_URL= "https://free-ap-south-1.cosmocloud.io/development/api/study_plan"

ENV_ID = "66dabc906f12fff792820bb0"
PROJECT_ID = "66dabc906f12fff792820baf"
# Your MongoDB credentials
username = 'manjushree1609'
password = 'mongodb@321'

# URL-encode the username and password
encoded_username = urllib.parse.quote_plus(username)
encoded_password = urllib.parse.quote_plus(password)

# Construct the connection URI with the encoded credentials
uri = f"mongodb+srv://{encoded_username}:{encoded_password}@sandbox.aw2sc.mongodb.net/?retryWrites=true&w=majority&appName=SandBox"

# Create a MongoClient instance
mongo_client = MongoClient(uri)
db = mongo_client['cert_db']
collection = db['cert_vectors']

# AWS S3 Configuration
S3_BUCKET = "quizquestionspdfs"
S3_KEY_AWS = "aws-certified-cloud-practitioner-clf-c02.pdf"
S3_KEY_AZURE = "azure_fundamentals.pdf"
# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Function to download PDF from S3
def download_pdf_from_s3(bucket, key):
    s3_client = boto3.client('s3')
    pdf_file = BytesIO()
    
    try:
        s3_client.download_fileobj(bucket, key, pdf_file)
        pdf_file.seek(0)  # Move pointer to the beginning of the file
        return pdf_file
    except Exception as e:
        st.error(f"Error downloading file from S3: {str(e)}")
        return None

# Function to extract text from PDF
def extract_pdf_content(pdf_file):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
        temp_pdf.write(pdf_file.read())
        temp_pdf_path = temp_pdf.name

    loader = PyPDFLoader(temp_pdf_path)
    documents = loader.load()
    limit_docs=documents[10:25]
    return limit_docs
    

# Function to split text into chunks for embedding
def split_text(documents):
    full_text = " ".join([doc.page_content for doc in documents])
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(full_text)
    return chunks

# Function to convert text chunks into vectors
def convert_text_to_vectors(chunks):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(chunks)
    st.write(f"Number of chunks: {len(chunks)}")
    st.write(f"Embedding dimensions for each chunk: {embeddings.shape}")
    return embeddings

# Function to save embeddings in batch to MongoDB
def save_embeddings_batch(embeddings, texts, collection, certification_type):
    if embeddings is not None and len(embeddings) > 0 and texts is not None and len(texts) > 0 and collection is not None:
        documents = []
        for idx, embedding in enumerate(embeddings):
            if embedding is not None and texts[idx]:
                # Check if this chunk is already in the collection
                query = {
                    "text": texts[idx],
                    "certification_type": certification_type,
                    "chunk_index": idx
                }
                existing_doc = collection.find_one(query)

                if existing_doc:
                    #st.write(f"Chunk {idx} for {certification_type} is already in the database. Skipping insertion.")
                    pass
                else:
                    document = {
                        "text": texts[idx],
                        "vector": embedding.tolist(),
                        "certification_type": certification_type,
                        "chunk_index": idx
                    }
                    documents.append(document)

        if documents:
            #st.write("Inserting new documents:", documents)
            try:
                collection.insert_many(documents)
                #st.write(f"{len(documents)} new documents for {certification_type} saved into MongoDB as embeddings!")
            except Exception as e:
                st.error(f"Error inserting documents into MongoDB: {str(e)}")



# Function to retrieve relevant documents from MongoDB 
def retrieve_relevant_docs(query, collection):
    if query and collection is not None:
        model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
        if model:
            # Encode the query to get the query vector
            query_vector = model.encode(query).reshape(1, -1)  # Reshape for compatibility
            
            # Fetch documents from the collection
            docs = list(collection.find({}, {"_id": 1, "text": 1, "vector": 1}))  # Limit fields to necessary ones
            
            if docs and query_vector is not None:
                # Extract vectors and calculate cosine similarity
                doc_vectors = np.array([doc["vector"] for doc in docs])
                
                # Calculate cosine similarities
                similarities = cosine_similarity(query_vector, doc_vectors).flatten()  # Flatten to 1D
                
                # Get indices of the top 2 most similar documents
                top_indices = np.argsort(similarities)[-2:][::-1]
                
                # Check if top_indices are within bounds of docs
                relevant_docs = []
                for i in top_indices:
                    if i < len(docs):  # Ensure index is valid
                        relevant_docs.append(docs[i])
                
                # Check if we found relevant docs
                if relevant_docs:
                    return relevant_docs
                
    return None  # Return None if no relevant documents are found


# Cosine similarity function
def cosine_similarity(vector_1, vector_2: np.ndarray):
    # Check if both vectors are not empty
    if vector_1.size > 0 and vector_2.size > 0:
        return sum(a * b for a, b in zip(vector_1, vector_2)) / (sum(a * a for a in vector_1) ** 0.5 * sum(b * b for b in vector_2) ** 0.5)
    else:
        raise ValueError("One or both vectors are empty.")

# Function to query LLM for quiz questions
def query_llm_for_questions(topics, qstn_count, certification_type, cert_name):
    query=f"""" Find the questions that relate to {topics}"""
    context_text=retrieve_relevant_docs(query, collection)
    # Limit context_text size
    if context_text:
        context_text = context_text[:2] 
        st.write(f"context_text:{context_text}")
    query_template = f"""You are a {certification_type} certification quiz generator. Ensure they are relevant to the {cert_name} certification. 
    Generate {qstn_count} questions from topics: {topics} ,refer {context_text}. Question should mimic actual certification exam.
    Format the output as JSON, with the following structure, do not give explanation or any other text in answer except a well formatted json:

    {{
        "questions": [
            {{
                "question_text": "{{generated_question}}", 
                "options": [
                    {{
                        "option_text": "{{generated_option_1}}",
                        "is_correct": {{if option_text is not generated_correct_option then false otherwise true}}
                    }},
                    {{
                        "option_text": "{{generated_option_2}}",
                        "is_correct": {{if option_text is not generated_correct_option then false otherwise true}}
                    }},
                    {{
                        "option_text": "{{generated_option_3}}",
                        "is_correct": {{if option_text is not generated_correct_option then false otherwise true}}
                    }},
                    {{
                        "option_text": "{{generated_option_4}}",
                        "is_correct": {{if option_text is not generated_correct_option then false otherwise true}}
                    }}
                ],
                "correct_option": "{{generated_correct_option}}"
            }}
        ]
    }}"""
    st.write(f"Input message length: {len(query_template)}")
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": query_template}],
        model="gemma2-9b-it"
    )
    try:
        response_content = chat_completion.choices[0].message.content
        #st.write("Raw API Response:", response_content)  # Debug line
        return response_content
    except Exception as e:
        st.error(f"Error querying LLM: {str(e)}")
        return None


def calculate_score(quiz_json, responses):
    correct_answers = 0
    for question in quiz_json["questions"]:
        correct_option = question["correct_option"]
        user_answer = responses.get(question["question_id"])
        question["user_selected_option"] = user_answer
        question["is_correct"] = user_answer == correct_option
        if question["is_correct"]:
            correct_answers += 1

    total_questions = len(quiz_json["questions"])
    percentage_score = (correct_answers / total_questions) * 100
    return correct_answers, total_questions, percentage_score

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
    
def get_quiz_data(user_id):
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
        return quiz_data  # Assuming this returns a list of records
    else:
        print(f"Error retrieving quiz data. Status code: {response.status_code}")
        return None

# Function to update quiz_data record for a particular user using CosmoCloud API
def update_quiz_data(user_id, update_payload):
    quiz_data = get_quiz_data(user_id)
    #st.write(f"quiz_data:{quiz_data}")
    quiz_record_id = quiz_data['data'][0]['_id'] 
    # CosmoCloud API endpoint for updating quiz data
    url = f"{QUIZ_DATA_URL}/{quiz_record_id}"
    
    headers = {
        "Content-Type": "application/json",
        "projectId": PROJECT_ID,
        "environmentId": ENV_ID
    }
    
    try:
        # Sending PATCH request to update quiz data
        response = requests.patch(url, json=update_payload, headers=headers)
        
        if response.status_code == 200:
            print("Quiz data updated successfully.")
        else:
            print(f"Error updating quiz data. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to update user_data record for a particular user using CosmoCloud API
def update_user_data(user_id, certification_goal):
    # API endpoint to update user data
    url = f"{USER_DATA_URL}/{user_id}"

    # Prepare the data to be updated
    update_payload = {
        "certification_goal": certification_goal
    }

    headers = {
        "Content-Type": "application/json",
        "projectId": PROJECT_ID,
        "environmentId": ENV_ID
    }

    try:
        # Sending PATCH request to update user data
        response = requests.patch(url, json=update_payload, headers=headers)

        if response.status_code == 200:
            st.write("User certification goal updated successfully.")
        else:
            st.error(f"Error updating user certification goal. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"An error occurred: {e}")


def analyze_user_performance(user_score,input_data,cert_name,user_id):
    # Extracting input data
    topics= input_data
    
    # Define the proficiency levels based on percentage ranges
    def determine_proficiency_level(score):
        if score >= 80:
            return 'Advanced'
        elif 50 <= score < 80:
            return 'Intermediate'
        else:
            return 'Beginner'

    # Function to query LLM for quiz questions and study recommendations
    def fetch_study_recommendations(topics, cert_name,proficency_level):
        # Create a query template to pass to the LLM for recommendations
        query_template = f"""
        You are a {cert_name} Certification Assistant. 
        The user lacks proficiency in the following {', '.join(topics)}and classify it under these (Cloud Concepts,Security and Compliance,Technology,
        Billing and Pricing,AWS Well-Architected Framework,Storage,Networking, IAM,Machine Learning, etc).
        Few should be in weak_areas. 
        Provide study resources, it should contain links to study and give suggestions to improve proficiency in these areas.
        Format the output as JSON, with the following structure, do not give explanation or any other text in answer except a well formatted json,
        {{
        "proficiency_level":{proficency_level},
        "weak_areas": ["{{areas_that_need_improvement}}"],
        "links": ["{{links_to_study}}"],
        "study_recommendations":["{{study_recommendation_topics}}]"
        }}
        """

        try:
            # Query the LLM using the GroqAPI client
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": query_template}],
                model="gemma2-9b-it"  # Model used for the recommendation
            )
            
            # Extract the response content from the API response
            response_content = chat_completion.choices[0].message.content
            
            # Debugging - Display raw response
            #st.write("Raw API Response:", response_content)
            
            return response_content
        
        except Exception as e:
            # Handle any errors during the API call
            st.error(f"Error querying LLM: {str(e)}")
            return None

    # Determine the proficiency level
    proficiency_level = determine_proficiency_level(user_score)
   
    # Fetch study recommendations from GroqAPI
    recommendations = fetch_study_recommendations(topics, cert_name,proficiency_level)
    cleaned_string = recommendations.replace("json", "").replace("```", "")
    #st.write("cleaned string:", cleaned_string)
    parsed_recommendations = json.loads(cleaned_string)
    #st.write(f"parsed_recommendations: {parsed_recommendations}")
    study_plan_id=get_study_plan_id(user_id)
    try:
        response = requests.patch(
            f"{STUDY_PLAN_URL}/{study_plan_id}",
            json=parsed_recommendations,
            headers={
                "Content-Type": "application/json",
                "projectId": PROJECT_ID,
                "environmentId": ENV_ID
            }
        )

        # Log the response details for debugging
        #st.write("Response Status Code:", response.status_code)
        #st.write("Response Text:", response.text)

        response.raise_for_status()  # Raise an error for HTTP error responses

        if response.status_code == 200:
            st.success("Study plan updated successfully!")
        else:
            st.error(f"Unexpected response status: {response.status_code}. Response: {response.text}")

    except requests.exceptions.HTTPError as e:
        st.error(f"Failed to update study plan. HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
# Function to add custom CSS for quiz styling
def add_quiz_css():
    st.markdown(
        """
        <style>
        .quiz-container {
            background-color: #f9f9f9;  /* Light grey background for contrast */
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);  /* Subtle shadow for depth */
            margin-bottom: 20px;
        }

        .quiz-question {
            font-size: 1.1rem;
            font-weight: bold;
            color: #333;  /* Darker text for readability */
            margin-bottom: 10px;
        }

        .quiz-options {
            display: flex;
            flex-direction: column;  /* Options stacked vertically */
            gap: 8px;  /* Space between each option */
        }

        .quiz-options input[type="radio"] {
            accent-color: green;  /* Color of radio buttons */
        }

        .stRadio label {
            font-size: 1rem;
            padding: 5px;
            background-color: #fff;  /* White background for options */
            border-radius: 5px;
            transition: background-color 0.3s, color 0.3s;
        }

        .stRadio label:hover {
            background-color: #e0f7e9;  /* Light green background on hover */
            color: #000;
        }

        .stRadio label[data-selected="true"] {
            background-color: #d9f9d8;  /* Highlight selected option */
            color: #000;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Streamlit App
def quiz_page():
    
    st.title("Quizzes")
    st.markdown(
            """
            - :trophy: **Tailored Quizzes:** Quizzes adapted to your certification needs (AWS, Azure).
            """
        )
    # Fetch the user_id from session state
    user_id = st.session_state.get('user_id')
    
    if not user_id:
        st.error("No user is logged in. Please log in first.")

    # Select certification type and input fields
    cert_type = st.selectbox("Select Certification Type", ("AWS", "Azure"))
    cert_name = st.text_input("Enter Certification Name (e.g., AWS Cloud Practitioner, Azure Fundamentals)")
    qstn_count = st.number_input("Enter the Number of Questions", min_value=1, step=1)
    topics = st.text_input("Enter Topics for the Quiz (comma separated)", "Security, Networking, ML, Storage")
    # Update user certification goal once entered
    update_user_data(user_id, cert_name)
    # Apply button hover style
    add_button_hover_style()
    # Generate quiz button
    if st.button("Generate Quiz"):
        pdf_file=None
        if cert_type.upper() == "AWS" and cert_name.upper() == "AWS CLOUD PRACTITIONER":
            pdf_file = download_pdf_from_s3(S3_BUCKET, S3_KEY_AWS)
        elif cert_type.upper() == "AZURE" and cert_name.upper() == "AZURE FUNDAMENTALS":
            pdf_file = download_pdf_from_s3(S3_BUCKET, S3_KEY_AZURE)
        
        if pdf_file:
            st.write(f"PDF for {cert_name} downloaded from S3 successfully!")
            documents = extract_pdf_content(pdf_file)
            st.write(f"PDF contains {len(documents)} pages.")
            chunks = split_text(documents)
            st.write(f"Text split into {len(chunks)} chunks for vectorization.")
            vectors = convert_text_to_vectors(chunks)
            save_embeddings_batch(vectors, chunks, collection, cert_type)
            st.write("Embeddings are successfully inserted into the database.")
            questions = query_llm_for_questions(topics, qstn_count, cert_type, cert_name)
            if not questions:
                st.error("No questions generated from the LLM.")
            else:
                try:
                    cleaned_string = questions.replace("json", "").replace("```", "")
                    parsed_questions = json.loads(cleaned_string)
                    #st.write("cleaned string:", cleaned_string)
                except json.JSONDecodeError as e:
                    st.error(f"Error parsing JSON: {e}")
                    return None
                
                if parsed_questions:
                    # Store the quiz questions in session state
                    st.session_state.quiz_json = parsed_questions 
                    st.session_state.responses = {}  # Initialize or reset responses
                

    # Check if quiz_json exists in session state to display the quiz
    if "quiz_json" in st.session_state:
        quiz_json = st.session_state.quiz_json

        # Display quiz questions and options
        if "responses" not in st.session_state:
            st.session_state.responses = {}  # Initialize or reset responses

        responses = st.session_state.responses
        for idx, question in enumerate(quiz_json["questions"]):
            # Check if question_id exists, if not generate a new one
            if "question_id" not in question:
                question["question_id"] = str(uuid.uuid4())  # Generate a unique ID

            # Wrap each question and its options in a styled container
            with st.container():
                st.markdown('<div class="quiz-container">', unsafe_allow_html=True)
                st.markdown(f'<div class="quiz-question">Q{idx + 1}: {question["question_text"]}</div>', unsafe_allow_html=True)
                
                options = [opt["option_text"] for opt in question["options"]]

                # Pre-select the previously chosen option if available
                user_response = st.radio(
                    f"Choose an answer for Q{idx + 1}",
                    options,
                    index=options.index(responses.get(question["question_id"], "")) if question["question_id"] in responses else 0,
                    key=f"question_{idx}"
                )

                responses[question["question_id"]] = user_response  # Store response in session state

                # End of the quiz container
                st.markdown('</div>', unsafe_allow_html=True)
        
        values_responses = list(responses.values())
        # Submit Quiz button
        if st.button("Submit Quiz"):
            correct_answers, total_questions, percentage_score = calculate_score(quiz_json, responses)
            # Analyze user performance and provide feedback
            result = analyze_user_performance(percentage_score, values_responses,cert_name,user_id)
            st.write(result)
            st.success(f"You scored {correct_answers} out of {total_questions} ({percentage_score:.2f}%).")
            
            update_payload = {
                "certification_type": cert_name,
                "quiz_generated_date":datetime.utcnow().isoformat(),
                "score": {
                    "total_questions": total_questions,
                    "correct_answers": correct_answers,
                    "percentage_score": percentage_score,
                },
                "questions": quiz_json["questions"],
                "attempt_date": datetime.utcnow().isoformat()

            }
            final_record=update_quiz_data(user_id, update_payload)
            st.write(final_record)

   


