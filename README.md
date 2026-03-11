# 🤖 JOB-TALK AI: Intelligent Recruitment Ecosystem
**Developed by:** [Khushi Tyagi](https://github.com/khushityaagi) | *Final Year Major Project*

A high-performance, dual-sided AI platform designed to bridge the gap between student talent and global job markets using **Vector Space Modeling** and **Generative AI**.

---

## 📸 Project Proof & UI
| **Candidate Experience** | **Recruiter Intelligence** |
| :--- | :--- |
| ![Student Portal](screenshots/system_dashboard_overview.png) | ![Recruiter Dashboard](screenshots/recruiter_dashboard_ui.png) |
| *Real-time resume parsing & AI coaching* | *Strategic sourcing & talent ranking* |

---

##  System Overview
* **Student Portal:** Interactive landing page for PDF resume uploads, skill-gap analysis, and LinkedIn job recommendations.
* **Recruiter Dashboard:** Command center for HR professionals to source the **Top 10 candidates** using mathematical alignment from raw Job Descriptions.

---

##  Technical Architecture
The system utilizes a **Retrieval-Augmented Generation (RAG)** and Vector Search workflow:

1. **Vectorization:** Text data is transformed into numerical vectors using **TF-IDF (Term Frequency-Inverse Document Frequency)**.
2. **Matching:** **Cosine Similarity** calculates the mathematical alignment between candidates and roles.
3. **Generative AI:** Powered by **Google Gemini 1.5 Flash**, the chatbot retrieves user-specific data from **MySQL** to provide context-aware career advice.



---

## Tech Stack
* **Backend:** FastAPI (Python) - High-performance asynchronous API framework.
* **AI Engine:** Google Gemini 1.5 Flash - Generative AI for personalized career coaching.
* **ML Libraries:** Scikit-Learn - Implemented for **TF-IDF Vectorization** and **Cosine Similarity**.
* **Database:** MySQL - Persistent storage for resumes, extracted skills, and chat history.
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API).

---

##  Dataset Specifications (Sourced from Kaggle)
The system is trained and tested on high-scale, real-world data:
* [cite_start]**Candidate Pool:** 2,484 Resumes categorized into 24 industries (e.g., IT, Engineering, Finance) from the **Snehaan Bhawal Resume Dataset** (Kaggle) [cite: 2, 6, 9, 10-57].
* [cite_start]**Job Market:** 123,842 LinkedIn Job Postings (2023-2024) from the **Arsh Koneru Dataset** (Kaggle)[cite: 3, 5].



---

## How to Run
1. **Database:** Ensure your MySQL server is running and the `resumes` table is created.
2. **Backend:** ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
