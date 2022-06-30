import discord
from discord import utils
from discord.utils import get
from discord.ext import commands, tasks
import os, sys, asyncio
import get_roles, stats, birthday
from datetime import datetime, time, timedelta, date, timezone
from random import randint
import pymorphy2
import sqlite3

intents = discord.Intents.default()
intents.members = True
msk = timezone(offset=timedelta(hours=3), name='МСК')
bot = commands.Bot(command_prefix='!', intents=intents)
morph = pymorphy2.MorphAnalyzer()
connection = sqlite3.connect('database.db')
cursor = connection.cursor()


Members = []
bot.remove_command('help')
ValentineCards = {}
Senders = []
EventProcessing = False

def transform(wor, mode, person=None):
	morph = pymorphy2.MorphAnalyzer()
	p = morph.parse(wor)[0]
	if mode == 'i':
		return p.inflect({'nomn'}).word
	elif mode == 'r':
		return p.inflect({'gent'}).word
	elif mode == 'd':
		return p.inflect({'datv'}).word
	elif mode == 'v':
		return p.inflect({'accs'}).word
	elif mode == 't':
		return p.inflect({'ablt'}).word
	elif mode == 'p':
		return p.inflect({'loct'}).word
	elif mode == 'pst':
		return p.inflect({'past'}).word
	elif mode == 'zhen':
		return p.inflect({'femn'}).word
	elif mode == 'muzh':
		return p.inflect({'муж'}).word
	elif mode.startswith('fn'):
		return p.make_agree_with_number(int(mode[2::])).word
	return ''

def get_nick(member:discord.Member):
	if member.nick == None:
		return member.name
	else:
		return member.nick


@tasks.loop(hours=24)
async def called_once_a_day():
	print('Ежедневная проверка событий: {0}'.format(str(datetime.now(tz=msk))))
	today = datetime.now(tz=msk)
	bdrole = utils.get(Members[0].guild.roles, id=birthday.Role)
	for line in birthday.birthdays.items():
		if line[1].day == (today - timedelta(days=1)).day and line[1].month == (today - timedelta(days=1)).month:
			member = await Members[0].guild.fetch_member(line[0])
			await member.remove_roles(bdrole, reason='Он/она больше не именниник')
		elif line[1].day == today.day and line[1].month == today.month:
			age = today.year - line[1].year
			member = await Members[0].guild.fetch_member(line[0])
			channel = await bot.fetch_channel(birthday.Channel)
			await member.add_roles(bdrole, reason='У него/неё сегодня день рождения')
			girl_role = utils.get(Members[0].guild.roles, id=birthday.GirlRole)
			desc = birthday.Greetings[randint(0, len(birthday.Greetings) - 1)]
			desc = desc.replace('user', member.mention)
			desc = desc.replace('age', str(age))
			desc = desc.replace('month1', birthday.NameOfMonths[today.month][0])
			desc = desc.replace('month2', birthday.NameOfMonths[today.month][1])

			if 'years' in desc:
				if age % 10 == 1 and a % 100 != 11:
					desc = desc.replace('years', 'год')
				elif age % 10 in [2, 3, 4] and a % 100 not in [12, 13, 14]:
					desc = desc.replace('years', 'года')
					desc = desc.replace('rod', 'zhen')
				else:
					desc = desc.replace('years', 'лет')
					desc = desc.replace('rod', 'muzh')
			if girl_role in member.roles:
				gif = birthday.GirlsGIFs[randint(0, len(birthday.GirlsGIFs) - 1)]
				desc = desc.replace('sex', 'она')
			else:
				gif = birthday.NeutralGIFs[randint(0, len(birthday.NeutralGIFs) - 1)]
				desc = desc.replace('sex', 'он')
			while '_' in desc:
					k = desc.index('_')
					begin = k - 1
					end = k + 1
					while desc[begin] != ' ':
						begin -= 1
					while desc[end] != ' ':
						end += 1
					begin += 1
					word = desc[begin:k:]

					desc = desc.replace(desc[begin:end:], transform(word, desc[k + 1:end:]))
			emb = discord.Embed(title='С днём рождения !', description=desc, colour=discord.Colour.random())
			emb.set_image(url=gif)
			await channel.send(embed=emb)




