import discord
from discord import utils
from discord.utils import get
from discord.ext import commands, tasks
import os, sys, asyncio
import get_roles
from birthday import NameOfMonths, Greetings, days_left
from datetime import datetime, time, timedelta, date, timezone
from random import randint
import pymorphy2
import sqlite3
import gifs, ids

intents = discord.Intents.default()
intents.members = True
msk = timezone(offset=timedelta(hours=3), name='МСК')
bot = commands.Bot(command_prefix='!', intents=intents)
morph = pymorphy2.MorphAnalyzer()
db = sqlite3.connect('database.db')
cursor = db.cursor()


Members = []
bot.remove_command('help')

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
	bdrole = utils.get(Members[0].guild.roles, id=ids.BirthdayRole)
	for line in cursor.execute("SELECT * FROM birthdays"):
		if int(line[1][8::]) == (today - timedelta(days=1)).day and int(line[1][5:7:]) == (today - timedelta(days=1)).month:
			member = await Members[0].guild.fetch_member(line[0])
			await member.remove_roles(bdrole, reason='Он/она больше не именниник')
		elif int(line[1][8::]) == today.day and int(line[1][5:7:]) == today.month:
			age = today.year - int(line[1][:4:])
			member = await Members[0].guild.fetch_member(line[0])
			channel = await bot.fetch_channel(birthday.Channel)
			await member.add_roles(bdrole, reason='У него/неё сегодня день рождения')
			girl_role = utils.get(Members[0].guild.roles, id=birthday.GirlRole)
			desc = Greetings[randint(0, len(Greetings) - 1)]
			desc = desc.replace('user', member.mention)
			desc = desc.replace('age', str(age))
			desc = desc.replace('month1', NameOfMonths[today.month][0])
			desc = desc.replace('month2', NameOfMonths[today.month][1])
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
				gif = gifs.GirlsGIFs[randint(0, len(gifs.GirlsGIFs) - 1)]
				desc = desc.replace('sex', 'она')
			else:
				gif = gifs.NeutralGIFs[randint(0, len(gifs.NeutralGIFs) - 1)]
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
			await ctx.message.author.send(embed=discord.Embed(title='Дни рождения', colour=discord.Colour.random(), description='`!set_birthday <участник> <дата рождения>` - устанавливает участнику дату рождения. Дата рождения вводится в формате YYYY-MM-DD\n`!change_birthday <участник> <дата>` - меняет день рождения участнику\n`!next_birthdays` - показывает ближайшие 10 дней рождений участников'))
		else:
			await ctx.reply(embed=discord.Embed(title='Дни рождения', colour=discord.Colour.random(), description='`!next_birthdays` - показывает ближайшие 10 дней рождений участников'))
		print('Помощь: [Успех] Пользователь {0.display_name} получил информацию по разделу Дни рождения'.format(ctx.message.author))
	elif arg == 'messages' and str(ctx.message.author.top_role) == 'Админ':
		await ctx.message.author.send(embed=discord.Embed(title='Сообщения и реакции', colour=discord.Colour.random(), description='`!write <сообщение>` - написать сообщение от имени бота\n`!react_to <ID> <эмодзи>` - добавить реакцию на пост с данным ID\n`!del_reaction <ID> <эмодзи>` - удаляет определённую реакцию с сообщения с данным ID'))
		print('Помощь: [Успех] Пользователь {0.display_name} получил информацию по разделу Сообщения и реакции'.format(ctx.message.author))
	else:
		ctx.reply('Такой категории, как ' + arg + ' не существует')
		print('Помощь: [Ошибка] Не существует категории {0}'.format(arg))


#############################################	kick, mute and ban #############################################

