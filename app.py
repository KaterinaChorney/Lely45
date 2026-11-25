import os
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

from config import Config
from models import Album, Track, User, db
from seed import generate_unique_slug, seed_database

PRESET_COVERS = [
    ("images/cover_retrospektyva.jpg", "РЕТРОспектива"),
    ("images/cover_vsi_divchata.jpg", "Всі дівчата хороші"),
    ("images/cover_chornyi_lebid.jpg", "Чорний лебідь"),
    ("images/cover_koly_sontse.jpg", "Коли сонце сідає за схил"),
]


def _allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def _parse_tracks_from_form(form) -> list[tuple[str, str | None, str | None]]:
    """Extract ordered track rows from dynamic album form fields."""
    titles = form.getlist("track_title[]")
    durations = form.getlist("track_duration[]")
    featurings = form.getlist("track_featuring[]")

    parsed = []
    for idx, raw_title in enumerate(titles):
        title = raw_title.strip()
        if not title:
            continue
        duration = durations[idx].strip() if idx < len(durations) else ""
        featuring = featurings[idx].strip() if idx < len(featurings) else ""
        parsed.append((title, duration or None, featuring or None))
    return parsed


def _resolve_cover_image(app: Flask, existing_cover: str | None = None) -> str:
    """Resolve album cover from uploaded file, external URL, or preset selection."""
    uploaded = request.files.get("cover_file")
    if uploaded and uploaded.filename:
        if _allowed_file(uploaded.filename, app.config["ALLOWED_EXTENSIONS"]):
            upload_dir = Path(app.config["UPLOAD_FOLDER"])
            upload_dir.mkdir(parents=True, exist_ok=True)
            safe_name = secure_filename(uploaded.filename)
            unique_name = f"{uuid4().hex[:10]}_{safe_name}"
            uploaded.save(upload_dir / unique_name)
            return f"uploads/{unique_name}"
        flash("Непідтримуваний формат зображення. Дозволено: PNG, JPG, JPEG, WEBP.", "warning")

    cover_url = request.form.get("cover_url", "").strip()
    if cover_url.startswith(("http://", "https://")):
        return cover_url

    preset = request.form.get("cover_preset", "").strip()
    valid_presets = {path for path, _ in PRESET_COVERS}
    if preset in valid_presets:
        return preset

    return existing_cover or "images/cover_retrospektyva.jpg"


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = "Будь ласка, увійдіть у систему, щоб керувати альбомами."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_globals():
        return {
            "total_albums_count": Album.query.count(),
            "artist_display_name": "Lely45 · Lyuda Bielousova",
        }

    # --- Main pages ---

    @app.route("/")
    def index():
        featured_album = (
            Album.query.filter_by(is_featured=True)
            .order_by(Album.release_year.desc(), Album.id.desc())
            .first()
        )
        albums = Album.query.order_by(Album.release_year.desc(), Album.id.desc()).all()
        if not featured_album and albums:
            featured_album = albums[0]
        total_tracks = Track.query.count()
        return render_template(
            "index.html",
            featured_album=featured_album,
            albums=albums,
            total_tracks=total_tracks,
        )

    @app.route("/about")
    def about():
        stats = {
            "albums": Album.query.count(),
            "tracks": Track.query.count(),
            "users": User.query.count(),
        }
        return render_template("about.html", stats=stats)

    @app.route("/history")
    def history():
        albums = Album.query.order_by(Album.release_year.asc(), Album.id.asc()).all()
        return render_template("history.html", albums=albums)

    # --- Albums CRUD ---

    @app.route("/albums")
    def albums_list():
        query_text = request.args.get("q", "").strip()
        year_filter = request.args.get("year", "").strip()

        query = Album.query
        if query_text:
            like_pattern = f"%{query_text}%"
            query = query.filter(
                db.or_(
                    Album.title.ilike(like_pattern),
                    Album.artist_credit.ilike(like_pattern),
                    Album.genre.ilike(like_pattern),
                    Album.description.ilike(like_pattern),
                )
            )
        if year_filter.isdigit():
            query = query.filter(Album.release_year == int(year_filter))

        albums = query.order_by(Album.release_year.desc(), Album.id.desc()).all()
        available_years = [
            row[0]
            for row in db.session.query(Album.release_year)
            .distinct()
            .order_by(Album.release_year.desc())
            .all()
        ]
        return render_template(
            "albums/list.html",
            albums=albums,
            query_text=query_text,
            year_filter=year_filter,
            available_years=available_years,
        )

    @app.route("/albums/<slug>")
    def album_detail(slug: str):
        album = Album.query.filter_by(slug=slug).first_or_404()
        other_albums = (
            Album.query.filter(Album.id != album.id)
            .order_by(Album.release_year.desc(), Album.id.desc())
            .limit(3)
            .all()
        )
        return render_template(
            "albums/detail.html",
            album=album,
            other_albums=other_albums,
        )

    @app.route("/albums/new", methods=["GET", "POST"])
    @login_required
    def album_create():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            artist_credit = request.form.get("artist_credit", "").strip() or "Lyuda Bielousova (Lely45)"
            release_year_raw = request.form.get("release_year", "").strip()
            release_date = request.form.get("release_date", "").strip()
            genre = request.form.get("genre", "").strip() or "Інді-рок / Альтернатива"
            label = request.form.get("label", "").strip()
            duration = request.form.get("duration", "").strip()
            tagline = request.form.get("tagline", "").strip()
            description = request.form.get("description", "").strip()
            streaming_url = request.form.get("streaming_url", "").strip()
            is_featured = request.form.get("is_featured") == "on"

            errors = []
            if not title:
                errors.append("Вкажіть назву альбому.")
            if not release_year_raw.isdigit() or not (1950 <= int(release_year_raw) <= 2100):
                errors.append("Вкажіть коректний рік релізу (наприклад, 2026).")
            if not description:
                errors.append("Додайте опис альбому.")

            tracks_data = _parse_tracks_from_form(request.form)

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "albums/form.html",
                    mode="create",
                    album=None,
                    form_data=request.form,
                    tracks_data=tracks_data,
                    preset_covers=PRESET_COVERS,
                )

            if is_featured:
                Album.query.update({Album.is_featured: False})

            cover_image = _resolve_cover_image(app)
            new_album = Album(
                slug=generate_unique_slug(title),
                title=title,
                artist_credit=artist_credit,
                release_year=int(release_year_raw),
                release_date=release_date or release_year_raw,
                genre=genre,
                label=label or "Independent",
                duration=duration or None,
                cover_image=cover_image,
                tagline=tagline or None,
                description=description,
                streaming_url=streaming_url or None,
                is_featured=is_featured,
                author_id=current_user.id,
            )
            for idx, (t_title, t_duration, t_feat) in enumerate(tracks_data, start=1):
                new_album.tracks.append(
                    Track(
                        track_number=idx,
                        title=t_title,
                        duration=t_duration,
                        featuring=t_feat,
                    )
                )

            db.session.add(new_album)
            db.session.commit()
            flash(f"Альбом «{new_album.title}» успішно додано до дискографії!", "success")
            return redirect(url_for("album_detail", slug=new_album.slug))

        return render_template(
            "albums/form.html",
            mode="create",
            album=None,
            form_data={},
            tracks_data=[("", "", "")],
            preset_covers=PRESET_COVERS,
        )

    @app.route("/albums/<slug>/edit", methods=["GET", "POST"])
    @login_required
    def album_edit(slug: str):
        album = Album.query.filter_by(slug=slug).first_or_404()

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            artist_credit = request.form.get("artist_credit", "").strip() or "Lyuda Bielousova (Lely45)"
            release_year_raw = request.form.get("release_year", "").strip()
            release_date = request.form.get("release_date", "").strip()
            genre = request.form.get("genre", "").strip() or "Інді-рок / Альтернатива"
            label = request.form.get("label", "").strip()
            duration = request.form.get("duration", "").strip()
            tagline = request.form.get("tagline", "").strip()
            description = request.form.get("description", "").strip()
            streaming_url = request.form.get("streaming_url", "").strip()
            is_featured = request.form.get("is_featured") == "on"

            errors = []
            if not title:
                errors.append("Вкажіть назву альбому.")
            if not release_year_raw.isdigit() or not (1950 <= int(release_year_raw) <= 2100):
                errors.append("Вкажіть коректний рік релізу.")
            if not description:
                errors.append("Опис альбому не може бути порожнім.")

            tracks_data = _parse_tracks_from_form(request.form)

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "albums/form.html",
                    mode="edit",
                    album=album,
                    form_data=request.form,
                    tracks_data=tracks_data,
                    preset_covers=PRESET_COVERS,
                )

            if is_featured:
                Album.query.filter(Album.id != album.id).update({Album.is_featured: False})

            if title != album.title:
                album.slug = generate_unique_slug(title, exclude_album_id=album.id)

            album.title = title
            album.artist_credit = artist_credit
            album.release_year = int(release_year_raw)
            album.release_date = release_date or release_year_raw
            album.genre = genre
            album.label = label or "Independent"
            album.duration = duration or None
            album.tagline = tagline or None
            album.description = description
            album.streaming_url = streaming_url or None
            album.is_featured = is_featured
            album.cover_image = _resolve_cover_image(app, existing_cover=album.cover_image)

            # Rebuild tracklist cleanly
            album.tracks.clear()
            db.session.flush()
            for idx, (t_title, t_duration, t_feat) in enumerate(tracks_data, start=1):
                album.tracks.append(
                    Track(
                        track_number=idx,
                        title=t_title,
                        duration=t_duration,
                        featuring=t_feat,
                    )
                )

            db.session.commit()
            flash(f"Зміни в альбомі «{album.title}» збережено!", "success")
            return redirect(url_for("album_detail", slug=album.slug))

        existing_tracks = [
            (t.title, t.duration or "", t.featuring or "") for t in album.tracks
        ] or [("", "", "")]
        return render_template(
            "albums/form.html",
            mode="edit",
            album=album,
            form_data={},
            tracks_data=existing_tracks,
            preset_covers=PRESET_COVERS,
        )

    @app.route("/albums/<slug>/delete", methods=["POST"])
    @login_required
    def album_delete(slug: str):
        album = Album.query.filter_by(slug=slug).first_or_404()
        deleted_title = album.title
        db.session.delete(album)
        db.session.commit()
        flash(f"Альбом «{deleted_title}» видалено з дискографії.", "warning")
        return redirect(url_for("albums_list"))

    # --- Authentication ---

    @app.route("/auth/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            errors = []
            if len(username) < 3 or len(username) > 40:
                errors.append("Логін має містити від 3 до 40 символів.")
            if "@" not in email or "." not in email:
                errors.append("Введіть коректну електронну адресу.")
            if len(password) < 6:
                errors.append("Пароль має містити щонайменше 6 символів.")
            if password != confirm_password:
                errors.append("Паролі не співпадають.")
            if User.query.filter_by(username=username).first():
                errors.append("Користувач із таким логіном уже існує.")
            if User.query.filter_by(email=email).first():
                errors.append("Користувач із таким email уже зареєстрований.")

            if errors:
                for err in errors:
                    flash(err, "danger")
                return render_template(
                    "auth/register.html",
                    username=username,
                    email=email,
                )

            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash(f"Вітаємо, {user.username}! Акаунт створено, тепер ви можете керувати альбомами.", "success")
            return redirect(url_for("albums_list"))

        return render_template("auth/register.html")

    @app.route("/auth/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        if request.method == "POST":
            identifier = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            remember = request.form.get("remember") == "on"

            user = User.query.filter(
                db.or_(
                    User.username == identifier,
                    User.email == identifier.lower(),
                )
            ).first()

            if user and user.check_password(password):
                login_user(user, remember=remember)
                flash(f"Ви увійшли як {user.username}.", "success")
                next_url = request.args.get("next")
                if next_url and next_url.startswith("/"):
                    return redirect(next_url)
                return redirect(url_for("albums_list"))

            flash("Невірний логін або пароль.", "danger")
            return render_template("auth/login.html", identifier=identifier)

        return render_template("auth/login.html")

    @app.route("/auth/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("Ви вийшли з облікового запису.", "info")
        return redirect(url_for("index"))

    # --- Error handlers ---

    @app.errorhandler(404)
    def not_found_error(_error):
        return render_template("error.html", code=404, title="Сторінку не знайдено", message="Схоже, цього треку чи альбому немає у нашому каталозі."), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template("error.html", code=500, title="Помилка сервера", message="Щось пішло не так. Спробуйте оновити сторінку."), 500

    with app.app_context():
        db.create_all()
        seed_database()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
