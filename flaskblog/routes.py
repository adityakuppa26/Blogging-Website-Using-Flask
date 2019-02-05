import secrets,os
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import RegistrationForm, LoginForm, AccountUpdateForm, PostForm, RequestResetForm, ResetPasswordForm
from flaskblog.models import User,Post  
from flask_login import login_user,current_user,logout_user, login_required
from flask_mail import Message
import smtplib
from email.mime.text import MIMEText


@app.route("/")															# URL for home page
def hello():
	page=request.args.get('page',1,type=int)
	posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=2)
	return render_template('hello.html',posts=posts)

@app.route("/about")
def about():
    return render_template('about.html',title='About')

@app.route("/register", methods=['GET','POST'])							# methods allow for posting requests from these URLs
def register():
	if current_user.is_authenticated:						# clicking the login and register redirects to hello if logged in
		return redirect(url_for('hello'))
	form = RegistrationForm()													# creating a form instance
	if form.validate_on_submit():												# validates the form on submission
		hashed_pw=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user=User(username=form.username.data,email=form.email.data,password=hashed_pw)	
		db.session.add(user)
		db.session.commit()									
		flash('Your account has been created. You are now able to login.', 'success')			# flash message of category=success
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=form)

@app.route("/login",methods=['GET','POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('hello'))
	form = LoginForm()
	if form.validate_on_submit():
		user=User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password,form.password.data):
			login_user(user,remember=form.remember.data)
			next_page=request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('hello'))											# redirects to a specific page
		else:
			flash('Wrong credentials. Please check your email and password.','danger')
	return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('hello'))


def save_picture(form_picture):

	picture_hex=secrets.token_hex(8)
	_,fn_ext=os.path.split(form_picture.filename)
	picture_fn=picture_hex+fn_ext
	picture_path=os.path.join(app.root_path,'static/profile_pics',picture_fn)
	form_picture.save(picture_path)

	return picture_fn

@app.route("/account",methods=['GET','POST'])
@login_required
def account():
	form=AccountUpdateForm()
	image_file=url_for('static',filename='profile_pics/'+current_user.image_file)



	if form.validate_on_submit():
		if form.picture.data:
			picture_name=save_picture(form.picture.data)
			current_user.image_file=picture_name
		current_user.username=form.username.data
		current_user.email=form.email.data
		db.session.commit()
		flash('Your account has been updated !','success')
		return redirect(url_for('account'))

	elif request.method=='GET':
		form.username.data=current_user.username
		form.email.data=current_user.email
	return render_template('account.html', title='Account',image_file=image_file,form=form)


@app.route("/post/new", methods=['GET','POST'])
@login_required
def new_post():
	form=PostForm()

	if form.validate_on_submit():
		post=Post(title=form.title.data, content=form.content.data,author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Your post has been successfully published !','success')
		return redirect(url_for('hello'))

	return render_template('newpost.html',title='New Post',form=form,legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):

	post=Post.query.get_or_404(post_id)
	return render_template('post.html',title='Post',post=post)

@app.route("/post/<int:post_id>/update",methods=['GET','POST'])
@login_required
def update_post(post_id):

	post=Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)

	form=PostForm()
	if form.validate_on_submit():
		post.title=form.title.data
		post.content=form.content.data
		db.session.commit()
		flash('Your post has been updated !','success')
		return redirect(url_for('post',post_id=post.id))

	elif request.method=='GET':
		form.title.data=post.title
		form.content.data=post.content
	

	return render_template('newpost.html',title='Update Post',form=form,legend='Update Post')

@app.route("/post/<int:post_id>/delete",methods=['POST'])
@login_required
def delete_post(post_id):

	post=Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)

	db.session.delete(post)
	db.session.commit()
	flash('Your post has been deleted!','success')
	return redirect(url_for('hello'))


@app.route("/user/<string:username>")															# URL for home page
def user_posts(username):
	page=request.args.get('page',1,type=int)
	user=User.query.filter_by(username=username).first_or_404()
	posts=Post.query.filter_by(author=user)\
		.order_by(Post.date_posted.desc())\
		.paginate(page=page,per_page=2)
	return render_template('user_posts.html',posts=posts,user=user)

"""
def send_reset_email(user):
	token=user.get_reset_token()
	msg=Message('Password Reset Request',sender='noreply@demo.com',recipients=[user.email])
	msg.body=f'''To reset your password visit the following link:
	{url_for('reset_token',token=token,_external=True)}

	If you did not request for this, then ignore the mail and no changes would be made.
	'''
	mail.send(msg)
"""

def send_reset_email(user):
   token=user.get_reset_token()
   FROM='aditya.kuppa@oracle.com'
   TO=user.email
   SERVER="internal-mail-router.oracle.com"
   bodyText=f'''To reset the password, visit the following link:
   {url_for('reset_token',token=token,_external=True)}

If you didnot make this request, you can simply ignore it. No changes will be made.
   '''
   msg=MIMEText(bodyText)
   s = smtplib.SMTP(SERVER)
   s.set_debuglevel(1)
   s.starttls()
   s.sendmail(FROM, TO, msg.as_string())

@app.route("/reset_password",methods=['GET','POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('hello'))

	form=RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash('An email has been sent with instructions to reset the password.','info')
		return redirect(url_for('login'))
	return render_template('reset_request.html',title='Reset Password',form=form)

@app.route("/reset_password/<token>",methods=['GET','POST'])
def reset_token(token):
	if current_user.is_authenticated:
		return redirect(url_for('hello'))

	user=User.verify_reset_token(token)
	if user is None:
		flash('This is an invalid or expired token.','warning')
		return redirect(url_for('reset_request'))

	form=ResetPasswordForm()
	if form.validate_on_submit():												# validates the form on submission
		hashed_pw=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user.password=hashed_pw
		db.session.commit()									
		flash('Your password has been reset. You are now able to login.', 'success')			# flash message of category=success
		return redirect(url_for('login'))
	return render_template('reset_password.html',title='Reset Password',form=form)