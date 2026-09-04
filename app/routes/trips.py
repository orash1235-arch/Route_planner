from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from sqlalchemy import or_, and_
from app import db
from app.models import Trip, TripSite, Car
from app.routes.auth import login_required
from flask_login import login_required, current_user

trips_bp = Blueprint('trips', __name__, url_prefix='/trips')


@trips_bp.route('/', methods=['GET'])
def list_trips():
    if current_user.is_authenticated:
        # Logged-in users see all published trips PLUS their own drafts
        rides = Trip.query.filter(
            or_(
                Trip.is_draft == False,
                and_(Trip.is_draft == True, Trip.user_id == current_user.id)
            )
        ).order_by(Trip.departure_date.asc(), Trip.departure_time.asc()).all()
    else:
        # Unauthenticated users only see published trips
        rides = Trip.query.filter(Trip.is_draft == False).order_by(
            Trip.departure_date.asc(), Trip.departure_time.asc()
        ).all()
    
    return render_template('trips.html', rides=rides)

@trips_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_ride():
    if request.method == 'POST':
        is_draft = request.form.get('action') == 'draft'
        license_plate = request.form.get('license_plate')
        
        # Parse date string (YYYY-MM-DD) into a date object
        date_str = request.form.get('departure_date')
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

        # 1. Instantiate the Trip record
        new_trip = Trip(
            car_license_plate=license_plate if license_plate else None,
            commander=request.form.get('commander'),
            driver=request.form.get('driver'),
            supervisor=request.form.get('supervisor'),
            passengers=request.form.get('passengers'),
            departure_date=parsed_date,
            departure_time=request.form.get('departure_time'),
            est_duration=float(request.form.get('est_duration')) if request.form.get('est_duration') else None,
            notes=request.form.get('notes'),
            is_draft=is_draft,
            user_id=current_user.id  # Assign ownership to active user
        )
        
        # 2. Update Car status ONLY if it's a published ride (not a draft)
        if not is_draft and license_plate:
            car = Car.query.get(license_plate)
            if car:
                car.is_on_ride = True

        db.session.add(new_trip)
        db.session.flush()  # Generates new_trip.id for the sites below

        # 3. Add dynamic sites
        site_names = request.form.getlist('site_name[]')
        site_difficulties = request.form.getlist('site_difficulty[]')
        site_descriptions = request.form.getlist('site_description[]')

        for name, difficulty, desc in zip(site_names, site_difficulties, site_descriptions):
            if name.strip():
                trip_site = TripSite(
                    trip_id=new_trip.id,
                    site_name=name,
                    difficulty=difficulty,
                    work_description=desc
                )
                db.session.add(trip_site)

        db.session.commit()
        
        if is_draft:
            flash("Expedition saved as a private draft!", "info")
        else:
            flash("Expedition scheduled successfully!", "success")
            
        return redirect(url_for('trips.list_trips'))

    cars = Car.query.all()
    return render_template('new_ride.html', cars=cars)

@trips_bp.route('/<int:trip_id>', methods=['GET'])
def view_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    return render_template('view_trip.html', trip=trip)
