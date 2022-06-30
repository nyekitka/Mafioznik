import os, sys

Mafia = {}
Doctor = {}
Sheriff = {}
Innocent = {}


path = os.path.abspath(os.path.dirname(sys.argv[0]))
def load_stats():
	with open(path + '/stats/mafia.txt') as mafia:
		for line in mafia:
			s = line.strip()
			s = s.split()
			Mafia[int(s[0])] = int(s[1])

	with open(path + '/stats/doctor.txt') as doctor:
		for line in doctor:
			s = line.strip()
			s = s.split()
			Doctor[int(s[0])] = int(s[1])

	with open(path + '/stats/sheriff.txt') as sheriff:
		for line in sheriff:
			s = line.strip()
			s = s.split()
			Sheriff[int(s[0])] = int(s[1])

	with open(path + '/stats/innocent.txt') as innocent:
		for line in innocent:
			s = line.strip()
			s = s.split()
			Innocent[int(s[0])] = int(s[1])

def save_stats(mafia=True, doctor=True, sheriff=True, innocent=True):
	if mafia:
		with open(path + '/stats/mafia.txt', mode='w') as maf:
			for i in Mafia.keys():
				maf.write(str(i) + ' ' + str(Mafia[i]) + '\n')

	if doctor:
		with open(path + '/stats/doctor.txt', mode='w') as doc:
			for i in Doctor.keys():
				doc.write(str(i) + ' ' + str(Doctor[i]) + '\n')

	if sheriff:
		with open(path + '/stats/sheriff.txt', mode='w') as sher:
			for i in Sheriff.keys():
				sher.write(str(i) + ' ' + str(Sheriff[i]) + '\n')

	if innocent:
		with open(path + '/stats/innocent.txt', mode='w') as inn:
			for i in Innocent.keys():
				inn.write(str(i) + ' ' + str(Innocent[i]) + '\n')


