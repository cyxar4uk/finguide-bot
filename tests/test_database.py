import asyncio

from database.models import Database


def run(coro):
    return asyncio.run(coro)


def test_user_profile_roundtrip(tmp_path):
    async def scenario():
        db = Database(str(tmp_path / "t.db"))
        await db.connect()
        assert await db.get_user(1) is None
        await db.create_user(1, "name", "Имя")
        await db.update_user_profile(1, "Финансовый факультет", 2)
        user = await db.get_user(1)
        await db.close()
        return user

    user = run(scenario())
    assert user["faculty"] == "Финансовый факультет" and user["course"] == 2


def test_faq_personalization_filter(tmp_path):
    async def scenario():
        db = Database(str(tmp_path / "t.db"))
        await db.connect()
        await db.add_faq("Общий", "a")
        await db.add_faq("Только ИТ", "b", faculty="ИТ")
        await db.add_faq("Только 3 курс", "c", course=3)
        mine = await db.search_faq("", faculty="ИТ", course=1)
        other = await db.search_faq("", faculty="Юр", course=3)
        await db.close()
        return mine, other

    mine, other = run(scenario())
    assert {r[0] for r in mine} == {"Общий", "Только ИТ"}
    assert {r[0] for r in other} == {"Общий", "Только 3 курс"}


def test_contacts_by_category(tmp_path):
    async def scenario():
        db = Database(str(tmp_path / "t.db"))
        await db.connect()
        await db.add_contact("Библиотека", category="Библиотека", phone="1")
        await db.add_contact("Деканат", category="Деканат")
        lib = await db.get_contacts("Библиотека")
        everything = await db.get_contacts()
        await db.close()
        return lib, everything

    lib, everything = run(scenario())
    assert [c["service_name"] for c in lib] == ["Библиотека"]
    assert len(everything) == 2


def test_seed_script_populates_db(tmp_path, monkeypatch):
    import seed_data

    path = tmp_path / "seed.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    run(seed_data.seed_database())

    async def count():
        db = Database(str(path))
        await db.connect()
        faq, contacts = await db.search_faq(""), await db.get_contacts()
        await db.close()
        return len(faq), len(contacts)

    faq, contacts = run(count())
    assert faq >= 10 and contacts >= 5
