from app import app
from peewee import *
from app.models import *
from flask import request,jsonify, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from datetime import date
from app.forms import *
from werkzeug.urls import url_parse
from playhouse.shortcuts import model_to_dict, dict_to_model

db = SqliteDatabase('db_transport_company.db')
db.connect()

@app.route('/')
@app.route('/index')
def index():
    if current_user.is_anonymous:
        lines = [line for line in Line().select()]
        return render_template('index.html', title = 'Home', lines = lines)
    if current_user.role == Role.ADMIN.value:
        return render_template('index_admin.html', title='Home', user=current_user)
    elif current_user.role == Role.MAINTAINER.value:
        return render_template('index_maintainer.html', title='Home', user=current_user)
    elif current_user.role == Role.TECHNICIAN.value:
        requests = [request for request in Request().select()]
        return render_template('index_technician.html', requests = requests)
    elif current_user.role ==Role.DISPATCHER.value:
        lines = [line for line in Line().select()]
        return render_template('index_dispatcher.html', lines = lines, user = current_user)
    elif current_user.role == Role.DRIVER.value:
        connections = Connection().select().where(Connection.driver == current_user.id)
        connections = [connection for connection in connections]
        if connections is not None:
            return render_template('index_driver.html', connections = connections, user = current_user)
    return render_template('index.html', title='Home')

@app.route('/add_defect', methods=['GET','POST'])
def add_defect():
    form = EditDefectForm()
    if form.validate_on_submit():
        vehicle = Vehicle.get_or_none(Vehicle.username == form.vehicle.data)
        if vehicle is None:
            flash('Vehicle does not exist')
            return redirect(url_for('add_defect'))
        DefectRecord(description=form.description.data, date = date.today(), author=current_user.id, vehicle=vehicle).save()
        return redirect(url_for('index'))
    if request.method == 'GET':
        return(render_template('add_defect.html', form = form))


@app.route('/add_maintenancerecord/<request_id>', methods=['GET', 'POST'])
@login_required
def add_maintenancerecord(request_id):
    req = Request().get_or_none(Request.id == request_id)
    if req is None:
        flash('Request does not exist')
        redirect(url_for('index'))
    form = EditMaintenaceRecordForm()
    if form.validate_on_submit():
        MaintenanceRecord(date=date.today(), status=form.status.data, author=current_user.id, request=req).save()
        return redirect(url_for('request_detail', request_id = request_id))
    if request.method == 'GET':
        return(render_template('add_maintenancerecord.html', form = form))

@app.route('/delete_record/<request_id>/<record_id>')
@login_required
def delete_record(request_id, record_id):
    MaintenanceRecord().delete_by_id(record_id)
    flash('Maintenance record was succesfully deleted.')
    return redirect(url_for('request_detail', request_id = request_id))

@app.route('/request_detail/<request_id>', methods=['GET'] )
def request_detail(request_id):
    req = Request().get_or_none(Request.id == request_id)
    if req is None:
        flash('Request dos not exist')
        return redirect(url_for('index'))
    records = MaintenanceRecord().select().where(MaintenanceRecord.request == request_id)
    return render_template('request_detail.html', request = req, records = records)

@app.route('/manage_lines', methods=['GET'])
@login_required
def manage_lines():
    lines = [line for line in Line().select()]
    return render_template('manage_lines.html', title = 'Lines', user = current_user, lines = lines)

# TO DO
@app.route('/add_line', methods=['GET','POST'])
@login_required
def add_line():
    form = EditLineForm()
    if form.validate_on_submit():
        line = Line(num = form.num.data, duration = form.duration.data)
        line.save()
        stops_list = [stop.strip() for stop in form.stops.data.split(',')]
        order = 0
        for stop_name in stops_list:
            stop = Stop().get_or_none(name = stop_name)
            if stop == None:
                stop = Stop(name = stop_name)
                stop.save()
            Stop2Line(stop_id = stop.id, line_id = line.id, order = order).save()
            order += 10           
        flash("New line was succesfully added!")
        return redirect(url_for('manage_lines'))
    return render_template('add_line.html', title = 'Line', form = form)