#kick
@bot.command()
@commands.has_permissions(administrator=True)
async def kick(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	await member.kick(reason = reason)
	emb = discord.Embed(title=f'Пользователь {get_nick(member)} был кикнут с сервера по причине \"{reason}\"', colour=discord.Colour.random())
	emb.set_image(url=gifs.KickGIFs[randint(0, len(gifs.KickGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Кик]: Участник {get_nick(member)} был успешно кикнут')

#ban
@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	await member.ban(reason = reason)
	emb = discord.Embed(title=f'Пользователь {get_nick(member)} был забанен по причине \"{reason}\"', colour=discord.Colour.random())
	emb.set_image(url=gifs.BanGIFs[randint(0, len(gifs.BanGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Бан]: Участник {get_nick(member)} был успешно забанен')


#mute person in voice channels
@bot.command()
@commands.has_permissions(administrator=True)
async def voice_mute(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	vmute_role = utils.get(ctx.message.author.guild.roles, id=ids.VoiceMuteRole)
	await member.add_roles(vmute_role)
	emb = discord.Embed(title=f'Пользователь {get_nick(member)} теперь не может говорить в голосовых каналах сервера по причине \"{reason}\"', colour=discord.Colour.random())
	emb.set_image(url=gifs.VoiceMuteGIFs[randint(0, len(gifs.VoiceMuteGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Голосовой мут]: Участник {get_nick(member)} был успешно замучен')


#mute in text channels
@bot.command()
@commands.has_permissions(administrator=True)
async def mute(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	mute_role = utils.get(ctx.message.author.guild.roles, id=ids.MuteRole)
	await member.add_roles(mute_role)
	emb = discord.Embed(title=f'Пользователь {get_nick(member)} теперь не может писать в текстовых каналах сервера по причине \"{reason}\"', colour=discord.Colour.random())
	emb.set_image(url=gifs.MuteGIFs[randint(0, len(gifs.MuteGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Голосовой мут]: Участник {get_nick(member)} был успешно замучен')

#unmute in voice channels
@bot.command()
@commands.has_permissions(administrator=True)
async def voice_unmute(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	vmute_role = utils.get(ctx.message.author.guild.roles, id=ids.VoiceMuteRole)
	if vmute_role not in member.roles:
		await ctx.send(embed=discord.Embed(title='Ошибка размьюта', description='Пользователь не находится в муте', colour=discord.Colour.random()))
		print('[Анмьют] Пользователь не был замьючен в голосовых каналах')
	else:
		await member.remove_roles(vmute_role, reason=reason)
		emb = discord.Embed(title=f'Пользователь {get_nick(member)} теперь может снова говорить в голосовых каналах!', colour=discord.Colour.random())
		emb.set_image(url=gifs.UnMuteGIFs[randint(0, len(gifs.UnMuteGIFs))])
		await ctx.send(embed=emb)
		print(f'[Анмьют] Пользователь {get_nick(member)} был успешно размучен в голосовых каналах')

#unmute in text channels
@bot.command()
@commands.has_permissions(administrator=True)
async def unmute(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	mute_role = utils.get(ctx.message.author.guild.roles, id=ids.MuteRole)
	if mute_role not in member.roles:
		await ctx.send(embed=discord.Embed(title='Ошибка размьюта', description='Пользователь не находится в муте', colour=discord.Colour.random()))
		print('[Анмьют] Пользователь не был замьючен в текстовых каналах')
	else:
		await member.remove_roles(mute_role, reason=reason)
		emb = discord.Embed(title=f'Пользователь {get_nick(member)} теперь может снова писать в текстовых каналах!', colour=discord.Colour.random())
		emb.set_image(url=gifs.UnMuteGIFs[randint(0, len(gifs.UnMuteGIFs))])
		await ctx.send(embed=emb)
		print(f'[Анмьют] Пользователь {get_nick(member)} был успешно размучен в текстовых каналах')

###############################################		fun		##############################################################

@bot.command()
async def kiss(ctx, member:discord.Member):
	c = ''
	if utils.get(ctx.message.author.guild.roles, id=ids.GirlRole) in ctx.message.author.roles: c = 'а'
	emb = discord.Embed(title='Поцелуй', description=f'{ctx.message.author.mention} поцеловал{c} {member.mention}', colour = discord.Colour.magenta())
	emb.set_image(url=gifs.KissGIFs[randint(0, len(gifs.KissGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Поцелуй] Пользователь {get_nick(ctx.message.author)} поцеловал{c} {get_nick(member)}')

@bot.command()
async def punch(ctx, member:discord.Member):
	c = ''
	if utils.get(ctx.message.author.guild.roles, id=ids.GirlRole) in ctx.message.author.roles: c = 'а'
	emb = discord.Embed(title='Удар', description= f'{ctx.message.author.mention} ударил{c} {member.mention}', colour = discord.Colour.from_rgb(255, 238, 0))
	emb.set_image(url=gifs.PunchGIFs[randint(0, len(gifs.PunchGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Удар] Пользователь {get_nick(ctx.message.author)} ударил{c} {get_nick(member)}')

###############################################		reactions/messages	#############################################################

#write messages on behalf of the bot
@bot.command()
@commands.has_permissions(administrator = True)
async def write(ctx, *, msg):
	await ctx.channel.purge(limit = 1)
	await ctx.send(msg)
	print('[Отправление сообщения] Отправление произошло успешно')

#clear messages in the channel
@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, number = 1):
	await ctx.channel.purge(limit=number)
	w = morph.parse('сообщение')[0]
	print(f'[Удаление сообщений] Удаление {number} {w.make_agree_with_number(number).word} произошло успешно')


@bot.command()
@commands.has_permissions(administrator=True)
async def react_to(ctx, msg_id, *, emoji_id):
	await ctx.channel.purge(limit = 1)
	message = await ctx.fetch_message(msg_id)
	await message.add_reaction(emoji=emoji_id)
	print('Добавление эмоции произошло успешно')

@bot.command()
@commands.has_permissions(administrator=True)
async def del_reaction(ctx, msg_id, emoji_id):
	await ctx.channel.purge(limit=1)
	message = await ctx.fetch_message(msg_id)
	await message.clear_reaction(emoji_id)
	print('Удаление эмоции произошло успешно')


##############################################		birthdays	#############################################################
@bot.command()
@commands.has_permissions(administrator=True)
async def set_birthday(ctx, user:discord.Member, dat:str):
	await ctx.channel.purge(limit = 1)
	if len(dat) != 10:
		print('Ошибка: Неверный формат даты рождения: длина даты != 10')
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Добавление дня рождения не удалось', colour=discord.Colour.red()))
		return
	day = None
	try:
		day = date(year = int(dat[:4:]), month = int(dat[5:7:]), day = int(dat[8::]))
	except:
		print('Ошибка: Неверный формат даты рождения')
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Добавление дня рождения не удалось', colour=discord.Colour.red()))
		return
	try:
		cursor.execute("INSERT INTO birthdays (id, birthday) VALUES (?, ?)", (user.id, dat))
		db.commit()
	except sqlite3.IntegrityError as err:
		print('Ошибка: Такой пользователь уже есть в базе данных')
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Добавление дня рождения не удалось, т.к. у данного пользователя уже установлен день рождения. Чтобы изменить его, воспользуйтесь командой !change_birthday', colour=discord.Colour.red()))
		return
	left = days_left((user.id, dat))
	w = morph.parse('день')[0]
	await ctx.send(embed = discord.Embed(description='Я поздравлю **{0}** через {1} {2}'.format(get_nick(user), left, w.make_agree_with_number(left).word), colour=discord.Colour.green(), title='Добавление дня рождения произошло успешно'))
	print('Пользователю {0} установлен день рождения: {1}'.format(get_nick(user), dat))


@bot.command()
@commands.has_permissions(administrator=True)
async def change_birthday(ctx, user: discord.Member, dat:str):
	await ctx.channel.purge(limit = 1)
	if len(dat) != 10:
		print('Неверный формат даты рождения: длина даты != 10')
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Изменение дня рождения не удалось', colour=discord.Colour.red()))
		return
	day = None
	try:
		day = date(year = int(dat[:4:]), month = int(dat[5:7:]), day = int(dat[8::]))
	except:
		print('Неверный формат даты рождения')
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Изменение дня рождения не удалось', colour=discord.Colour.red()))
		return
	cursor.execute("UPDATE birthdays SET birthday = ? WHERE id = ?", (dat, user.id))
	db.commit()
	left = days_left((user.id, dat))
	w = morph.parse('день')[0]
	await ctx.send(embed=discord.Embed(description='Изменение дня рождения произошло успешно. Я поздравлю **{0}** через {1} {2}'.format(get_nick(user), left, w.make_agree_with_number(left).word), title='Изменение дня рождения', colour=discord.Colour.green()))
	print('Пользователю {0} установлен день рождения: {1}'.format(get_nick(user), dat))

@bot.command()
async def next_birthdays(ctx):
	await ctx.channel.purge(limit = 1)
	today = datetime.now(tz=msk)
	bdays = {i : days_left(i) for i in sorted(list(cursor.execute("SELECT * FROM birthdays")),key=days_left)[:10:]}
	descr = ''
	i = 1
	w = morph.parse("день")[0]
	for mem in bdays.items():
		member = await Members[0].guild.fetch_member(mem[0][0])
		descr += '{0}) **{1}** - {2} {3} (через {4} {5})\n'.format(i, get_nick(member), int(mem[0][1][8::]), morph.parse(NameOfMonths[int(mem[0][1][5:7:])][0])[0].inflect({'gent'}).word, mem[1], w.make_agree_with_number(mem[1]).word)
		i += 1
	await ctx.send(embed=discord.Embed(description=descr, title='Ближайшие дни рождения', colour=discord.Colour.teal()))
	print('Список следующих десяти дней рождений выведен успешно')

@bot.command()
async def birthday (ctx, member:discord.Member):
	today = datetime.now(tz=msk)
	bday = tuple(cursor.execute("SELECT * FROM birthdays WHERE id = ?", (member.id,)))
	if len(bday) == 0:
		emb = discord.Embed(title=f'У {get_nick(member)} не установлено дня рождения', colour=discord.Colour.random())
		emb.set_image(url=member.avatar_url)
	else:
		bday = bday[0]
		day = morph.parse('день')[0]
		month = morph.parse(NameOfMonths[int(bday[1][5:7:])][0])[0]
		emb = discord.Embed(title='У {0} день рождения {1} {2} (будет через {3} {4})'.format(get_nick(member), int(bday[1][8::]), month.inflect({'gent'}).word, days_left(bday), day.make_agree_with_number(days_left(bday)).word), colour=discord.Colour.random())
		emb.set_image(url=member.avatar_url)
	await ctx.send(embed=emb)
	print('[Получение дня рождения] День рождения получен успешно')

bot.run(os.getenv('TOKEN'))