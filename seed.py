import re
from sqlalchemy.exc import IntegrityError

from models import Album, Track, User, db

TRANSLIT_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
    "є": "ye", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "yi", "й": "y",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ь": "", "ю": "yu", "я": "ya", "ё": "yo", "э": "e",
    "ы": "y", "ъ": "",
}


def slugify(text: str) -> str:
    """Create a URL-friendly ASCII slug from Ukrainian or Latin album titles."""
    lowered = text.lower().strip()
    transliterated = "".join(TRANSLIT_MAP.get(ch, ch) for ch in lowered)
    cleaned = re.sub(r"[^a-z0-9]+", "-", transliterated).strip("-")
    return cleaned or "album"


def generate_unique_slug(title: str, exclude_album_id: int | None = None) -> str:
    base_slug = slugify(title)
    candidate = base_slug
    counter = 2
    while True:
        existing = Album.query.filter_by(slug=candidate).first()
        if not existing or (exclude_album_id and existing.id == exclude_album_id):
            return candidate
        candidate = f"{base_slug}-{counter}"
        counter += 1


INITIAL_ALBUMS = [
    {
        "slug": "retrospektyva-2026",
        "title": "РЕТРОспектива",
        "artist_credit": "Lyuda Bielousova (ex-Lely45)",
        "release_year": 2026,
        "release_date": "30 жовтня 2026",
        "genre": "Альтернативний рок / Інді-поп / Пост-бард",
        "label": "Lyuda Bielousova Music",
        "duration": "32 хв 08 с",
        "cover_image": "images/cover_retrospektyva.jpg",
        "tagline": "Перша повноформатна платівка під власним ім'ям — чесна розмова про час, пам'ять, дорослішання і любов до музики.",
        "description": (
            "«РЕТРОспектива» (2026) — знакова робота Людмили Бєлоусової та перший великий альбом, "
            "виданий після прощання зі сценічним псевдонімом Lely45. Десять композицій складаються у цілісну "
            "кінематографічну історію про те, як минуле проростає крізь сьогодення.\n\n"
            "У звучанні поєднано теплий аналоговий рок-н-рол, оголені гітарні рифи, пронизливий вокальний надрив "
            "та інтимну сповідальність. Від тривожної відкривачки «переслідувати час» до фінального зізнання "
            "«я люблю тебе музико» — платівка фіксує момент внутрішньої свободи й повернення до самої себе."
        ),
        "streaming_url": "https://music.apple.com/",
        "is_featured": True,
        "tracks": [
            ("переслідувати час", "3:30", None),
            ("на одній зі старих планет", "3:25", None),
            ("посередній Бог", "3:10", None),
            ("останній вистріл", "3:20", None),
            ("рок-н-рол", "2:32", None),
            ("у наступному житті", "3:05", None),
            ("мила весно", "3:29", None),
            ("так любиш", "3:22", None),
            ("середній палець", "3:24", None),
            ("я люблю тебе музико", "2:55", None),
        ],
    },
    {
        "slug": "nevdyachna-hlyadachka",
        "title": "Невдячна глядачка",
        "artist_credit": "Lyuda Bielousova (Lely45)",
        "release_year": 2024,
        "release_date": "3 грудня 2024",
        "genre": "Інді-рок / Альтернативний поп",
        "label": "Money Gun",
        "duration": "24 хв 34 с",
        "cover_image": "images/cover_nevdjachna_hljadachka.jpg",
        "tagline": "Відверта та гостра платівка про втрату ілюзій, дорослішання і сміливість дивитися правді в очі.",
        "description": (
            "«Невдячна глядачка» — студійний альбом Lely45, що вийшов у грудні 2024 року на лейблі Money Gun. "
            "Вісім композицій поєднують фірмовий емоційний надрив, гостру самоіронію та безкомпромісну щирість.\n\n"
            "Серед ключових треків — пронизливі «Бинтуй», «Де моя молодість?», фінальна «Я святкую свій похорон» "
            "та спільна робота з Женею Галичем «Усе ж таки друзі»."
        ),
        "streaming_url": "https://open.spotify.com/album/6WET3pEZ3hniBwvYfBPvZ3?si=Xl6iB2tSTAuCRJvZUcs51Q",
        "is_featured": False,
        "tracks": [
            ("Бинтуй", "3:13", None),
            ("Кого ти вигадав?", "3:06", None),
            ("Усе ж таки друзі", "2:36", "feat. Женя Галич"),
            ("Матриця", "2:44", None),
            ("А якщо чесно", "3:51", None),
            ("Де моя молодість?", "3:04", None),
            ("Intermezzo", "2:59", None),
            ("Я святкую свій похорон", "2:58", None),
        ],
    },
    {
        "slug": "vsi-divchata-khoroshi-2023",
        "title": "Всі дівчата хороші",
        "artist_credit": "Lely45",
        "release_year": 2023,
        "release_date": "2023",
        "genre": "Інді-рок / Постпанк / Альтернатива",
        "label": "MG Music",
        "duration": "31 хв 15 с",
        "cover_image": "images/cover_vsi_divchata.jpg",
        "tagline": "Номінант премії Megogo Music Awards 2023 у категорії «Альбом року» — гіркий і щирий портрет великого міста.",
        "description": (
            "«Всі дівчата хороші» — один із найгучніших релізів епохи Lely45, який закріпив за виконавицею "
            "статус голосу нового покоління української інді-сцени. Альбом балансує між нічними київськими "
            "магістралями, бунтарським сарказмом і глибокою вразливістю.\n\n"
            "Особливе місце в релізі посідає композиція «Автомагістралі», а також камерні й водночас вибухові "
            "треки «Дівчинка із Київського гетто» та «Місто. Музика»."
        ),
        "streaming_url": "https://open.spotify.com/",
        "is_featured": False,
        "tracks": [
            ("Всі дівчата хороші", "3:08", None),
            ("Автомагістралі", "3:19", "feat. SadSvit"),
            ("Дівчинка із Київського гетто", "2:54", None),
            ("Тісно", "3:11", None),
            ("Маленький принц", "3:26", None),
            ("Місто. Музика", "2:58", None),
            ("А може?", "3:04", None),
            ("Габарити", "2:49", None),
            ("І кожен дасть мені своє ім'я", "3:20", None),
            ("До побачення", "3:06", None),
        ],
    },
    {
        "slug": "chornyi-lebid-2023",
        "title": "Чорний лебідь",
        "artist_credit": "Lely45",
        "release_year": 2023,
        "release_date": "2023",
        "genre": "Дарк-поп / Альтернативний рок",
        "label": "MG Music",
        "duration": "24 хв 40 с",
        "cover_image": "images/cover_chornyi_lebid.jpg",
        "tagline": "Театральний драматизм, холодний нерв і безкомпромісна відвертість у восьми темних історіях.",
        "description": (
            "«Чорний лебідь» розкриває режисерський бекграунд Людмили Бєлоусової: кожен трек тут звучить "
            "як окрема сцена камерної вистави. Мінімалістичні, але напружені аранжування підкреслюють "
            "харизматичний вокал із характерною хрипотцею.\n\n"
            "Композиції «Дай мені шанс», «На люстрі» та «Спробуй купи мене» говорять про межі власної гідності, "
            "емоційне вигорання й силу залишатися собою всупереч чужим очікуванням."
        ),
        "streaming_url": "https://open.spotify.com/",
        "is_featured": False,
        "tracks": [
            ("Дай мені шанс", "3:12", None),
            ("На люстрі", "2:58", None),
            ("Бережи", "3:15", None),
            ("Хто ти дівчинко?", "3:04", None),
            ("Спробуй купи мене", "2:52", None),
            ("Давай, дивись", "3:01", None),
            ("Буде холодно", "3:22", None),
            ("Інфаркт", "2:56", None),
        ],
    },
    {
        "slug": "artkhaus-2022",
        "title": "Артхаус",
        "artist_credit": "Lely45",
        "release_year": 2022,
        "release_date": "14 жовтня 2022",
        "genre": "Інді-поп / Альтернативний рок",
        "label": "Money Gun",
        "duration": "30 хв 12 с",
        "cover_image": "images/cover_arthouse.jpg",
        "tagline": "Концептуальний україномовний альбом-сповідь, побудований як цілісне кіно від Intro до Outro.",
        "description": (
            "«Артхаус» (2022) — один із найглибших концептуальних релізів Lely45, випущений у жовтні 2022 року "
            "на лейблі Money Gun. У ньому відчутний театральний і режисерський бекграунд Людмили Бєлоусової: "
            "десять треків розгортаються як послідовні сцени від «Публічна самотність (Intro)» до «Доля (Outro)».\n\n"
            "Альбом досліджує внутрішні суперечності, пошук опори в темряві та вразливість людини на тлі "
            "буремного часу («Навпомацки», «Мамо, я вплуталась», «Чорне з білим», «У рваних дротах»)."
        ),
        "streaming_url": "https://music.apple.com/",
        "is_featured": False,
        "tracks": [
            ("Публічна самотність (Intro)", "2:45", None),
            ("Навпомацки", "3:08", None),
            ("Мамо, я вплуталась", "3:15", None),
            ("Дощ", "2:58", None),
            ("Лиши мене саму", "3:12", None),
            ("Мене ноги несуть", "3:04", None),
            ("Чорне з білим", "3:19", None),
            ("Вилікуй", "3:06", None),
            ("У рваних дротах", "2:54", None),
            ("Доля (Outro)", "2:31", None),
        ],
    },
    {
        "slug": "trudnoshchi-perekladu-2022",
        "title": "Труднощі перекладу",
        "artist_credit": "Lely45",
        "release_year": 2022,
        "release_date": "30 серпня 2022",
        "genre": "Інді-поп / Альтернативний рок",
        "label": "Money Gun",
        "duration": "27 хв 45 с",
        "cover_image": "images/cover_trudnoshchi_perekladu.jpg",
        "tagline": "Головні ранні хіти Lely45, переосмислені та перекладені українською мовою у 2022 році.",
        "description": (
            "«Труднощі перекладу» — знаковий реліз серпня 2022 року, у якому Людмила Бєлоусова подарувала нове "
            "україномовне життя своїм найвідомішим раннім пісням. Замість буквального перекладу артистка переписала "
            "тексти так, щоб вони зберегли первісний емоційний нерв і водночас органічно зазвучали українською.\n\n"
            "До платівки увійшли культові композиції «Вісім», «Біля гори», «Моя душа» та «Ромашки», які стали "
            "частиною переходу виконавиці до повністю україномовного репертуару."
        ),
        "streaming_url": "https://music.apple.com/",
        "is_featured": False,
        "tracks": [
            ("Вісім", "3:02", None),
            ("Біля гори", "3:10", None),
            ("Ромашки", "2:56", None),
            ("Цілуй мене", "3:08", None),
            ("Ти не пишеш листи", "3:12", None),
            ("Розганяю тьму", "3:05", None),
            ("Навперекосяк", "2:58", None),
            ("Моя душа", "3:14", None),
            ("Гладіолуси", "3:00", None),
        ],
    },
    {
        "slug": "koly-sontse-sidaye-za-skhyl-2022",
        "title": "Коли сонце сідає за схил",
        "artist_credit": "Lely45",
        "release_year": 2022,
        "release_date": "2022",
        "genre": "Інді-поп / Альтернативна балада",
        "label": "MG Music",
        "duration": "28 хв 50 с",
        "cover_image": "images/cover_koly_sontse.jpg",
        "tagline": "Перший повноформатний україномовний альбом — про пам'ять, вразливість і світло у темні часи.",
        "description": (
            "«Коли сонце сідає за схил» став переломним моментом у творчості Lely45 — першим великим "
            "україномовним альбомом, записаним на тлі повномасштабної війни. Платівка сповнена щемливої "
            "лірики, образів Києва у сутінках і тихої внутрішньої стійкості.\n\n"
            "До альбому увійшли знакові треки «Місто залите вогнями», «Світ мене ловив» та заголовна "
            "композиція «Коли сонце сідає за схил», які миттєво відгукнулися слухачам по всій країні."
        ),
        "streaming_url": "https://music.apple.com/",
        "is_featured": False,
        "tracks": [
            ("Місто залите вогнями", "3:18", None),
            ("Друже", "3:09", None),
            ("Світ мене ловив", "3:24", None),
            ("Війна", "3:32", None),
            ("Залиш мені трохи пам'яті", "3:14", None),
            ("Спи собі сама", "3:05", None),
            ("Я впускаю твій біль", "3:11", None),
            ("Коли сонце сідає за схил", "3:19", None),
            ("Холодно", "2:38", None),
        ],
    },
]


def seed_database() -> None:
    """Create default admin account and seed initial Lely45 / Lyuda Bielousova albums if empty."""
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@lely45.ua",
            is_admin=True,
        )
        admin.set_password("lely45admin")
        db.session.add(admin)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            admin = User.query.filter_by(username="admin").first()

    if Album.query.count() == 0:
        for album_data in INITIAL_ALBUMS:
            album = Album(
                slug=album_data["slug"],
                title=album_data["title"],
                artist_credit=album_data["artist_credit"],
                release_year=album_data["release_year"],
                release_date=album_data["release_date"],
                genre=album_data["genre"],
                label=album_data["label"],
                duration=album_data["duration"],
                cover_image=album_data["cover_image"],
                tagline=album_data["tagline"],
                description=album_data["description"],
                streaming_url=album_data["streaming_url"],
                is_featured=album_data["is_featured"],
                author_id=admin.id if admin else None,
            )
            for idx, (track_title, track_duration, feat) in enumerate(
                album_data["tracks"], start=1
            ):
                album.tracks.append(
                    Track(
                        track_number=idx,
                        title=track_title,
                        duration=track_duration,
                        featuring=feat,
                    )
                )
            db.session.add(album)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
