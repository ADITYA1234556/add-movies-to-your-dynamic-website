from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

ENDPOINT = "https://api.themoviedb.org/3/search/movie"
API_KEY = "YOUR_API_KEY FROM THEMOVIE"
ID_URL = "https://api.themoviedb.org/3/movie/"

class Base(DeclarativeBase):
  pass

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-movies.db"
app.config['SECRET_KEY'] = 'TYPE A SECRET KEY OF YOUR CHOICE'
Bootstrap5(app)

db = SQLAlchemy(model_class=Base)
db.init_app(app)

class EditRating(FlaskForm):
    rating = StringField(label="your rating out of 10 e.g 7.5")
    review = StringField(label="your review")
    submit = SubmitField(label="submit")

class AddMovie(FlaskForm):
    movie_name = StringField(label="movie name")
    done = SubmitField(label="Done")

class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float,nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url:Mapped[str] = mapped_column(String(300), nullable=False)

    # Optional: this will allow each book object to be identified by its title when printed.
    def __repr__(self):
        return f'<Movies {self.title}>'

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    list = []
    rating_movie = db.session.execute(db.select(Movies.rating)).scalars()
    for i in rating_movie:
        list.append(i)
    list.sort(reverse=True)
    print(list)
    rank = 1
    for j in list:
        selected = db.session.execute(db.select(Movies).where(Movies.rating == j)).scalar()
        selected.ranking = rank
        db.session.commit()
        rank += 1
    all_movies = db.session.execute(db.select(Movies).order_by(Movies.ranking)).scalars()
    return render_template("index.html", data = all_movies)

@app.route("/edit", methods = ["GET", "POST"])
def edit():
    form = EditRating()
    book_id = request.args.get("id")
    book_data = db.session.execute(db.select(Movies).where(Movies.id == book_id)).scalar()
    if form.validate_on_submit():
        book_data.rating = float(form.rating.data)
        book_data.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", data = book_data, form = form )

@app.route("/delete")
def delete():
    book_id = request.args.get("id")
    book_data = db.get_or_404(Movies, book_id)
    db.session.delete(book_data)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods = ["GET", "POST"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        movie_name = form.movie_name.data
        response = requests.get(url = ENDPOINT, params={"api_key": API_KEY, "query":movie_name})
        data = response.json()["results"]
        return render_template("select.html", data=data, )
    print(form.movie_name.data)
    return render_template("add.html", form=form)

@app.route("/find")
def find_movie():
    ID = request.args.get("id")
    if ID:
        IMG_URL = "https://image.tmdb.org/t/p/original"
        print(ID)
        ENDPOINT2 = f'{ID_URL}{ID}'
        response = requests.get(ENDPOINT2, params={
                                "api_key": API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movies(title=data["title"], year=data["release_date"].split("-")[0], img_url=f"{IMG_URL}{data['poster_path']}", description=data["overview"],)
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)