@bot.event
async def on_ready():
	for member in bot.get_all_members():
		if not member.bot:
			Members.append(member)
	cursor.execute("""CREATE TABLE IF NOT EXISTS birthdays (
			id BIGINT NOT NULL,
			birthday VARCHAR(10),
			PRIMARY KEY(id)
		)""")

	stats.load_stats()
	birthday.load_birthdays()
	called_once_a_day.start()
	print('Я уже выехал, отец')

@bot.event
async def on_raw_reaction_add(payload):
	channel = bot.get_channel(payload.channel_id) # получаем объект канала
	message = await channel.fetch_message(payload.message_id) # получаем объект сообщения
	member = utils.get(message.guild.members, id=payload.user_id) # получаем объект пользователя который поставил реакцию
	if payload.message_id == get_roles.PostID1:
		try:
			emoji = str(payload.emoji) # эмоджик который выбрал юзер
			role = utils.get(message.guild.roles, id=get_roles.Roles1[emoji]) # объект выбранной роли (если есть)
			if(len([i for i in member.roles if i.id in get_roles.CountableRoles1]) < get_roles.MaxRolesPerUser or member.id in get_roles.ExcUsers):	
				await member.add_roles(role)
				print('Добавление ролей: [Успех] Пользователю {0.display_name} была выдана роль {1.name}'.format(member, role))
			else:
				await message.remove_reaction(payload.emoji, member)
				print('Добавление ролей: [Ошибка] Слишком много ролей у пользователя {0.display_name}'.format(member))
		except KeyError as e:
			print('Добавление ролей: [Ошибка] Не найдено ролей для ' + emoji)
		except Exception as e:
			print(repr(e))
	elif payload.message_id == get_roles.PostID2:
		try:
			emoji = str(payload.emoji) # эмоджик который выбрал юзер
			role = utils.get(message.guild.roles, id=get_roles.Roles2[emoji]) # объект выбранной роли (если есть)
			if(len([i for i in member.roles if i.id in get_roles.CountableRoles2]) < get_roles.MaxRolesPerUser or member.id in get_roles.ExcUsers):	
				await member.add_roles(role)
				print('Добавление ролей: [Успех] Пользователю {0.display_name} была выдана роль {1.name}'.format(member, role))
			else:
				await message.remove_reaction(payload.emoji, member)
				print('Добавление ролей: [Ошибка] Слишком много ролей у пользователя {0.display_name}'.format(member))
		except KeyError as e:
			print('Добавление ролей: [Ошибка] Не найдено ролей для ' + emoji)
		except Exception as e:
			print(repr(e))


@bot.event
async def on_raw_reaction_remove(payload):
	channel = bot.get_channel(payload.channel_id) # получаем объект канала
	message = await channel.fetch_message(payload.message_id) # получаем объект сообщения
	member = utils.get(message.guild.members, id=payload.user_id) # получаем объект пользователя который поставил реакцию
	if payload.message_id == get_roles.PostID1:
		try:
			emoji = str(payload.emoji) # эмоджик который выбрал юзер
			role = utils.get(message.guild.roles, id=get_roles.Roles1[emoji]) # объект выбранной роли (если есть)
			await member.remove_roles(role)
			print('Удаление роли: [Успех] Роль {1.name} была удалена у {0.display_name}'.format(member, role))
		except KeyError as e:
			print('Удаление роли: [Ошибка] Не найдено роли для ' + emoji)
		except Exception as e:
			print(repr(e))
	elif payload.message_id == get_roles.PostID2:
		try:
			emoji = str(payload.emoji) # эмоджик который выбрал юзер
			role = utils.get(message.guild.roles, id=get_roles.Roles2[emoji]) # объект выбранной роли (если есть)
			await member.remove_roles(role)
			print('Удаление роли: [Успех] Роль {1.name} была удалена у {0.display_name}'.format(member, role))
		except KeyError as e:
			print('Удаление роли: [Ошибка] Не найдено роли для ' + emoji)
		except Exception as e:
			print(repr(e))
@bot.command()
async def congratulate(ctx, holiday : str):
	emb = None
	if holiday == 'newyear':
		emb =  discord.Embed(title='С Новым {0} годом, @everyone!'.format(datetime.now(tz=msk).year), colour=discord.Colour.green(), description='Вот и подошёл к концу {0} год! С наступающим Новым годом! Искренне желаем, чтобы он был наполнен неожиданными подарками, позитивными эмоциями и яркими мгновениями. Пусть этот год принесет в вашу жизнь перемены к лучшему, чудеса, радости и исполнит самые фантастические мечты!'.format(datetime.now(tz=msk).year - 1))
		emb.set_image(url='https://c.tenor.com/YYEAOYTgiH4AAAAC/happy-new-year-novy-god.gif')
	if emb == None:
		print('Поздравление: [Ошибка] Нет праздника с тегом {0}'.format(holiday))
	else:
		channel = await bot.fetch_channel(903652133121982465)
		await channel.send(embed=emb)
		print('Поздравление: [Успех] Поздравление произошло успешно')

