from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from sqlalchemy import or_, and_
from app import db
from app.models import Trip, TripSite, Car, Soldier, Site
from app.routes.auth import login_required
from flask_login import login_required, current_user

trips_bp = Blueprint('trips', __name__, url_prefix='/trips')


@trips_bp.route('/', methods=['GET'])
def list_trips():
    selected_view = request.args.get('view', 'all')

    if selected_view == 'history':
        rides = Trip.query.filter(
            Trip.is_draft == False,
            Trip.departure_date < date.today()
        ).order_by(Trip.departure_date.desc(), Trip.departure_time.desc()).all()
    elif selected_view == 'mine' and current_user.is_authenticated:
        assigned_soldier = Soldier.query.filter_by(id_number=current_user.id).first()
        if assigned_soldier:
            rides = Trip.query.filter(
                or_(
                    Trip.driver == assigned_soldier.full_name,
                    Trip.supervisor == assigned_soldier.full_name,
                    Trip.commander == assigned_soldier.full_name
                )
            ).order_by(Trip.departure_date.asc(), Trip.departure_time.asc()).all()
        else:
            rides = []
    elif current_user.is_authenticated:
        # Logged-in users see all published trips PLUS their own drafts
        selected_view = 'all'
        rides = Trip.query.filter(
            Trip.departure_date >= date.today(),
            or_(
                Trip.is_draft == False,
                and_(Trip.is_draft == True, Trip.user_id == current_user.id)
            )
        ).order_by(Trip.departure_date.asc(), Trip.departure_time.asc()).all()
    else:
        # Unauthenticated users only see published trips
        selected_view = 'all'
        rides = Trip.query.filter(
            Trip.is_draft == False,
            Trip.departure_date >= date.today()
        ).order_by(
            Trip.departure_date.asc(), Trip.departure_time.asc()
        ).all()
    
    return render_template('trips.html', rides=rides, selected_view=selected_view)

@trips_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_ride():
    if request.method == 'POST':
        is_draft = request.form.get('action') == 'draft'
        license_plate = request.form.get('license_plate')
        commander = request.form.get('commander')
        driver = request.form.get('driver')
        supervisor = request.form.get('supervisor')
        date_str = request.form.get('departure_date')
        departure_time = request.form.get('departure_time')

        if not all([license_plate, commander, driver, supervisor, date_str, departure_time]):
            flash("Vehicle, commander, driver, supervisor, date, and time are required.", "danger")
            return redirect(url_for('trips.new_ride'))
        
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        passengers = ', '.join(request.form.getlist('passengers[]'))

        new_trip = Trip(
            car_license_plate=license_plate if license_plate else None,
            commander=commander,
            driver=driver,
            supervisor=supervisor,
            passengers=passengers or None,
            departure_date=parsed_date,
            departure_time=departure_time,
            est_duration=float(request.form.get('est_duration')) if request.form.get('est_duration') else None,
            notes=request.form.get('notes'),
            is_draft=is_draft,
            user_id=current_user.id
        )
        
        if not is_draft and license_plate:
            car = Car.query.get(license_plate)
            if car:
                car.is_on_ride = True

        db.session.add(new_trip)
        db.session.flush()

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

    # GET Request: Fetch options for form dropdowns
    commanders = Soldier.query.filter(Soldier.job_title.contains("מפקד")).all()
    drivers = Soldier.query.filter(
        or_(
            Soldier.has_driver_license == True,
            Soldier.job_title.contains("נהג")
        )
    ).all()
    cars = Car.query.all()
    all_sites = Site.query.order_by(Site.name.asc()).all()
    soldiers = Soldier.query.order_by(Soldier.full_name.asc()).all()

    return render_template(
        'new_ride.html',
        cars=cars,
        commanders=commanders,
        drivers=drivers,
        soldiers=soldiers,
        sites=all_sites
    )


@trips_bp.route('/<int:trip_id>', methods=['GET'])
def view_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    return render_template('view_trip.html', trip=trip)


