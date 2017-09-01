import os
import requests
import json

import subprocess

QUIZLET_CLIENT_ID = 'AHx9Qur45k'
QUIZLET_SECRET_KEY = 'uG66b7NSPcx9YQBBF4eqbv'

REDIRECT_URL = 'http://htmlpreview.github.io/?https://github.com/Just4test/QuizletThisWord.popclipext/blob/master/docs/guide.html?'
POPCLIP_BUNDLE_ID = 'com.pilotmoon.popclip'
EXTENSION_ID = 'net.just4test.popclip.quizit'
OAUTH_CODE_ENV = 'POPCLIP_OPTION_OAUTH_CODE'
SET_ID_ENV = 'POPCLIP_OPTION_SET_ID'


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
	
def get_oauth_token(code):
	url = 'https://api.quizlet.com/oauth/token'
	params = {
		'code': code,
		'redirect_uri': REDIRECT_URL,
		'grant_type': 'authorization_code'
	}
	auth = requests.auth.HTTPBasicAuth(QUIZLET_CLIENT_ID, QUIZLET_SECRET_KEY)
	try:
		r = requests.post(url=url, params=params, auth=auth)
		print(r.json())
		if r.status_code == 200:
			return r.json()
		return None
	except requests.exceptions.RequestException as e:
		print('发生网络错误')
		exit()
	
def get_token():
	AUTH_SUCCESS = '******'
	code = defaults_storage_read('oauth_code')
	if code is not None and code != "" and code != AUTH_SUCCESS:
		data = get_oauth_token(code)
		if data is None:
			defaults_storage_write('oauth_code', '不正确的值')
			exit(2)
		defaults_storage_write('oauth_code', AUTH_SUCCESS)
		defaults_storage_write('access_token', data['access_token'])
		
	token = defaults_storage_read('access_token')
	if token is None:
		defaults_storage_write('oauth_code', '请指定此值')
		exit(2)
		
	return token
		
			
	
def add_term(set_id, term, definition):
	url = 'https://api.quizlet.com/2.0/sets/{}/terms'.format(set_id)
	params = {
		'term': term,
		'definition': definition
	}
	headers = {
		'Authorization': 'Bearer ' + get_token()
	}
	try:
		r = requests.post(url=url, params=params, headers=headers)
		if r.status_code == 201:
			return
		if r.status_code == 404 or r.status_code == 403:
			defaults_storage_write('set_id', '不正确的值')
			exit(2)
		if r.status_code == 401:
			defaults_storage_write('oauth_code', '过期，请重新输入')
			exit(2)
		print('发生未知错误，添加条目时返回 {}'.format(r.status_code))
		exit()
	except requests.exceptions.RequestException as e:
		print('发生网络错误')
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
		print('发生网络错误')
		exit()
	

word = os.environ.get('POPCLIP_TEXT', '')
word, definition = get_word_definition(word)

set_id = os.environ.get(SET_ID_ENV, '')
add_term(set_id, word, definition)

print(definition.replace('\n', ' '))
