# coding: utf-8
# !/usr/bin/python

import sys
import requests
import json
from Crypto.Cipher import AES
import base64
import math
import random
import re

stuid = ''  # 请填入学号

data = {
	'username': '',  # 请输入统一认证号
	'password': ''  # 请输入统一认证号密码
}

headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
	'Host': 'my.cqu.edu.cn',
	'Referer': 'http://my.cqu.edu.cn/enroll/cas',
	'Upgrade-Insecure-Requests': '1',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Encoding': 'gzip, deflate',
	'Connection': 'keep-alive'
}


class AESUtil:
	__BLOCK_SIZE_16 = BLOCK_SIZE_16 = AES.block_size

	@staticmethod
	def encrypt(str, key, iv):
		cipher = AES.new(key, AES.MODE_CBC, iv)
		x = AESUtil.__BLOCK_SIZE_16 - (len(str) % AESUtil.__BLOCK_SIZE_16)
		if x != 0:
			str = str + chr(x)*x
		str = str.encode()
		msg = cipher.encrypt(str)
		# msg = base64.urlsafe_b64encode(msg).replace('=', '')
		msg = base64.b64encode(msg)
		return msg

	@staticmethod
	def decrypt(enStr, key, iv):
		cipher = AES.new(key, AES.MODE_CBC, iv)
		# enStr += (len(enStr) % 4)*"="
		# decryptByts = base64.urlsafe_b64decode(enStr)
		decryptByts = base64.b64decode(enStr)
		msg = cipher.decrypt(decryptByts)
		paddingLen = ord(msg[len(msg)-1])
		return msg[0:-paddingLen]


chars = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
charsLen = len(chars)


def randomString(len):
	retStr = ''
	i = 0
	while(i < len):
		index = int(math.floor(random.random()*charsLen))
		retStr += chars[index]
		i += 1
	return retStr


def getAesString(data, key, iv):
	key = key.encode()
	iv = iv.encode()
	return AESUtil.encrypt(data, key, iv)


def encryptAes(data, aesKey):
	encrypted = getAesString(randomString(64) + data, aesKey, randomString(16))
	return encrypted


def printJson(courseName, instructorName, courseDetails):
	dic1 = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7}
	timestr = courseDetails['teachingWeekFormat']
	times = timestr.split(',')

	global classTimejson, errors, classInfoArray

	i = 0
	while(i < len(times)):  # 对于每个课程时间单独处理
		if(times[i].find('-') != -1):
			startWeek = times[i].partition('-')[0]
			endWeek = times[i].partition('-')[2]
		else:
			startWeek = endWeek = times[i]
		weekday = dic1[courseDetails['weekDayFormat']]
		classroom = courseDetails['roomName']
		
		j = 0
		classTime = -1
		while(j < len(classTimejson['classTime'])):  # 获取json中对应编号
			if(courseDetails['periodFormat'] == classTimejson['classTime'][j]['name']):
				classTime = j
			j += 1

		if(classTime == -1):
			print('检测到未配置的课程时间：' + courseDetails['periodFormat'] + '小节，请在 conf_classTime.json 中进行配置')
			errors += 1
		else:
			classTime += 1

		timeMap = {}
		timeMap['startWeek'] = int(startWeek)
		timeMap['endWeek'] = int(endWeek)

		classMap = {}
		classMap['className'] = courseName + ' ' + instructorName  # 课程名 + 导师名
		classMap['week'] = timeMap  # 开始结束周
		classMap['weekday'] = weekday  # 周几
		classMap['classTime'] = classTime  # 上课时间
		classMap['classroom'] = classroom  # 教室
		# sheet1.write(row, 4, 3)  # 单数双数周（暂无用）
		
		classInfoArray.append(classMap)

		i += 1


def getSubUtilSimple(soap, regx):
	matchObj = re.findall(regx, soap)
	return matchObj[0]
	return ""


loginHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}


