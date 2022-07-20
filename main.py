import discord
from discord import utils
from discord.utils import get
from discord.ext import commands, tasks
import os, sys, asyncio
from Cybernator import Paginator as pag
from birthday import NameOfMonths, Greetings, days_left
from datetime import datetime, time, timedelta, date, timezone
from random import randint
import pymorphy2
import psycopg2
import gifs, ids, levels, get_roles

DB_URI = "postgres://wekhaeduhjfgdq:a818bfc043503eda3165d29c7ced0453f291eeaa4af82d16a9945e391dfa5e4a@ec2-52-49-120-150.eu-west-1.compute.amazonaws.com:5432/dc39934i40p5ji"
intents = discord.Intents.default()
intents.members = True
msk = timezone(offset=timedelta(hours=3), name='МСК')
bot = commands.Bot(command_prefix='!', intents=intents)
morph = pymorphy2.MorphAnalyzer()
db = psycopg2.connect(DB_URI, sslmode='require')
cursor = db.cursor()


Members = []
InVoiceChannels = {}
bot.remove_command('help')

################################################	help functions	####################################################

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

async def give_xp(number:int, member:discord.Member):
	cursor.execute("UPDATE levels SET exp = exp + %s WHERE id = %s", (number, member.id))
	db.commit()
	cursor.execute("SELECT lvl, exp FROM levels WHERE id = %s", (member.id,))
	cur_condition = cursor.fetchone()
	dif = levels.check_level(cur_condition[0], cur_condition[1])
	if dif != 0:
		cursor.execute("UPDATE levels SET lvl = lvl + %s WHERE id = %s", (dif, member.id))
		db.commit()
		old_role = utils.get(member.guild.roles, id = ids.titles[cur_condition[0]])
		new_role = utils.get(member.guild.roles, id = ids.titles[cur_condition[0] + dif])
		await member.send(f'Хорошая работа, {member.mention}, ты достиг {cur_condition[0] + dif} уровня! Теперь твое звание - {new_role.name}')
		await member.remove_roles(old_role)
		await member.add_roles(new_role)
		print(f'[Новый уровень] Пользователь {member.display_name} получил {cur_condition[0] + dif} уровень')

############################################	called once a day 	################################################

@tasks.loop(hours=24)
async def called_once_a_day():
	print('Ежедневная проверка событий: {0}'.format(str(datetime.now(tz=msk))))
	today = datetime.now(tz=msk)
	bdrole = utils.get(Members[0].guild.roles, id=ids.BirthdayRole)
	for mem in bdrole.members:
		cursor.execute("SELECT id, birthday FROM birthdays WHERE id = %s", (mem.id,))
		result = cursor.fetchone()
		if result and result[1][5::] != today.strftime("%m-%d"):
			await mem.remove_roles(bdrole, reason='Он/она больше не именниник')
	cursor.execute("SELECT id, birthday FROM birthdays WHERE RIGHT(birthday, 5) = %s", (today.strftime("%m-%d"),))
	data = cursor.fetchall()
	for line in data:
		age = today.year - int(line[1][:4:])
		member = await Members[0].guild.fetch_member(line[0])
		channel = await bot.fetch_channel(ids.BirthdayChannel)
		await member.add_roles(bdrole, reason='У него/неё сегодня день рождения')
		girl_role = utils.get(Members[0].guild.roles, id=ids.GirlRole)
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
			gif = gifs.GirlsCongratsGIFs[randint(0, len(gifs.GirlsCongratsGIFs) - 1)]
			desc = desc.replace('sex', 'она')
		else:
			gif = gifs.NeutralCongratsGIFs[randint(0, len(gifs.NeutralCongratsGIFs) - 1)]
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


#################################################	events	#################################################

@bot.event
async def on_ready():
	for member in bot.get_all_members():
		if not member.bot:
			Members.append(member)
	called_once_a_day.start()
	print('Я уже выехал, отец')

