# ==== AURA_V2/app/admin/routes.py ====

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
import json
from . import admin
from .forms import UserForm, ClientForm, DataSourceForm
from app import db
from app.models import User, Client, DataSource
from app.utils import admin_required

# --- Dashboard do Admin ---
@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    client_count = Client.query.count()
    user_count = User.query.count()
    return render_template('admin/dashboard.html', title='Admin Dashboard',
                           client_count=client_count, user_count=user_count)

# --- Gestão de Clientes ---
@admin.route('/clients')
@login_required
@admin_required
def list_clients():
    clients = Client.query.order_by(Client.name).all()
    return render_template('admin/clients.html', title='Gerir Clientes', clients=clients)

@admin.route('/client/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(name=form.name.data)
        db.session.add(client)
        db.session.commit()
        flash('Cliente adicionado com sucesso!', 'success')
        return redirect(url_for('admin.list_clients'))
    return render_template('admin/client_form.html', title='Adicionar Cliente', form=form)

@admin.route('/client/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(original_name=client.name, obj=client)
    if form.validate_on_submit():
        client.name = form.name.data
        db.session.commit()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('admin.list_clients'))
    return render_template('admin/client_form.html', title='Editar Cliente', form=form)

@admin.route('/client/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Cliente apagado com sucesso!', 'success')
    return redirect(url_for('admin.list_clients'))

# --- Gestão de Fontes de Dados ---
@admin.route('/client/<int:client_id>/datasources')
@login_required
@admin_required
def list_datasources(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('admin/datasources.html', client=client)

@admin.route('/client/<int:client_id>/datasource/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_datasource(client_id):
    client = Client.query.get_or_404(client_id)
    form = DataSourceForm()
    if form.validate_on_submit():
        try:
            json.loads(form.credentials_json.data)
            datasource = DataSource(
                client_id=client.id,
                platform=form.platform.data,
                credentials_json=form.credentials_json.data
            )
            db.session.add(datasource)
            db.session.commit()
            flash(f'Fonte de dados {datasource.platform} adicionada com sucesso!', 'success')
            return redirect(url_for('admin.list_datasources', client_id=client.id))
        except json.JSONDecodeError:
            flash('Erro: O texto das credenciais não é um JSON válido.', 'danger')
    return render_template('admin/datasource_form.html', title='Adicionar Fonte de Dados', form=form, client=client)

@admin.route('/datasource/edit/<int:datasource_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_datasource(datasource_id):
    datasource = DataSource.query.get_or_404(datasource_id)
    client = datasource.client
    form = DataSourceForm(obj=datasource)
    if form.validate_on_submit():
        try:
            json.loads(form.credentials_json.data)
            datasource.platform = form.platform.data
            datasource.credentials_json = form.credentials_json.data
            db.session.commit()
            flash(f'Fonte de dados {datasource.platform} atualizada com sucesso!', 'success')
            return redirect(url_for('admin.list_datasources', client_id=client.id))
        except json.JSONDecodeError:
            flash('Erro: O texto das credenciais não é um JSON válido.', 'danger')
    form.credentials_json.data = datasource.credentials_json
    return render_template('admin/datasource_form.html', title='Editar Fonte de Dados', form=form, client=client, datasource=datasource)

@admin.route('/datasource/delete/<int:datasource_id>', methods=['POST'])
@login_required
@admin_required
def delete_datasource(datasource_id):
    datasource = DataSource.query.get_or_404(datasource_id)
    client_id = datasource.client_id
    db.session.delete(datasource)
    db.session.commit()
    flash('Fonte de dados apagada com sucesso!', 'success')
    return redirect(url_for('admin.list_datasources', client_id=client_id))

# --- Gestão de Utilizadores ---
@admin.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', title='Gerir Utilizadores', users=users)

@admin.route('/user/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        if form.password.data:
            user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Utilizador adicionado com sucesso!', 'success')
        return redirect(url_for('admin.list_users'))
    return render_template('admin/user_form.html', title='Adicionar Utilizador', form=form)

@admin.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(original_username=user.username, original_email=user.email, obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Utilizador atualizado com sucesso!', 'success')
        return redirect(url_for('admin.list_users'))
    form.username.data = user.username
    form.email.data = user.email
    form.role.data = user.role
    return render_template('admin/user_form.html', title='Editar Utilizador', form=form, user=user)

@admin.route('/user/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Utilizador apagado com sucesso!', 'success')
    return redirect(url_for('admin.list_users'))