
from flask_apscheduler import APScheduler
from flask_mail import Mail, Message
from datetime import datetime
from models import db, Reminder, User
from app import app
from config import Config
from sqlalchemy.orm import Session

# Initialize Mail and Scheduler
app.config.from_object(Config)
mail = Mail(app)
scheduler = APScheduler()


# helper function to generate email-to-SMS address (if there was a carrier column in users table)
"""
def get_sms_email(phone_number, carrier_name):
    carrier_domain = ""
    # add logic to map carrier to carrier_domain
    return f"{phone_number}@{carrier_domain}"
"""

# send reminders using email-to-sms (not the ideal way but it doesn't cost $50)
def send_sms_via_email(to_email, body):
    msg = Message(
        subject="Reminder",
        sender=app.config['MAIL_USERNAME'],
        recipients=[to_email],
        body=body
    )
    mail.send(msg)

# task that checks every 30 seconds to see if there are any reminders to send to users
@scheduler.task('interval', id='check_reminders', seconds=30)
def check_and_send_reminders():
    with app.app_context():
        session = db.session
        now = datetime.now()
        reminders = Reminder.query.filter(
            Reminder.reminder_time <= now,
            Reminder.is_sent == False
        ).all()

        for reminder in reminders: 
            user = session.get(User, reminder.user_id)

            # allows the user to choose to recieve in-app reminders or sms reminders

            # if sending notification via sms 
            if reminder.send_sms and user.phone_number:
                # sms_email = get_sms_email(user.phone_number, user.carrier) # use if there was a carrier column in user
                # sms_email = user.phone_number + '@txt.att.net'
                # sms_email = user.phone_number + '@tmomail.net'
                # sms_email = user.phone_number + 'messaging.sprintpcs.com'
                sms_email = user.phone_number + '@vtext.com' # for demo
                try:
                    send_sms_via_email(sms_email, reminder.description)
                    print(f"SMS sent to {sms_email}: {reminder.description}")
                except Exception as e:
                    print(f"Failed to send SMS to {sms_email}: {e}")
            # if just wants an in-app notification
            else:
                print(f"In-app reminder only for {user.email}: {reminder.description}")

            # mark the reminder as sent
            reminder.is_sent = True

        db.session.commit()

# start the scheduler
def start_scheduler():
    scheduler.init_app(app)
    scheduler.start()

# run scheduler.py in a separate terminal while app.py is running (for development & demo)
if __name__ == "__main__":
    start_scheduler()
    print("Scheduler is running... Press Ctrl+C to stop.")
    try:
        while True:
            pass  # Keep the script running
    except KeyboardInterrupt:
        print("Scheduler stopped.")
    # app.run(debug=True, use_reloader=False) # uncomment if not running app.py and scheduler.py separately
