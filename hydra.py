import cv2
from PIL import ImageGrab
import numpy as np
from copy import deepcopy
import time
import ctypes
import pyautogui as cs
from random import randint

hydra_folder_path = "C:\\Users\\Igor Farszky\\Desktop\\hydra\\"
png_ext = ".PNG"

templates = {}
templatesPaths = ['hydra_battle', 'hydra_boss', 'hydra_empty', 'hydra_fight', 
		'hydra_lost', 'hydra_me', 'hydra_x']
keys = ['1', '2', '3', '4', 'x', 
		'o', 'p', '[', ']', 'u', 
		'k', 'l', 'w', 'num7', 'h', 
		',', '.', '/', 'num1', 'num3']
middle_keys = ['p', ']', 'l',
			   'num7', '[', 'w']
cornerKeys = ['1', 'x', ',', 'num3']
			
blockBossMap = {'1' : ['o', '2'], 'x' : ['4', 'u'],
				',' : ['k', '.'], 'num3' : ['num1', 'h']}			
keymap = {}
		
#INITIALIZE TEMPLATES
def initTemplates():
	for path in templatesPaths:
		template = cv2.imread(hydra_folder_path + path + png_ext)
		template = np.float32(template)
		templates[path] = template
	
#DETERMINES IF GIVEN CENTER ALREADY FOUND IN RECTS OR NOT
def is_new_center(rects, center, dist):
    for c in rects:
        if np.abs(c[0]-center[0]) < dist and np.abs(c[1]-center[1]) < dist:
              return False

    return True	

#FIND LOCATION OF ME (LOC = CENTER OF ME BOX)	
def findMatchingTemplate(ss, tempName, thresh):
	template = templates.get(tempName)
	w, h = len(template[0]), len(template)
	
	ssc = deepcopy(ss)
	
	res = cv2.matchTemplate(ss, template, cv2.TM_CCOEFF_NORMED)
	threshold = thresh
	loc = np.where(res >= threshold)
	pos_rects = []
	for pt in zip(*loc[::-1]):
		cv2.rectangle(ssc, pt, (pt[0]+w, pt[1]+h), 255, 2)
		centar = (pt[0]+int(w/2), pt[1]+int(h/2))
		if is_new_center(pos_rects, centar, 20) == True:
			pos_rects.append(centar)
			
	return pos_rects

#REDUCE LIST TO  HAVE UNIQUE VALUES
def reduceList(sortList):
	redList = []
	for v in sortList:
		isInList = False
		for c in redList:
			if np.abs(v-c) < 20:
				isInList = True
				break
				
		if isInList == False:
			redList.append(v)
	
	return redList
	
#SORT THE HYDRA NET BY X THEN Y
def sortNet(net):
	sortX = []
	sortY = []
	for v in net:
		sortX.append(v[0])
		sortY.append(v[1])
		
	sortX.sort()
	sortY.sort()
	
	sortX = reduceList(sortX)
	sortY = reduceList(sortY)
	
	sortedNet = []
	
	for i in sortY:
		for j in sortX:
			sortedNet.append((j, i))
		
	return sortedNet
	
#INITIALIZE NET OF HYDRA BATTLEFIELD TO INITIALIZE KEY MAPS
def initNet(ss):
	me = findMatchingTemplate(ss, 'hydra_me', 0.8)
	boss = findMatchingTemplate(ss, 'hydra_boss', 0.8)
	battles = findMatchingTemplate(ss, 'hydra_battle', 0.7)
	empties = findMatchingTemplate(ss, 'hydra_empty', 0.65)
	
	print ('me: ', me)
	print ('boss: ', boss)
	print ('empties: ', empties)
	print ('battles: ', battles)
	
	if len(me) == 0 or len(battles) == 0:
		print ('INITIALIZATION FAILED - EXITING')
		exit(1)
	
	net = []
	net.extend(me)
	net.extend(boss)
	net.extend(empties)
	net.extend(battles)
	
	net = sortNet(net)
	
	j = 0
	for i in keys:
		keymap[i] = net[j]
		j = j + 1
		
	
		
#EUKLID DISTANCE
def euklid(me, battle):
	return np.sqrt(np.square(me[0][0]-battle[0])+np.square(me[0][1]-battle[1]))

#CLOSEST BATTLE TO ME
def findClosestbattle(me, battles):
	minBattle = (0, 0)
	minDist = 999
	for battle in battles:
		dist = euklid(me, battle)
		if dist < minDist:
			minDist = dist
			minBattle = battle
	
	return minBattle
	
#FIND KEY TO PRESS FOR GIVEN BATTLE
def findKey(battle):
	for key in keymap:
		keyBattle = keymap[key]
		if np.abs(keyBattle[0]-battle[0]) < 20 and np.abs(keyBattle[1]-battle[1]) < 20:
			return key
			
