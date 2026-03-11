import pandas as pd
import mysql.connector

# Database Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sj8=63GpJ", 
    database="job_talk"
)
cursor = db.cursor()

try:
   
    df = pd.read_csv(r'C:\Users\khushi tyagi\Major project -2 (JOB - TALK)\backend\job description\postings.csv')
    
   
    for _, row in df.head(500).iterrows():
        title = str(row.get('title', 'Unknown Job'))
        description = str(row.get('description', 'No description available'))
        skills = "Python, SQL, Management" 
        
        sql = "INSERT INTO jobs (title, description, required_skills) VALUES (%s, %s, %s)"
        cursor.execute(sql, (title, description, skills))
    
    db.commit()
    print("Training Phase Complete: 50 Job Postings loaded into MySQL.")
except Exception as e:
    print(f"Error: {e}")