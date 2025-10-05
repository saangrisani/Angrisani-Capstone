# Angrisani-Capstone

**Veterans Mental Health Companion**  
Capstone design project for **Fall 2025** with *Matt Hill*  
Author: **Sean Angrisani**

---

##  Overview
This Django-based web application, **Vet_Mh**, provides an AI-powered chat assistant for U.S. veterans.  
It includes pages for **Home**, **Chat**, **About**, and **Resources**, with secure user authentication (sign up, login, logout).  
The chatbot uses the **OpenAI API** to provide supportive and resource-driven responses.

---

## ⚙️ What’s Implemented
- Django project: `Vet_Mh`
- App: `ai_mhbot`
- Pages:
  - `/` → Home  
  - `/chat/` → AI Chatbot  
  - `/about/` → About page  
  - `/resources/` → Veteran resource links
- Shared **Bootstrap-based Navbar**
- **Auth System:** register/login/logout
- **OpenAI Chat Integration:** handled in `ai_mhbot/openai_utility.py`  
  Uses environment variables for secure key loading.

---

##  Quickstart (Local Setup)
### 1. Clone the Repository
```bash
git clone https://github.com/SeanAngrisani/Angrisani-Capstone.git
cd Angrisani-Capstone