@app.route('/edit_line/<line_id>', methods=['GET', 'POST'])
@login_required
def edit_line(line_id):
    form = EditLineForm()
    line = Line().get_or_none(Line.id == line_id)
    if line is None:
        flash('Line does not exist.')
        return redirect('manage_lines')
    if form.validate_on_submit():
        line.num = form.num.data
        line.duration = form.duration.data
        stops_list = [stop.strip() for stop in form.stops.data.split(',')]
        order = 0
        for stop_name in stops_list:
            stop = Stop().get_or_none(name = stop_name)
            if stop == None:
                stop = Stop(name = stop_name)
                stop.save()
            stop2line = Stop2Line.get_or_none(Stop2Line.stop_id == stop.id, Stop2Line.line_id == line.id, Stop2Line.order == order)
            if stop2line is not None:
                continue # stop is assigned to line with correct order
            else:
                stop2line_wrong_order = Stop2Line.get_or_none(Stop2Line.stop_id == stop.id, Stop2Line.line_id == line.id)
                if stop2line_wrong_order is not None:
                    # Exists with wrong order
                    print("WRONG ORDER - NEW " + str(order))
                    stop2line_wrong_order.order = order
                    stop2line_wrong_order.save()
                    #Stop2Line(stop_id=stop.id, line_id=line_id, order = order).save()
                else: # stop2line_wrong_order is None -> does not exist at all add it
                    print("NEW " + str(order))
                    Stop2Line(stop_id = stop.id, line_id = line.id, order = order).save()
            order += 10
            
        # Check if any stop was deleted from line
        stops2line = Stop2Line.select().where(Stop2Line.line_id == line.id)
        index = 0
        for stop2line in stops2line:
            if stop2line.stop_id.name not in stops_list: # stop was previously attached to line, but was removed
                stop2line.delete_instance()

        line.save()
        flash("Changes have been saved!")
        return redirect(url_for('line_details', line_id = line_id))
    elif request.method == 'GET':
        form.num.data = line.num
        form.duration.data = line.duration
        stop2lines = Stop2Line.select().where(Stop2Line.line_id == line_id)
        stop_names = [stop2line.stop_id.name for stop2line in stop2lines]
        form.stops.data = ', '.join(stop_names)
        return render_template('add_line.html', form = form, title = 'Line', line_id = line_id)

@app.route('/line_details/<line_id>', methods=['GET'])
def line_details(line_id):
    line = Line().get_or_none(id = line_id)
    connections = Connection().select().where(Connection.line == line.id)
    if line == None:
        return "Not Found!", 404
    stops = []
    stops2line = line.stop2line.select().order_by(Stop2Line.order)
    for stop2line in stops2line:
        stop = Stop().get_or_none(id = stop2line.stop_id)
        if stop is not None:
            stops.append(stop)
    if current_user.is_authenticated:
        return render_template('line_details.html', line = line, stops = stops, connections = connections, user = current_user)
    else:
        return render_template('line_details_unregistered.html', line = line, stops = stops, connections = connections)

@app.route('/delete_line/<line_id>', methods=['GET'])
@login_required
def delete_line(line_id):
    Line().delete_by_id(line_id)
    stops2line = Stop2Line().select().where(Stop2Line.line_id == line_id)
    for stop2line in stops2line:
        stop2line.delete_instance()
    flash('Line has been deleted.')
    return redirect(url_for('manage_lines'))

# TO DO
@app.route('/find_line', methods=['GET'])
def find_line():
    requested_stop = request.args.get('requested_stop') # upload of stop name
    stop = Stop().get(stop.name == requested_stop) # find requested stop
    lines = stop.lines
    for line in lines:
        line.num

@app.route('/add_connection/<line_id>', methods=['GET', 'POST'])
@login_required
def add_connection(line_id):
    form = EditConnectionForm()
    line = Line().get_or_none(Line.id == line_id)
    if line is None:
        flash("Line does not exist!")
        return redirect(url_for('line_details', line_id = line_id))
    if form.validate_on_submit():
        if current_user.role == Role.ADMIN.value:
            vehicle = Vehicle().get_or_none(Vehicle.username == form.vehicle_username.data)
            driver_name = User().get_or_none(User.name == form.driver_name.data)
        elif current_user.role == Role.MAINTAINER.value:
            vehicle = Vehicle().get_or_none(Vehicle.name == 'undefined')
            driver_name = User().get_or_none(User.name == 'undefined')
        else:
            flash('Unauthorized!')
            return redirect(url_for('index'))
        if vehicle is not None and driver_name is not None and driver_name.role == Role.DRIVER.value:
            connection = Connection(departure = form.departure.data, direction = form.direction.data, only_working_days = form.only_working_days.data, line = line, vehicle = vehicle, driver = driver_name)
            connection.save()
            flash("New connection was succesfully added!")
            return redirect(url_for('line_details', line_id = line_id))
        else:
            if vehicle is None:
                flash("Vehicle with given name does not exist!")
            if driver_name is None:
                flash("Driver with given name does not exist!")
            else:
                flash("Given user is a " + driver_name.role + " not a " + Role.DRIVER.value)
    vehicles = [vehicle.username for vehicle in Vehicle().select()]
    drivers = [user.name for user in User().select().where(User.role == Role.DRIVER.value)]
    return render_template('add_connection.html', title = 'Add Connection', form = form, vehicles=vehicles, drivers = drivers )