def login():

	global session

	loginURL = "http://authserver.cqu.edu.cn/authserver/login"
	session = requests.session()
	html = session.get(loginURL).text
	
	ltRegex = r'name=\"lt\" value=\"(.*)\"/>'
	executionRegex = r'name=\"execution\" value=\"(.*)\"/>'
	keyRegex = r'pwdDefaultEncryptSalt = \"(.*)\"'
	
	lt = getSubUtilSimple(html, ltRegex)
	execution = getSubUtilSimple(html, executionRegex)
	key = getSubUtilSimple(html, keyRegex)
	
	data['password'] = encryptAes(data['password'], key).decode('utf-8')
	data['dllt'] = 'userNamePasswordLogin'
	data['execution'] = execution
	data['lt'] = lt
	data['_eventId'] = 'submit'
	data['rmShown'] = '1'
	
	postResult = session.post(url=loginURL, data=data, headers=loginHeaders)
	
	# print(postResult.text)
	
	'''
	res = requests.get(loginURL)
	
	cookies = requests.utils.dict_from_cookiejar(res.cookies)  # 转成字典格式
	
	print(cookies)
	
	cookiesStr = "; ".join([str(x)+"="+str(y) for x,y in cookies.items()])
	loginHeaders['Cookie'] = cookiesStr
	headers['Cookie'] = cookiesStr
	
	print(cookiesStr)
	'''
	
if __name__ == '__main__':
	
	global session
	
	login()
	
	data = {}
	data['client_id'] = 'enroll-prod'
	data['client_secret'] = 'app-a-1234'
	data['redirect_uri'] = 'http://my.cqu.edu.cn/enroll/token-index'
	data['grant_type'] = 'authorization_code'
	
	'''
	session.headers = headers
	
	cookies_str = ''
	cookies_str = str(dict([l.split("=", 1) for l in cookies_str.split("; ")]))
	cookies_dict = json.loads(cookies_str.replace("'","\""))
	cookies = requests.utils.cookiejar_from_dict(cookies_dict)
	session.cookies = cookies
	
	print(session.headers)
	print(session.cookies)
	'''
	res = session.get('http://my.cqu.edu.cn/authserver/oauth/authorize?client_id=enroll-prod&response_type=code&scope=all&state=&redirect_uri=http://my.cqu.edu.cn/enroll/token-index')
	print(res.status_code)
	print(res.url)
	print(res.headers)
	print(res.text)
	
	
	res = session.get(url = 'http://my.cqu.edu.cn/enroll/token-index', data=data, headers=loginHeaders)
	print(res.text)

	url = 'http://my.cqu.edu.cn/api/enrollment/timetable/student/' + stuid

	body = session.get(url, data=data, headers=headers)  # 完成假访问
	courses = json.loads(body.text)
	
	print(body.text)

	global classTimejson, errors, classInfoArray
	
	classInfoArray = []

	with open(sys.path[0] + '/conf_classTime.json', 'r', encoding='UTF-8') as jsonfile:
		classTimejson = json.load(jsonfile)

	i = 0
	lasting = 1
	lastID = 0
	while(i < len(courses['data'])):
		courseDetails = courses['data'][i]
		courseName = courseDetails['courseName']
		instructorName = courseDetails['classTimetableInstrVOList'][0]['instructorName']
		courseID = courseDetails['id']
		
		if(courseDetails['classType'] != '理论'):
			courseName = courseName + courseDetails['classType']
		
		if(lastID == courseID):
			lasting += 1
		else:
			lasting = 1
		
		if(lasting == 1):
			print('已获取课程 ' + courseName + ' 导师名: ' + instructorName + ' 与课程时间地点')
		
		printJson(courseName, instructorName, courseDetails)  # 获取信息填充Json
		
		if(lasting == body.text.count("\"id\":\"" + str(courseID) + "\"")):
			print('已储存课程信息\n')
		
		i += 1
		lastID = courseID

	map = {}
	map['classInfo'] = classInfoArray
	
	with open(sys.path[0] + '/conf_classInfo.json', 'w', encoding = 'gb2312') as f:
		f.write(json.dumps(map, ensure_ascii = False))
		f.close()
	
	print('已导出json\n')