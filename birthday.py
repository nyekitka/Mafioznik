from datetime import datetime, time, timedelta, date, timezone
import os, sys

path = os.path.abspath(os.path.dirname(sys.argv[0]))

Greetings = ['В этот замечательный month2 день отмечает своё age-летие user. Пожелаем sex_d крепкого здоровья, счастья, любви и всего самого самого наилучшего 🥳', 'Сегодня день рождения у user! Желаем sex_d крепкого здоровья, любви, удачи и конечно же денежных stonks 💸',\
'Ровно age years назад появиться_pst на свет user! Поздравим sex_v и пожелаем огромнейшего счастья, крепкого здоровья, вселенского терпения, надежных и верных друзей 🎊', 'До меня дошёл слух, что сегодня день рождения у замечательный_rod user!\nСрочно готовьте торт с age свечкой_fnage или хотя бы age торт_fnage с одной свечкой 🎂',\
'*Happy birthday to you*\n*Happy birthday to yoouuuu...*\nЭта песня посвящается нашему_rod имениннику_rod user, ведь сегодня sex_d исполняется age лет! 🎉']
msk = timezone(offset=timedelta(hours=3), name='МСК')
NameOfMonths = {
	1: ['январь', 'январьский'],
	2: ['февраль', 'февральский'],
	3: ['март', 'мартовский'],
	4: ['апрель', 'апрельский'],
	5: ['май', 'майский'],
	6: ['июнь', 'июньский'],
	7: ['июль', 'июльский'],
	8: ['август', 'августовский'],
	9: ['сентябрь', 'сентябрьский'],
	10: ['октябрь', 'октябрьский'],
	11: ['ноябрь', 'ноябрьский'],
	12: ['декабрь', 'декабрьский'],
}

def days_left(bday):
	birthday = date(day = int(bday[1][8::]), month = int(bday[1][5:7:]), year = int(bday[1][:4:]))
	today = datetime.now(tz=msk)
	today = date(day=today.day, year=today.year, month=today.month)
	birthday = date(year=today.year, month=birthday.month, day=birthday.day)
	if (birthday - today).days < 0:
		birthday = date(year=today.year + 1, month=birthday.month, day=birthday.day)
	return (birthday - today).days