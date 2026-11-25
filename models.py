from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    albums = db.relationship("Album", back_populates="author", lazy="dynamic")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Album(db.Model):
    __tablename__ = "albums"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(140), unique=True, nullable=False, index=True)
    title = db.Column(db.String(140), nullable=False)
    artist_credit = db.Column(db.String(120), nullable=False, default="Lely45")
    release_year = db.Column(db.Integer, nullable=False)
    release_date = db.Column(db.String(60), nullable=True)
    genre = db.Column(db.String(100), nullable=False, default="Інді-рок / Альтернативний поп")
    label = db.Column(db.String(100), nullable=True, default="Independent")
    duration = db.Column(db.String(40), nullable=True)
    cover_image = db.Column(
        db.String(300),
        nullable=False,
        default="images/cover_retrospektyva.jpg",
    )
    tagline = db.Column(db.String(240), nullable=True)
    description = db.Column(db.Text, nullable=False)
    streaming_url = db.Column(db.String(300), nullable=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    author = db.relationship("User", back_populates="albums")

    tracks = db.relationship(
        "Track",
        back_populates="album",
        cascade="all, delete-orphan",
        order_by="Track.track_number",
        lazy="select",
    )

    @property
    def cover_is_external(self) -> bool:
        return self.cover_image.startswith(("http://", "https://"))

    def __repr__(self) -> str:
        return f"<Album {self.title} ({self.release_year})>"


class Track(db.Model):
    __tablename__ = "tracks"

    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(
        db.Integer, db.ForeignKey("albums.id", ondelete="CASCADE"), nullable=False
    )
    track_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(160), nullable=False)
    duration = db.Column(db.String(20), nullable=True)
    featuring = db.Column(db.String(120), nullable=True)

    album = db.relationship("Album", back_populates="tracks")

    def __repr__(self) -> str:
        return f"<Track {self.track_number}. {self.title}>"