@app.route('/delete_connection/<line_id>/<connection_id>', methods = ['GET'])
@login_required
def delete_connection(connection_id, line_id):
    Connection().delete_by_id(connection_id)
    flash('Connection has been deleted.')
    return redirect(url_for('line_details', line_id = line_id))

@app.route('/edit_connection/<line_id>/<connection_id>', methods = ['GET','POST'])
@login_required
def edit_connection(connection_id, line_id):
    form = EditConnectionForm()
    line = Line().get_or_none(Line.id == int(line_id))
    if line is None:
        flash("Line does not exist!")
        return redirect(url_for('line_details', line_id = line_id))
    if form.validate_on_submit():
        vehicle = Vehicle().get_or_none(Vehicle.username == form.vehicle_username.data)
        driver_name = User().get_or_none(User.name == form.driver_name.data)
        if vehicle is not None and driver_name is not None and driver_name.role == Role.DRIVER.value:
            connection = Connection().get_or_none(Connection.id == connection_id)
            connection.departure = form.departure.data
            connection.only_working_days = form.only_working_days.data
            connection.vehicle = vehicle
            connection.driver = driver_name
            connection.save()
            flash("Connection was succesfully edited!")
            return redirect(url_for('line_details', line_id = line_id))
        else:
            if vehicle is None:
                flash("Vehicle with given name does not exist!")
                return redirect(url_for('edit_connection', line_id = line_id, connection_id = connection_id))
            if driver_name is None:
                flash("Driver with given name does not exist!")
                return redirect(url_for('edit_connection', line_id = line_id, connection_id = connection_id))
            else:
                flash("Given user is a " + driver_name.role + " not a " + Role.DRIVER.value)
                return redirect(url_for('edit_connection', line_id = line_id, connection_id = connection_id))
    if request.method == 'GET':
        vehicles = [vehicle.username for vehicle in Vehicle().select()]
        drivers = [user.name for user in User().select().where(User.role == Role.DRIVER.value)]
        connection = Connection.get_or_none(Connection.id == connection_id)
        if(connection is not None):
            form.departure.data = connection.departure
            form.direction.data = connection.direction
            form.only_working_days.data = connection.only_working_days
            form.driver_name.data = connection.driver.name
            form.vehicle_username.data = connection.vehicle.username
        return render_template('add_connection.html', title = 'Add Connection', connection_id = connection_id, form = form, vehicles=vehicles, drivers = drivers)
    return redirect(url_for('line_details', line_id = line_id))

@app.route('/stops', methods=['GET'])
@login_required
def writeout_stops():
    stops = [stop for stop in Stop().select().dicts()] ##
    return render_template('stops_management.html', title = 'Stops', stops = stops)

@app.route('/add_stop', methods=['GET','POST'])
@login_required
def add_stop():
    form = EditStopForm()
    if form.validate_on_submit():
        stop = Stop(name = form.name.data)
        stop.save()
        flash("New stop was succesfully added!")
        return redirect(url_for('writeout_stops'))
    return render_template('add_stop.html', title = 'Add Stop', form = form)

@app.route('/delete_stop/<stop_id>', methods=['GET'])
@login_required
def delete_stop(stop_id):
    Stop().delete_by_id(stop_id)
    flash('Stop has been deleted.')
    return redirect(url_for('writeout_stops'))

@app.route('/edit_stop/<stop_id>', methods=['GET', 'POST'])
@login_required
def edit_stop(stop_id):
    form = EditStopForm()
    stop = Stop().get(id = int(stop_id))
    if form.validate_on_submit():
        stop.name = form.name.data
        stop.save()
        flash('Your changes have been saved.')
        return redirect(url_for('writeout_stops'))
    elif request.method == 'GET':
        form.name.data = stop.name
        return render_template('add_stop.html', form = form, title = 'Edit Stop', stop_id = stop_id)

@app.route('/manage-vehicles', methods=['GET'])
@login_required
def manage_vehicles():
    vehicles = [vehicle for vehicle in Vehicle().select()]
    return render_template('manage_vehicles.html', title = 'Vehicles', vehicles = vehicles)

@app.route('/add_vehicle', methods=['GET','POST'])
@login_required
def add_vehicle():
    form = EditVehicleForm()
    if form.validate_on_submit():
        vehicle = Vehicle(spz = form.spz.data, username = form.username.data, type = form.type.data, brand = form.brand.data, condition = form.condition.data)
        vehicle.save()
        flash("New vehicle was succesfully added!")
        return redirect(url_for('manage_vehicles'))
    return render_template('add_vehicle.html', title = 'Add vehicle', form = form)

