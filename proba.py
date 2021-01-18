import peewee
import datetime

# Создадим новую БД, для подключения будем использовать SQLite
database = peewee.SqliteDatabase('external_data/music.db')


class BaseTable(peewee.Model):
    # В подклассе Meta указываем подключение к той или иной базе данных
    class Meta:
        database = database


# Чтобы создать таблицу в нашей БД, нам нужно создать класс
class Artist(BaseTable):
    name = peewee.CharField()  # от типа столбца зависит тип данных, который мы сможем в него записать


class Album(BaseTable):
    artist = peewee.ForeignKeyField(Artist)
    title = peewee.CharField()
    release_date = peewee.DateTimeField()
    publisher = peewee.CharField()
    media_type = peewee.CharField()


# Создание таблиц:
database.create_tables([Artist, Album])

# Запись данных в таблицы:
# Один способ с явным save()
new_artist = Artist(name='Newsboys')
new_artist.save()
# Второй способ без явного save()
album_one = Album.create(
    artist=new_artist,
    title='Read All About It',
    release_date=datetime.date(1988, 12, 1),
    publisher='Refuge',
    media_type='CD',
)
