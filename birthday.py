from datetime import datetime, time, timedelta, date, timezone
import os, sys

path = os.path.abspath(os.path.dirname(sys.argv[0]))

Role = 905036152552161322
GirlRole = 908038006521348106
Channel = 907899975625768970
Greetings = ['В этот замечательный month2 день отмечает своё age-летие user. Пожелаем sex_d крепкого здоровья, счастья, любви и всего самого самого наилучшего 🥳', 'Сегодня день рождения у user! Желаем sex_d крепкого здоровья, любви, удачи и конечно же денежных stonks 💸',\
'Ровно age years назад появиться_pst на свет user! Поздравим sex_v и пожелаем огромнейшего счастья, крепкого здоровья, вселенского терпения, надежных и верных друзей 🎊', 'До меня дошёл слух, что сегодня день рождения у замечательный_rod user!\nСрочно готовьте торт с age свечкой_fnage или хотя бы age торт_fnage с одной свечкой 🎂',\
'*Happy birthday to you*\n*Happy birthday to yoouuuu...*\nЭта песня посвящается нашему_rod имениннику_rod user, ведь сегодня sex_d исполняется age лет! 🎉']
msk = timezone(offset=timedelta(hours=3), name='МСК')
GirlsGIFs = []
NeutralGIFs = []
birthdays = {}
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

def days_left(birthday):
	today = datetime.now(tz=msk)
	today = date(day=today.day, year=today.year, month=today.month)
	birthday = date(year=today.year, month=birthday.month, day=birthday.day)
	if (birthday - today).days < 0:
		birthday = date(year=today.year + 1, month=birthday.month, day=birthday.day)
	return (birthday - today).days

def load_birthdays():
	with open(path + '/birthday/birthdays.txt') as data:
		for line in data:
			s = line.strip().split()
			t = date(year=int(s[1][:4:]), month=int(s[1][5:7:]), day=int(s[1][8::]))
			birthdays[int(s[0])] = t
	with open(path + '/birthday/girls_gifs.txt') as data:
		for line in data:
			GirlsGIFs.append(line.strip())
	with open(path + '/birthday/neutral_gifs.txt') as data:
		for line in data:
			NeutralGIFs.append(line.strip())

def save_birthdays():
	try:
		with open(path + '/birthday/birthdays.txt', mode='w') as data:
			for member in birthdays.items():
 				data.write(str(member[0]) + ' ' + str(member[1]) + '\n')
	except:
		print('Ошибка при сохранении')

def set_birthday(user_id, dat):
	if len(dat) != 10:
		raise ValueError('Неверный формат даты рождения: длина даты != 10')
	try:
		birthdays[user_id] = date(year=int(dat[:4:]), month=int(dat[5:7:]), day=int(dat[8::]))
		save_birthdays()
	except:
		raise ValueError('Неверный формат даты рождения')

def delete_birthday(user_id):
	birthdays.pop(user_id, 0)
	save_birthdays()

def next_birthdays():
	ans = {k: v for k, v in sorted(birthdays.items(), key=lambda item: days_left(item[1]))}
	for i in ans.keys():
		ans[i] = days_left(ans[i])
	if len(ans) <= 10:
		return ans
	else:
		i = 0
		nans = {}
		for k in ans.keys():
			if i == 10:
				break
			nans[k] = ans[k]
			i += 1
		return nans