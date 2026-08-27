from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.auth import login_required
from app.models import Car, db
from datetime import datetime

cars_bp = Blueprint('cars', __name__, url_prefix='/cars')

@cars_bp.route('/', methods=['GET', 'POST'])
@login_required
def list_cars():
    if request.method == 'POST':
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
    return render_template('cars.html', cars=cars)


@cars_bp.route('/edit/<string:license_plate>', methods=['POST'])
@login_required
def edit_car(license_plate):
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