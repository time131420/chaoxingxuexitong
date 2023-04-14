import datetime
import random
import requests
from bs4 import BeautifulSoup
import schedule
import logging
from pyDes import des, PAD_PKCS5, ECB
import binascii

# 日报内容
dayContent = ['xxxx','感受很好']
# 周报内容
weekContent = []
# 月报内容 
mondayContent = []

header = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
}

# 用户密码加密
def des_encrypt(s):
    """
    DES 加密
    :param s: 原始字符串
    :return: 加密后字符串，16进制
    """
    secret_key = b'u2oh6Vu^'
    iv = secret_key
    k = des(secret_key, ECB, iv, pad=None, padmode=PAD_PKCS5)
    en = k.encrypt(s, padmode=PAD_PKCS5)
    return binascii.b2a_hex(en).decode('utf-8')

# 登录
def login(username, password):
    url = 'https://passport2.chaoxing.com/fanyalogin'
    header = {
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With':'XMLHttpRequest',
    }
    data = {
        'fid': '-1',
        'uname': username,
        'password': des_encrypt(password),
        'refer': 'https%3A%2F%2Fi.chaoxing.com',
        't': True,
        'forbidotherlogin': 0,
        'validate': '',
        'doubleFactorLogin': 0,
        'independentId': 0,

    }
    res = requests.post(url, data=data,headers=header)
    if res.json()['status']:
        global cookie
        cookie = requests.utils.dict_from_cookiejar(res.cookies)
        return cookie
    return False

# 获取打卡参数
def getParameter():
    html_doc = requests.get('https://v1059.dgsx.chaoxing.com/mobile/clockin/show',cookies=cookie).text
    soup = BeautifulSoup(html_doc, 'html.parser')
    recruitId = soup.find('input',id='recruitId')['value']
    pcid = soup.find('input',id='pcid')['value']
    pcmajorid = soup.find('input',id='pcmajorid')['value']
    return recruitId,pcid,pcmajorid

# 打卡
def addclockin():
    url = 'https://v1059.dgsx.chaoxing.com/mobile/clockin/addclockin2'

    recruitId,pcid,pcmajorid = getParameter()
    data = {
        'id': 0,
        'type': 0,
        'recruitId': recruitId,
        'pcid': pcid,
        'pcmajorid': pcmajorid,
        'address': address,
        'geolocation': geolocation,
        'remark': '',
        'workEnd': '',
        'allowOffset': 2000,
        'offset': 'NaN',
        'offduty': 0,
        'changeLocation': '',
        'workStart': '',
        'images': '',
    }
    res = requests.post(url=url, data=data, headers=header,cookies=cookie)
    if res.json()['success']:
        print('打卡成功')
    else:
        print('打卡失败')

# 日报
def daily():
    now = datetime.datetime.now()
    d = datetime.datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
    global day
    day = (now-d).days
    newDay = now.strftime('%Y-%m-%d')
    if int(day) > maxDays:
        return
    url = 'https://v1059.dgsx.chaoxing.com/daily/mobile/student/save?id=&newspaperid=' + str(day) + '&type='
    dt = random.choices(dayContent)
    data = {
        'experience': dt,
        'report': '<p>' + dt +'</p >',
        'content1': '',
        'content2': '',
        'content3': '',
        'content4': '',
        'date': newDay,
        'exceptionalcase': '',
        'professionalrelatedinformation': '',
        'outstandingachievements': ''
    }
    requests.post(url=url, data=data, headers=header,cookies=cookie)

# 周报
def week():
    '''
        newspaperid:第几周
        report:主要内容
        experience:收获和感受
    '''
    newspaperid = int(day/7)
    dt = random.choices(mondayContent)
    data = {
        'newspaperid':newspaperid,
        'report':f'<p>' + dt + '</p>',
        'experience':dt
    }
    requests.post(url='https://v1059.dgsx.chaoxing.com/stunews/mobile/save?id=&type=0',data=data,cookies=cookie)

# 月报
def monday():
    '''
        newspaperid:第几个月
        report:主要内容
        experience:收获和感受
    '''
    
    newspaperid = round(day/30)
    dt = random.choices(mondayContent)
    data = {
        'newspaperid':newspaperid,
        'report':f'<p>' + dt + '</p>',
        'experience':dt
    }
    requests.post(url='https://v1059.dgsx.chaoxing.com/stunews/mobile/save?id=&type=1',data=data,cookies=cookie)

def main():
    # 打卡
    schedule.every().day.at("08:30").do(addclockin)
    # 日报
    schedule.every().day.at("08:30").do(daily)
    # 每周三执行周报
    schedule.every().wednesday.at("00:00").do(week)
    # 每月执行
    schedule.every().monday.do(monday)

def start():
    global address,geolocation,maxDays,startTime
    # 地址
    address  = 'xxx'
    # 经纬度
    geolocation = '11,31'
    # 开始时间
    startTime = "2022-08-31 08:30:00"
    # 最大打卡天数
    maxDays = 181
    if login('账号','密码'):
        addclockin()
        daily()
        week()
        monday()
    else:
        print('用户名或密码错误')

# 阿里云函数计算主函数
def handler(event, context):
  logger = logging.getLogger()
  logger.info('hello world')
  start()
  return 'hello world'