@app.route('/delete_vehicle/<vehicle_id>')
@login_required
def delete_vehicle(vehicle_id):
    Vehicle().delete_by_id(vehicle_id)
    flash('Vehicle was succesfully deleted.')
    return redirect(url_for('manage_vehicles'))

@app.route('/add_request', methods=['GET', 'POST'])
@login_required
def add_request():
    form = EditRequestForm()
    if form.validate_on_submit():
        vehicle = Vehicle().get_or_none(Vehicle.username == form.vehicle_username.data)
        request = Request(description = form.description.data,  deadline = form.deadline.data, is_done = form.is_done.data, creation_date = date.today(), vehicle = vehicle.id)
        request.save()
        flash("New request was succesfully added!")
        return redirect(url_for('manage_requests'))
    vehicles = [vehicle.username for vehicle in Vehicle().select()]
    return render_template('add_request.html', title = 'Add request', form = form, vehicles = vehicles)

@app.route('/delete_request/<request_id>', methods=['GET'])
@login_required
def delete_request(request_id):
    Request().delete_by_id(request_id)
    flash('Request was succesfully deleted.')
    return redirect(url_for('manage_requests'))


@app.route('/manage_requests', methods = ['GET'])
@login_required
def manage_requests():
    requests = [request for request in Request().select()]
    return render_template('manage_requests.html', title='Requests', requests = requests, current_user = current_user)

# TO DO
@app.route('/record', methods=['POST'])
def create_record():
    input = request.get_json()
    state_in = input['state']
    request = input['request']
    date = date.today()
    if (state_in and request and date):
        MaintenanceRecord(request=Request().get_by_id(request), state=state_in, date=date, author=current_user).save()
        return 'OK',200
    else:
        return 'Wrong input',400       

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User().get_or_none(User.email == form.email.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/edit_own_profile', methods=['GET', 'POST'])
@login_required
def edit_own_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.username.data
        current_user.email = form.email.data
        current_user.save()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_own_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.name 
        form.email.data = current_user.email
    return render_template('edit_own_profile.html', title='Edit Profile', form=form)
    
@app.route('/employees_management', methods = ['GET'])
@login_required
def manage_employees():
    employees = [employee for employee in User().select().where(User.id != current_user.id).dicts()]
    return render_template('employees_management.html', title = 'Employees', user = current_user, employees = employees)

@app.route('/users', methods=['POST'])
@login_required
def create_user():
    if current_user.role != Role.ADMIN:
        return "Unauthorized", 401
    input = request.get_json()
    name_in = input['name']
    email_in = input['email']
    password_in = input['password']
    role_in = input['role']
    if (name_in and email_in and role_in and password_in):
        new_user = User(name = name_in, email = email_in, role = role_in)
        new_user.set_password(password_in)
        new_user.save()
        return 'OK', 200
    else:
        return 'Wrong input',400
    
@app.route('/users/<id>', methods=['GET'])
@login_required
def user(id):
    user = User().get_or_none(id = int(id))
    if user == None:
        return "Not Found", 404
    return render_template('user.html', user = user)

@app.route('/edit_user_profile/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_user_profile(user_id):
    if current_user.role != Role.ADMIN.value:
        flash("Unauthorized!")
        return redirect(url_for('index'))
    form = EditUserForm()
    user = User().get(id = int(user_id))
    if form.validate_on_submit():
        user.name = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.set_password(form.password.data)
        user.save()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_user_profile', user_id = user_id))
    elif request.method == 'GET':
        form.username.data = user.name
        form.email.data = user.email
        form.role.data = user.role
        form.password.data = user.password
        return render_template('edit_user_profile.html', title='Edit User Profile', form = form, creating = False)

@app.route('/register', methods = ['GET', 'POST'])
@login_required
def register():
    if current_user.role != Role.ADMIN.value:
        flash("Registration of new user can be done only by admin.")
        return redirect(url_for('index'))
    form = EditUserForm()
    if form.validate_on_submit():
        try:
            user = User(name = form.username.data, email = form.email.data, role = form.role.data)
            user.set_password(form.password.data)
            user.save()
            flash("New user was succesfully registered!")
            return redirect(url_for('manage_employees'))
        except:
            flash("Email already in use.")
    return render_template('edit_user_profile.html', title='Register', form = form, creating = True)

@app.route('/delete_user/<user_id>', methods=['GET'])
@login_required
def delete_user(user_id):
    User().delete_by_id(user_id)
    return redirect(url_for('manage_employees'))