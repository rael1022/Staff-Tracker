# 🏫 Staff Training and Certification Tracker

A web-based application developed as a project for the **Software Engineering Fundamentals** course.  
This system applies core software engineering principles to design and implement a structured solution for managing **staff training**, **certifications**, **CPD (Continuing Professional Development)**, **attendance**, and **automated notifications**.

The project emphasizes modular design, maintainability, and real-world applicability using modern web technologies.

---

## 📘 Project Overview

Managing staff training and certification records manually is inefficient and error-prone.  
This project addresses these issues by providing a centralized system that improves data organization, tracking efficiency, and notification accuracy.

The system supports:
- Digital certificate generation (PDF)
- QR code integration for verification
- Automated email reminders for certificate expiry

---

## ✨ Key Features

- 📚 Staff training and certification management  
- 📊 CPD tracking and summary reports  
- 🕒 Attendance management  
- 📧 Automated certificate expiry reminder emails  
- 📄 PDF certificate generation  
- 🔳 QR code generation for certificates  
- 🔐 Secure authentication and authorization  
- 🌐 RESTful API support  

---

## 🛠️ Technology Stack

- **Backend Framework:** Django 5.1.4  
- **API Framework:** Django REST Framework  
- **Authentication:** SimpleJWT, Knox  
- **Database:** SQLite (default)  
- **PDF & Certificate:** ReportLab, PyHanko, PyPDF  
- **QR Code:** qrcode  
- **Email Service:** Gmail SMTP  

---

## 🗂️ Project Structure

```text
Staff-Tracker/
├── backend/
│   ├── .myvenv/
│   ├── StaffTracker/
│   │   ├── accounts/
│   │   ├── assessment/
│   │   ├── assets/
│   │   ├── attendance/
│   │   ├── certificate/
│   │   ├── cpd/
│   │   ├── department/
│   │   ├── evaluation/
│   │   ├── registration/
│   │   ├── reports/
│   │   ├── StaffTracker/
│   │   ├── training/
│   │   └── manage.py
│   └── requirements.txt
├── frontend/
│   ├── assessment/
│   ├── attendance/
│   ├── certificate/
│   ├── cpd/
│   ├── dashboard/
│   ├── evaluation/
│   ├── login/
│   ├── manage_account/
│   ├── register/
│   ├── reports/
│   ├── trainer/
│   └── training/
├── .gitignore
└── README.md

```    
---

## ⚙️ Installation & Setup

Follow the steps below to run the project locally.

### 1️⃣ Clone the Repository

git clone <your-repository-url>
cd Staff-Tracker/backend

### 2️⃣ Create & Activate Virtual Environment

python -m venv myvenv

**Windows**

myvenv\Scripts\activate


**macOS / Linux**

source myvenv/bin/activate


### 3️⃣ Install Dependencies

pip install -r requirements.txt

### 4️⃣ Apply Database Migrations

cd StaffTracker
python manage.py migrate

### 5️⃣ Create Superuser (Optional)

python manage.py createsuperuser

### 6️⃣ Run Development Server

python manage.py runserver

📍 Access the system at:  
http://127.0.0.1:8000/

---

## Gmail Email Configuration

To enable the system to send email reminders, you need to configure Gmail SMTP in `settings.py`. It is recommended to use a **Gmail App Password** instead of your regular Gmail password.

### 1. Generate a Gmail App Password
1. Log in to your Gmail account → click your avatar → **Manage Google Account** → **Security**.  
2. Under **App Passwords**, generate a 16-character password for the application.  
3. ⚠ Note: Use this password only for sending emails via the system, not your Gmail login.

### 2. Update `settings.py`
Open `settings.py` and modify the following lines:

```python
EMAIL_HOST = 'smtp.gmail.com'                     # line 145: SMTP host
EMAIL_HOST_USER = 'your_email@gmail.com'          # line 146: replace with your Gmail address
EMAIL_HOST_PASSWORD = 'your_app_password'         # line 147: replace with your 16-character App Password
EMAIL_PORT = 587                                  # line 148: SMTP port
EMAIL_USE_TLS = True                              # enable TLS

```
---

## 📄 PDF & Certificate Generation

The system generates certificates in PDF format using **ReportLab**, **PyHanko**, and **PyPDF**.  
QR codes embedded in certificates are generated using the **qrcode** library.

All required libraries are included in the `requirements.txt` file.

---

## 🔐 API Authentication

- JWT authentication via **djangorestframework-simplejwt**  
- Token-based authentication using **django-rest-knox**  
- Cross-Origin Resource Sharing (CORS) enabled  

---

## 📦 Requirements

All project dependencies are listed in `requirements.txt` and can be installed using:
pip install -r requirements.txt

---

## 📝 Notes

This project was developed as part of the **Software Engineering Fundamentals** course and demonstrates the application of key software engineering concepts including modular architecture, dependency management, and system configuration.

The system has been tested on **Windows**.  
SQLite is used as the default database but can be replaced with other relational databases if required.

---

## 👤 Author

Developed by **rael** **teio** **kumbobo**