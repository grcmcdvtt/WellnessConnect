from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import hashlib, os, uuid
from models import *
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import func

app = Flask(__name__)
# app.secret_key = 'b11_secret_key'
app.config.from_object('config.Config')
print("DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])

# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup for uploading profile pictures
# app.config['UPLOAD_FOLDER'] = os.path.join('static', 'profile_pics')
# app.config['PROOF_FOLDER'] = os.path.join('static', 'proof_pics')

# app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # limit file size to 2MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROOF_FOLDER'], exist_ok=True)

def allowed_filetype(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

# Error handler for large photos
@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    ref = request.referrer or ''
    if '/user/activity/tracker' in ref:
        flash("File too large.\nPlease upload a file smaller than 2MB.", category='activity')
        return redirect(url_for('user_activity_tracker'))
    elif '/user/account' in ref:
        flash("Profile image too large.\nPlease upload a file smaller than 2MB.", category='profile')
        return redirect(url_for('user_account'))
    elif '/companyAdmin/account' in ref:
        flash("Profile image too large.\nPlease upload a file smaller than 2MB.", category='company_profile')
        return redirect(url_for('companyAdmin_account'))
    elif '/admin/account' in ref:
        flash("Profile image too large.\nPlease upload a file smaller than 2MB.", category='admin_profile')
        return redirect(url_for('admin_account'))
    else:
        flash("File too large.", category='general')
        return redirect(request.referrer or url_for('user_homepage'))
    
# Uploading profile pictures for each user type
@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('start_app'))

    # Determine redirect page
    def redirect_to_account():
        if user.role == 'CompanyAdmin':
            return redirect(url_for('companyAdmin_account'))
        elif user.role == 'SystemAdmin':
            return redirect(url_for('admin_account'))
        else:
            return redirect(url_for('user_account'))

    # Determine flash category
    def get_flash_category():
        return {
            'CompanyAdmin': 'company_profile',
            'SystemAdmin': 'admin_profile'
        }.get(user.role, 'profile')

    category = get_flash_category()

    file = request.files.get('profile_pic')
    if not file or file.filename == '':
        flash("No file selected.", category=category)
        return redirect_to_account()

    if not allowed_filetype(file.filename):
        flash("Invalid file type.", category=category)
        return redirect_to_account()

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(save_path)

    user.profile_picture = f"profile_pics/{unique_name}"
    db.session.commit()

    return redirect_to_account()

# Removing profile pictures for each user type
@app.route('/remove_profile_pic', methods=['POST'])
def remove_profile_pic():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if user.profile_picture:
        pic_path = os.path.join(app.static_folder, user.profile_picture)
        if os.path.exists(pic_path):
            os.remove(pic_path)

        user.profile_picture = None
        db.session.commit()
    if user.role == 'CompanyAdmin':
        return redirect(url_for('companyAdmin_account'))
    elif user.role == 'SystemAdmin':
        return redirect(url_for('admin_account'))
    else:
        return redirect(url_for('user_account'))

# ------Default route------
@app.route('/')
def start_app():
    return render_template('index.html')

# ------Logging in------
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return render_template('index.html', error="Missing email or password.")

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    user = User.query.filter_by(email=email, password=hashed_password).first()

    if not user:
        session.clear()
        return render_template('index.html', error="Invalid email or password.")

    session['email'] = user.email
    session['role'] = user.role
    session['user_id'] = user.user_id

    if user.role == 'SystemAdmin':
        return redirect(url_for('admin_homepage'))

    elif user.role == 'CompanyAdmin':
        active_vouchers = Voucher.query.filter_by(
            is_active=True, company_id=user.company_id
        ).order_by(Voucher.voucher_id.desc()).all()

        inactive_vouchers = Voucher.query.filter_by(
            is_active=False, company_id=user.company_id
        ).order_by(Voucher.voucher_id.desc()).all()

        return render_template(
            "companyAdmin_homepage.html",
            active_vouchers=active_vouchers,
            inactive_vouchers=inactive_vouchers
        )

    return redirect(url_for('user_homepage'))

# ------Creating an account------
@app.route('/user/register')
def user_register():
    return render_template('user_register.html')

@app.route('/userRegisterAuth', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    phone = request.form['phone_number']

    existing_user = User.query.filter(func.lower(User.email) == email.lower()).first()
    if existing_user:
        flash('An account with that email already exists.')
        return redirect(url_for('user_register'))

    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        phone_number=phone
    )

    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('start_app'))

