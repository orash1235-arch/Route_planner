from datetime import datetime, date
from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True)  # Stores Israeli ID (ת"ז)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    used_invitation_code = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<User {self.id} - {self.full_name}>"


class Car(db.Model):
    __tablename__ = 'cars'

    license_plate = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    car_type = db.Column(db.String(50), nullable=False)
    current_km = db.Column(db.Integer, default=0, nullable=False)
    last_garage_check = db.Column(db.Date, nullable=True)
    is_on_ride = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Car {self.license_plate} - {self.car_type}>"


class Site(db.Model):
    __tablename__ = 'sites'

    loc_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gpt_coordinates = db.Column(db.String(100), nullable=True)
    sector = db.Column(db.String(100), nullable=True)
    food = db.Column(db.String(255), nullable=True)
    food_rating = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<Site {self.loc_id} - {self.name}>"


class Trip(db.Model):
    __tablename__ = 'trips'
    is_draft = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    car_license_plate = db.Column(db.String(20), db.ForeignKey('cars.license_plate'), nullable=False)
    commander = db.Column(db.String(100), nullable=False)
    driver = db.Column(db.String(100), nullable=False)
    supervisor = db.Column(db.String(100), nullable=False)
    passengers = db.Column(db.Text, nullable=True)
    
    departure_date = db.Column(db.Date, nullable=False, default=date.today)
    departure_time = db.Column(db.String(10), nullable=False)
    est_duration = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    car = db.relationship('Car', backref=db.backref('trips', lazy=True))
    assigned_sites = db.relationship('TripSite', backref='trip', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trip #{self.id} - Date: {self.departure_date} - Vehicle: {self.car_license_plate}>"


class TripSite(db.Model):
    __tablename__ = 'trip_sites'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    site_name = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(50), nullable=True)
    work_description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<TripSite {self.site_name} (Trip #{self.trip_id})>"


class Soldier(db.Model):
    __tablename__ = 'soldiers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # ID Number (ת"ז) stored locally and linked to users.id
    id_number = db.Column(db.String(9), db.ForeignKey('users.id'), unique=True, nullable=True)
    
    personal_id = db.Column(db.String(20), unique=True, nullable=False)  # מ"א
    full_name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    has_driver_license = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('soldier_profile', uselist=False))

    def __repr__(self):
        return f"<Soldier {self.personal_id} - {self.full_name}>"