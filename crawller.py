# coding: utf-8
#!/usr/bin/python

import sys
import requests
import json
import xlwt

headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
	'Host': 'my.cqu.edu.cn',
	'Referer': 'http://my.cqu.edu.cn/enroll/CourseStuSelectionList',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Encoding': 'gzip, deflate',
	'Connection': 'keep-alive',
	'Authorization': '', # 填入Bearer码
	'Cookie': '' # 填入Cookie
}

def getCourseTime(encryptedCourseId): # 通过课程加密名称获取已选课程信息
	url = 'http://my.cqu.edu.cn/enroll-api/enrollment/courseDetails/'+encryptedCourseId+'?selectionSource=%E4%B8%BB%E4%BF%AE'

	body = requests.get(url,headers=headers) # 完成假访问
	courseTable = json.loads(body.text)

	classes = courseTable['selectCourseListVOs'][0]['selectCourseVOList']
	
	i = 0
	while(i < len(classes)):
		if(classes[i]['selectedFlag'] == True): # 找到选课
			return classes[i]
		i += 1

def printExcel(courseName, courseDetails):
	dic1 = { '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7 }
	timestr = courseDetails['classTime']
	times = timestr.split(';')

	global f, sheet1, row, classTimejson

	i = 0
	while(i < len(times)): # 对于每个课程时间单独处理
		timeformat = times[i].split(' ')
		if(len(timeformat) < 4): # 格式有误，可能是未分配时间
			print(courseName + '时间或地点未分配，已跳过处理')
			i += 1
			continue
		row += 1
		if(timeformat[0].find('-') != -1):
			startWeek = timeformat[0].partition('周')[0].partition('-')[0]
			endWeek = timeformat[0].partition('周')[0].partition('-')[2]
		else:
			startWeek = endWeek = timeformat[0].partition('周')[0]
		weekday = dic1[timeformat[1].partition('星期')[2]]
		classroom = timeformat[3].partition('&')[2]
		
		j = 0
		classTime = -1
		while(j < len(classTimejson['classTime'])): # 获取json中对应编号
			if(timeformat[2] == classTimejson['classTime'][j]['name']):
				classTime = j
			j += 1

		if(classTime == -1):
			print('检测到未配置的课程时间：'+timeformat[2]+'，请在 conf_classTime.json 中进行配置')
		else:
			classTime += 1

		extraWeek = -1
		if(endWeek.find(',') != -1): # 有的时间分配带逗号，单独处理
			extraWeek = endWeek.partition(',')[2]
			endWeek = endWeek.partition(',')[0]

		sheet1.write(row,0,courseName + ' ' + courseDetails['instructorNames']) # 课程名+导师名
		sheet1.write(row,1,startWeek) # 开始周
		sheet1.write(row,2,endWeek) # 结束周
		sheet1.write(row,3,weekday) # 周几
		sheet1.write(row,4,3) # 单数双数周（暂无用）
		sheet1.write(row,5,classTime) # 上课时间
		sheet1.write(row,6,classroom) # 教室

		if(extraWeek != -1):
			row += 1
			sheet1.write(row,0,courseName + ' ' + courseDetails['instructorNames']) # 课程名+导师名
			sheet1.write(row,1,extraWeek) # 开始周
			sheet1.write(row,2,extraWeek) # 结束周
			sheet1.write(row,3,weekday) # 周几
			sheet1.write(row,4,3) # 单数双数周（暂无用）
			sheet1.write(row,5,classTime) # 上课时间
			sheet1.write(row,6,classroom) # 教室

		i += 1

def processDetails(courseName, courseDetails):
	printExcel(courseName,courseDetails) # 一般理论课
	
	if(courseDetails['childrenList'] != None): # 有实验课
		print('课程包含实验课，正在处理实验课信息')
		printExcel(courseName+'实验',courseDetails['childrenList'][0])

if __name__ == '__main__':
	url = 'http://my.cqu.edu.cn/enroll-api/enrollment/course-list?selectionSource=%E4%B8%BB%E4%BF%AE'

	body = requests.get(url,headers=headers) # 完成假访问
	courses = json.loads(body.text)

	flag = 0
	courseList = []

	global f, sheet1, row, classTimejson
	f = xlwt.Workbook()
	sheet1 = f.add_sheet(u'sheet1',cell_overwrite_ok=True) # 创建Excel
	row0 = [u'className',u'startWeek',u'endWeek',u'weekday',u'week',u'classTime',u'classroom']
	row = 0

	for i in range(0,len(row0)): # 第一行
		sheet1.write(0,i,row0[i])

	with open(sys.path[0] + '/conf_classTime.json', 'r', encoding='UTF-8') as jsonfile:
		classTimejson = json.load(jsonfile)


	while(flag < 5): # 主修、体育、英语、通识、非限
		i = 0
		while(i < len(courses['data'][flag]['courseVOList'])):
			if(courses['data'][flag]['courseVOList'][i]['courseEnrollSign'] == '已选'):
				courseList += courses['data'][flag]['courseVOList'][i]
				print('正在获取课程 ' + courses['data'][flag]['courseVOList'][i]['name'] + ' 信息')
				courseDetails = getCourseTime(courses['data'][flag]['courseVOList'][i]['encryptedCourseId'])
				print('已获取导师名: ' + courseDetails['instructorNames'] + ' 与课程时间地点')
				processDetails(courses['data'][flag]['courseVOList'][i]['name'], courseDetails)
				print('已储存课程信息\n')
			i += 1
		flag += 1

	f.save('classInfo.xls')