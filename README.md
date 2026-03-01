# AI-Powered Data Analysis Platform

<img width="1344" height="768" alt="A screenshot of the application dashboard showing a successful analysis with an accuracy score and a training history chart." src="https://github.com/user-attachments/assets/e94bdad1-fc74-4a52-8745-a05aacb466e6" />

A secure, web-based platform that allows users to upload their own datasets and instantly train a logistic regression model. The application provides a detailed performance analysis, including model accuracy and a visual training history, all wrapped in a secure authentication system built with Flask and MariaDB.

---

## 🚀 Core Features

### Machine Learning & Analysis
- **Dynamic CSV Upload:** Analyze any CSV file where the last column is the target variable.
- **Automated Model Training:** Automatically trains a TensorFlow-based logistic regression model on user-provided data.
- **Performance Visualization:** Displays the model's test accuracy and a Chart.js graph of training vs. validation accuracy over epochs.
- **Data Validation:** Intelligently checks if the target variable is suitable for binary classification and provides clear user feedback.

### Security & Authentication
- **Secure User Accounts:** Robust registration and login system powered by Flask-Login and Bcrypt for salted password hashing.
- **Session Management:** Secure server-side sessions to protect user data.
- **Cache Protection:** Implements `Cache-Control` headers to prevent logged-out users from accessing sensitive pages via the browser's back button.
- **Password Recovery:** Secure, timed reset tokens (`itsdangerous`) delivered via SMTP or an HTTPS API for production environments.

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Gunicorn
- **Machine Learning:** TensorFlow, Pandas, Scikit-learn
- **Database:** MariaDB / MySQL (with Flask-SQLAlchemy)
- **Frontend:** HTML5, CSS3, JavaScript (with Chart.js for visualizations)
- **Deployment:** Railway

---

## 💻 How to Use

1.  **Register & Login:** Create a secure account or log in.
2.  **Navigate to Dashboard:** Access the main analysis dashboard.
3.  **Upload a Dataset:** Upload a CSV file. **Important:** The dataset must have a binary target variable (a column with exactly two unique values, like `0/1` or `Yes/No`) as the **last column**.
4.  **Analyze:** Click the "Analyze" button to begin the model training.
5.  **View Results:** See the model's test accuracy and the training history chart.

---

## 🚢 Deployment Notes

This application is configured for production deployment on platforms like Railway.

### Environment Variables
The application uses a `.env` file for configuration. Key variables include database credentials and email settings.

### Email Backend (Important for Railway)
Railway's free plan blocks outbound SMTP traffic. To ensure password reset emails work, you must use an API-based email service like Resend.

Set the following environment variables in your deployment environment:
```env
EMAIL_BACKEND=resend
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL=no-reply@your-verified-domain.com
```

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository, make your changes, and submit a pull request for review.