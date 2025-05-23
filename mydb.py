from models import User, Game, GameInfo, GameDownload, SharedFile, GameStats
from models import db
from datetime import date
from mysecurity import myhash, verify, encode
import uuid
from sqlalchemy.orm import joinedload


def save_to_db(instance):
    db.session.add(instance)
    db.session.commit()

# Юзеры

def post_login(username, password):

    user = User.query.filter_by(username=username).first()
    print(user)

    if not user:
        raise ValueError('Такого аккаунта не существует')

    password = myhash(password)
    if not user.password == password:
        raise ValueError('Пароль не подходит')

    token = encode(username)
    return token

def get_users_all():
    return User.query.all()

def get_users_one(username):
    user = User.query.filter_by(username=username).first()
    return user.anonim() if user else None

def post_register(username, password):

    # Проверки перед отправкой
    if not username or not password:
        raise ValueError("Заполните все поля")
    
    existing_user = User.query.filter_by(username = username).first()
    if existing_user:
        raise ValueError("Аккаунт с таким именем уже существует")
    
    if len(username) < 3:
        raise ValueError("Юзернейм должен быть от 3 символов")
    
    if len(password) < 5:
        raise ValueError("Пароль должен быть от 5 символов")

    password = myhash(password)

    user = User(username = username, password = password)
    save_to_db(user)

    return user


# Приложения

def get_shares_all():
    return Game.query.filter_by(is_archived=False).all()

def get_app_one(link):
    apps = get_shares_all()
    return next((game for game in apps if game.link == link), None)

def get_latest(limit):
    return Game.query\
        .join(GameInfo)\
        .filter(Game.is_archived == False)\
        .order_by(GameInfo.published_at.desc())\
        .limit(limit)\
        .all()

def get_all_apps():
    return [game for game in get_shares_all() if game.game_info and game.game_info.app_type == 'app']

def get_all_games():
    return [game for game in get_shares_all() if game.game_info and game.game_info.app_type == 'game']


def get_app_by_user(username):
    apps = get_shares_all()
    return [apps for game in apps if game.game_info and game.game_info.published_by == username]

# def post_comment(userid, gameid, text):
#     game_comment = GameComment(
#         gameid = gameid,
#         userid = userid,
        
#         text = text,
#     )
#     save_to_db(game_comment)

def post_game(
        title, link, comments_allowed, preview,
        # GameInfo
        description, price, release_date, language, published_by, app_type, category,
        # GameDownload
        file):
    game = Game(
        title=title,
        preview=preview,
        link=link,
        comments_allowed=comments_allowed,
        is_archived=False,
    )
    save_to_db(game)

    game_info = GameInfo(
        game_id=game.id,
        description=description,
        price=price,
        release_date=release_date,
        language=language,
        published_by=published_by,
        app_type=app_type,
        category=category
    )
    save_to_db(game_info)

    print("Game created:", game)
    return game

def get_all_games_with_stats():
    return Game.query.options(joinedload(Game.stats)).all()

def update_game_stats(game_id, serious_fun, utility_gamified):
    game = Game.query.get(game_id)
    if not game:
        return False
    if not game.stats:
        game.stats = GameStats(game_id=game.id)
        db.session.add(game.stats)
    stats = game.stats
    stats.serious_fun = serious_fun
    stats.utility_gamified = utility_gamified
    db.session.commit()
    return True

def create_sample_games():
    sample_data = [
        # Игры
        ("Arma 3", "arma3", 90, 30),
        ("Roblox", "roblox", 60, 50),
        ("Minecraft", "minecraft", 70, 40),
        ("CS:GO", "csgo", 85, 25),
        ("Fortnite", "fortnite", 75, 35),
        ("The Sims 4", "sims4", 55, 60),
        ("GTA V", "gta5", 80, 30),
        ("Factorio", "factorio", 65, 55),
        ("RimWorld", "rimworld", 60, 45),
        ("Kerbal Space Program", "kerbal", 70, 70),

        # Программы
        ("Paint", "paint", 20, 80),
        ("After Effects", "after_effects", 85, 65),
        ("Photoshop", "photoshop", 80, 70),
        ("Notepad++", "notepadpp", 30, 90),
        ("Premiere Pro", "premiere_pro", 75, 60),
        ("Blender", "blender", 85, 75),
        ("Visual Studio Code", "vscode", 60, 85),
        ("FL Studio", "flstudio", 70, 65),
        ("Unity", "unity", 90, 70),
        ("DaVinci Resolve", "davinci_resolve", 75, 60),
    ]

    for title, link, serious_fun, utility_gamified in sample_data:
        game = Game(title=title, link=link)
        db.session.add(game)
        db.session.flush()

        stats = GameStats(
            game_id=game.id,
            serious_fun=serious_fun,
            utility_gamified=utility_gamified
        )
        db.session.add(stats)

    db.session.commit()

def get_download_info(filename):
    game_download = db.session.query(GameDownload).filter_by(file_link=filename).first()
    game = db.session.query(Game).filter_by(id=game_download.game_id).first()

    game_name = game.title
    title = game_download.title
    file_link = game_download.file_link
    extension = '.' + file_link.rsplit('.', 1)[-1]

    if title:
        download_name = game_name + " · " + title + " · apps.lbvo.ru" + extension
    else:
        download_name = game_name + " · apps.lbvo.ru" + extension
    return download_name

def add_game_download(game_id, title, file_link, file_size, order=0):
    game_download = GameDownload(game_id=game_id, title=title, file_link=file_link, file_size=file_size, order=order)
    save_to_db(game_download)

    return game_download

def archive_game(game):
    game.is_archived = True
    print(game.is_archived)
    db.session.commit()

def get_files_all():
    return SharedFile.query.all()

def get_files_one(link):
    file = SharedFile.query.filter_by(link=link).first()
    return file

def post_file(title, preview, file_link, link, uploaded_by):
    shared_file = SharedFile(
        title=title,
        preview=preview,
        file_link=file_link,
        uploaded_by=uploaded_by,
        is_active=True,
        expires=30,
        auto_download=0,
        link=link
        # link="file-" + uuid.uuid4().hex[:10]
    )
    save_to_db(shared_file)

    view_url = f"{shared_file.link}"
    print("File shared:", shared_file)
    return view_url