# ------User Homepage------
@app.route('/user/homepage')
def user_homepage():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('start_app'))

    logs = ActivityLog.query.filter_by(user_id=user.user_id).order_by(ActivityLog.logged_at.desc()).all()

    streak = user.cumulative_points // 1000
    progress_bar_points = user.cumulative_points % 1000
    percentage = (progress_bar_points / 1000) * 100

    sort_order = request.args.get("filter", "highest")

    if sort_order == "lowest":
        users = User.query.filter_by(role="Customer").order_by(User.cumulative_points.asc()).all()
    else:
        users = User.query.filter_by(role="Customer").order_by(User.cumulative_points.desc()).all()

    leaderboard = [
        {"rank": idx + 1, "username": u.username, "points": u.cumulative_points}
        for idx, u in enumerate(users)
    ]

    return render_template(
        'user_homepage.html',
        user=user,
        logs=logs,
        streak=streak,
        raw_points=progress_bar_points,
        percentage=percentage,
        spendable_points=user.spendable_points,
        leaderboard=leaderboard,
        current_filter=sort_order
    )

# Displays user's activity logs
@app.route('/my-activities')
def my_activities():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    logs = ActivityLog.query.filter_by(user_id=user.user_id).order_by(ActivityLog.logged_at.desc()).all()

    return render_template('user_homepage.html', logs=logs)

# Allows customers to clear their activity logs
@app.route('/clear_activities', methods=['POST'])
def clear_activities():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('start_app'))

    ActivityLog.query.filter_by(user_id=user.user_id).delete()
    db.session.commit()

    flash("All your activity logs have been cleared.", category="my-activities")
    return redirect(url_for('user_homepage'))

# ------User Account------
@app.route('/user/account')
def user_account():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    return render_template("user_account.html", user=user)

# ------User activity tracking page------
@app.route('/user/activity/tracker')
def user_activity_tracker():
    return render_template('user_activity_tracker.html')

# Logs activity
@app.route('/log-activity', methods=['POST'])
def log_activity():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('start_app'))

    data = request.form
    file = request.files.get('proof_image')

    proof_path = None
    proof_uploaded = False

    if file and file.filename:
        if allowed_filetype(file.filename):
            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            save_path = os.path.join(app.config['PROOF_FOLDER'], unique_name)
            file.save(save_path)
            proof_path = f"proof_pics/{unique_name}"
            proof_uploaded = True
        else:
            flash("Invalid file type. Please upload another image (png, jpg, jpeg, gif).", category='activity')
            return redirect(url_for('user_activity_tracker'))

    try:
        log = ActivityLog(
            user_id=user.user_id,
            activity_type=data['activity_type'],
            value=data['value'],
            unit=data.get('unit') or None,
            exercise_type=data.get('exercise_type') or None,
            proof=proof_uploaded,
            proof_valid=None if proof_uploaded else False,
            proof_url=proof_path
        )

        db.session.add(log)
        db.session.commit()

        if proof_uploaded:
            flash("Activity logged with proof.\nAwaiting validation.", category='activity')
        else:
            flash("No proof provided.\nRejected.", category='activity')

    except Exception as e:
        flash("Something went wrong while logging your activity. Please try again.", category='activity')

    return redirect(url_for('user_activity_tracker'))

# ------User voucher page------
@app.route('/user/vouchers')
def user_vouchers():
    if 'email' not in session:
        return redirect(url_for('start_app'))
    
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('start_app'))

    # Vouchers available for buying
    available_vouchers_query = (
    db.session.query(Voucher, Company)
    .join(Company, Voucher.company_id == Company.company_id)
    .filter(Voucher.is_active == True, Voucher.available_quantity > 0)
    .all()
)

    available_vouchers = []
    for voucher, company in available_vouchers_query:
        available_vouchers.append({
            'voucher_id': voucher.voucher_id,
            'company_name': company.name,
            'title': voucher.title,
            'description': voucher.description,
            'cost_in_points': voucher.cost_in_points,
            'available_quantity': voucher.available_quantity
        })

    # user's owned vouchers
    owned_vouchers = (
        db.session.query(UserVoucher, Voucher, Company)
        .join(Voucher, UserVoucher.voucher_id == Voucher.voucher_id)
        .join(Company, Voucher.company_id == Company.company_id)
        .filter(UserVoucher.user_id == user.user_id)
        .all()
    )

    user_vouchers = []
    for user_voucher, voucher, company in owned_vouchers:
        user_vouchers.append({
            'user_voucher_id': user_voucher.user_voucher_id,
            'company_name': company.name,
            'title': voucher.title,
            'description': voucher.description,
            'acquired_at': user_voucher.acquired_at,
            'redeemed': user_voucher.redeemed,
            'redeemed_at': user_voucher.redeemed_at
        })

    return render_template('user_vouchers.html', available_vouchers=available_vouchers, user_vouchers=user_vouchers, spendable_points=user.spendable_points)

