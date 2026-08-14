"""Seed data for the Azerbaijan location catalog (LocationPlace).

Covers all major cities/regions of Azerbaijan plus Baku's districts,
settlements, metro stations and popular landmarks. Load with:

    python -m app.services.location_seed
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import func, select

import app.models  # noqa: F401  (register all ORM models)
from app.db.session import async_session_factory as session_factory
from app.models.location import LocationPlace

# (name, latitude, longitude) — approximate city centres.
CITIES = [
    ("Bakı", 40.4093, 49.8671),
    ("Gəncə", 40.6828, 46.3606),
    ("Sumqayıt", 40.5855, 49.6317),
    ("Mingəçevir", 40.77, 47.0489),
    ("Şirvan", 39.9319, 48.9204),
    ("Şəki", 41.1975, 47.1706),
    ("Lənkəran", 38.7529, 48.8512),
    ("Quba", 41.3611, 48.5133),
    ("Qusar", 41.4275, 48.4379),
    ("Xaçmaz", 41.4645, 48.8058),
    ("Şamaxı", 40.6314, 48.6422),
    ("Ağsu", 40.5691, 48.4009),
    ("Göyçay", 40.6506, 47.7406),
    ("Ucar", 40.5189, 47.6542),
    ("Zərdab", 40.2198, 47.7083),
    ("Kürdəmir", 40.3453, 48.1636),
    ("İmişli", 39.8704, 48.0595),
    ("Saatlı", 39.9312, 48.3692),
    ("Sabirabad", 40.0124, 48.4774),
    ("Hacıqabul", 40.0399, 48.9208),
    ("Salyan", 39.5962, 48.9849),
    ("Neftçala", 39.3557, 49.247),
    ("Masallı", 39.0354, 48.6656),
    ("Yardımlı", 38.9074, 48.2406),
    ("Lerik", 38.7754, 48.4152),
    ("Astara", 38.456, 48.8782),
    ("Cəlilabad", 39.2096, 48.4919),
    ("Biləsuvar", 39.4583, 48.5456),
    ("Cəbrayıl", 39.4, 47.0261),
    ("Füzuli", 39.6009, 47.1452),
    ("Ağdam", 39.993, 46.9291),
    ("Bərdə", 40.3747, 47.1266),
    ("Tərtər", 40.3417, 46.9291),
    ("Ağcabədi", 40.0503, 47.4616),
    ("Beyləqan", 39.7755, 47.6191),
    ("Xocavənd", 39.7952, 47.1133),
    ("Şuşa", 39.7601, 46.7496),
    ("Kəlbəcər", 40.1072, 46.0389),
    ("Laçın", 39.6384, 46.5503),
    ("Qubadlı", 39.3441, 46.5816),
    ("Zəngilan", 39.0649, 46.5557),
    ("Göygöl", 40.5866, 46.3188),
    ("Daşkəsən", 40.4937, 46.0803),
    ("Gədəbəy", 40.5656, 45.8162),
    ("Tovuz", 40.9926, 45.6295),
    ("Şəmkir", 40.8297, 46.0188),
    ("Samux", 40.7648, 46.4102),
    ("Qazax", 41.0925, 45.3661),
    ("Ağstafa", 41.1171, 45.455),
    ("Balakən", 41.726, 46.4047),
    ("Zaqatala", 41.6336, 46.6432),
    ("Qax", 41.4225, 46.9243),
    ("Şabran", 41.1967, 48.9865),
    ("Siyəzən", 41.0774, 49.1124),
    ("Xızı", 40.9085, 49.0733),
    ("Abşeron", 40.4429, 49.4714),
    ("İsmayıllı", 40.789, 48.1512),
    ("Oğuz", 41.0714, 47.4654),
    ("Qəbələ", 40.9814, 47.8459),
    ("Naxçıvan", 39.2089, 45.4122),
    ("Ordubad", 38.9082, 46.0234),
    ("Culfa", 38.9537, 45.6306),
    ("Babək", 39.1523, 45.4425),
    ("Şərur", 39.5549, 44.9834),
    ("Şahbuz", 39.4099, 45.5734),
    ("Xankəndi", 39.8264, 46.7667),
]

# Baku administrative districts.
BAKU_DISTRICTS = [
    "Binəqədi",
    "Qaradağ",
    "Xətai",
    "Xəzər",
    "Nərimanov",
    "Nəsimi",
    "Nizami",
    "Pirallahı",
    "Sabail",
    "Sabunçu",
    "Suraxanı",
    "Yasamal",
]

# (name, city, district) — Baku settlements (qəsəbə).
BAKU_SETTLEMENTS = [
    ("Əmircan", "Bakı", "Suraxanı"),
    ("Buzovna", "Bakı", "Xəzər"),
    ("Mərdəkan", "Bakı", "Xəzər"),
    ("Şüvəlan", "Bakı", "Xəzər"),
    ("Qala", "Bakı", "Xəzər"),
    ("Zirə", "Bakı", "Xəzər"),
    ("Türkan", "Bakı", "Xəzər"),
    ("Hövsan", "Bakı", "Suraxanı"),
    ("Binə", "Bakı", "Xəzər"),
    ("Balaxanı", "Bakı", "Sabunçu"),
    ("Maştağa", "Bakı", "Sabunçu"),
    ("Kürdəxanı", "Bakı", "Sabunçu"),
    ("Qaraçuxur", "Bakı", "Suraxanı"),
    ("Bakıxanov", "Bakı", "Suraxanı"),
    ("Rəsulzadə", "Bakı", "Binəqədi"),
    ("Əhmədli", "Bakı", "Xətai"),
    ("Xocəsən", "Bakı", "Binəqədi"),
    ("Lökbatan", "Bakı", "Qaradağ"),
    ("Qobustan", "Bakı", "Qaradağ"),
    ("Badamdar", "Bakı", "Səbail"),
    ("Sulutəpə", "Bakı", "Qaradağ"),
    ("Günəşli", "Bakı", "Suraxanı"),
    ("Yeni Günəşli", "Bakı", "Suraxanı"),
    ("Sahil", "Bakı", "Qaradağ"),
    ("20-ci sahə", "Bakı", "Nizami"),
    ("25-ci sahə", "Bakı", "Nizami"),
    ("8-ci kilometr", "Bakı", "Sabunçu"),
    ("Bülbülə", "Bakı", "Sabunçu"),
    ("Zabrat", "Bakı", "Sabunçu"),
    ("Yeni Suraxanı", "Bakı", "Suraxanı"),
    ("Həzi Aslanov", "Bakı", "Suraxanı"),
    ("Xırdalan", "Abşeron", None),
    ("Masazır", "Abşeron", None),
    ("Saray", "Abşeron", None),
    ("Ceyranbatan", "Abşeron", None),
    ("Digah", "Abşeron", None),
    ("Pirəkəşkül", "Abşeron", None),
    ("Hökməli", "Abşeron", None),
]

# (name, city, latitude, longitude)
BAKU_METROS = [
    ("İçərişəhər", "Bakı", 40.366, 49.832),
    ("Sahil", "Bakı", 40.3751, 49.8511),
    ("28 May", "Bakı", 40.3796, 49.8492),
    ("Gənclik", "Bakı", 40.3966, 49.8528),
    ("Nəriman Nərimanov", "Bakı", 40.4025, 49.8726),
    ("Ulduz", "Bakı", 40.4041, 49.8845),
    ("Koroğlu", "Bakı", 40.4136, 49.9039),
    ("Qara Qarayev", "Bakı", 40.4182, 49.9205),
    ("Neftçilər", "Bakı", 40.4166, 49.9461),
    ("Xalqlar Dostluğu", "Bakı", 40.4163, 49.9686),
    ("Əhmədli", "Bakı", 40.4149, 49.9763),
    ("Həzi Aslanov", "Bakı", 40.413, 49.9879),
    ("Bakmil", "Bakı", 40.4068, 49.8964),
    ("Nizami Gəncəvi", "Bakı", 40.3771, 49.8345),
    ("Elmlər Akademiyası", "Bakı", 40.3728, 49.8118),
    ("İnşaatçılar", "Bakı", 40.3684, 49.7973),
    ("20 Yanvar", "Bakı", 40.381, 49.8069),
    ("Memar Əcəmi", "Bakı", 40.3943, 49.8169),
    ("Cəfər Cabbarlı", "Bakı", 40.3798, 49.8587),
    ("Xətai", "Bakı", 40.3809, 49.8688),
    ("Avtovağzal", "Bakı", 40.3996, 49.8276),
    ("8 Noyabr", "Bakı", 40.4054, 49.8067),
    ("Memar Əcəmi-2", "Bakı", 40.3921, 49.8202),
    ("Mehdi Hüseynzadə", "Bakı", 40.3611, 49.8232),
    ("Şah İsmail Xətai", "Bakı", 40.3616, 49.8347),
]

# (name, district, latitude, longitude) — Baku landmarks.
BAKU_LANDMARKS = [
    ("28 Mall", "Nərimanov", 40.3852, 49.8516),
    ("Gənclik Mall", "Nərimanov", 40.4007, 49.8542),
    ("Port Baku", "Səbail", 40.3748, 49.8462),
    ("Ağ Şəhər", "Yasamal", 40.3699, 49.8257),
    ("Tibb Universiteti", "Nəsimi", 40.3828, 49.8094),
    ("Elmlər Akademiyası", "Nəsimi", 40.3728, 49.8118),
    ("Sea Breeze", "Xəzər", 40.4811, 50.2307),
    ("MIDA Yasamal", "Yasamal", 40.3765, 49.7955),
    ("Deniz Mall", "Səbail", 40.3635, 49.8525),
    ("Park Bulvar", "Səbail", 40.365, 49.851),
    ("Gənclik Parkı", "Nərimanov", 40.3938, 49.8553),
    ("Dənizkənarı Milli Park", "Səbail", 40.3603, 49.8387),
    ("Qız Qalası", "Səbail", 40.3665, 49.8373),
    ("İçərişəhər", "Səbail", 40.3662, 49.8347),
    ("Heydər Əliyev Mərkəzi", "Binəqədi", 40.3958, 49.8687),
    ("Nizami Kino Mərkəzi", "Nəsimi", 40.3794, 49.8434),
    ("Təzə Bazar", "Səbail", 40.3692, 49.8297),
    ("Bazar-90", "Xətai", 40.3712, 49.8652),
    ("Grand Plaza", "Nərimanov", 40.3934, 49.8389),
    ("Baku City Walk", "Səbail", 40.3746, 49.8459),
    ("Baku Crystal Hall", "Səbail", 40.3441, 49.8539),
    ("Bakı Ağ Şəhər Parkı", "Yasamal", 40.3692, 49.8201),
    ("Fəvvarələr Meydanı", "Səbail", 40.3686, 49.8312),
    ("Nizami küçəsi", "Səbail", 40.373, 49.8398),
    ("Azadlıq prospekti", "Nərimanov", 40.3887, 49.8584),
    ("Bakı Dövlət Universiteti", "Səbail", 40.3732, 49.8115),
    ("Azərbaycan Dövlət İqtisad Universiteti", "Səbail", 40.3711, 49.8395),
    ("Dəniz Gəmiçilik Akademiyası", "Nəsimi", 40.3763, 49.8175),
    ("Narimanov Bazarı", "Nərimanov", 40.405, 49.8727),
    ("Gənclik bazarı", "Nərimanov", 40.3977, 49.8517),
    ("Mərkəzi Univermağ", "Nəsimi", 40.3776, 49.8508),
    ("Azerbaijan Plaza", "Səbail", 40.3758, 49.8469),
    ("Mall Baku", "Nəsimi", 40.3827, 49.8465),
    ("Digesta Plaza", "Yasamal", 40.3749, 49.8026),
    ("Beş Mərtəbə", "Nəsimi", 40.3857, 49.8428),
    ("Təzə Şəhər", "Nərimanov", 40.3902, 49.8399),
    ("Xalq Bank Binası", "Nəsimi", 40.3783, 49.8525),
    ("Mehdi Hüseyn küçəsi", "Nəsimi", 40.3752, 49.8281),
    ("Səməd Vurğun bağı", "Səbail", 40.3651, 49.8274),
    ("İsmailiyyə Sarayı", "Səbail", 40.3697, 49.8345),
]

# Major districts of other cities (name, city).
OTHER_DISTRICTS = [
    ("Kəpəz", "Gəncə"),
    ("Nizami Gəncə", "Gəncə"),
    ("Xətai Gəncə", "Gəncə"),
    ("Sumqayıt mərkəz", "Sumqayıt"),
    ("Corat", "Sumqayıt"),
    ("Hacı Zeynalabdin", "Sumqayıt"),
    ("Şəki mərkəz", "Şəki"),
    ("Aşağı Şəki", "Şəki"),
    ("Lənkəran mərkəz", "Lənkəran"),
    ("Quba mərkəz", "Quba"),
    ("Naxçıvan şəhər", "Naxçıvan"),
]

# (name, city, latitude, longitude) — metro stations of Sumqayıt.
SUMQAYIT_METROS = [
    ("Sumqayıt-1", "Sumqayıt", 40.5909, 49.6679),
    ("Sumqayıt-2", "Sumqayıt", 40.5784, 49.6508),
]


def _slugify(value: str) -> str:
    normalized = (
        value.lower()
        .replace("ə", "e")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ç", "c")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("ı", "i")
    )
    out = []
    for ch in normalized:
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "/", "&"):
            out.append("-")
    return "".join(out).strip("-") or "place"


def build_seed() -> list[LocationPlace]:
    places: list[LocationPlace] = []
    seen: set[tuple[str, str]] = set()

    def add(
        kind: str,
        name: str,
        city: str | None,
        district: str | None,
        metro: str | None,
        lat: float | None,
        lng: float | None,
        sort: int = 0,
    ) -> None:
        slug = _slugify(name)
        key = (kind, slug)
        if key in seen:
            return
        seen.add(key)
        places.append(
            LocationPlace(
                id=uuid.uuid4(),
                kind=kind,
                name_az=name,
                slug=slug,
                city=city,
                district=district,
                metro=metro,
                latitude=lat,
                longitude=lng,
                is_active=True,
                sort_order=sort,
            )
        )

    for i, (name, lat, lng) in enumerate(CITIES):
        add("city", name, None, None, None, lat, lng, sort=i)

    for i, name in enumerate(BAKU_DISTRICTS):
        add("district", name, "Bakı", None, None, None, None, sort=i)

    for i, (name, city, district) in enumerate(BAKU_SETTLEMENTS):
        add("settlement", name, city, district, None, None, None, sort=i)

    for i, (name, city, lat, lng) in enumerate(BAKU_METROS):
        add("metro", name, city, None, None, lat, lng, sort=i)

    for i, (name, city, lat, lng) in enumerate(SUMQAYIT_METROS):
        add("metro", name, city, None, None, lat, lng, sort=i)

    for i, (name, district, lat, lng) in enumerate(BAKU_LANDMARKS):
        add("landmark", name, "Bakı", district, None, lat, lng, sort=i)

    for i, (name, city) in enumerate(OTHER_DISTRICTS):
        add("district", name, city, None, None, None, None, sort=i)

    return places


async def seed() -> int:
    async with session_factory() as session:
        count = (
            await session.execute(select(func.count(LocationPlace.id)))
        ).scalar_one()
        if count:
            print(f"Location catalog already seeded ({count} places); skipping.")
            return 0
        places = build_seed()
        session.add_all(places)
        await session.commit()
        print(f"Seeded {len(places)} location places.")
        return len(places)


if __name__ == "__main__":
    asyncio.run(seed())