@bot.command()
async def valentine(ctx, arg: discord.Member):
	global EventProcessing
	await ctx.channel.purge(limit = 1)
	if not EventProcessing:
		await ctx.send('Неизвестная команда')
		return
	if arg == None:
		await ctx.send('Чтобы отправить валентинку кому-либо напишите следующую команду: `!valentine <упоминание игрока>`')
	else:
		if ctx.message.author.id in Senders:
			await ctx.send('Вы уже отправляли сегодня валентинку!')
			return
		if arg.id == ctx.message.author.id:
			await ctx.send('Нельзя отправить валентинку самому себе!')
			return
		if arg not in ValentineCards.keys():
			ValentineCards[arg] = 1
		else:
			ValentineCards[arg] += 1
		Senders.append(ctx.message.author.id)
		emb = discord.Embed(title='Валентинка отправлена <3', colour=discord.Colour.magenta())
		emb.set_image(url='https://acegif.com/wp-content/uploads/gif-heart-51.gif')
		await ctx.send(embed=emb)


@bot.command()
async def start_event(ctx):
	global EventProcessing
	if str(ctx.message.author.top_role) != 'Админ':
		return
	EventProcessing = True
	channel = await bot.fetch_channel(903652133121982465)
	emb = discord.Embed(title='С днём святого Валентина', colour = discord.Colour.dark_magenta(), description = 'С днём святого Валентина!\nВ этот день мы решили провести ивент:\nКаждый может отправить анонимную валентинку своему дорогому человеку. Для этого нужно\
		воспользоваться командой `!valentine <упоминание адресанта>`.\nВ конце дня подведём итоги и узнаем кому отправили наибольшее число валентинок.')
	emb.set_image(url='https://thumbs.gfycat.com/IncompatibleInsignificantAfricangroundhornbill-max-1mb.gif')
	await channel.send(embed=emb)


@bot.command()
async def close_event(ctx):
	if str(ctx.message.author.top_role) != 'Админ':
		return
	EventProcessing = False
	channel = await bot.fetch_channel(903652133121982465)
	desc = ''
	i = 1
	word = morph.parse('валентинка')[0]
	for m in sorted(ValentineCards.items(), key= lambda item: -item[1]):
		desc += '{0}. {1} - {2} {3}\n'.format(str(i), get_nick(m[0]), m[1], word.make_agree_with_number(m[1]).word)
		i += 1
		if i == 6:
			break
	emb = discord.Embed(title='Подведём итоги!', colour=discord.Colour.magenta(), description=desc)
	emb.set_image(url='https://c.tenor.com/03Mpv9Rj4K4AAAAC/love-love-you.gif')
	await channel.send(embed=emb)

