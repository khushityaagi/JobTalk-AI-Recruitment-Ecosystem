from google import genai

client = genai.Client(api_key="enter your unique api key ")

def get_chatbot_response(query, resume_text, skills):
    if resume_text == "No resume uploaded yet.":
        return "Please upload your resume first so I can scan your background!"
    
    try:
        prompt = f"""
        You are an expert AI Tech Recruiter Assistant named 'JOB-TALK AI'.
        A candidate is asking you a question: "{query}"
        
        Here is the candidate's actual resume text:
        {resume_text[:2000]} 
        
        Extracted Core Skills: {skills}
        
        Answer the candidate's question directly, professionally, and warmly. 
        Give specific advice or observations based *only* on the resume text provided above. 
        Keep your response concise and conversational (2-4 sentences max). Do not use bold/markdown asterisks.
        """
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        
        return response.text.replace('*', '') 
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return "I'm analyzing your profile, but my AI connection is currently taking a break. Try again in a moment!"