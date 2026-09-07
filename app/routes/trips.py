from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from sqlalchemy import or_, and_
from app import db
from app.models import Trip, TripSite, Car, Soldier, Site
from app.routes.auth import login_required
from app.routes.cars import get_car_statuses
from flask_login import login_required, current_user

trips_bp = Blueprint('trips', __name__, url_prefix='/trips')


@trips_bp.route('/', methods=['GET'])
def list_trips():
    selected_view = request.args.get('view', 'all')

    if selected_view == 'drafts':
        if not current_user.is_authenticated or current_user.used_invitation_code != "NORTH-ADMIN":
            flash("Permission denied. Only admin users can view drafts.", "danger")
            return redirect(url_for('trips.list_trips', view='all'))

        rides = Trip.query.filter(
            Trip.is_draft == True
        ).order_by(Trip.departure_date.asc(), Trip.departure_time.asc()).all()
    elif selected_view == 'history':
        rides = Trip.query.filter(
            Trip.is_draft == False,
            Trip.departure_date < date.today()
        ).order_by(Trip.departure_date.desc(), Trip.departure_time.desc()).all()
    elif selected_view == 'mine' and current_user.is_authenticated:
        assigned_soldier = Soldier.query.filter_by(id_number=current_user.id).first()
        if assigned_soldier:
            rides = Trip.query.filter(
                Trip.is_draft == False,
                or_(
                    Trip.driver == assigned_soldier.full_name,
                    Trip.supervisor == assigned_soldier.full_name,
                    Trip.commander == assigned_soldier.full_name
                )
            ).order_by(Trip.departure_date.asc(), Trip.departure_time.asc()).all()
        else:
            rides = []
    elif current_user.is_authenticated:
        # Active rides contain only published trips scheduled for today or later.
        selected_view = 'all'
        rides = Trip.query.filter(
            Trip.is_draft == False,
            Trip.departure_date >= date.today(),
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
    
    return render_template('trips.html', rides=rides, selected_view=selected_view, today=date.today())

@trips_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_ride():
    if current_user.used_invitation_code != "NORTH-ADMIN":
        flash("Permission denied. Only users with the NORTH-ADMIN code can add rides.", "danger")
        return redirect(url_for('trips.list_trips'))

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

    return render_ride_form()


@trips_bp.route('/edit/<int:trip_id>', methods=['GET', 'POST'])
@login_required
def edit_ride(trip_id):
    if current_user.used_invitation_code != "NORTH-ADMIN":
        flash("Permission denied. Only admin users can edit rides.", "danger")
        return redirect(url_for('trips.list_trips'))

    ride = Trip.query.get_or_404(trip_id)
    if not ride.is_draft and (not ride.departure_date or ride.departure_date < date.today()):
        flash("Only today's and future rides can be edited.", "warning")
        return redirect(url_for('trips.list_trips'))

    if request.method == 'POST':
        license_plate = request.form.get('license_plate')
        commander = request.form.get('commander')
        driver = request.form.get('driver')
        supervisor = request.form.get('supervisor')
        date_str = request.form.get('departure_date')
        departure_time = request.form.get('departure_time')

        if not all([license_plate, commander, driver, supervisor, date_str, departure_time]):
            flash("Vehicle, commander, driver, supervisor, date, and time are required.", "danger")
            return redirect(url_for('trips.edit_ride', trip_id=trip_id))

        ride.car_license_plate = license_plate
        ride.commander = commander
        ride.driver = driver
        ride.supervisor = supervisor
        ride.passengers = ', '.join(request.form.getlist('passengers[]')) or None
        ride.departure_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        ride.departure_time = departure_time
        ride.est_duration = float(request.form.get('est_duration')) if request.form.get('est_duration') else None
        ride.notes = request.form.get('notes')

        TripSite.query.filter_by(trip_id=ride.id).delete()
        for name, difficulty, desc in zip(
            request.form.getlist('site_name[]'),
            request.form.getlist('site_difficulty[]'),
            request.form.getlist('site_description[]')
        ):
            if name.strip():
                db.session.add(TripSite(
                    trip_id=ride.id,
                    site_name=name,
                    difficulty=difficulty,
                    work_description=desc
                ))

        db.session.commit()
        flash("Ride updated successfully!", "success")
        return redirect(url_for('trips.list_trips'))

    return render_ride_form(ride)


def render_ride_form(ride=None):
    """Load the shared create/edit ride form data."""
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
    car_statuses = get_car_statuses(cars)

    return render_template(
        'new_ride.html',
        ride=ride,
        edit_mode=ride is not None,
        selected_passengers=ride.passengers.split(', ') if ride and ride.passengers else [],
        assigned_sites=ride.assigned_sites if ride else [],
        cars=cars,
        commanders=commanders,
        drivers=drivers,
        soldiers=soldiers,
        sites=all_sites,
        car_statuses=car_statuses
    )


@trips_bp.route('/<int:trip_id>', methods=['GET'])
def view_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    return render_template('view_trip.html', trip=trip)