@bot.command()
async def help(ctx, arg : str =''):
	if arg == '':
		emb=discord.Embed(title='Команды бота Мафиозник', colour=discord.Colour.random())
		emb.add_field(name='Статистика мафия', value='`!help stats`')
		emb.add_field(name='Дни рождения', value='`!help birthdays`')
		if str(ctx.message.author.top_role) == 'Админ':
			emb.add_field(name='Сообщения и реакции', value='`!help messages`')
			await ctx.message.author.send(embed=emb)
		else:
			await ctx.reply(embed=emb)
		print('Помощь: [Успех] Пользователь {0.display_name} получил список возможной информации'.format(ctx.message.author))
	elif arg == 'stats':
		if str(ctx.message.author.top_role) == 'Админ':
			await ctx.message.author.send(embed=discord.Embed(title='Статистика мафии', description='Статистика ведётся следующим образом.\nМафия: количество убийств + 10*количество отхиленных самострелов\nКомиссар: количество правильных проверок\
		 + количество дневных убийств мафии по наводке\nДоктор: количество верных лечений\n Мирный: количество прожитых дней\n`!add_points <роль> <участник> <очки>` - добавляет участнику за роль очки\n\
		 `!set_points <роль> <участник> <количество очков>` - устанавливает участнику количество очков за роль\n`!stats_of <роль> <участник>` -  выводит статистику игрока за роль\n`!top <роль>` - выводит топ игроков за данную роль', colour=discord.Colour.random()))
		else:
			await ctx.reply(embed=discord.Embed(title='Статистика мафии', description='Статистика ведётся следующим образом.\nМафия: количество убийств + 10*количество отхиленных самострелов\nКомиссар: количество правильных проверок\
		 + количество дневных убийств мафии по наводке\nДоктор: количество верных лечений\n Мирный: количество прожитых дней\n`!stats_of <роль> <участник>` -  выводит статистику игрока за роль\n`!top <роль>` - выводит топ игроков за данную роль', colour=discord.Colour.random()))
		print('Помощь: [Успех] Пользователь {0.display_name} получил информацию по разделу Статистика'.format(ctx.message.author))
	elif arg == 'birthdays':
		if str(ctx.message.author.top_role) == 'Админ':
			await ctx.message.author.send(embed=discord.Embed(title='Дни рождения', colour=discord.Colour.random(), description='`!set_birthday <участник> <дата рождения>` - устанавливает участнику дату рождения. Дата рождения вводится в формате YYYY-MM-DD\n`!del_birthday <участник>` - удаляет день рождения\n`!next_birthdays` - показывает ближайшие 10 дней рождений участников'))
		else:
			await ctx.reply(embed=discord.Embed(title='Дни рождения', colour=discord.Colour.random(), description='`!next_birthdays` - показывает ближайшие 10 дней рождений участников'))
		print('Помощь: [Успех] Пользователь {0.display_name} получил информацию по разделу Дни рождения'.format(ctx.message.author))
	elif arg == 'messages' and str(ctx.message.author.top_role) == 'Админ':
		await ctx.message.author.send(embed=discord.Embed(title='Сообщения и реакции', colour=discord.Colour.random(), description='`!write <сообщение>` - написать сообщение от имени бота\n`!react_to <ID> <эмодзи>` - добавить реакцию на пост с данным ID\n`!del_reaction <ID> <эмодзи>` - удаляет определённую реакцию с сообщения с данным ID'))
		print('Помощь: [Успех] Пользователь {0.display_name} получил информацию по разделу Сообщения и реакции'.format(ctx.message.author))
	else:
		ctx.reply('Такой категории, как ' + arg + ' не существует')
		print('Помощь: [Ошибка] Не существует категории {0}'.format(arg))


@bot.command()
async def write(ctx, *, msg):
	await ctx.channel.purge(limit = 1)
	if str(ctx.message.author.top_role) != 'Админ':
		return
	await ctx.send(msg)
	print('Отправление сообщения: [Успех] отправление произошло успешно')

@bot.command()
async def add_points(ctx, type_of_role, member:discord.Member, points : int):
	await ctx.channel.purge(limit = 1)
	message = ctx.message
	if str(ctx.message.author.top_role) != 'Админ':
		return
	db = None
	role = None
	if type_of_role == 'mafia':
		db = stats.Mafia
		role = Members[0].guild.get_role(902834854528425985)
	elif type_of_role == 'sheriff':
		db = stats.Sheriff
		role = Members[0].guild.get_role(902834576102162442)
	elif type_of_role == 'doctor':
		db = stats.Doctor
		role = Members[0].guild.get_role(907626656678678538)
	elif type_of_role == 'innocent':
		db = stats.Innocent
		role = Members[0].guild.get_role(902835631389044837)
	else:
		await ctx.send(embed=discord.Embed(title='Добавление очков', description='Ошибка: не существует такой роли', colour=discord.Colour.red()))
		return
	if member.id in db.keys():
		db[member.id] += points
	else:
		db[member.id] = points
	leaders = []
	max_value = 0
	for i in db.items(): 
		if max_value < i[1]:
			leaders = [i[0]]
			max_value = i[1]
		elif max_value == i[1]:
			leaders.append(i[0])
	if db[member.id] == max_value and len(leaders) == 1:
		for i in role.members:
			await i.remove_roles(role, reason='He/she isn\'t best ' + type_of_role + ' now')
		await member.add_roles(role, reason='He/she is best ' + type_of_role + ' now')
	elif db[member.id] == max_value:
		await member.add_roles(role, reason='He/she is best ' + type_of_role + ' now')
	await ctx.send(embed=discord.Embed(title='Добавление очков', description='Добавление очков игроку ' + get_nick(member) + ' произошло успешно', colour=discord.Colour.green()))
	if type_of_role == 'mafia':
		stats.save_stats(doctor=False, innocent=False, sheriff=False)
	elif type_of_role == 'doctor':
		stats.save_stats(mafia=False, innocent=False, sheriff=False)
	elif type_of_role == 'innocent':
		stats.save_stats(doctor=False, mafia=False, sheriff=False)
	else:
		stats.save_stats(doctor=False, innocent=False, mafia=False)

