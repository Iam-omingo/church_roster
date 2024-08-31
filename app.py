from flask import Flask, render_template, request, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Sample Member Data (initially empty, filled by admin)
members = []

# Admin and Member credentials
credentials = {
    "admin": "admin",
    "user": "user"
}

# Function to generate monthly rosters
def generate_monthly_rosters():
    if not members:
        return {'January': [], 'February': [], 'March': [], 'April': []}

    rosters = {'January': [], 'February': [], 'March': [], 'April': []}
    weeks_per_month = 4

    deacons = [m for m in members if m['role'] == 'Deacon']
    deaconesses = [m for m in members if m['role'] == 'Deaconess']
    
    def get_unique_assignment(assignments, member, limit=2):
        """ Ensure that a member is not repeated more than `limit` times. """
        count = sum(1 for a in assignments if member in a)
        return count < limit

    def assign_duties(deacons, deaconesses, week_assignments, last_pulpit_gents, last_pulpit_ladies):
        # Assign pulpit duty
        available_deacons = [d for d in deacons if get_unique_assignment([week['pulpit_gents'] for week in rosters[month]], d['name'])]
        available_deaconesses = [d for d in deaconesses if get_unique_assignment([week['pulpit_ladies'] for week in rosters[month]], d['name'])]

        if len(available_deacons) >= 2:
            pulpit_gents = [d['name'] for d in available_deacons if d['name'] not in last_pulpit_gents]
            week_assignments['pulpit_gents'] = random.sample(pulpit_gents, 2)
        else:
            week_assignments['pulpit_gents'] = []
        
        if len(available_deaconesses) >= 1:
            pulpit_ladies = [d['name'] for d in available_deaconesses if d['name'] not in last_pulpit_ladies]
            week_assignments['pulpit_ladies'] = random.sample(pulpit_ladies, 1)
        else:
            week_assignments['pulpit_ladies'] = []
        
        last_pulpit_gents = week_assignments['pulpit_gents']
        last_pulpit_ladies = week_assignments['pulpit_ladies']
        
        # Assign envelope collection duty
        if deacons:
            week_assignments['envelope_deacon'] = random.choice([d['name'] for d in deacons if get_unique_assignment([week['envelope_deacon'] for week in rosters[month]], d['name'])])
        else:
            week_assignments['envelope_deacon'] = 'No deacon available'
        
        if deaconesses:
            week_assignments['envelope_deaconess'] = random.choice([d['name'] for d in deaconesses if get_unique_assignment([week['envelope_deaconess'] for week in rosters[month]], d['name'])])
        else:
            week_assignments['envelope_deaconess'] = 'No deaconess available'

        # Assign welcoming duty
        if deacons:
            week_assignments['welcoming_deacon'] = random.choice([d['name'] for d in deacons if get_unique_assignment([week['welcoming_deacon'] for week in rosters[month]], d['name'])])
        else:
            week_assignments['welcoming_deacon'] = 'No deacon available'
        
        if deaconesses:
            week_assignments['welcoming_deaconess'] = random.choice([d['name'] for d in deaconesses if get_unique_assignment([week['welcoming_deaconess'] for week in rosters[month]], d['name'])])
        else:
            week_assignments['welcoming_deaconess'] = 'No deaconess available'
        
        return last_pulpit_gents, last_pulpit_ladies

    for month, start_week in zip(['January', 'February', 'March', 'April'], range(0, 16, weeks_per_month)):
        last_pulpit_gents = []
        last_pulpit_ladies = []

        for week in range(start_week, start_week + weeks_per_month):
            week_assignments = {
                'pulpit_gents': [],
                'pulpit_ladies': [],
                'envelope_deacon': 'No deacon available',
                'envelope_deaconess': 'No deaconess available',
                'welcoming_deacon': 'No deacon available',
                'welcoming_deaconess': 'No deaconess available'
            }
            
            last_pulpit_gents, last_pulpit_ladies = assign_duties(deacons, deaconesses, week_assignments, last_pulpit_gents, last_pulpit_ladies)
            
            rosters[month].append({
                'week': week + 1,
                'pulpit_gents': ', '.join(week_assignments['pulpit_gents']),
                'pulpit_ladies': ', '.join(week_assignments['pulpit_ladies']),
                'envelope_deacon': week_assignments['envelope_deacon'],
                'envelope_deaconess': week_assignments['envelope_deaconess'],
                'welcoming_deacon': week_assignments['welcoming_deacon'],
                'welcoming_deaconess': week_assignments['welcoming_deaconess']
            })

    return rosters

@app.route('/')
def home():
    if 'logged_in' in session:
        if session['user_role'] == 'admin':
            return redirect(url_for('admin_page'))
        else:
            return redirect(url_for('user_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in credentials and credentials[username] == password:
            session['logged_in'] = True
            session['user_role'] = username
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_role', None)
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if 'logged_in' in session and session['user_role'] == 'admin':
        if request.method == 'POST':
            global members
            action = request.form.get('action')
            if action == 'Update Roster':
                members = []
                new_members = request.form.get('members').strip().split('\n')
                for member in new_members:
                    parts = member.split(',')
                    if len(parts) == 3:
                        name, gender, role = [part.strip() for part in parts]
                        if gender in ['Male', 'Female'] and role in ['Deacon', 'Deaconess']:
                            members.append({'name': name, 'gender': gender, 'role': role})
                        else:
                            print(f"Skipping invalid role or gender: {member}")
                    else:
                        print(f"Skipping invalid input: {member}")
                rosters = generate_monthly_rosters()
                return render_template('admin.html', rosters=rosters, show_form=False)
            elif action == 'Edit Week':
                # Handle week updates if needed
                pass

        # GET request, show existing data if available
        rosters = generate_monthly_rosters() if members else None
        return render_template('admin.html', rosters=rosters, show_form=not members)
    
    return redirect(url_for('login'))

@app.route('/user')
def user_page():
    if 'logged_in' in session and session['user_role'] == 'user':
        rosters = generate_monthly_rosters()
        return render_template('user.html', rosters=rosters)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