# User buys voucher
@app.route('/buy_voucher/<int:voucher_id>', methods=['POST'])
def buy_voucher(voucher_id):
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('start_app'))

    voucher = Voucher.query.get_or_404(voucher_id)

    if user.spendable_points < voucher.cost_in_points:
        flash('You do not have enough points to buy this voucher.', 'vouchers')
        return redirect(url_for('user_vouchers'))

    user.spendable_points -= voucher.cost_in_points

    voucher.available_quantity -= 1

    user_voucher = UserVoucher(
        user_id=user.user_id,
        voucher_id=voucher_id,
        redeemed=False
    )

    db.session.add(user_voucher)
    db.session.commit()

    flash('Voucher bought successfully!', 'vouchers')
    return redirect(url_for('user_vouchers'))

# User redeems voucher
@app.route('/redeem_voucher/<int:user_voucher_id>', methods=['POST'])
def redeem_voucher(user_voucher_id):
    if 'email' not in session:
        return redirect(url_for('start_app'))
    
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('start_app'))
    
    user_voucher = UserVoucher.query.get_or_404(user_voucher_id)

    user_voucher.redeemed = True
    user_voucher.redeemed_at = db.func.current_timestamp()
    db.session.commit()

    flash('Voucher redeemed successfully!', 'vouchers')
    return redirect(url_for('user_vouchers'))

# Users can clear their redeemed vouchers
@app.route('/clear_redeemed_vouchers', methods=['POST'])
def clear_redeemed_vouchers():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('start_app'))

    # Delete only redeemed vouchers for this user
    UserVoucher.query.filter_by(user_id=user.user_id, redeemed=True).delete()
    db.session.commit()

    flash('All redeemed vouchers cleared.', 'vouchers')
    return redirect(url_for('user_vouchers'))

# ------User reminders page------
@app.route("/user/reminders", methods=["GET", "POST"])
def reminders():
    if 'email' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()

    if request.method == "POST":
        reminder_time = request.form["reminder_time"]
        description = request.form["description"]
        send_sms_flag = bool(request.form.get("send_sms"))

        # check if reminder already exists
        existing_reminder = Reminder.query.filter_by(user_id=user.user_id, reminder_time=datetime.fromisoformat(reminder_time), description=description, send_sms=send_sms_flag).first()
        if not existing_reminder:
            new_reminder = Reminder(
                user_id=user.user_id,
                reminder_time=datetime.fromisoformat(reminder_time),
                description=description,
                send_sms=send_sms_flag
            )
            db.session.add(new_reminder)
            db.session.commit()

        # need this redirect to avoid form resubmission on refresh 
        return redirect(url_for("reminders"))  # PRG pattern: redirect after POST

    # split reminders into upcoming and inbox reminders and completed reminders
    upcoming_reminders = Reminder.query.filter_by(user_id=user.user_id, is_sent=False).order_by(Reminder.reminder_time.asc()).all()
    inbox_reminders = Reminder.query.filter_by(user_id=user.user_id, is_sent=True, is_completed=False).order_by(Reminder.reminder_time.asc()).all()
    completed_reminders = Reminder.query.filter_by(user_id=user.user_id, is_completed=True).order_by(Reminder.reminder_time.asc()).all()

    return render_template("user_reminders.html", user=user, upcoming_reminders=upcoming_reminders, inbox_reminders=inbox_reminders, completed_reminders=completed_reminders)

@app.route("/reminders/status") # background update check for reminder status (moves reminders from upcoming list to inbox list once sent)
def reminders_status():
    if 'email' not in session:
        return jsonify({'error': 'Not logged in'}), 403

    user = User.query.filter_by(email=session['email']).first()

    upcoming = Reminder.query.filter_by(user_id=user.user_id, is_sent=False).order_by(Reminder.reminder_time).all()
    inbox = Reminder.query.filter_by(user_id=user.user_id, is_sent=True, is_completed=False).order_by(Reminder.reminder_time.asc()).all()
    completed = Reminder.query.filter_by(user_id=user.user_id, is_completed=True).order_by(Reminder.reminder_time.asc()).all()

    return jsonify({
        "upcoming": [
            {
                "id": r.reminder_id,
                "time": r.reminder_time.strftime('%m/%d/%y %I:%M %p'),
                "description": r.description
            } for r in upcoming
        ],
        "inbox": [
            {
                "id": r.reminder_id,
                "time": r.reminder_time.strftime('%m/%d/%y %I:%M %p'),
                "description": r.description
            } for r in inbox
        ],
        "completed": [
            {
                "id": r.reminder_id,
                "time": r.reminder_time.strftime('%m/%d/%y %I:%M %p'),
                "description": r.description
            } for r in completed
        ]
    })