@bot.command()
async def set_points(ctx, type_of_role, member:discord.Member, points : int):
	await ctx.channel.purge(limit = 1)
	message = ctx.message
	if str(ctx.message.author.top_role) != 'Админ':
		return
	db = role = None
	if type_of_role == 'mafia':
		db = stats.Mafia
		role = Members[0].guild.get_role(902834854528425985)
	elif type_of_role == 'sheriff':
		db = stats.Sheriff
		role = Members[0].guild.get_role(902834576102162442)
	elif type_of_role == 'doctor':
		db = stats.Doctor
		role = Members[0].guild.get_role(907626656678678538)
	elif type_of_role == 'innocent':
		db = stats.Innocent
		role = Members[0].guild.get_role(902835631389044837)
	else:
		await ctx.send(embed=discord.Embed(title='Изменение очков', description='Ошибка: не существует такой роли', colour=discord.Colour.red()))
		return
	db[member.id] = points
	leaders = []
	max_value = 0
	for i in db.items():
		if max_value < i[1]:
			leaders = [i[0]]
			max_value = i[1]
		elif max_value == i[1]:
			leaders.append(i[0])
	if db[member.id] == max_value and len(leaders) == 1:
		for i in role.members:
			await i.remove_roles(role, reason='He/she isn\'t best ' + type_of_role + ' now')
		await member.add_roles(role, reason='He/she is best ' + type_of_role + ' now')
	elif db[member.id] == max_value:
		await member.add_roles(role, reason='He/she is best ' + type_of_role + ' now')
	await ctx.send(embed=discord.Embed(title='Изменение количества очков', description='Изменение количества очков игроку ' + get_nick(member) + ' произошло успешно', colour=discord.Colour.green()))
	if type_of_role == 'mafia':
		stats.save_stats(doctor=False, innocent=False, sheriff=False)
	elif type_of_role == 'doctor':
		stats.save_stats(mafia=False, innocent=False, sheriff=False)
	elif type_of_role == 'innocent':
		stats.save_stats(doctor=False, mafia=False, sheriff=False)
	else:
		stats.save_stats(doctor=False, innocent=False, mafia=False)

@bot.command()
async def stats_of (ctx, type_of_role, member:discord.Member):
	await ctx.channel.purge(limit = 1)
	message = ctx.message
	db = ttl = color = None
	if type_of_role == 'mafia':
		db = stats.Mafia
		ttl = 'мафию'
		color = discord.Colour.red()
	elif type_of_role == 'sheriff':
		db = stats.Sheriff
		ttl = 'комиссара'
		color = discord.Colour.blue()
	elif type_of_role == 'doctor':
		db = stats.Doctor
		ttl = 'доктора'
		color = discord.Colour.green()
	elif type_of_role == 'innocent':
		ttl = 'мирного'
		db = stats.Innocent
		color = discord.Colour.blue()
	else:
		await ctx.send(embed=discord.Embed(title='Статистика' + ttl, description='Ошибка: не существует такой роли', colour=discord.Colour.red()))
		return
	await ctx.send(embed=discord.Embed(title='Статистика ' + get_nick(member) + ' игры за ' + ttl, description='У игрока ' + get_nick(member) + ' ' + str(db[member.id])))