@bot.event
async def on_raw_reaction_add(payload):
	channel = bot.get_channel(payload.channel_id) 
	message = await channel.fetch_message(payload.message_id)
	member = utils.get(message.guild.members, id=payload.user_id)
	if member.bot: return
	if payload.message_id == get_roles.PostID1:
		try:
			emoji = str(payload.emoji)
			role = utils.get(message.guild.roles, id=get_roles.Roles1[emoji])
			if(len([i for i in member.roles if i.id in get_roles.CountableRoles1]) < get_roles.MaxRolesPerUser or member.id in get_roles.ExcUsers):	
				await member.add_roles(role)
				print('[Добавление ролей] Пользователю {0.display_name} была выдана роль {1.name}'.format(member, role))
			else:
				await message.remove_reaction(payload.emoji, member)
				print('[Добавление ролей] Слишком много ролей у пользователя {0.display_name}'.format(member))
		except KeyError as e:
			print('[Добавление ролей] Не найдено ролей для ' + emoji)
		except Exception as e:
			print(repr(e))
	elif payload.message_id == get_roles.PostID2:
		try:
			emoji = str(payload.emoji) # эмоджик который выбрал юзер
			role = utils.get(message.guild.roles, id=get_roles.Roles2[emoji]) # объект выбранной роли (если есть)
			if(len([i for i in member.roles if i.id in get_roles.CountableRoles2]) < get_roles.MaxRolesPerUser or member.id in get_roles.ExcUsers):	
				await member.add_roles(role)
				print('[Добавление ролей] Пользователю {0.display_name} была выдана роль {1.name}'.format(member, role))
			else:
				await message.remove_reaction(payload.emoji, member)
				print('[Добавление ролей] Слишком много ролей у пользователя {0.display_name}'.format(member))
		except KeyError as e:
			print('[Добавление ролей] Не найдено ролей для ' + emoji)
		except Exception as e:
			print(repr(e))


@bot.event
async def on_raw_reaction_remove(payload):
	channel = bot.get_channel(payload.channel_id)
	message = await channel.fetch_message(payload.message_id)
	member = utils.get(message.guild.members, id=payload.user_id)
	if member.bot: return
	if payload.message_id == get_roles.PostID1:
		try:
			emoji = str(payload.emoji) 
			role = utils.get(message.guild.roles, id=get_roles.Roles1[emoji])
			await member.remove_roles(role)
			print('[Удаление роли] Роль {1.name} была удалена у {0.display_name}'.format(member, role))
		except KeyError as e:
			print('[Удаление роли] Не найдено роли для ' + emoji)
		except Exception as e:
			print(repr(e))
	elif payload.message_id == get_roles.PostID2:
		try:
			emoji = str(payload.emoji)
			role = utils.get(message.guild.roles, id=get_roles.Roles2[emoji]) 
			await member.remove_roles(role)
			print('[Удаление роли] Роль {1.name} была удалена у {0.display_name}'.format(member, role))
		except KeyError as e:
			print('[Удаление роли] Не найдено роли для ' + emoji)
		except Exception as e:
			print(repr(e))

@bot.event
async def on_member_join(member):
	if member.bot: return
	channel = bot.get_channel(ids.GreetingsChannel)
	await channel.send(f'Привет, {member.mention}. Добро пожаловать в нашу банду!')
	cursor.execute("INSERT INTO levels (id, lvl, exp) VALUES (%s, 0, 0)", (member.id, ))
	db.commit()
	await member.add_roles(utils.get(member.guild.roles, id=ids.titles[0]), utils.get(member.guild.roles, id=ids.TitleRole))
	print(f'[Новый участник] У нас новый участник - {member.display_name}')