@app.route("/reminders/delete/<int:reminder_id>", methods=["POST"])
def delete_reminder(reminder_id):
    if 'email' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 403

    user = User.query.filter_by(email=session['email']).first()
    reminder = Reminder.query.filter_by(reminder_id=reminder_id, user_id=user.user_id).first()

    if reminder:
        db.session.delete(reminder)
        db.session.commit()
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Reminder not found"}), 404

@app.route("/reminders/delete_completed", methods=["POST"])
def delete_all_completed_reminders():
    if 'email' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 403

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Delete all reminders marked as completed for this user
    Reminder.query.filter_by(user_id=user.user_id, is_completed=True).delete()
    db.session.commit()

    return jsonify({"success": True})

@app.route("/reminders/edit/<int:reminder_id>", methods=["POST"])
def edit_reminder(reminder_id):
    if 'email' not in session:
        return jsonify(success=False, error="Not logged in"), 403

    user = User.query.filter_by(email=session['email']).first()
    reminder = Reminder.query.filter_by(reminder_id=reminder_id, user_id=user.user_id).first()

    if not reminder:
        return jsonify(success=False, error="Reminder not found"), 404

    data = request.get_json()

    new_time = datetime.fromisoformat(data["new_time"])
    new_description = data["new_description"]
    now = datetime.now()
    is_future = new_time > now

    reminder.reminder_time = new_time
    reminder.description = new_description
    reminder.is_sent = not is_future # set is_sent to false if new time is in the future (so that if the reminder was in the inbox it moves to upcoming)

    db.session.commit()
    return jsonify(success=True)