@bot.command()
async def top (ctx, type_of_role):
	await ctx.channel.purge(limit = 1)
	db = ttl = color = None
	if type_of_role == 'mafia':
		db = stats.Mafia
		ttl = 'мафии'
		color = discord.Colour.red()
	elif type_of_role == 'sheriff':
		db = stats.Sheriff
		ttl = 'комиссаров'
		color = discord.Colour.blue()
	elif type_of_role == 'doctor':
		db = stats.Doctor
		ttl = 'докторов'
		color = discord.Colour.green()
	elif type_of_role == 'innocent':
		ttl = 'мирных'
		db = stats.Innocent
		color = discord.Colour.blue()
	else:
		await ctx.send(embed=discord.Embed(title='Статистика' + ttl, description='Ошибка: не существует такой роли', colour=discord.Colour.red()))
		return
	descr = ''
	i = 1
	for player in sorted(db.items(), key = lambda item: -item[1]):
		mem = await Members[0].guild.fetch_member(player[0])
		descr += str(i) + '. ' + get_nick(mem) + ' - ' + str(player[1]) + '\n'
		i += 1
		if i == 11:
			break
	await ctx.send(embed=discord.Embed(title='Статистика' + ttl, description=descr, colour=color))

@bot.command()
async def react_to(ctx, msg_id, *, emoji_id):
	await ctx.channel.purge(limit = 1)
	if str(ctx.message.author.top_role) != 'Админ':
		return
	message = await ctx.fetch_message(msg_id)
	await message.add_reaction(emoji=emoji_id)
	print('Добавление эмоции произошло успешно')

@bot.command()
async def set_birthday(ctx, user:discord.Member, dat:str):
	if str(ctx.message.author.top_role) != 'Админ':
		return
	await ctx.channel.purge(limit = 1)
	try:
		if len(dat) != 10:
			print('Неверный формат даты рождения: длина даты != 10')
			return
		day = None
		try:
			day = date(year = int(dat[:4:]), month = int(dat[5:7:]), day = int(dat[8::]))
		except:
			print('Неверный формат даты рождения')
		#there
		birthday.set_birthday(user.id, dat)
		left = birthday.days_left(birthday.birthdays[user.id])
		if left % 10 == 1 and left % 100 != 11:
			await ctx.send(embed = discord.Embed(description='Я поздравлю **' + user.name + '** через ' + str(left) + ' день', colour=discord.Colour.green(), title='Добавление дня рождения произошло успешно'))
		elif left % 10 in [2, 3, 4] and left % 100 not in [11, 12, 13, 14]:
			await ctx.send(embed = discord.Embed(description='Я поздравлю **' + user.name + '** через ' + str(left) + ' дня', colour=discord.Colour.green(), title='Добавление дня рождения произошло успешно'))
		else:
			await ctx.send(embed = discord.Embed(description='Я поздравлю **' + user.name + '** через ' + str(left) + ' дней', colour=discord.Colour.green(), title='Добавление дня рождения произошло успешно'))
	except ValueError as err:
		print(err)
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Добавление дня рождения не удалось', colour=discord.Colour.red()))

@bot.command()
async def del_birthday(ctx, user: discord.Member):
	if str(ctx.message.author.top_role) != 'Админ':
		return
	await ctx.channel.purge(limit = 1)
	try:
		birthday.delete_birthday(user.id)
		await ctx.send(embed=discord.Embed(description='Удаление дня рождения произошло успешно', title='Удаление дня рождения', colour=discord.Colour.green()))
	except:
		await ctx.send(embed=discord.Embed(description='Удаление дня рождения не удалось', title='Удаление дня рождения', colour=discord.Colour.red()))

@bot.command()
async def next_birthdays(ctx):
	await ctx.channel.purge(limit = 1)
	bdays = birthday.next_birthdays()
	today = datetime.now(tz=msk)
	i = 1
	descr = ''
	for mem in bdays.items():
		member = await Members[0].guild.fetch_member(mem[0])
		dney = None
		if mem[1] % 10 == 1 and mem[1] % 100 != 11:
			dney = 'день'
		elif mem[1] % 10 in [2, 3, 4] and mem[1] % 100 not in [12, 13, 14]:
			dney = 'дня'
		else:
			dney = 'дней'
		descr += str(i) + '. **' +  get_nick(member) + '** - ' + str((today + timedelta(days=mem[1])).strftime("%d.%m.%y")) + '(через ' + str(mem[1]) + ' ' +  dney + ')\n'
		i += 1
	await ctx.send(embed=discord.Embed(description=descr, title='Ближайшие дни рождения', colour=discord.Colour.teal()))


@bot.command()
async def del_reaction(ctx, msg_id, emoji_id):
	await ctx.channel.purge(limit=1)
	if str(ctx.message.author.top_role) != 'Админ':
		return
	message = await ctx.fetch_message(msg_id)
	await message.clear_reaction(emoji_id)
	print('Удаление эмоции произошло успешно')

bot.run(os.getenv('TOKEN'))