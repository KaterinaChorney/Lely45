import re
import tempfile
import unittest
from pathlib import Path

from app import create_app
from config import Config
from models import Album, User, db


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = "test-secret-key"


def extract_csrf_token(html_text: str) -> str:
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html_text)
    if not match:
        raise AssertionError("CSRF token not found in HTML response")
    return match.group(1)


class FlaskLab9TestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test_lely45.db"

        class LocalTestConfig(TestConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
            UPLOAD_FOLDER = str(Path(self.tmpdir.name) / "uploads")

        self.app = create_app(LocalTestConfig)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.tmpdir.cleanup()

    def test_public_pages_render(self):
        for route, expected_text in [
            ("/", "РЕТРОспектива"),
            ("/about", "Про проект"),
            ("/history", "Lyuda Bielousova"),
            ("/albums", "Всі дівчата хороші"),
            ("/albums/retrospektyva-2026", "переслідувати час"),
            ("/albums/retrospektyva-2026", "я люблю тебе музико"),
            ("/auth/login", "Увійти в акаунт"),
            ("/auth/register", "Реєстрація"),
        ]:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed")
            self.assertIn(expected_text, resp.get_data(as_text=True))

    def test_404_page(self):
        resp = self.client.get("/albums/nonexistent-album-xyz")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Сторінку не знайдено", resp.get_data(as_text=True))

    def test_album_crud_requires_authentication(self):
        resp = self.client.get("/albums/new")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/auth/login", resp.headers["Location"])

        resp = self.client.get("/albums/retrospektyva-2026/edit")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/auth/login", resp.headers["Location"])

    def test_register_and_full_album_crud_flow(self):
        # 1. Register new user
        reg_page = self.client.get("/auth/register").get_data(as_text=True)
        token = extract_csrf_token(reg_page)
        resp = self.client.post(
            "/auth/register",
            data={
                "csrf_token": token,
                "username": "tester_lb",
                "email": "tester@example.com",
                "password": "strongpassword",
                "confirm_password": "strongpassword",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Акаунт створено", resp.get_data(as_text=True))

        # 2. Create album with tracks
        new_page = self.client.get("/albums/new").get_data(as_text=True)
        token = extract_csrf_token(new_page)
        resp = self.client.post(
            "/albums/new",
            data={
                "csrf_token": token,
                "title": "Артгаус",
                "artist_credit": "Lely45",
                "release_year": "2022",
                "release_date": "2022",
                "genre": "Арт-рок / Інді",
                "label": "MG Music",
                "duration": "26 хв",
                "tagline": "Концептуальний експеримент 2022 року",
                "description": "Тестовий опис концептуального альбому Артгаус.",
                "cover_preset": "images/cover_koly_sontse.jpg",
                "track_title[]": ["Інтро", "Головна роль"],
                "track_duration[]": ["2:15", "3:40"],
                "track_featuring[]": ["", "feat. Guest"],
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("Артгаус", body)
        self.assertIn("Головна роль", body)
        self.assertIn("feat. Guest", body)

        # 3. Edit album
        edit_page = self.client.get("/albums/arthaus/edit").get_data(as_text=True)
        token = extract_csrf_token(edit_page)
        resp = self.client.post(
            "/albums/arthaus/edit",
            data={
                "csrf_token": token,
                "title": "Артгаус (Deluxe)",
                "artist_credit": "Lely45",
                "release_year": "2022",
                "release_date": "2022",
                "genre": "Арт-рок",
                "label": "MG Music",
                "duration": "29 хв",
                "tagline": "Оновлене видання",
                "description": "Оновлений опис альбому.",
                "cover_preset": "images/cover_chornyi_lebid.jpg",
                "track_title[]": ["Інтро", "Головна роль", "Фінал"],
                "track_duration[]": ["2:15", "3:40", "3:10"],
                "track_featuring[]": ["", "", ""],
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("Артгаус (Deluxe)", body)
        self.assertIn("Фінал", body)

        # 4. Delete album
        token = extract_csrf_token(body)
        resp = self.client.post(
            "/albums/arthaus-deluxe/delete",
            data={"csrf_token": token},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("видалено з дискографії", resp.get_data(as_text=True))

        with self.app.app_context():
            self.assertIsNone(Album.query.filter_by(slug="arthaus-deluxe").first())

    def test_seeded_admin_login_and_search(self):
        login_page = self.client.get("/auth/login").get_data(as_text=True)
        token = extract_csrf_token(login_page)
        resp = self.client.post(
            "/auth/login",
            data={
                "csrf_token": token,
                "username": "admin",
                "password": "lely45admin",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Ви увійшли як admin", resp.get_data(as_text=True))

        search_resp = self.client.get("/albums?year=2026")
        self.assertEqual(search_resp.status_code, 200)
        html = search_resp.get_data(as_text=True)
        self.assertIn("РЕТРОспектива", html)
        self.assertNotIn("Чорний лебідь", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)