@app.route('/reminders/complete/<int:reminder_id>', methods=['POST'])
def complete_reminder(reminder_id):
    try:
        # Get the reminder from the database by ID
        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            return jsonify({'success': False, 'message': 'Reminder not found'}), 404

        # Get the 'is_completed' status from the request body
        data = request.get_json()
        is_completed = data.get('is_completed')

        # Update the reminder's completion status
        reminder.is_completed = is_completed
        db.session.commit()

        return jsonify({'success': True, 'message': 'Reminder updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ------Admin Homepage------
@app.route('/admin/homepage')
def admin_homepage():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user or user.role != 'SystemAdmin':
        return redirect(url_for('start_app'))

    all_logs = ActivityLog.query.order_by(ActivityLog.logged_at.desc()).all()

    pending_logs = [log for log in all_logs if log.proof and log.proof_valid is None]
    approved_logs = [log for log in all_logs if log.proof and log.proof_valid is True]
    rejected_logs = [log for log in all_logs if not log.proof or log.proof_valid is False]

    return render_template(
        'admin_homepage.html',
        pending_logs=pending_logs,
        approved_logs=approved_logs,
        rejected_logs=rejected_logs
    )

# ------Admin Account Page------
@app.route('/admin/account')
def admin_account():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    return render_template("admin_account.html", user=user)

def calculate_points(activity_type, value, streak, unit=None):
    try:
        value = float(value)
    except ValueError:
        return 0

    if activity_type == "exercise" and unit and unit.lower() == "hours":
        value *= 60

    base_points = 0
    if activity_type == "water":
        base_points = value * 1
    elif activity_type == "steps":
        base_points = value * 0.1
    elif activity_type == "exercise":
        base_points = value * 3
    elif activity_type == "sleep":
        base_points = value * 20
    else:
        return 0

    multiplier = 1 + min(streak * 0.05, 0.5)
    return int(base_points * multiplier)

# Admin approve proof
@app.route('/approve_proof/<int:log_id>', methods=['POST'])
def approve_proof(log_id):
    log = ActivityLog.query.get_or_404(log_id)
    if log.proof_valid is not None:
        return redirect(url_for('admin_homepage'))

    log.proof_valid = True
    user = User.query.get(log.user_id)

    points = calculate_points(log.activity_type, log.value, user.streak_count, log.unit)

    user.cumulative_points += points                    # total earned (for streaks)
    user.spendable_points += points                     # points that can be spent
    user.streak_count = user.cumulative_points // 1000  # based on cumulative points

    db.session.commit()
    return redirect(url_for('admin_homepage'))

# Admin reject proof
@app.route('/reject_proof/<int:log_id>', methods=['POST'])
def reject_proof(log_id):
    log = ActivityLog.query.get_or_404(log_id)
    log.proof_valid = False
    db.session.commit()
    return redirect(url_for('admin_homepage'))

# ------CompanyAdmin Homepage------
@app.route('/companyAdmin/homepage')
def manage_vouchers():
    if 'email' not in session or session.get('role') != 'CompanyAdmin':
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()

    if not user or not user.company_id:
        flash("You must be logged in as a valid CompanyAdmin with an associated company.", category='company_voucher')
        return redirect(url_for('start_app'))

    expand = request.args.get('expand') == 'true'

    active_vouchers = Voucher.query.filter_by(
        is_active=True, company_id=user.company_id
    ).order_by(Voucher.voucher_id.desc()).all()

    inactive_vouchers = Voucher.query.filter_by(
        is_active=False, company_id=user.company_id
    ).order_by(Voucher.voucher_id.desc()).all()

    return render_template(
        "companyAdmin_homepage.html",
        active_vouchers=active_vouchers,
        inactive_vouchers=inactive_vouchers,
        expand_tables=expand
    )

# ------CompanyAdmin Account------
@app.route('/companyAdmin/account')
def companyAdmin_account():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    return render_template("companyAdmin_account.html", user=user)

# ------CompanyAdmin Vouchers Page------
@app.route('/companyAdmin/vouchers')
def companyAdmin_vouchers():
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    return render_template("companyAdmin_vouchers.html", user=user)

# CompanyAdmin adds vouchers
@app.route('/add-voucher', methods=['POST'])
def add_voucher():
    if 'email' not in session or session.get('role') != 'CompanyAdmin':
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user or not user.company_id:
        flash('You must be associated with a company to add vouchers.', category='company_voucher')
        return redirect(url_for('companyAdmin_vouchers'))

    try:
        title = request.form.get('title')
        description = request.form.get('description')
        cost_in_points = request.form.get('cost_in_points', type=int)
        available_quantity = request.form.get('available_quantity', type=int)
        is_active = request.form.get('is_active') == 'on'

        new_voucher = Voucher(
            title=title,
            description=description,
            cost_in_points=cost_in_points,
            available_quantity=available_quantity,
            is_active=is_active,
            company_id=user.company_id
        )

        db.session.add(new_voucher)
        db.session.commit()

        flash("Voucher added successfully!", category="company_voucher")
        return redirect(url_for('companyAdmin_vouchers'))

    except Exception as e:
        print("Error adding voucher:", e)
        db.session.rollback()
        flash('Error adding voucher. Please try again.', category='company_voucher')
        return redirect(url_for('companyAdmin_vouchers'))

# CompanyAdmin activating vouchers
@app.route('/activate-voucher/<int:voucher_id>', methods=['POST'])
def activate_voucher(voucher_id):
    user = User.query.filter_by(email=session['email']).first()
    voucher = Voucher.query.filter_by(voucher_id=voucher_id, company_id=user.company_id).first_or_404()
    voucher.is_active = True
    db.session.commit()
    return redirect(url_for('manage_vouchers'))

# CompanyAdmin deactivating vouchers
@app.route('/deactivate-voucher/<int:voucher_id>', methods=['POST'])
def deactivate_voucher(voucher_id):
    user = User.query.filter_by(email=session['email']).first()
    voucher = Voucher.query.filter_by(voucher_id=voucher_id, company_id=user.company_id).first_or_404()
    voucher.is_active = False
    db.session.commit()
    return redirect(url_for('manage_vouchers'))

# CompanyAdmin deleting vouchers
@app.route('/delete-voucher/<int:voucher_id>', methods=['POST'])
def delete_voucher(voucher_id):
    if 'email' not in session:
        return redirect(url_for('start_app'))

    user = User.query.filter_by(email=session['email']).first()
    if not user or user.role != 'CompanyAdmin':
        return redirect(url_for('start_app'))

    voucher = Voucher.query.filter_by(voucher_id=voucher_id, company_id=user.company_id).first_or_404()

    UserVoucher.query.filter_by(voucher_id=voucher_id).delete()

    db.session.delete(voucher)
    db.session.commit()

    flash('Voucher has been deleted.', 'company_voucher_deletion')
    return redirect(url_for('manage_vouchers'))

# ------LOGOUT------
@app.route('/logout')
def logout():
    session.clear()
    return render_template('index.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
