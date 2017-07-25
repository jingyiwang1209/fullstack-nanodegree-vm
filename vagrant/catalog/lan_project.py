from lan_model import Base, Book, User, Interaction, Rating
from flask import Flask, render_template, request, \
                  redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc, func
from sqlalchemy.orm import sessionmaker, relationship, join
from sqlalchemy.ext.declarative import declarative_base
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask_httpauth import HTTPBasicAuth
import json
from flask import make_response
import requests

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    search = StringField('search', validators=[DataRequired()])


class NewBookForm(FlaskForm):
    picture = StringField('picture', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    author = StringField('author', validators=[DataRequired()])
    description = StringField('description', validators=[DataRequired()])
    link = StringField('link', validators=[DataRequired()])
    category = StringField('category', validators=[DataRequired()])


auth = HTTPBasicAuth()
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets_google.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "my language"

# Connect to Database and create database session
engine = create_engine('sqlite:///lan5.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/books/JSON')
def booksJSON():
    books = session.query(Book).all()
    return jsonify(books=[b.serialize for b in books])


@app.route('/like', methods=['POST'])
def like():
    likeId = request.json['likeId']
    likedBook = session.query(Book)\
        .filter_by(id=likeId).one()
    likedInteraction = session.query(Interaction)\
        .filter_by(book_id=likeId).one()

    userid = login_session['user_id']
    msg = ''
    if userid:
        struserid = str(userid)+';'
        if likedInteraction.marker.find(struserid) >= 0:
            likedInteraction.marker = likedInteraction.marker\
                .replace(struserid, '')
            session.commit()
            likedInteraction.like -= 1
            session.commit()
            msg = str(likedInteraction.like)+' other people'

        else:
            likedInteraction.marker = likedInteraction.marker+struserid
            session.commit()
            likedInteraction.like += 1
            session.commit()
            msg = 'You and '+str(likedInteraction.like-1)+' other people'

        return json.dumps({'likeId': likeId,
                          'clicks': likedInteraction.like, 'msg': msg})


@app.route('/getData')
def getData():
    lst = []
    interactions = session.query(Interaction)\
        .order_by(desc(Interaction.book_id)).all()
    for inter in interactions:
        book = session.query(Book).filter_by(id=inter.book_id).one()
        dic = {'picture': book.picture, 'name': book.name,
               'cate': book.category,
               'id': book.id, 'like': inter.like}
        lst.append(dic)

    return json.dumps({'list': lst})


@app.route('/getSort')
def getSort():
    sortedInteractions = session.query(Interaction)\
        .order_by(desc(Interaction.like)).all()
    lst = []
    for si in sortedInteractions:
        sortedBook = session.query(Book).filter_by(id=si.book_id).one()
        dic = {'picture': sortedBook.picture,
               'name': sortedBook.name,
               'cate': sortedBook.category,
               'id': sortedBook.id,
               'like': si.like}
        lst.append(dic)

    return json.dumps({'sorted': lst})


@app.route('/', methods=['POST', 'GET'])
@app.route('/books', methods=['POST', 'GET'])
def showBooks():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    categories = session.query(Book.category, func.count(Book.category))\
        .group_by(Book.category).all()

    contributors = session.query(Book.user_id, func.count(Book.user_id))\
        .group_by(Book.user_id)\
        .order_by(desc(func.count(Book.user_id))).limit(5).all()
    # print "contributors", contributors
    # print"username",session.query(User).all()
    lst = []
    for con in contributors:
        username = session.query(User.username)\
            .filter_by(id=con[0]).one()

        picture = session.query(User.picture)\
            .filter_by(id=con[0]).one()
        userid = con[0]
        number = con[1]
        booklist = session.query(Book.name).\
            filter_by(user_id=con[0]).all()
        contributor = {'userid': userid,
                       'username': username,
                       'number': number,
                       'picture': picture,
                       'booklist': booklist}
        lst.append(contributor)

    searchForm = SearchForm()
    if request.method == 'POST':
        bookName = request.form['search']
        bookList = session.query(Book).\
            filter(Book.name.contains(bookName)).all()
        length = len(bookList)
        if 'username' in login_session:
            return render_template('searchBooks.html',
                                   bookList=bookList, length=length,
                                   picture=login_session['picture'],
                                   searchForm=searchForm)
        else:
            return render_template('publicSearchBooks.html',
                                   bookList=bookList, length=length,
                                   STATE=login_session['state'],
                                   searchForm=searchForm)

    if request.method == 'GET':
        rating = session.query(Rating.book_id, func.avg(Rating.star))\
            .group_by(Rating.book_id)\
            .order_by(desc(func.avg(Rating.star))).limit(6).all()

        # [(1, 5.0), (7, 4.5), (2, 4.0), (3, 4.0), (5, 4.0), (6, 3.5)]

        bookCarousel = []
        for r in rating:
            bookname = session.query(Book.name).filter_by(id=r[0]).one()
            picture = session.query(Book.picture).filter_by(id=r[0]).one()
            dic = {'bookid': r[0],
                   'bookname': bookname,
                   'picture': picture,
                   'star': r[1]}
            bookCarousel.append(dic)

        if 'username' not in login_session:
            return render_template('publicbooks.html',
                                   STATE=state,
                                   categories=categories,
                                   lst=lst,
                                   bookCarousel=bookCarousel,
                                   searchForm=searchForm)
        else:
            return render_template('books.html',
                                   categories=categories,
                                   bookCarousel=bookCarousel,
                                   picture=login_session['picture'],
                                   lst=lst,
                                   searchForm=searchForm)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Deal with Google sign in
    print'state back', request.args.get('state')
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets_google.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        # print "cred!!!!!!!", credentials
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        print 'response', response
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['credentials'] = credentials.access_token
    print"login_session!!!!!", login_session['credentials']
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    login_session['provider'] = 'google'
    return 'welcome!'+login_session['username']


# User Helper Functions
def createUser(login_session):
    newUser = User(username=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Deal with Facebook signin
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    # Exchange client token for long-lived server-side token
    app_id = json.loads(
        open('client_secrets_fb.json', 'r').read())['web']['app_id']
    app_secret = json.loads(
        open('client_secrets_fb.json', 'r').read())['web']['app_secret']
    url = ('https://graph.facebook.com/v2.9/oauth/access_token?'
           'grant_type=fb_exchange_token&client_id=%s&client_secret=%s'
           '&fb_exchange_token=%s') % (app_id, app_secret, access_token)
    http = httplib2.Http()
    result = http.request(url, 'GET')[1]
    data = json.loads(result)

    # Extract the access token from response
    token = 'access_token=' + data['access_token']

    # Use token to get user info from API
    url = 'https://graph.facebook.com/v2.9/me?%s&fields=name,id,email,'\
          'picture' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['provider'] = 'facebook'
    login_session['username'] = data.get("name")
    login_session['email'] = data.get("email")
    login_session['facebook_id'] = data.get('id')
    # new: put the "picture" here, it is now part of default "public_profile"
    login_session['picture'] = data['picture']["data"]["url"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "<h1>Welcome, "+login_session['username']+"</h1>"


@app.route('/logout')
def logout():
    if login_session['provider'] == 'google':
        credentials = login_session.get('credentials')
        print "credentials", credentials
        if credentials is None:
            response = make_response(
                json.dumps('Current user not connected.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        access_token = login_session.get('access_token')
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
              % access_token
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        if result['status'] != '200':
            print "status", result['status']
            # For whatever reason, the given token was invalid.
            response = make_response(
                json.dumps('Failed to revoke token for given user.'), 400)
            response.headers['Content-Type'] = 'application/json'
            return response
    elif login_session['provider'] == 'facebook':
        facebook_id = login_session['facebook_id']
        # The access token must be included to successfully logout
        access_token = login_session['access_token']
        url = 'https://graph.facebook.com/%s/permissions?%s' \
              % (facebook_id, access_token)
        print "url", url
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1]

    # login_session.pop('username')
    login_session.clear()
    return redirect(url_for('showBooks'))


@app.route('/submittedNewBook', methods=['POST'])
def submittedNewBook():
    form = NewBookForm()
    if form.validate_on_submit():
        newBook = Book(picture=form.picture.data,
                       name=form.name.data,
                       author=form.author.data,
                       description=form.description.data,
                       link=form.link.data,
                       category=form.category.data,
                       user_id=login_session['user_id'])

        session.add(newBook)
        session.commit()

        newInteraction = Interaction(book_id=newBook.id)
        session.add(newInteraction)
        session.commit()

        # print"newInteraction.id!!!!!!", newInteraction.id
        # print"newInteraction.book_id!!!!!!", newInteraction.book_id
        # print"newInteraction.like!!!!!!", newInteraction.like

        success = 'The book was successfully added.'
        return json.dumps({'success': success})

    else:
        failure = 'Bummer: please fill all the areas.'
        return json.dumps({'failure': failure})


@app.route('/books/new', methods=['GET', 'POST'])
def newBooks():
    searchForm = SearchForm()
    form = NewBookForm()
    if request.method == 'POST':
        print('DATA:', searchForm.search.data)
        if searchForm.validate_on_submit():
            bookList = session.query(Book)\
                .filter(Book.name.contains(searchForm.search.data)).all()
            length = len(bookList)
            return render_template('searchBooks.html',
                                   bookList=bookList, length=length,
                                   picture=login_session['picture'],
                                   searchForm=searchForm)
        else:
            flash('Bummer: please type a name.')
            return redirect(url_for('newBooks'))

        return render_template('newBooks.html', form=form,
                               searchForm=searchForm)

    else:
        return render_template('newBooks.html',
                               picture=login_session['picture'],
                               form=form, searchForm=searchForm)


@app.route('/bookDetails', methods=['POST'])
def bookDetails():
    data = request.json['bookId']
    book = session.query(Book).filter(Book.id == data).one()
    return json.dumps({'name': book.name, 'picture': book.picture,
                       'author': book.author, 'description': book.description,
                       'link': book.link, 'category': book.category,
                       'bookId': book.id})


@app.route('/books/<int:book_id>', methods=['POST', 'GET'])
def expandBooks(book_id):
    searchForm = SearchForm()
    if request.method == 'POST':
        bookName = request.form['search']
        bookList = session.query(Book)\
            .filter(Book.name.contains(bookName)).all()
        length = len(bookList)
        if 'username' in login_session:
            return render_template('searchBooks.html',
                                   bookList=bookList, length=length,
                                   picture=login_session['picture'],
                                   searchForm=searchForm)
        else:
            return render_template('publicSearchBooks.html',
                                   bookList=bookList, length=length,
                                   searchForm=searchForm)

    if request.method == 'GET':
        book = session.query(Book).filter_by(id=book_id).one()
        points = session.query(func.count(Rating.book_id),
                               func.avg(Rating.star))\
            .filter_by(book_id=book_id).all()

        if 'username' in login_session:
            return render_template('expandBooks.html',
                                   book=book, picture=login_session['picture'],
                                   searchForm=searchForm,
                                   username=login_session['username'],
                                   points=points)
        else:
            return render_template('publicExpandBooks.html',
                                   searchForm=searchForm,
                                   STATE=login_session['state'],
                                   book=book, points=points)


@app.route('/books/<int:book_id>/edit', methods=['POST', 'GET'])
def editBooks(book_id):
    categories = session.query(
        Book.category).group_by(Book.category).all()

    editedBook = session.query(
        Book).filter_by(id=book_id).one()

    searchForm = SearchForm()
    form = NewBookForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            editedBook.picture = request.form['picture']
            editedBook.name = request.form['name']
            editedBook.author = request.form['author']
            editedBook.description = request.form['description']
            editedBook.link = request.form['link']
            editedBook.category = request.form['category']
            return redirect(url_for('myList'))

        elif searchForm.validate_on_submit():
            bookList = session.query(Book)\
                .filter(Book.name.contains(searchForm.search.data)).all()
            length = len(bookList)
            return render_template('searchBooks.html',
                                   bookList=bookList, length=length,
                                   picture=login_session['picture'],
                                   searchForm=searchForm, form=form)
        else:
            flash('Please type.')
            return redirect(url_for('editBooks', book_id=editedBook.id))

        return render_template('editBooks.html',
                               form=form, searchForm=searchForm)

    else:
        return render_template("editBooks.html", editedBook=editedBook,
                               categories=categories,
                               picture=login_session['picture'],
                               searchForm=searchForm, form=form)


@app.route('/delete', methods=['POST'])
def deleteBooks():
    delId = request.json['delId']
    deletedBook = session.query(Book).filter_by(id=delId).one()

    deletedInteraction = session.query(Interaction)\
        .filter_by(book_id=delId).one()
    session.delete(deletedInteraction)
    session.commit()

    session.delete(deletedBook)
    session.commit()

    return json.dumps({'delId': delId})


@app.route('/books/<book_category>', methods=['POST', 'GET'])
def expandCategories(book_category):
    searchForm = SearchForm()
    if request.method == 'POST':
        bookName = request.form['search']
        bookList = session.query(Book)\
            .filter(Book.name.contains(bookName)).all()
        length = len(bookList)
        if 'username' in login_session:
            return render_template('searchBooks.html',
                                   bookList=bookList, length=length,
                                   picture=login_session['picture'],
                                   searchForm=searchForm)
        else:
            return render_template('publicSearchBooks.html',
                                   bookList=bookList, length=length,
                                   searchForm=searchForm)

    if request.method == 'GET':
        books = session.query(Book).filter_by(category=book_category).all()

        if 'username' in login_session:
            return render_template('expandCategories.html',
                                   category=book_category,
                                   books=books,
                                   picture=login_session['picture'],
                                   searchForm=searchForm)
        else:
            return render_template('publicExpandCategories.html',
                                   category=book_category, books=books,
                                   STATE=login_session['state'],
                                   searchForm=searchForm)


@app.route('/books/mylist', methods=['POST', 'GET'])
def myList():
    id = login_session['user_id']
    searchForm = SearchForm()
    if request.method == 'GET':
        books = session.query(Book).filter_by(user_id=id).all()
        return render_template('myList.html', books=books,
                               searchForm=searchForm,
                               picture=login_session['picture'])

    if request.method == 'POST':
        bookName = request.form['search']
        bookList = session.query(Book)\
            .filter(Book.name.contains(bookName)).all()
        length = len(bookList)
        if 'username' in login_session:
            return render_template('searchBooks.html',
                                   bookList=bookList, length=length,
                                   picture=login_session['picture'],
                                   searchForm=searchForm)
        else:
            return render_template('publicSearchBooks.html',
                                   bookList=bookList, length=length,
                                   searchForm=searchForm)


@app.route('/userbooks/<int:book_userid>', methods=['POST', 'GET'])
def userBooks(book_userid):
    searchForm = SearchForm()
    if request.method == 'GET':
        books = session.query(Book).filter_by(user_id=book_userid).all()
        if 'username'not in login_session:
            return render_template('publicUserBooks.html',
                                   STATE=login_session['state'],
                                   books=books, searchForm=searchForm)
        else:
            return render_template('userBooks.html', books=books,
                                   picture=login_session['picture'],
                                   searchForm=searchForm)

    if request.method == 'POST':
        bookName = request.form['search']
        bookList = session.query(Book)\
            .filter(Book.name.contains(bookName)).all()
        length = len(bookList)
        if 'username' in login_session:
            return render_template('searchBooks.html',
                                   bookList=bookList, length=length,
                                   picture=login_session['picture'],
                                   searchForm=searchForm)
        else:
            return render_template('publicSearchBooks.html',
                                   bookList=bookList, length=length,
                                   searchForm=searchForm)


@app.route('/ratings', methods=['POST'])
def ratings():
    bookid = request.json['bookid']
    feedback = request.json['feedback']
    points = request.json['points']

    rating = Rating(book_id=bookid, feedback=feedback,
                    star=points, user_id=login_session['user_id'])
    username = login_session['username']

    session.add(rating)
    session.commit()
    return json.dumps({'bookid': bookid, 'feedback': feedback,
                      'reader': username, 'points': points})


@app.route('/getRating', methods=['POST'])
def getRating():
    bookid = request.json['bookid']
    rating = session.query(Rating)\
        .filter_by(book_id=bookid).order_by(desc(Rating.id)).all()
    ratingList = []
    if 'username' in login_session:
        for r in rating:
            userid = r.user_id
            user = session.query(User).filter_by(id=userid).one()
            dic = {'star': r.star, 'bookid': r.book_id,
                   'username': user.username,
                   'feedback': r.feedback}
            ratingList.append(dic)

    return json.dumps({'ratingList': ratingList})


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
