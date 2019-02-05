# Intro:

* In our main function, we need to run our flask variable, to do that we need to use the app variable which we declared before and use the run method on it. This run method starts a local server in your machine. Usually, the default address is “localhost:5000.” To change the port address, we can pass in a parameter to the run method assigning it to any desired port number. 

```python3
if __name__ =="__main__":
    app.run(debug=True, port=8080)
```

* We then use the **route() decorator** on the app variable to tell Flask what URL should trigger our function. The desired URL pattern should be written in the string to the route decorator. 

```python
@app.route('/')
def hello_world():
    return 'Hello, World!'
```

# Flask Templating:

* So, how to insert plain HTML code into a Flask Application?

```python3
@app.route('/greet')

def greet():
    user = {'username': 'John', 'age': "20"}
    return '''
<html>
    <head>
        <title>Templating</title>
    </head>
    <body>
        <h1>Hello, ''' + user['username'] + '''!, you’re ''' + user['age'] + ''' years old.</h1>
    </body>
</html>'''
```

This is totally cumbersome if at all HTML code must be changed on a regular basis. Thus, we use render_template function.

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/hello')
def hello():
    return render_template('index.html', name="Alex")
```

The index.html looks as follows:

```html
<html>
<body>
  {% if name %}
    <h2>Hello {{ name }}.</h2>
  {% else %}
    <h2>Hello.</h2>
  {% endif %}
 </body>
</html>
```

* {{ }} is used as placeholder for the variables and {% %} is used to show the opening and the closing of a block.

# Models:

* SQLAlchemy : ORM ( same python code for creating and maintaining models even when the db changes)
* The baseclass for all your models is called `db.Model`.  It’s storedon the SQLAlchemy instance you have to create. 

```python3
Simple Example:

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username
```

* Data types for columns:

![flasknotes-1](images/flasknotes-1.PNG) 

**Relationships:**

* Relationships are expressed with the [`relationship()`](http://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship) function.  However the foreign key has to be separately declared with the[`ForeignKey`](http://docs.sqlalchemy.org/en/latest/core/constraints.html#sqlalchemy.schema.ForeignKey) class:

```python3
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    addresses = db.relationship('Address', backref='person', lazy=True)

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
        nullable=False)
```

* What does [`db.relationship()`](http://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship) do? 

  That function returns a new property that can do multiple things. In this case we told it to point to the `Address` class and load multiple of those.  How does it know that this will return more than one address?  Because SQLAlchemy guesses a useful default from your declaration.  If you would want to have a **one-to-one relationship** you can pass `uselist=False` to [`relationship()`](http://docs.sqlalchemy.org/en/latest/orm/relationship_api.html#sqlalchemy.orm.relationship).

* So what do `backref` and `lazy` mean?  `backref` is a simple way to also declare a new property on the `Address` class.  You can then also use `my_address.person` to get to the person at that address.  `lazy` defines when SQLAlchemy will load the data from the database:
  - `'select'` / `True` (which is the default, but explicit is better than implicit) means that SQLAlchemy will load the data as necessary in one go using a standard select statement.
  - `'joined'` / `False` tells SQLAlchemy to load the relationship in the same query as the parent using a `JOIN` statement.

**Many-Many relationships:**

If you want to use many-to-many relationships you will need to define a helper table that is used for the relationship.  For this helper table it is strongly recommended to *not* use a model but an actual table:

```python3
tags = db.Table('tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('page_id', db.Integer, db.ForeignKey('page.id'), primary_key=True)
)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tags = db.relationship('Tag', secondary=tags, lazy='subquery',
        backref=db.backref('pages', lazy=True))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
```

Here we configured `Page.tags` to be loaded immediately after loading a Page, but using a separate query.  This always results in two queries when retrieving a Page, but when querying for multiple pages you will not get additional queries.

The list of pages for a tag on the other hand is something that’s rarely needed. For example, you won’t need that list when retrieving the tags for a specific page.  Therefore, the backref is set to be lazy-loaded so that accessing it for the first time will trigger a query to get the list of pages for that tag.

# Flask-Login:

* Flask-Login provides user session management for Flask. It handles the common tasks of logging in, logging out, and remembering your users’ sessions over extended periods of time.

* The most important part of an application that uses Flask-Login is the [`LoginManager`](https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager) class.

```python
	login_manager = LoginManager()
    login_manager.init_app(app)
```

The login manager contains the code that lets your application and Flask-Login work together, such as 					how to load a user from an ID, where to send users when they need to log in, and the like.

**How it works?**

You will need to provide a [`user_loader`](https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader) callback. This callback is used to reload the user object from the user ID stored in the session. It should take the `unicode` ID of a user, and return the corresponding user object. For example:

```python
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
```

It should return [`None`](https://docs.python.org/3/library/constants.html#None) (**not raise an exception**) if the ID is not valid.

**Login Example:**

Once a user has authenticated, you log them in with the [`login_user`](https://flask-login.readthedocs.io/en/latest/#flask_login.login_user) function.

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('index'))
    return flask.render_template('login.html', form=form)
```

* Views that require your users to be logged in can be decorated with the [`login_required`](https://flask-login.readthedocs.io/en/latest/#flask_login.login_required) decorator:

```
@app.route("/settings")
@login_required
def settings():
    pass
```

* When the user is ready to log out:

  ```
  @app.route("/logout")
  @login_required
  def logout():
      logout_user()
      return redirect(somewhere)
  ```

  They will be logged out, and any cookies for their session will be cleaned up.

**Customising login:**

* The name of the log in view can be set as [`LoginManager.login_view`](https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.login_view). For example:

  ```
  login_manager.login_view = "users.login"
  ```

* The default message flashed is `Please log in to access this page.` To customize the message, set [`LoginManager.login_message`](https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.login_message):

  ```
  login_manager.login_message = u"Bonvolu ensaluti por uzi tiun paĝon."
  ```

* To customize the message category, set `LoginManager.login_message_category`:

  ```
  login_manager.login_message_category = "info"
  ```

**UserMixin**

```python

class User(db.Model,UserMixin):							
	id=db.Column(db.Integer,primary_key=True)	
	username=db.Column(db.String(20),unique=True,nullable=False)
	email=db.Column(db.String(20),unique=True,nullable=False)		
	image_file=db.Column(db.String(20),nullable=False, default='default.jpg')
	password=db.Column(db.String(60),nullable=False)
	posts=db.relationship('Post',backref='author',lazy=True)		

```

```python
    class UserMixin(object):
        '''
        This provides default implementations for the methods that Flask-Login
        expects user objects to have.
        '''
        @property
        def is_active(self):
            return True
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)
        except **AttributeError**:
            raise **NotImplementedError**('No `id` attribute - override `get_id`')

    def __eq__(self, other):
        '''
        Checks the equality of two `UserMixin` objects using `get_id`.
        '''
        if isinstance(other, UserMixin):
            return self.get_id() == other.get_id()
        return NotImplemented

    def __ne__(self, other):
        '''
        Checks the inequality of two `UserMixin` objects using `get_id`.
        '''
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal

    if sys.version_info[0] != 2:  *# pragma: no cover*
        *# Python 3 implicitly set __hash__ to None if we override __eq__*
        *# We set it back to its default implementation*
        __hash__ = object.__hash__
```