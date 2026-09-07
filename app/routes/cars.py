from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Car, Trip, db
from datetime import date, datetime

cars_bp = Blueprint('cars', __name__, url_prefix='/cars')


def get_car_statuses(cars):
    today = date.today()
    todays_ride_plates = {
        license_plate for (license_plate,) in db.session.query(Trip.car_license_plate).filter(
            Trip.is_draft == False,
            Trip.departure_date == today
        ).all()
    }

    return {
        car.license_plate: (
            'On Ride' if car.license_plate in todays_ride_plates
            else 'At Garage' if car.last_garage_check == today
            else 'Available'
        )
        for car in cars
    }

@cars_bp.route('/', methods=['GET', 'POST'])
@login_required
def list_cars():
    if request.method == 'POST':
        # Direct check for invitation code
        if current_user.used_invitation_code != "NORTH-ADMIN":
            flash("Permission denied. Only users with the NORTH-ADMIN code can add vehicles.", "danger")
            return redirect(url_for('cars.list_cars'))

        license_plate = request.form.get('license_plate')
        car_type = request.form.get('car_type')
        current_km = request.form.get('current_km', type=int)
        last_garage_check_str = request.form.get('last_garage_check')

        if not license_plate or not car_type:
            flash("License plate and car model are required.", "danger")
            return redirect(url_for('cars.list_cars'))

        if Car.query.get(license_plate):
            flash("A vehicle with this license plate already exists.", "warning")
            return redirect(url_for('cars.list_cars'))

        last_garage_check = None
        if last_garage_check_str:
            last_garage_check = datetime.strptime(last_garage_check_str, '%Y-%m-%d').date()

        new_car = Car(
            license_plate=license_plate,
            car_type=car_type,
            current_km=current_km or 0,
            last_garage_check=last_garage_check,
            is_on_ride=False
        )
        db.session.add(new_car)
        db.session.commit()

        flash("New vehicle added successfully!", "success")
        return redirect(url_for('cars.list_cars'))

    cars = Car.query.all()
    return render_template('cars.html', cars=cars, car_statuses=get_car_statuses(cars))


@cars_bp.route('/edit/<string:license_plate>', methods=['POST'])
@login_required
def edit_car(license_plate):
    # Direct check for invitation code
    if current_user.used_invitation_code != "NORTH-ADMIN":
        flash("Permission denied. Only users with the NORTH-ADMIN code can edit vehicles.", "danger")
        return redirect(url_for('cars.list_cars'))

    car = Car.query.get_or_404(license_plate)
    
    car.car_type = request.form.get('car_type', car.car_type)
    car.current_km = request.form.get('current_km', type=int) or 0
    
    last_garage_check_str = request.form.get('last_garage_check')
    if last_garage_check_str:
        car.last_garage_check = datetime.strptime(last_garage_check_str, '%Y-%m-%d').date()
    else:
        car.last_garage_check = None
        
    db.session.commit()
    flash(f"Vehicle {license_plate} updated successfully!", "success")
    return redirect(url_for('cars.list_cars'))

@cars_bp.route('/delete/<string:license_plate>', methods=['POST'])
@login_required
def delete_car(license_plate):
    # Direct check for invitation code
    if current_user.used_invitation_code != "NORTH-ADMIN":
        flash("Permission denied. Only users with the NORTH-ADMIN code can delete vehicles.", "danger")
        return redirect(url_for('cars.list_cars'))

    car = Car.query.get_or_404(license_plate)
    
    # Only today's published rides make a vehicle unavailable for deletion.
    is_on_todays_ride = Trip.query.filter(
        Trip.car_license_plate == car.license_plate,
        Trip.is_draft == False,
        Trip.departure_date == date.today()
    ).first()
    if is_on_todays_ride:
        flash(f"Cannot delete vehicle {license_plate} because it is currently on a ride.", "warning")
        return redirect(url_for('cars.list_cars'))

    db.session.delete(car)
    db.session.commit()
    
    flash(f"Vehicle {license_plate} deleted successfully!", "success")
    return redirect(url_for('cars.list_cars'))