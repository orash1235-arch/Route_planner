from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Soldier, User
from app.routes.auth import login_required

soldiers_bp = Blueprint('soldiers', __name__, url_prefix='/soldiers')

RANKS = ["טוראי", "רב״ט", "סמל", "סמ״ר", "רס״ל", "רס״ם", "סג״ם", "סגן", "סרן", "רס״ן"]
JOB_TITLES = ["טכנאי", "מפקד", "נהג", "אדום", "לוגיסטיקה", "בקר"]

@soldiers_bp.route('/', methods=['GET', 'POST'])
@login_required
def list_soldiers():
    if request.method == 'POST':
        id_number = request.form.get('id_number')
        personal_id = request.form.get('personal_id')
        full_name = request.form.get('full_name')
        rank = request.form.get('rank')
        job_title = request.form.get('job_title')
        has_driver_license = True if request.form.get('has_driver_license') else False

        if not id_number or not personal_id or not full_name:
            flash("ID Number, Personal ID, and Name are required.", "danger")
            return redirect(url_for('soldiers.list_soldiers'))

        if Soldier.query.filter_by(id_number=id_number).first():
            flash("A soldier with this ID Number already exists.", "warning")
            return redirect(url_for('soldiers.list_soldiers'))

        if Soldier.query.filter_by(personal_id=personal_id).first():
            flash("A soldier with this Personal ID already exists.", "warning")
            return redirect(url_for('soldiers.list_soldiers'))

        new_soldier = Soldier(
            id_number=id_number,
            personal_id=personal_id,
            full_name=full_name,
            rank=rank,
            job_title=job_title,
            has_driver_license=has_driver_license
        )
        db.session.add(new_soldier)
        db.session.commit()

        flash("Soldier added successfully!", "success")
        return redirect(url_for('soldiers.list_soldiers'))

    soldiers = Soldier.query.all()
    users = User.query.all()
    return render_template(
        'soldiers.html',
        soldiers=soldiers,
        ranks=RANKS,
        job_titles=JOB_TITLES,
        users=users
    )


@soldiers_bp.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_soldier(id):
    soldier = Soldier.query.get_or_404(id)

    soldier.id_number = request.form.get('id_number', soldier.id_number)
    soldier.personal_id = request.form.get('personal_id', soldier.personal_id)
    soldier.full_name = request.form.get('full_name', soldier.full_name)
    soldier.rank = request.form.get('rank', soldier.rank)
    soldier.job_title = request.form.get('job_title', soldier.job_title)
    soldier.has_driver_license = True if request.form.get('has_driver_license') else False

    db.session.commit()
    flash(f"Soldier {soldier.full_name} updated successfully!", "success")
    return redirect(url_for('soldiers.list_soldiers'))


@soldiers_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_soldier(id):
    soldier = Soldier.query.get_or_404(id)

    db.session.delete(soldier)
    db.session.commit()

    flash("Soldier removed successfully!", "success")
    return redirect(url_for('soldiers.list_soldiers'))