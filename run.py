import sys
if not ('packages' in sys.path):
	sys.path.insert(0, 'packages')
if not ('packages.zip' in sys.path):
	sys.path.insert(0, 'packages.zip')

import os
import googletrans
import requests
import json
import subprocess

REDIRECT_URL = 'http://htmlpreview.github.io/?https://github.com/Just4test/QuizletThisWord.popclipext/blob/master/docs/guide.html?'
POPCLIP_BUNDLE_ID = 'com.pilotmoon.popclip'
EXTENSION_ID = 'net.just4test.popclip.quizit'
POPCLIP_OPTION_PREFIX = 'POPCLIP_OPTION_'

#现在可以从guide页面上直接获取access token了
def defaults_storage_write(key, value):
	'使用defaults存储文本'
	args = ['defaults', 'write', POPCLIP_BUNDLE_ID, 'extension#{}#{}'.format(EXTENSION_ID, key), str(value)]
	temp = subprocess.run(args, stdout=subprocess.PIPE)

def defaults_storage_read(key, default_value = None):
	'读取存储在defaults中的文本'
	args = ['defaults', 'read', POPCLIP_BUNDLE_ID, 'extension#{}#{}'.format(EXTENSION_ID, key)]
	temp = subprocess.run(args, stdout=subprocess.PIPE)
	if temp.returncode == 0:
		return temp.stdout.decode('unicode-escape').rstrip('\n') #turn binary string to string, and remove \n
	return default_value
	
def read_config(*keys):
	'''
	假设插件提供了id为xxx的选项：
	用户指定xxx的值为1时，Popclip将其写入defaults，可使用 defaults_storage_read('xxx') 读出。
	插件运行时，Popclip将环境变量 POPCLIP_OPTION_XXX 指定为1。
	安装插件新版本时，Popclip清空该插件的所有选项的值。
	
	为了调试方便，读取option的逻辑如下：
	1. 从环境变量读取 POPCLIP_OPTION_XXX 值。这包含两种情况：
		1. 代码在Popclip中运行，读出的值来自 defaults 默认位置。
		2. 代码在IDE中运行，读出的值来自IDE配置。
	2. 如果值存在，则写入 defaults 备份位置。 defaults_storage_write(key + '_backup', v)
	3. 如果值不存在，则从 defaults 备份位置读出备份的值，并写入defaults默认位置。这个动作可以保证，用户下次打开配置面板时，该option已被填充。
	'''
	results = []
	for key in keys:
		# read config from env. If no value, 
		v = os.environ.get(POPCLIP_OPTION_PREFIX + key.upper(), '')
		if v == '':
			v = defaults_storage_read(key + '_backup', '')
			defaults_storage_write(key, v)
		else:
			defaults_storage_write(key + '_backup', v)
		results.append(v)
	
	return results

#def get_oauth_token(code):
#	url = 'https://api.quizlet.com/oauth/token'
#	params = {
#		'code': code,
#		'redirect_uri': REDIRECT_URL,
#		'grant_type': 'authorization_code'
#	}
#	auth = requests.auth.HTTPBasicAuth(QUIZLET_CLIENT_ID, QUIZLET_SECRET_KEY)
#	try:
#		r = requests.post(url=url, params=params, auth=auth)
#		if r.status_code == 200:
#			return r.json()
#		return None
#	except requests.exceptions.RequestException as e:
#		print('发生网络错误')
#		exit()
#
#def get_token():
#	AUTH_SUCCESS = '******'
#	code = defaults_storage_read('oauth_code')
#	if code is not None and code != "" and code != AUTH_SUCCESS:
#		data = get_oauth_token(code)
#		if data is None:
#			defaults_storage_write('oauth_code', '不正确的值')
#			exit(2)
#		defaults_storage_write('oauth_code', AUTH_SUCCESS)
#		defaults_storage_write('access_token', data['access_token'])
#
#	token = defaults_storage_read('access_token')
#	if token is None:
#		defaults_storage_write('oauth_code', '请指定此值')
#		exit(2)
#
#	return token



def add_term(access_token, set_id, term, definition):
	url = 'https://api.quizlet.com/2.0/sets/{}/terms'.format(set_id)
	params = {
		'term': term,
		'definition': definition
	}
	headers = {
		'Authorization': 'Bearer ' + access_token
	}
	try:
		r = requests.post(url=url, params=params, headers=headers)
		if r.status_code == 201:
			return
		if r.status_code == 404 or r.status_code == 403:
			defaults_storage_write('set_id', '不正确的值')
			print('Set ID 不正确！')
			exit(2)
		if r.status_code == 401:
			defaults_storage_write('oauth_code', '过期，请重新输入')
			print('Oauth Code 过期！')
			exit(2)
		print('发生未知错误，添加条目时返回 {}'.format(r.status_code))
		exit()
	except requests.exceptions.RequestException as e:
		print('向Quizlet添加生词时发生网络错误\n{}\n{}'.format(url, e))
		exit()

def get_word_definition(word):
	try:
		r = requests.get('https://api.shanbay.com/bdc/search/',
			params={'word': word}
		)
		r = r.json()

		if r['status_code'] != 0:
			print(r['msg'])
			exit(0)

		return r['data']['content'], r['data']['definition']
	except requests.exceptions.RequestException as e:
		print('查询单词定义时发生网络错误\n', e)
		exit()
		
def get_sentences_translation(sentence):
	sentence = sentence.replace('\r\n', ' ').replace('\n', ' ').replace('\n', ' ')
	try:
		translator = googletrans.Translator()
		return sentence, translator.translate(sentence, dest='zh-cn').text
	except requests.exceptions.RequestException as e:
		print('查询句子定义时发生网络错误\n', e)
		exit()
		
		
#def check_new_
		


word = os.environ.get('POPCLIP_TEXT', '')
if ' ' in word:
	word, definition = get_sentences_translation(word)
else:
	word, definition = get_word_definition(word)

set_id, access_token = read_config('set_id', 'access_token')
if set_id == '' or access_token == '':
	print('set_id = "{}", access_token = "{}"'.format(set_id, access_token))
	exit(2)
	
add_term(access_token, set_id, word, definition)

print(definition.replace('\n', ' '))
