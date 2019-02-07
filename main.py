from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databaseSetup import Base, Category, Item
import random
import string
import json
import httplib2
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:///catalogitem.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/catalog')
def showCatalog():
    categories = session.query(Category)
    return render_template('catalog.html', categories=categories, login_session=login_session)


@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html', login_session=login_session)


@app.route('/catalog/<categoryName>/items')
def showCategory(categoryName):
    category = session.query(Category).filter_by(name=categoryName).one()
    items = session.query(Item).filter_by(categoryId=category.id)
    return render_template('showCategory.html', category=category, items=items, login_session=login_session)


@app.route('/catalog/<categoryName>/edit', methods=['GET', 'POST'])
def editCategory(categoryName):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToEdit = session.query(Category).filter_by(name=categoryName).one()
    if request.method == 'POST':
        categoryToEdit.name = request.form['name']
        session.add(categoryToEdit)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', category=categoryToEdit, login_session=login_session)


@app.route('/catalog/<categoryName>/delete', methods=['GET', 'POST'])
def deleteCategory(categoryName):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(Category).filter_by(name=categoryName).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', category=categoryToDelete, login_session=login_session)


@app.route('/catalog/<categoryName>/items/new', methods=['GET', 'POST'])
def newItem(categoryName):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=categoryName).one()
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category=category,
                       owner=login_session['username']
                       )
        session.add(newItem)
        session.commit()
        return redirect(url_for('showCategory', categoryName=category.name))
    else:
        return render_template('newItem.html', category=category, login_session=login_session)


@app.route('/catalog/<categoryName>/<itemName>')
def showItem(categoryName, itemName):
    category = session.query(Category).filter_by(name=categoryName).one()
    item = session.query(Item).filter_by(categoryId=category.id).filter(Item.name == itemName).one()
    return render_template('showItem.html', item=item, login_session=login_session)


@app.route('/catalog/<categoryName>/<itemName>/edit', methods=['GET', 'POST'])
def editItem(categoryName, itemName):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=categoryName).one()
    itemToEdit = session.query(Item).filter_by(categoryId=category.id).filter(Item.name == itemName).one()
    if request.method == 'POST':
        if itemToEdit.owner == login_session['username']:
            itemToEdit.name = request.form['name']
            itemToEdit.description = request.form['description']
            session.add(itemToEdit)
            session.commit()
            return redirect(url_for('showCategory', categoryName=category.name))
        else:
            return redirect(url_for('unauthorized'))
    else:
        return render_template('editItem.html', category=category, item=itemToEdit, login_session=login_session)


@app.route('/catalog/<categoryName>/<itemName>/delete', methods=['GET', 'POST'])
def deleteItem(categoryName, itemName):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=categoryName).one()
    itemToDelete = session.query(Item).filter_by(categoryId=category.id).filter(Item.name == itemName).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showCategory', categoryName=category.name))
    else:
        return render_template('deleteItem.html', category=category, item=itemToDelete, login_session=login_session)


@app.route('/catalog.json')
def showCatalogJSON():
    jsonDict = {'Category': []}
    categories = session.query(Category).all()
    for category in categories:
        items = session.query(Item).filter_by(categoryId=category.id).all()
        jsonDict['Category'].append({'id': category.id,
                                     'name': category.name,
                                     'Item': []})
        for item in items:
            jsonDict['Category'][-1]['Item'].append({'name': item.name,
                                                     'id': item.id,
                                                     'description': item.description,
                                                     'categoryId': item.categoryId})
    return jsonify(jsonDict)


@app.route('/catalog/<categoryName>/items/json')
def showCategoryJSON(categoryName):
    category = session.query(Category).filter_by(name=categoryName).one()
    items = session.query(Item).filter_by(categoryId=category.id)
    jsonDict = {'name': category.name, 'id': category.id, 'Item': []}
    for item in items:
        jsonDict['Item'].append({'name': item.name,
                                 'id': item.id,
                                 'description': item.description,
                                 'categoryId': item.categoryId})
    return jsonify(jsonDict)


@app.route('/catalog/<categoryName>/<itemName>/json')
def showItemJSON(categoryName, itemName):
    category = session.query(Category).filter_by(name=categoryName).one()
    item = session.query(Item).filter_by(categoryId=category.id).filter(Item.name == itemName).one()
    return jsonify(item.serialize)


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, login_session=login_session)


@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')


@app.route('/logout')
def showLogout():
    return render_template('logout.html', login_session=login_session)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['email']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    #output += '<img src="'
    # output += login_session['picture']
    #output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    # flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gDisconnet():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5050)