#CHECK IS CURRENT FIGHT LOST MAYBE
def fightIsLost():
	ss = ImageGrab.grab()
	ss = np.array(ss.getdata()).reshape((ss.size[1], ss.size[0], 3))
	ss = np.float32(ss)
	temp = deepcopy(ss[:, :, 0])
	ss[:, :, 0] = ss[:, :, 2]
	ss[:, :, 2] = temp[:]
	
	lost = findMatchingTemplate(ss, 'hydra_lost', 0.7)
	
	if len(lost) == 0:
		return False
	else:
		return True
		
#REALIZE THE FIGHT WITH GIVEN KEY PRESS FOR FOUND FIGHT
def doFight(key):
	cs.press(key)
	time.sleep(2)
	cs.press('e')
	time.sleep(1)
	cs.press('q')
	time.sleep(1)
	cs.press('q')
	
	return 0
	
#FIND BATTLES IN THE MIDDLE 6 SQUARES
def findMiddleBattles(battles):

	middle_battles = []

	for i in range(0, len(battles)):
		key = findKey(battles[i])
		if key in middle_keys:
			middle_battles.append(battles[i])
			
	return middle_battles
	
#DO FIGHTS IF BOSS IS BLOCKED
def blockedBoss(keyBoss, battles):
	
	blockedKeys = blockBossMap[keyBoss]
	
	count = 0
	for i in range(0, len(battles)):
		key = findKey(battles[i])
		if key in blockedKeys:
			count = count + 1
			
		if count > 1:
			print ('boss or me in corner - doing fight')
			doFight(key)
			break
			
def closeUnwantedWindows(ss):
	lost = findMatchingTemplate(ss, 'hydra_x', 0.8)
	print ('LOST: ', lost)
	
	if len(lost) == 0:
		return False
	else:
		cs.press('esc')
		return True

#STARTING FUNCTION
def main():

	print ('PROGRAM STARTED')
	
	initTemplates()
	print ('TEMPLATES INITIALIZED')
	time.sleep(2)
	
	ss = ImageGrab.grab()
	ss = np.array(ss.getdata()).reshape((ss.size[1], ss.size[0], 3))
	ss = np.float32(ss)
	temp = deepcopy(ss[:, :, 0])
	ss[:, :, 0] = ss[:, :, 2]
	ss[:, :, 2] = temp[:]
	print ('TOOK INIT SCREENSHOT')
	
	initNet(ss)
	print ('INITIALIZED HYDRA BATTLE NETWORK')
	print ('BATTLE NETWORK: \n')
	for key in keymap:
		print (key, ' : ', keymap[key])
	
	time.sleep(1)
	lives = 5
	
	while lives > 2:
	
		time.sleep(2)
		
		#SCREENSHOT
		print ('TOOKING BATTLE SCREENSHOT')
		ss = ImageGrab.grab()
		ss = np.array(ss.getdata()).reshape((ss.size[1], ss.size[0], 3))
		ss = np.float32(ss)
		temp = deepcopy(ss[:, :, 0])
		ss[:, :, 0] = ss[:, :, 2]
		ss[:, :, 2] = temp[:]
		
		me = findMatchingTemplate(ss, 'hydra_me', 0.7)
		battles = findMatchingTemplate(ss, 'hydra_battle', 0.7)
		boss = findMatchingTemplate(ss, 'hydra_boss', 0.7)
		
		if closeUnwantedWindows(ss):
			lives = lives - 1
			time.sleep(1)
			continue
		
		print ('ME: ', me)
		print ('BATTLES: ', battles)
		print ('BOSS: ', boss)
		
		if len(me) == 0 or len(battles) == 0:
			print ('NO BATTLES OR ME - SOMETHING IS WRONG - EXITING')
			exit(1)
		
		middle_battles = findMiddleBattles(battles)
		
		print ('MIDDLE: ', middle_battles)
		
		meKey = findKey(me[0])
		
		if len(boss) > 0:
		
			boss = boss[0]
			key = findKey(boss)
			print ('BOSS KEY: ', key)
			
			if key in cornerKeys:
				blockedBoss(key, battles)
			elif meKey in cornerKeys:
				blockedBoss(meKey, battles)
				
			lives = lives + doFight(key)
			
		elif len(middle_battles) > 0:
		
			closestBattle = findClosestbattle(me, middle_battles)
			key = findKey(closestBattle)
			print ('CLOSEST BATTLE: ', key, closestBattle)
			
			if meKey in cornerKeys:
				print ('ME IN CORNER: ', meKey)
				blockedBoss(meKey, battles)
			
			lives = lives + doFight(key)
			
		else:
		
			closestBattle = findClosestbattle(me, battles)
			key = findKey(closestBattle)
			print ('CLOSEST BATTLE: ', key, closestBattle)
			
			if meKey in cornerKeys:
				print ('ME IN CORNER: ', meKey)
				blockedBoss(meKey, battles)
			
			lives = lives + doFight(key)
			
main()