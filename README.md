# Staff Training and Certification Tracker



extend pakage pip install qrcode

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