@bot.event
async def on_message(message):
	if message.author.bot: return
	author_id = message.author.id
	cursor.execute("SELECT id FROM levels WHERE id = %s", (author_id,))
	result = cursor.fetchone()
	if not result:
		cursor.execute("INSERT INTO levels (id, exp, lvl) VALUES (%s, 1, 1)", (author_id,))
		db.commit()
	else:
		await give_xp(1, message.author)
	await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
	if member.bot: return
	if before.channel is None and after.channel is not None:
		InVoiceChannels[member] = datetime.now(tz=msk)
	elif before.channel is not None and after.channel is None:
		spent_time = datetime.now(tz=msk) - InVoiceChannels[member]
		del InVoiceChannels[member]
		await give_xp(spent_time.total_seconds() // 60, member)

###################################################		help	####################################################

@bot.command(aliases=['помощь'])
async def help(ctx, arg : str =''):
	if arg == '':
		emb=discord.Embed(title='Команды бота Мафиозник', colour=discord.Colour.random())
		emb.add_field(name='Дни рождения', value='`!help birthdays`')
		emb.add_field(name='Разное', value='`!help other`')
		emb.add_field(name='Статистика пользователей', value='`!help stats`')
		if str(ctx.message.author.top_role) == 'Админ':
			emb.add_field(name='Сообщения и реакции', value='`!help messages`')
			emb.add_field(name='Управление пользователями', value='`!help user_management`')
			await ctx.message.author.send(embed=emb)
		else:
			await ctx.reply(embed=emb)
		print('[Помощь] Пользователь {0.display_name} получил список возможной информации'.format(ctx.message.author))
	elif arg == 'birthdays':
		if str(ctx.message.author.top_role) == 'Админ':
			await ctx.message.author.send(embed=discord.Embed(title='Дни рождения', colour=discord.Colour.random(), \
				description='`!set_birthday <участник> <дата рождения>` - устанавливает участнику дату рождения. Дата рождения вводится в формате YYYY-MM-DD\
				\n`!change_birthday <участник> <дата>` - меняет день рождения участнику\
				\n`!next_birthdays` - показывает ближайшие 10 дней рождений участников\
				\n`!birthday` <участник> - показывет день рождения участника'))
		else:
			await ctx.reply(embed=discord.Embed(title='Дни рождения', colour=discord.Colour.random(), description='`!next_birthdays` - показывает ближайшие 10 дней рождений участников\
				\n`!birthday <участник> - показывет день рождения участника'))
		print('[Помощь] Пользователь {0.display_name} получил информацию по разделу Дни рождения'.format(ctx.message.author))
	elif arg == 'messages' and str(ctx.message.author.top_role) == 'Админ':
		await ctx.message.author.send(embed=discord.Embed(title='Сообщения и реакции', colour=discord.Colour.random(), \
			description='`!write <сообщение>` - написать сообщение от имени бота\
			\n`!react_to <ID> <эмодзи>` - добавить реакцию на пост с данным ID\
			\n`!del_reaction <ID> <эмодзи>` - удаляет определённую реакцию с сообщения с данным ID\
			\n`!clear <число>` - удаляет указанное количество сообщений в данном канале'))
		print('[Помощь] Пользователь {0.display_name} получил информацию по разделу Сообщения и реакции'.format(ctx.message.author))
	elif arg == 'other':
		await ctx.reply(embed=discord.Embed(title='Другие команды', colour=discord.Colour.random(), description=\
			'`!kiss <участник>` - поцеловать участника\
			\n`!punch <участник>` - ударить участника\
			\n`!ship <участник>` - проверить совместимость с участником'))
		print('[Помощь] Пользователь {0.display_name} получил информацию по разделу Другое'.format(ctx.message.author))
	elif arg == 'user_management' and str(ctx.message.author.top_role) == 'Админ':
		await ctx.message.author.send(embed=discord.Embed(title='Управление пользователями', colour = discord.Colour.random(), description=\
			'`!kick <участник>` - кикнуть участника\n\
			`!mute <участник>` - запретить пользователю писать в текстовых каналах\n\
			`!voice_mute <участник>` - запретить пользователю заходить в голосовые чаты и говорить там\n\
			`!unmute <участник>` - снимает запрет писать в текстовых каналах\n\
			`!voice_unmute <участник>` - снимает запрет заходить на голосовые каналы и говорить там\n\
			`!ban <участник>` - забанить участника'))
		print('[Помощь] Пользователь {0.display_name} получил информацию по разделу Управление пользователями'.format(ctx.message.author))
	elif arg == 'stats':
		await ctx.reply(embed=discord.Embed(title='Статистика пользователей', colour=discord.Colour.random(), description=\
			'`!stats` - собственная статистика\n\
			`!stats <участник>` - статистика участника\n\
			`!rating` - рейтинг участников по уровням'))
		print('[Помощь] Пользователь {0.display_name} получил информацию по разделу Статистика пользователей'.format(ctx.message.author))
	else:
		ctx.reply('Такой категории, как ' + arg + ' не существует')
		print('[Помощь] Ошибка: Не существует категории {0}'.format(arg))


#############################################	kick, mute and ban #############################################

#kick
@bot.command()
@commands.has_permissions(administrator=True)
async def kick(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	cursor.execute("DELETE FROM birthdays WHERE id = %s", (member.id,))
	await member.kick(reason = reason)
	emb = discord.Embed(title=f'Пользователь {member.display_name} был кикнут с сервера по причине \"{reason}\"', colour=discord.Colour.random())
	emb.set_image(url=gifs.KickGIFs[randint(0, len(gifs.KickGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Кик]: Участник {member.display_name} был успешно кикнут')

#ban
@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	cursor.execute("DELETE FROM birthdays WHERE id = %s", (member.id,))
	cursor.execute("DELETE FROM levels WHERE id = %s", (member.id,))
	await member.ban(reason = reason)
	emb = discord.Embed(title=f'Пользователь {member.display_name} был забанен по причине \"{reason}\"', colour=discord.Colour.random())
	emb.set_image(url=gifs.BanGIFs[randint(0, len(gifs.BanGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Бан]: Участник {member.display_name} был успешно забанен')


#mute person in voice channels
@bot.command()
@commands.has_permissions(administrator=True)
async def voice_mute(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	vmute_role = utils.get(ctx.message.author.guild.roles, id=ids.VoiceMuteRole)
	await member.add_roles(vmute_role)
	emb = discord.Embed(title=f'Пользователь {member.display_name} теперь не может говорить в голосовых каналах сервера по причине \"{reason}\"', colour=discord.Colour.random())
	emb.set_image(url=gifs.VoiceMuteGIFs[randint(0, len(gifs.VoiceMuteGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Голосовой мут]: Участник {member.display_name} был успешно замучен')


#mute in text channels
@bot.command()
@commands.has_permissions(administrator=True)
async def mute(ctx, member:discord.Member, reason=None):
	await ctx.channel.purge(limit = 1)
	mute_role = utils.get(ctx.message.author.guild.roles, id=ids.MuteRole)
	await member.add_roles(mute_role)
	emb = discord.Embed(title=f'Пользователь {member.display_name} теперь не может писать в текстовых каналах сервера по причине \"{reason}\"', colour=discord.Colour.random())
	emb.set_image(url=gifs.MuteGIFs[randint(0, len(gifs.MuteGIFs) - 1)])
	await ctx.send(embed=emb)
	print(f'[Голосовой мут]: Участник {member.display_name} был успешно замучен')

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
		emb = discord.Embed(title=f'Пользователь {member.display_name} теперь может снова говорить в голосовых каналах!', colour=discord.Colour.random())
		emb.set_image(url=gifs.UnMuteGIFs[randint(0, len(gifs.UnMuteGIFs))])
		await ctx.send(embed=emb)
		print(f'[Анмьют] Пользователь {member.display_name} был успешно размучен в голосовых каналах')

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
		emb = discord.Embed(title=f'Пользователь {member.display_name} теперь может снова писать в текстовых каналах!', colour=discord.Colour.random())
		emb.set_image(url=gifs.UnMuteGIFs[randint(0, len(gifs.UnMuteGIFs))])
		await ctx.send(embed=emb)
		print(f'[Анмьют] Пользователь {member.display_name} был успешно размучен в текстовых каналах')

###############################################		fun		##############################################################

@bot.command(aliases=['поцеловать', 'поцелуй'])
async def kiss(ctx, member:discord.Member):
	c = ''
	if utils.get(ctx.message.author.guild.roles, id=ids.GirlRole) in ctx.message.author.roles: c = 'а'
	emb = discord.Embed(title='Поцелуй', description=f'{ctx.message.author.mention} поцеловал{c} {member.mention}', colour = discord.Colour.magenta())
	emb.set_image(url=gifs.KissGIFs[randint(0, len(gifs.KissGIFs) - 1)])
	await ctx.reply(embed=emb)
	print(f'[Поцелуй] Пользователь {ctx.message.author.display_name} поцеловал{c} {member.display_name}')

@bot.command(aliases=['ударить', 'удар'])
async def punch(ctx, member:discord.Member):
	c = ''
	if utils.get(ctx.message.author.guild.roles, id=ids.GirlRole) in ctx.message.author.roles: c = 'а'
	emb = discord.Embed(title='Удар', description= f'{ctx.message.author.mention} ударил{c} {member.mention}', colour = discord.Colour.from_rgb(255, 238, 0))
	emb.set_image(url=gifs.PunchGIFs[randint(0, len(gifs.PunchGIFs) - 1)])
	await ctx.reply(embed=emb)
	print(f'[Удар] Пользователь {ctx.message.author.display_name} ударил{c} {member.display_name}')

@bot.command(aliases=['шип', 'совместимость'])
async def ship(ctx, member:discord.Member):
	percent = randint(0, 100)
	if ctx.author == member:
		percent = 100
	rate = None
	if percent < 20: 
		rate = 'Несовместимы 😞'
	elif percent < 40:
		rate = 'Мало вероятно 😕'
	elif percent < 60:
		rate = 'Всё возможно 😉'
	elif percent < 80:
		rate = 'Хорошая пара 🥰'
	elif percent < 100:
		rate = 'Это любовь 💕'
	elif percent == 100 and ctx.author == member:
		rate = 'Каждый любит себя 😉'
	else:
		rate = 'Невероятно 💞'
	lane = '▣'*(percent//5) + '☐'*(20 - percent//5)
	await ctx.reply(content = f'💗 **СОВМЕСТИМОСТЬ** 💗\n🔻 `{ctx.author.display_name}`\n🔺 `{member.display_name}`', embed=discord.Embed(title = f'{ctx.author.display_name} + {member.display_name}', description = f'{percent}% {lane} {rate}', colour = discord.Colour.magenta()))
	print(f'[Совместимость] Пользователь {ctx.author.display_name} шипперит себя с {member.display_name}')

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
async def clear(ctx, number = 2):
	await ctx.channel.purge(limit=number)
	w = morph.parse('сообщение')[0]
	print(f'[Удаление сообщений] Удаление {number} {w.make_agree_with_number(number).word} произошло успешно')


@bot.command()
@commands.has_permissions(administrator=True)
async def react_to(ctx, msg_id, *, emoji_id):
	await ctx.channel.purge(limit = 1)
	message = await ctx.fetch_message(msg_id)
	await message.add_reaction(emoji=emoji_id)
	print('[Добавление эмоции] Добавление эмоции произошло успешно')

@bot.command()
@commands.has_permissions(administrator=True)
async def del_reaction(ctx, msg_id, emoji_id):
	await ctx.channel.purge(limit=1)
	message = await ctx.fetch_message(msg_id)
	await message.clear_reaction(emoji_id)
	print('[Удаление эмоции] Удаление эмоции произошло успешно')


##############################################		birthdays	#############################################################
@bot.command()
@commands.has_permissions(administrator=True)
async def set_birthday(ctx, user:discord.Member, dat:str):
	await ctx.channel.purge(limit = 1)
	if len(dat) != 10:
		print('[Установка дня рождения] Ошибка: Неверный формат даты рождения: длина даты != 10')
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Добавление дня рождения не удалось', colour=discord.Colour.red()))
		return
	day = None
	try:
		day = date(year = int(dat[:4:]), month = int(dat[5:7:]), day = int(dat[8::]))
	except:
		print('[Установка дня рождения] Ошибка: Неверный формат даты рождения')
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Добавление дня рождения не удалось', colour=discord.Colour.red()))
		return
	cursor.execute("SELECT id FROM birthdays WHERE id = %s", (user.id, ))
	result = cursor.fetchone()
	if not result:
		cursor.execute("INSERT INTO birthdays (id, birthday) VALUES (%s, %s)", (user.id, dat))
		db.commit()
	else:
		print('[Установка дня рождения] Ошибка: Такой пользователь уже есть в базе данных')
		await ctx.send(embed = discord.Embed(title='Произошла ошибка', description='Добавление дня рождения не удалось, т.к. у данного пользователя уже установлен день рождения. Чтобы изменить его, воспользуйтесь командой !change_birthday', colour=discord.Colour.red()))
		return
	left = days_left((user.id, dat))
	w = morph.parse('день')[0]
	await ctx.send(embed = discord.Embed(description='Я поздравлю **{0}** через {1} {2}'.format(user.display_name, left, w.make_agree_with_number(left).word), colour=discord.Colour.green(), title='Добавление дня рождения произошло успешно'))
	print('[Установка дня рождения] Пользователю {0} установлен день рождения: {1}'.format(user.display_name, dat))


@bot.command()
@commands.has_permissions(administrator=True)
async def change_birthday(ctx, user: discord.Member, dat:str):
	await ctx.channel.purge(limit = 1)
	if len(dat) != 10:
		print('[Изменение дня рождения] Неверный формат даты рождения: длина даты != 10')
		await ctx.send(embed = discord.Embed(title='Произошла ошибка', description='Изменение дня рождения не удалось', colour=discord.Colour.red()))
		return
	day = None
	try:
		day = date(year = int(dat[:4:]), month = int(dat[5:7:]), day = int(dat[8::]))
	except:
		print('[Изменение дня рождения] Неверный формат даты рождения')
		await ctx.send(embed = discord.Embed(title='Произошла ошибка', description='Изменение дня рождения не удалось', colour=discord.Colour.red()))
		return
	cursor.execute("SELECT id FROM birthdays WHERE id = %s", (user.id, ))
	result = cursor.fetchone()
	if not result:
		await ctx.send(embed = discord.Embed(description='Произошла ошибка', title='Изменение дня рождения не удалось, т.к. у данного пользователя не установлен день рождения. Чтобы установить его, воспользуйтесь командой !set_birthday', colour=discord.Colour.red()))
		print('[Изменение дня рождения] Ошибка: у данного пользователя уже установлен день рождения')
	cursor.execute("UPDATE birthdays SET birthday = %s WHERE id = %s", (dat, user.id))
	db.commit()
	left = days_left((user.id, dat))
	w = morph.parse('день')[0]
	await ctx.send(embed=discord.Embed(description='Изменение дня рождения произошло успешно. Я поздравлю **{0}** через {1} {2}'.format(user.display_name, left, w.make_agree_with_number(left).word), title='Изменение дня рождения', colour=discord.Colour.green()))
	print('[Изменение дня рождения] Пользователю {0} установлен день рождения: {1}'.format(user.display_name, dat))

@bot.command()
async def next_birthdays(ctx):
	today = datetime.now(tz=msk)
	cursor.execute("SELECT * FROM birthdays")
	bdays = {i : days_left(i) for i in sorted(cursor.fetchall(),key=days_left)[:10:]}
	descr = ''
	i = 1
	w = morph.parse("день")[0]
	for mem in bdays.items():
		member = await Members[0].guild.fetch_member(mem[0][0])
		colour = next((x[0] for x in get_roles.Roles1.items() if utils.get(member.guild.roles, id=x[1]) in member.roles), None)
		if colour is None: colour = ':white_circle:'
		if mem[1] == 0: descr += '{4} **#{0} {1}**\n**День рождения: **{2} {3} (сегодня)\n'.format(i, member.display_name, int(mem[0][1][8::]), morph.parse(NameOfMonths[int(mem[0][1][5:7:])][0])[0].inflect({'gent'}).word, colour)
		elif mem[1] == 1: descr += '{4} **#{0} {1}**\n**День рождения: **{2} {3} (завтра)\n'.format(i, member.display_name, int(mem[0][1][8::]), morph.parse(NameOfMonths[int(mem[0][1][5:7:])][0])[0].inflect({'gent'}).word, colour)
		else: descr += '{6} **#{0} {1}**\n**День рождения: **{2} {3} (через {4} {5})\n'.format(i, member.display_name, int(mem[0][1][8::]), morph.parse(NameOfMonths[int(mem[0][1][5:7:])][0])[0].inflect({'gent'}).word, mem[1], w.make_agree_with_number(mem[1]).word, colour)
		i += 1
	emb = discord.Embed(description=descr, title='Ближайшие дни рождения 🎂', colour=discord.Colour.teal())
	emb.set_thumbnail(url=Members[0].guild.icon_url)
	await ctx.reply(embed=emb)
	print('[Следующие дни рождения] Список следующих десяти дней рождений выведен успешно')

@bot.command(aliases=['др', 'день_рождения', 'день-рождения'])
async def birthday (ctx, member:discord.Member):
	today = datetime.now(tz=msk)
	cursor.execute("SELECT * FROM birthdays WHERE id = %s", (member.id,))
	bday = cursor.fetchall()
	if len(bday) == 0:
		emb = discord.Embed(title=f'У {member.display_name} не установлено дня рождения', colour=discord.Colour.random())
		emb.set_image(url=member.avatar_url)
	else:
		bday = bday[0]
		day = morph.parse('день')[0]
		month = morph.parse(NameOfMonths[int(bday[1][5:7:])][0])[0]
		dleft = days_left(bday)
		if dleft == 0:
			emb = discord.Embed(title='У {0} день рождения {1} {2} (сегодня) :birthday:'.format(member.display_name, int(bday[1][8::]), month.inflect({'gent'}).word), colour=discord.Colour.random())
		elif dleft == 1:
			emb = discord.Embed(title='У {0} день рождения {1} {2} (завтра)'.format(member.display_name, int(bday[1][8::]), month.inflect({'gent'}).word), colour=discord.Colour.random())
		else:
			emb = discord.Embed(title='У {0} день рождения {1} {2} (будет через {3} {4})'.format(member.display_name, int(bday[1][8::]), month.inflect({'gent'}).word, days_left(bday), day.make_agree_with_number(days_left(bday)).word), colour=discord.Colour.random())
		emb.set_image(url=member.avatar_url)
	await ctx.reply(embed=emb)
	print('[Получение дня рождения] День рождения получен успешно')

##############################################################		levels and stats 	#################################################################################

@bot.command(aliases=['статистика', 'стат', 'rang', 'ранк'])
async def stats(ctx, member = None):
	if member is None:
		member = ctx.message.author
	else:
		try:
			member = await Members[0].guild.fetch_member(int(member[2:-1:]))
		except:
			print('[Статистика] Был передан неверный аргумент')
			await ctx.reply('Неправильное использование команды. Для уточнения `!help stats`')
			return
	cursor.execute("SELECT * FROM levels WHERE id = %s", (member.id, ))
	info = cursor.fetchone()
	cursor.execute("SELECT * FROM levels WHERE exp <> 0 ORDER BY exp DESC")
	table = cursor.fetchall()
	rank = '-'
	try:
		rank = '#' + str(table.index(info) + 1)
	except:
		pass
	lane = levels.exp_lane(info[2], info[1])
	emb = discord.Embed(title=f'Уровень участника **{member.display_name}**', description=f'Уровень: **{info[2]}**    Ранг: **{rank}**\n{lane} {info[1]}/{levels.levels_exp[info[2] + 1]} EXP', colour = discord.Colour.random())
	emb.set_thumbnail(url=member.avatar_url)
	await ctx.reply(embed=emb)
	print(f'[Статистика] Пользователь {ctx.message.author.display_name} получил статистику по пользователю {member.display_name}')

@bot.command(aliases=['top', 'топ', 'рейтинг'])
async def rating(ctx):
	cursor.execute("SELECT * FROM levels WHERE exp <> 0 ORDER BY exp DESC")
	rating = cursor.fetchall()
	size = len(rating)
	embeds = []
	i = 1
	while len(rating) > 0:
		page = None
		if len(rating) < 10:
			page = rating
			rating = []
		else:
			page = rating[:10:]
			rating = rating[10::]
		description = ''
		stop_num = i + 10
		while i != stop_num and i <= size:
			person = utils.get(ctx.message.guild.members, id=page[(i - 1)%10][0])
			supplement = ''
			if i == 1: supplement = ':first_place:'
			elif i ==2: supplement = ':second_place:'
			elif i == 3: supplement = ':third_place:'
			else: 
				supplement = next((x[0] for x in get_roles.Roles1.items() if utils.get(person.guild.roles, id=x[1]) in person.roles), None)
				if supplement is None: supplement = ':white_circle:'
			description += f'{supplement} **#{i}.{person.display_name}**\n**Уровень:** {page[(i - 1) % 10][2]} | **Опыт:** {page[(i - 1)%10][1]}\n'
			i += 1
		embed = discord.Embed(title='🏆 Рейтинг участников', description=description, colour=discord.Colour.gold())
		embed.set_thumbnail(url=Members[0].guild.icon_url)
		embeds.append(embed)
	message = await ctx.reply(embed=embeds[0])
	paginator = pag(bot, message, only=ctx.author, embeds=embeds, use_more=False)
	await paginator.start()
	print(f'[Рейтинг] Пользователь {ctx.author.display_name} успешно получил рейтинг пользователей')
#############################################################################################

bot.run(os.getenv('TOKEN'))