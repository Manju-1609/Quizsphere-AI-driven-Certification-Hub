# Quizsphere-AI-driven-Certification-Hub
QuizSphere is an AI-driven web application designed to streamline preparation for cloud certifications, currently supporting AWS Cloud Practitioner and Azure Fundamentals.
## Objective
The goal of QuizSphere is to streamline and enhance the preparation process for cloud certification exams by providing personalized and adaptive quizzes. Using generative AI, QuizSphere dynamically generates quiz questions tailored to the chosen certification path and specific learning topics, helping users focus on their strengths and identify weak areas. It also creates a customized study plan based on the user’s performance, ensuring efficient preparation within the available timeframe.
## Background
Preparing for cloud certification exams, such as AWS Cloud Practitioner and Azure Fundamentals, often requires candidates to purchase dumps or rely on multiple resources, leading to a scattered and inefficient study process. The credibility of these resources can be questionable, and the lack of structured, customized learning paths can hinder effective preparation. QuizSphere addresses these challenges by using AI to generate questions that mimic actual exam scenarios, providing real-time feedback, and offering a study plan that evolves with user performance.

## Description:

Users sign up, log in, and select a certification path.
They specify topics and the number of questions to generate custom quizzes.
Questions are generated using the Gemma2-9b-it LLM via Groq API, based on vectors stored in MongoDB, derived from PDFs on AWS S3.

Performance Analysis & Study Plan:

After each quiz, users receive a score breakdown, identifying weak areas and proficiency levels (Beginner, Intermediate, Advanced).
Users can specify preparation days to receive a customized study plan that adapts based on performance, focusing on improvement areas.

Data Management:

Backend operations, including user data, quiz results, and study plans, are managed via CosmoCloud, with user IDs linking related data.
## Tech stack
![image](https://github.com/user-attachments/assets/55a3a962-64d0-4c1f-97a7-a1ead54776e5)

## Architecture
![Blank diagram](https://github.com/user-attachments/assets/9cbaae2f-e84c-488d-831f-e44fb3ec8f4a)
## Output
Quiz Generation:
![image](https://github.com/user-attachments/assets/2c0d5f60-04d8-4693-b0e9-0db04fe8397a)
![image](https://github.com/user-attachments/assets/07fd9ddf-e2bc-4be9-9523-18ecd16a7ad7)

Study plan recommendation:
![image](https://github.com/user-attachments/assets/5b701b7e-c9a2-4f79-aab1-460f2ab1b996)
![image](https://github.com/user-attachments/assets/b488c9f0-3a77-47b5-96b5-bb544cb8162d)
![image](https://github.com/user-attachments/assets/02a152ec-8dc6-4e37-a0d2-7532e6b851f4)

## References
- https://docs.cosmocloud.io/
- https://www.mongodb.com/docs/
- https://console.groq.com/docs/quickstart
- https://www.examtopics.com/
