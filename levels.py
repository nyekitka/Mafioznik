levels_exp = [
	0,		#0
	1,		#1
	5,		#2
	20,		#3
	50,		#4
	100,	#5
	200,	#6
	325,	#7
	500,	#8
	700,	#9
	1000,	#10
	1500,	#11
	2000,	#12
	2750,	#13
	3750,	#14
	5000,	#15
	7000,	#16
	10000,	#17
	15000,	#18
	20000,	#19
	30000	#20
]
def check_level(cur_lvl, exp):
	if cur_lvl == 20:
		return 0
	else:
		new_lvl = cur_lvl
		while levels_exp[new_lvl] > exp:
			new_lvl += 1
		new_lvl -= 1
		return new_lvl - cur_lvl

def exp_lane(cur_lvl, exp):
	if cur_lvl == 20:
		return '▣'*50
	else:
		percent = round(((exp - levels_exp[cur_lvl])/(levels_exp[cur_lvl + 1] - levels_exp[cur_lvl]))*50)
		return '▣'*percent + '☐'*(50 - percent)

