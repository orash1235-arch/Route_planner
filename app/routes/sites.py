from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.auth import login_required
from app.models import Site, db

sites_bp = Blueprint('sites', __name__, url_prefix='/sites')

SECTORS = ["עמקים וים", "קו כחול", "רמת הגולן"]

@sites_bp.route('/', methods=['GET', 'POST'])
@login_required
def list_sites():
    if request.method == 'POST':
        loc_id = request.form.get('loc_id')
        name = request.form.get('name')
        gpt_coordinates = request.form.get('gpt_coordinates')
        sector = request.form.get('sector')
        food = request.form.get('food') or None
        food_rating = request.form.get('food_rating')
        food_rating = int(food_rating) if food_rating and food_rating.isdigit() else None

        if not loc_id or not name:
            flash("Location ID and Site Name are required.", "danger")
            return redirect(url_for('sites.list_sites'))

        if Site.query.get(loc_id):
            flash("A site with this Location ID already exists.", "warning")
            return redirect(url_for('sites.list_sites'))

        new_site = Site(
            loc_id=loc_id,
            name=name,
            gpt_coordinates=gpt_coordinates,
            sector=sector,
            food=food,
            food_rating=food_rating
        )
        db.session.add(new_site)
        db.session.commit()

        flash("New site added successfully!", "success")
        return redirect(url_for('sites.list_sites'))

    sites = Site.query.all()
    return render_template('sites.html', sites=sites, sectors=SECTORS)


@sites_bp.route('/edit/<string:loc_id>', methods=['POST'])
@login_required
def edit_site(loc_id):
    site = Site.query.get_or_404(loc_id)
    
    site.name = request.form.get('name', site.name)
    site.gpt_coordinates = request.form.get('gpt_coordinates', site.gpt_coordinates)
    site.sector = request.form.get('sector', site.sector)
    
    food = request.form.get('food')
    site.food = food if food else None
    
    food_rating = request.form.get('food_rating')
    site.food_rating = int(food_rating) if food_rating and food_rating.isdigit() else None
        
    db.session.commit()
    flash(f"Site {loc_id} updated successfully!", "success")
    return redirect(url_for('sites.list_sites'))


@sites_bp.route('/delete/<string:loc_id>', methods=['POST'])
@login_required
def delete_site(loc_id):
    site = Site.query.get_or_404(loc_id)
    
    db.session.delete(site)
    db.session.commit()
    
    flash('Site deleted successfully!', 'success')
    return redirect(url_for('sites.list_sites'))

