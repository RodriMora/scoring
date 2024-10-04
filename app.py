from flask import Flask, render_template, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import json
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///athletes.db'
db = SQLAlchemy(app)

class Athlete(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0)

class Preference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_count = db.Column(db.Integer, default=5)

@app.route('/')
def index():
    pref = Preference.query.first()
    if not pref:
        pref = Preference(display_count=5)
        db.session.add(pref)
        db.session.commit()
    return render_template('index.html', display_count=pref.display_count)

@app.route('/get_athletes')
def get_athletes():
    athletes = Athlete.query.order_by(Athlete.score.desc()).all()
    return jsonify([{"id": a.id, "name": a.name, "score": a.score} for a in athletes])

@app.route('/add_athlete', methods=['POST'])
def add_athlete():
    name = request.form['name']
    new_athlete = Athlete(name=name)
    db.session.add(new_athlete)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/update_score', methods=['POST'])
def update_score():
    athlete_id = request.form['athlete_id']
    score_change = int(request.form['score_change'])
    athlete = Athlete.query.get(athlete_id)
    athlete.score += score_change
    db.session.commit()
    return jsonify({'success': True})

@app.route('/remove_athlete', methods=['POST'])
def remove_athlete():
    athlete_id = request.form['athlete_id']
    athlete = Athlete.query.get(athlete_id)
    if athlete:
        db.session.delete(athlete)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/wipe_all', methods=['POST'])
def wipe_all():
    Athlete.query.delete()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/update_display_count', methods=['POST'])
def update_display_count():
    count = int(request.form['count'])
    pref = Preference.query.first()
    if not pref:
        pref = Preference(display_count=count)
        db.session.add(pref)
    else:
        pref.display_count = count
    db.session.commit()
    return jsonify({'success': True})

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            with app.app_context():
                athletes = Athlete.query.order_by(Athlete.score.desc()).all()
                pref = Preference.query.first()
                data = {
                    "athletes": [{"id": a.id, "name": a.name, "score": a.score} for a in athletes],
                    "display_count": pref.display_count if pref else 5
                }
                yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.5)  # Send update every 0.5 seconds
    return Response(event_stream(), content_type='text/event-stream')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
