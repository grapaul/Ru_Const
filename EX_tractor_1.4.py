import io
import os
import re
import yaml
import json
import pathlib
import argparse
import itertools
import traceback


def error1(msg):
	print('ERROR: {}'.format(msg))
	exit(1)


class TokenMatching:
	def __init__(self):
		self.token_index = None
		self.token = None
		self.constituent = None
		self.slot_name = None
		self.rule_elem = None

	def __repr__(self):
		return self.token['token']


class SlotValue:
	def __init__(self):
		self.text = None
		self.key_index = None
		self.key_word = None
		self.key_lemma = None

	def __repr__(self):
		return self.text


class ExtractedExample:
	def __init__(self):
		self.example_name = None
		self.matched_rule = None
		self.example_text = None
		self.slot2value = None

	def __repr__(self):
		s = self.example_name if self.example_name else ''
		if self.matched_rule:
			s += ', ' + self.matched_rule.get_name()
		s += ' -> '
		if self.example_text:
			s += self.example_text

		return s

	def get_example_name(self):
		return self.example_name

	def get_subexample_name(self):
		return self.matched_rule.get_name()

	def get_text(self):
		return self.example_text

	def get_slots(self):
		return list(self.slot2value.items())


class SubexampleItem:
	"""Загруженная секция в разделе Items подпримера"""
	def __init__(self):
		self.participant = None
		self.slot_name = None
		self.Lex = None
		self.LexNonHead = None
		self.Wordform = None
		self.WordformNonHead = None
		self.RussianLex = None
		self.RussianLexNonHead = None
		self.RussianWordform = None
		self.ConstituentType = None
		self.Morph = None
		self.Orth = None
		self.optional = False
		self.value = 'token'
		self.Show = None

	def __repr__(self):
		s = '{}: {}'.format(self.participant, self.slot_name)
		return s

	def load_yaml(self, yaml_data, dirname):
		self.participant = list(yaml_data.keys())[0]  # !!! завязались на порядок, нехорошо
		self.slot_name = yaml_data[self.participant]
		if self.slot_name is None:
			raise RuntimeError('Для участника "{}" не задано имя слота'.format(self.participant))

		if 'Lex' in yaml_data:
			self.Lex = [lex.strip() for lex in yaml_data['Lex'].split('|')]
		elif 'List' in yaml_data:
			fname = os.path.join(dirname, yaml_data['List'] + '.txt')
			with io.open(fname, 'r', encoding='utf-8') as rdr:
				self.Lex = [line.strip() for line in rdr]

		if 'LexNonHead' in yaml_data:
			self.LexNonHead = [lex.strip() for lex in yaml_data['LexNonHead'].split('|')]
		elif 'ListNonHead' in yaml_data:
			fname = os.path.join(dirname, yaml_data['ListNonHead'] + '.txt')
			with io.open(fname, 'r', encoding='utf-8') as rdr:
				self.LexNonHead = [line.strip() for line in rdr]

		if 'Wordform' in yaml_data:
			self.Wordform = [lex.strip() for lex in yaml_data['Wordform'].split('|')]
		elif 'ListWordform' in yaml_data:
			fname = os.path.join(dirname, yaml_data['ListWordform'] + '.txt')
			with io.open(fname, 'r', encoding='utf-8') as rdr:
				self.Wordform = [line.strip() for line in rdr]

		if 'WordformNonHead' in yaml_data:
			self.WordformNonHead = [lex.strip() for lex in yaml_data['WordformNonHead'].split('|')]
		elif 'ListWordformNonHead' in yaml_data:
			fname = os.path.join(dirname, yaml_data['ListWordformNonHead'] + '.txt')
			with io.open(fname, 'r', encoding='utf-8') as rdr:
				self.WordformNonHead = [line.strip() for line in rdr]

		if 'RussianLex' in yaml_data:
			self.RussianLex = [lex.strip() for lex in yaml_data['RussianLex'].split('|')]
		elif 'ListRussianLex' in yaml_data:
			fname = os.path.join(dirname, yaml_data['ListRussianLex'] + '.txt')
			with io.open(fname, 'r', encoding='utf-8') as rdr:
				self.RussianLex = [line.strip() for line in rdr]

		if 'RussianLexNonHead' in yaml_data:
			self.RussianLexNonHead = [lex.strip() for lex in yaml_data['RussianLexNonHead'].split('|')]
		elif 'ListRussianLexNonHead' in yaml_data:
			fname = os.path.join(dirname, yaml_data['ListRussianLexNonHead'] + '.txt')
			with io.open(fname, 'r', encoding='utf-8') as rdr:
				self.RussianLexNonHead = [line.strip() for line in rdr]

		if 'RussianWordform' in yaml_data:
			self.RussianWordform = [lex.strip() for lex in yaml_data['RussianWordform'].split('|')]
		elif 'ListRussianWordform' in yaml_data:
			fname = os.path.join(dirname, yaml_data['ListRussianWordform'] + '.txt')
			with io.open(fname, 'r', encoding='utf-8') as rdr:
				self.RussianWordform = [line.strip() for line in rdr]
		
		if 'ConstituentType' in yaml_data:
			self.ConstituentType = [s.strip() for s in yaml_data['ConstituentType'].split('|')]

		if 'Morph' in yaml_data:
			self.Morph = [s.strip() for s in yaml_data['Morph'].split(',')]

		if 'Orth' in yaml_data:
			self.Orth = yaml_data['Orth']
			if self.Orth not in ['FirstCapital', 'AllSmall', 'AllCapital', 'CamelCase']:
				error1('Неверный предикат Ortho: {}'.format(self.Orth))

		if 'Value' in yaml_data:
			self.value = yaml_data['Value']

		if 'Show' in yaml_data:
			self.Show = yaml_data['Show']


class OrderConstraints:
	def __init__(self):
		self.var1 = None
		self.var2 = None

	def load_yaml(self, data_yaml):
		vars = [v.strip() for v in data_yaml.strip().split(',')]
		self.var1 = vars[0]
		self.var2 = vars[1]

	def __repr__(self):
		return '{}, {}'.format(self.var1, self.var2)


class SubExampleRule:
	def __init__(self, priority):
		self.name = None
		self.priority = priority
		self.obligatory_participants = None
		self.optional_participants = None
		self.items = None
		self.links = None
		self.var2slot = None
		self.order_constraints = []

	def __repr__(self):
		return self.name

	def load_yaml(self, yaml_data, dirname):
		self.name = yaml_data['Name']

		self.optional_participants = []

		participants = yaml_data['Participants']
		for ppp in participants:
			for participant_type, participant_list in ppp.items():
				if participant_type == 'Obligatory':
					self.obligatory_participants = [s.strip() for s in participant_list.split(',')]
				elif participant_type == 'Optional':
					self.optional_participants = [s.strip() for s in participant_list.split(',')]
				else:
					error1('Неизвестный тип участника: {}'.format(participant_type))

		self.links = yaml_data.get('Links')  # считали связи из правила
		self.items = []
		for item_data in yaml_data['Items']:
			item = SubexampleItem()
			item.load_yaml(item_data, dirname)
			if item.slot_name in self.optional_participants:
				item.optional = True
			self.items.append(item)

		if 'Constraints' in yaml_data:
			for constraint_yaml in yaml_data['Constraints']:
				if 'Order' in constraint_yaml:
					d = constraint_yaml['Order']
					ord = OrderConstraints()
					ord.load_yaml(d)
					self.order_constraints.append(ord)
				else:
					raise NotImplementedError()

		self.var2slot = dict((item.participant, item) for item in self.items)

	def get_name(self):
		return self.name

	def match(self, parser_data):
		matched_pairs = dict()

		#index2token = dict((t['itoken'], t) for t in parser_data['tokens'])
		for arg in itertools.chain(self.obligatory_participants, self.optional_participants):
			for elem in self.items:
				# не анализируем опциональных участников!
				if elem.slot_name in arg or elem.slot_name in ('Dummy', 'Dummy1', 'Dummy2', 'Dummy3', 'Dummy4', 'Dummy5', 'Key'):
					if elem.participant not in matched_pairs:
						#if elem.Lex or elem.LexNonHead or elem.ConstituentType or elem.Orth or elem.Morph:
						compareTags(elem, parser_data, elem.participant, elem.slot_name, matched_pairs)
		# если не извлечен какой-то из обязательных участников, то
		# считаем, что правило вообще не сработало.
		all_oblig_matched = True
		for elem in self.items:
			if not elem.optional and elem.participant not in matched_pairs:
				all_oblig_matched = False
				break

			#if elem.slot_name in self.obligatory_participants or elem.slot_name in ('Dummy', 'Key'):

		extracted_examples = []

		if all_oblig_matched and len(matched_pairs) > 0:
			# Теперь для каждой переменной известны сопоставленные токены.
			# Перебираем все сочетания сопоставлений токенов и переменных.
			# Каждое сочетание проверяем по ограничениям Links
			matched_tokens = [matched_pairs[var] for var in matched_pairs.keys()]
			for matched_tokens1 in itertools.product(*matched_tokens):
				matched_pairs1 = dict(zip(matched_pairs.keys(), matched_tokens1))

				# Теперь в matched_pairs1 для каждой переменной есть единственный сопоставленный токен.

				constraints_ok = True

				if self.order_constraints:
					for ord in self.order_constraints:
						first_var = ord.var1
						second_var = ord.var2

						if first_var not in matched_pairs1:
							if self.var2slot[first_var].optional:
								continue

							constraints_ok = False
							continue

						if second_var not in matched_pairs1:
							if self.var2slot[second_var].optional:
								continue

							constraints_ok = False
							continue

						first_itoken = matched_pairs1[first_var].token_index
						sec_itoken = matched_pairs1[second_var].token_index
						if first_itoken >= sec_itoken:
							constraints_ok = False

				# Проверяем ограничения - связи.
				if self.links and constraints_ok:
					for link_constraint in self.links:
						assert(len(link_constraint) == 1)
						key = list(link_constraint.keys())[0]
						cur_link = list(link_constraint.values())[0]

						letters = [l.strip() for l in key.split(',')]   # элементы из правила
						first_var = letters[0]
						second_var = letters[1]

						if first_var not in matched_pairs1:
							if self.var2slot[first_var].optional:
								continue

							constraints_ok = False
							continue

						if second_var not in matched_pairs1:
							if self.var2slot[second_var].optional:
								continue

							constraints_ok = False
							continue

						first_itoken = matched_pairs1[letters[0]].token_index
						sec_itoken = matched_pairs1[letters[1]].token_index

						#print(sec_itoken, 'sec_itoken')  # второй элемент из пары связей из правила
						#print(first_itoken, 'first_itoken')  # первый элемент из пары связей из правила

						link_matched = False

						for token in parser_data['tokens']:
							if token['itoken'] == sec_itoken:  # находим второй элемент в json
								if ('edge_type' in token) and (token['edge_type'] == cur_link) and (token['parent_token_index'] == first_itoken):
									#print('тип связи совпал')  # если задан конкретный тип связи, пытаемся его найти
									link_matched = True
									break
								elif cur_link == 'one':  # если конкретный тип связи не задан
									if 'parent_token_index' in token and token['parent_token_index'] == first_itoken:
										#print('тип связи one или any совпал', token['parent_token_index'])
										link_matched = True
										break
								elif cur_link == 'any':
									# только для типа связи any. вызываем функцию, которая будет пытаться установить
									f = ifLinkExists(data[0]['tokens'], token['parent_token_index'], first_itoken)
									#print(f)
									if f:
										link_matched = True
										break
								#else:
									# ???
									#if first_itoken == token:  # дошли до root и связь не нашли, значит связи нет
									#	print('обязательная связь не найдена!')
									#	break
									#pass

						if not link_matched:
							constraints_ok = False
							break

				# ограничения проверены, осталось сформировать описание факта
				if constraints_ok:
					constituents = parser_data['constituents']
					matched_tokens = matched_pairs1.values()
					matched_tokens = sorted(matched_tokens, key=lambda z: z.token_index)
					example_tokens = dict()
					for matched_token in matched_tokens:
						example_tokens[matched_token.token_index] = matched_token.token['token']

						if True:
							# Для токена попробуем найти NP-составляющую минимального размера. Выведем
							# все токены этой составляющей в текст факта.
							if matched_token.constituent and matched_token.constituent['is_head'] is True:
								for c in constituents:
									if c['id'] == matched_token.constituent['id']:
										if c['name'] == 'NP' or (matched_token.rule_elem is not None and matched_token.rule_elem.Show == 'Constituent'):
											#if c['head_id'] == matched_token.token_index and c['name'] == 'NP':
											#	cx.append(c['tokens'])
											for t in c['tokens']:
												token_index = t[0]
												word = t[1]  #index2token[token_index]['token']
												example_tokens[token_index] = word


					example_tokens = sorted(example_tokens.items(), key=lambda z: z[0])
					example_tokens = [t[1] for t in example_tokens]

					extracted_example = ExtractedExample()
					extracted_example.example_name = example.get_name()
					extracted_example.matched_rule = subexample
					extracted_example.example_text = ' '.join(example_tokens)

					extracted_example.slot2value = dict()
					for matched_token in matched_tokens:
						if not matched_token.slot_name.startswith('Dummy'):
							slot_tokens = dict()
							slot_tokens[matched_token.token_index] = matched_token.token['token']

							slot_value = SlotValue()
							slot_value.key_word = matched_token.token['token']
							slot_value.key_lemma = matched_token.token['lemma']
							slot_value.key_index = matched_token.token['itoken']

							slot_filling = 'token'
							if matched_token.constituent:
								if matched_token.constituent['is_head'] is True and matched_token.constituent['name'] == 'NP':
									slot_filling = 'constituent'
								elif matched_token.constituent['is_head'] is True and matched_token.rule_elem is not None and matched_token.rule_elem.Show == 'Constituent':
									slot_filling = 'constituent'
								else:
									#slot_name = matched_token.slot_name
									for item in self.items:
										if item.slot_name == matched_token.slot_name:
											slot_filling = item.value
											break

							# если слот сопоставлен с NP и токен - главный, то значением слота будет вся NP.
							if slot_filling == 'constituent':
								for c in constituents:
									if c['id'] == matched_token.constituent['id']:
										# if c['head_id'] == matched_token.token_index and c['name'] == 'NP':
										#	cx.append(c['tokens'])
										for t in c['tokens']:
											token_index = t[0]
											word = t[1]  # index2token[token_index]['token']
											slot_tokens[token_index] = word
										break

							slot_tokens = sorted(slot_tokens.items(), key=lambda z: z[0])
							slot_tokens = [t[1] for t in slot_tokens]
							slot_value.text = ' '.join(slot_tokens)

							extracted_example.slot2value[matched_token.slot_name] = slot_value

					extracted_examples.append(extracted_example)

		return extracted_examples


class Example:
	def __init__(self, name):
		self.name = name
		self.subexamples = []

	def __repr__(self):
		return self.name

	def get_name(self):
		return self.name

	def load_yaml(self, filepath):
		"""Загружаем новую порцию правил для подпримеров, добавляя их в общий список факта."""
		with io.open(filepath, 'r', encoding='utf-8') as f:
			try:
				data = yaml.safe_load(f)
				dirname = os.path.dirname(filepath)

				if 'Priority' in data:
					priority = data['Priority']
				else:
					priority = 1

				for irule, d in enumerate(data['SubExamples']):
					subexample = SubExampleRule((priority, irule))
					subexample.load_yaml(d['SubExample'], dirname)
					self.subexamples.append(subexample)
			except Exception as ex:
				error1('При загрузке правил из файла "{}" произошла ошибка: {}'.format(filepath, ex))

	def enum_subexamples(self):
		# Считаем, что первое правило по умолчанию более приоритетно, чем последующие.
		return sorted(self.subexamples, key=lambda z: z.priority[0] - z.priority[1]*1e-10, reverse=True)


#функция проверяет есть ли синтаксическая связь между элементами
def ifLinkExists(tokens, sec_itoken, first_itoken):
	if sec_itoken == first_itoken:
		return True

	for token in tokens:
		if token['itoken'] == sec_itoken:
			#print(sec_itoken, 'второй элемен из связи')
			#print(first_itoken, 'первый элемен из связи')
			if token['parent_token_index'] == first_itoken: # нашли связь
				return True
			elif token['parent_token_index'] == -1: #дошли до root, т е не нашли связи
				return False
			else:
				return ifLinkExists(data[0]['tokens'], token['parent_token_index'], first_itoken)


def compareMorphTags(rule_elem, data_elem):
	""" функция возвращает true, если все морфологические теги совпали """
	if rule_elem.Morph:
		tagset = data_elem['tagsets'][0]  # теги ищем в первом тегсете разметки

		for tag in rule_elem.Morph:
			if '|' in tag: #дробим альтернативные теги
				tag_matched = False
				for tag1 in tag.split('|'):
					tag1 = tag1.strip()
					if tag1 in tagset:
						tag_matched = True
						break

				if not tag_matched:
					#print('морф тег из правила не найден', tag)
					return False

			elif 'NOT' in tag:
				tag = tag.split('=>')[1].strip()
				if tag not in tagset: #если тег с пометкой NOT не найден, продолжаем проверку
					continue
				else:
					#print('неправильный морф тег найден в json')
					return False
			else:
				if tag not in tagset:
					#print('морф тег из правила не найден', tag)
					return False

	return True


def checkOrth(rule_elem, token):
	if rule_elem.Orth:
		if rule_elem.Orth == 'FirstCapital':
			return token[0].isupper() and all(c.islower() for c in token[1:])
		elif rule_elem.Orth == 'AllSmall':
			return all(c.islower() for c in token)
		elif rule_elem.Orth == 'AllCapital':
			return all(c.isupper() for c in token)
		elif rule_elem.Orth == 'CamelCase':
			raise NotImplementedError()
		else:
			raise NotImplementedError()

		return False
	else:
		return True


# функция сравнивает леммы
def compareTags(rule_elem, data_elem, participant, slot_name, matched_pairs):
	flag = False  #в качестве метки для найденой леммы из правила
	if rule_elem.Lex:
		for elem in data_elem['tokens']:
			if elem['lemma'] in rule_elem.Lex:  # находим нужную лемму
				if 'constituent' in elem and elem['constituent']['is_head'] is True:  # and ('Lex' in rule_elem): #проверяем, is_head == True в json и в правиле стоит Lex
					flag = True
					if compareConstitTypes(rule_elem, elem):  # вызываем функцию проверки типа состовляющей
						#print("лемма и тип сост совпали")
						if compareMorphTags(rule_elem, elem):  # вызываем функцию проверки морфологии
							if checkOrth(rule_elem, elem):
								#print("морф теги совпали", elem, rule_elem)
								#на этом этапе идет добавление в словарь matched_pairs пар (элемент из правила: itoken сопоставленного ему элеменрта из json)
								#но! для элемента из правила может быть найдено >1 претендента из json. Поэтому здесь мы проверяем, был ли добавлен элемент из
								# правила. Если был - то бы в его значение добавляем еще один элемент. Если не был - то бы создаем добавляем itoken в новый список,
								# и кладем этот список в значение словаря
								tm = TokenMatching()
								tm.slot_name = slot_name
								tm.token_index = elem['itoken']
								tm.token = elem
								tm.constituent = elem['constituent']

								if participant in matched_pairs:
									matched_pairs[participant].append(tm)
								else:
									matched_pairs[participant] = [tm]

			if (elem == data_elem['tokens'][-1]) and not flag:
				#print('лемма из правила не найдена или условие is_head не совпало с тегом Lex/LexNonHead')
				pass

	#аналогичная ситуация для LexNonHead (is_head == false)
	elif rule_elem.LexNonHead:
		for elem in data_elem['tokens']:
			if elem['itoken'] not in [t.token_index for t in itertools.chain(*matched_pairs.values())]:
				#print(elem['lemma'])
				if elem['lemma'] in rule_elem.LexNonHead:
					if 'constituent' in elem and elem['constituent']['is_head'] is False:  # and ('LexNonHead' in rule_elem):
						flag = True
						if compareConstitTypes(rule_elem, elem):
							#print("лемма и тип сост совпали",)
							if compareMorphTags(rule_elem, elem):
								#print("морф теги совпали")
								if checkOrth(rule_elem, elem):
									tm = TokenMatching()
									tm.slot_name = slot_name
									tm.token_index = elem['itoken']
									tm.token = elem
									tm.constituent = elem['constituent']

									if participant in matched_pairs:
										matched_pairs[participant].append(tm)
									else:
										matched_pairs[participant] = [tm]

			if (elem == data_elem['tokens'][-1]) and not flag:
				#print('лемма из правила не найдена или is_head не совпало с тегом Lex/LexNonHead')
				pass

	elif rule_elem.Wordform:
		for elem in data_elem['tokens']:
			if elem['itoken'] not in [t.token_index for t in itertools.chain(*matched_pairs.values())]:
				#print(elem['lemma'])
				if elem['token'] in rule_elem.Wordform:
					if 'constituent' in elem and elem['constituent']['is_head'] is True:  # and ('LexNonHead' in rule_elem):
						if compareConstitTypes(rule_elem, elem):
							#print("лемма и тип сост совпали",)
							if compareMorphTags(rule_elem, elem):
								#print("морф теги совпали")
								if checkOrth(rule_elem, elem):
									tm = TokenMatching()
									tm.slot_name = slot_name
									tm.token_index = elem['itoken']
									tm.token = elem
									tm.constituent = elem['constituent']

									if participant in matched_pairs:
										matched_pairs[participant].append(tm)
									else:
										matched_pairs[participant] = [tm]

			if (elem == data_elem['tokens'][-1]) and not flag:
				#print('лемма из правила не найдена или is_head не совпало с тегом Lex/LexNonHead')
				pass

	elif rule_elem.WordformNonHead:
		for elem in data_elem['tokens']:
			if elem['itoken'] not in [t.token_index for t in itertools.chain(*matched_pairs.values())]:
				#print(elem['lemma'])
				if elem['token'] in rule_elem.WordformNonHead:
					if 'constituent' in elem and elem['constituent']['is_head'] is False:  # and ('LexNonHead' in rule_elem):
						if compareConstitTypes(rule_elem, elem):
							#print("лемма и тип сост совпали",)
							if compareMorphTags(rule_elem, elem):
								#print("морф теги совпали")
								if checkOrth(rule_elem, elem):
									tm = TokenMatching()
									tm.slot_name = slot_name
									tm.token_index = elem['itoken']
									tm.token = elem
									tm.constituent = elem['constituent']

									if participant in matched_pairs:
										matched_pairs[participant].append(tm)
									else:
										matched_pairs[participant] = [tm]

			if (elem == data_elem['tokens'][-1]) and not flag:
				#print('лемма из правила не найдена или is_head не совпало с тегом Lex/LexNonHead')
				pass

	elif rule_elem.RussianLex:
		for elem in data_elem['tokens']:
			if elem['itoken'] not in [t.token_index for t in itertools.chain(*matched_pairs.values())]:
				#print(elem['lemma'])
				if elem['translation'] in rule_elem.RussianLex:
					if 'constituent' in elem and elem['constituent']['is_head'] is True:  # and ('LexNonHead' in rule_elem):
						if compareConstitTypes(rule_elem, elem):
							#print("лемма и тип сост совпали",)
							if compareMorphTags(rule_elem, elem):
								#print("морф теги совпали")
								if checkOrth(rule_elem, elem):
									tm = TokenMatching()
									tm.slot_name = slot_name
									tm.token_index = elem['itoken']
									tm.token = elem
									tm.constituent = elem['constituent']

									if participant in matched_pairs:
										matched_pairs[participant].append(tm)
									else:
										matched_pairs[participant] = [tm]

			if (elem == data_elem['tokens'][-1]) and not flag:
				#print('лемма из правила не найдена или is_head не совпало с тегом Lex/LexNonHead')
				pass

	elif rule_elem.RussianLexNonHead:
		for elem in data_elem['tokens']:
			if elem['itoken'] not in [t.token_index for t in itertools.chain(*matched_pairs.values())]:
				#print(elem['lemma'])
				if elem['translation'] in rule_elem.RussianLexNonHead:
					if 'constituent' in elem and elem['constituent']['is_head'] is False:  # and ('LexNonHead' in rule_elem):
						if compareConstitTypes(rule_elem, elem):
							#print("лемма и тип сост совпали",)
							if compareMorphTags(rule_elem, elem):
								#print("морф теги совпали")
								if checkOrth(rule_elem, elem):
									tm = TokenMatching()
									tm.slot_name = slot_name
									tm.token_index = elem['itoken']
									tm.token = elem
									tm.constituent = elem['constituent']

									if participant in matched_pairs:
										matched_pairs[participant].append(tm)
									else:
										matched_pairs[participant] = [tm]

			if (elem == data_elem['tokens'][-1]) and not flag:
				#print('лемма из правила не найдена или is_head не совпало с тегом Lex/LexNonHead')
				pass

	elif rule_elem.RussianWordform:
			common_words = set([x.lower() for x in re.split(r"[\s.,;:-]+", data_elem['russian_text'])]) & set(rule_elem.RussianWordform)
			if common_words:
					flag = True
					index = 1
					for common_word in common_words:
						tm = TokenMatching()
						tm.slot_name = slot_name
						tm.token_index = index
						tm.token = {"itoken": index, "token": common_word, "lemma": common_word, "tagsets": [["None", "-"]], "parent_token_index": "-", "edge_type": "-", "constituent": {"name": "-", "is_head": "-", "id": "-"}, "translation": "None"}
						tm.constituent = {"name": "-", "is_head": "-", "id": "-"}
						index += 1

						if participant in matched_pairs:
							matched_pairs[participant].append(tm)
						else:
							matched_pairs[participant] = [tm]

			if not flag:
				#print('лемма из правила не найдена или is_head не совпало с тегом Lex/LexNonHead')
				pass


	else:
		# аналогичная ситуация, когда леммы нет в правиле
		for elem in data_elem['tokens']:
			if True:  #elem['itoken'] not in [t.token_index for t in itertools.chain(*matched_pairs.values())]:
				if compareConstitTypes(rule_elem, elem):
					#print("леммы нет тип сост совпал")
					if compareMorphTags(rule_elem, elem):
						#print("морф теги совпали")
						if checkOrth(rule_elem, elem['token']):
							tm = TokenMatching()
							tm.slot_name = slot_name
							tm.rule_elem = rule_elem
							tm.token_index = elem['itoken']
							tm.token = elem
							tm.constituent = elem.get('constituent')

							if participant in matched_pairs:
								matched_pairs[participant].append(tm)
							else:
								matched_pairs[participant] = [tm]


def compareConstitTypes(rule_elem, data_elem):
	""" функция сравнивает типы составляющих """
	if rule_elem.ConstituentType:
		for const_type in rule_elem.ConstituentType:
			if 'constituent' in data_elem and data_elem['constituent']['name'] == const_type:
				return True
		return False
	else:
		return True


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Example extractor')
	parser.add_argument('--rules', type=str, default='24', help='directory with rules')
	parser.add_argument('--dir_in', type=str, default='Input/main', help='corpora files')
	parser.add_argument('--output_txt', type=str, default='Output/search_result.txt', help='example extraction results text')
	parser.add_argument('--verbosity', type=int, default=1, help='print messages')
	parser.add_argument('--output_csv', type=str, default='Output/search_result.csv', help='example extraction results csv')
	parser.add_argument('--csv_verbosity', type=int, default=1, help='print to csv')

	args = parser.parse_args()
	rules_dir = args.rules
	parsing_path = args.dir_in
	output_path_txt = args.output_txt
	verbosity = args.verbosity
	output_csv = args.output_csv
	csv_verbosity = args.csv_verbosity


	# Загружаем правила из указанного каталога, просматривая рекурсивно все вложенные
	# подкаталоги в поисках файлов *.yaml
	examples = dict()

	if verbosity:
		print('Loading rules from "{}"'.format(rules_dir))

	rul_dir_p = os.path.join(os.getcwd(), 'Rules', rules_dir)
	for fl in os.listdir(rul_dir_p): # перебираем файлы с примерами
		fpath = os.path.join(rul_dir_p, fl)

		try:
			with open(fpath, 'r', encoding='utf-8') as f:
				data = yaml.safe_load(f)
				example_name = data['ExampleName']

			if example_name not in examples:
				examples[example_name] = Example(example_name)

			examples[example_name].load_yaml(fpath)
		except Exception as ex:
			print('Error occured when loading examples from "{}":\n{}'.format(fpath, ex))
			exit(0)

	ex_id, examples_number = 1, set()
	f_out = open(output_path_txt, mode = 'w', encoding = 'utf-8')
	csv_out = open(output_csv, mode = 'w', encoding = 'utf-8')
	directory_in = os.path.join(os.getcwd(), parsing_path)

	if csv_verbosity:
		csv_out.write('ex_id' + '\t' + 'id' + '\t' + 'example_name' + '\t' + 'subexample_name' + '\t' + 'text' + '\t' + 'tree' + '\t' + 'sent_len' + '\n')


	for file in os.listdir(directory_in): # перебираем файлы с примерами и разных json'ах
		fi = os.path.join(directory_in, file)

		#считываем json с результатами парсинга.
		if verbosity:
			print('Loading parsing data from "{}"'.format(fi))
		with io.open(fi, "r", encoding='utf-8') as f2:
			data = json.load(f2)


		for isent, sent_data in enumerate(data):
			# Ищем вхождение правил подпримеров в результаты парсинга
			extracted_examples = []
			for example in examples.values():
				for subexample in example.enum_subexamples():
					#try:
						matchings = subexample.match(sent_data)
						if matchings:
							extracted_examples.extend(matchings)
							break


			odata = dict()
			odata['text'] = sent_data['text']
			example_jsons = []
			for eexample in extracted_examples:
				if verbosity:
					print(eexample)
				slots = eexample.get_slots()

				example_json = dict()
				example_jsons.append(example_json)
				example_json['example_name'] = eexample.get_example_name()
				example_json['subexample_name'] = eexample.get_subexample_name()
				example_json['example_text'] = eexample.get_text()

				slots_json = []
				if csv_verbosity:
					co_length, str_csv_tmp, str_csv = 0, [], [str(ex_id), str(sent_data['id']), eexample.get_example_name(), eexample.get_subexample_name(), sent_data['text'], sent_data['sentence_tree'], str(sent_data['length'])]
				example_json['slots'] = slots_json

				if slots:
					if verbosity:
						f_out.write(
							'=>Найден пример {} номер {} типа {} с текстом \n{}\n{}\n\t=>из предложения #{} \n\t{}\n'.format(
								eexample.get_example_name(), ex_id, eexample.get_subexample_name(), sent_data['text'], sent_data['russian_text'], sent_data['id'], sent_data['sentence_tree']))
						examples_number.add(sent_data['id'])

						print('Слоты:')
						f_out.write('\t=>Слоты:')
					slots_el = {}
					for slot_name, slot_value in slots:
						if verbosity:
							print('{} = {}'.format(slot_name, slot_value))
							f_out.write('\n\t\t=>{} = {}'.format(slot_name, slot_value.text))
						if csv_verbosity:
							slot_type = ''
							for co in sent_data["constituents"]:
								if co["head_id"] == slot_value.key_index:
#									print(co)
									co_length = co["length"]
									break
							for si in subexample.items:
								if slot_name == si.slot_name:
									slot_type = si.ConstituentType
									break
							co_length = co_length if slot_type else 0
							slots_el[slot_name] = [slot_value.text, str(slot_value.key_index), str(co_length)]
					for i in dict(sorted(slots_el.items())).values():
						str_csv_tmp = str_csv_tmp + i

						slots_json.append({'name': slot_name,
											'text': slot_value.text,
											#'key_word': slot_value.key_word,
											'key_lemma': slot_value.key_lemma,
											'key_index': slot_value.key_index})
				print('')
				str_csv = str_csv + str_csv_tmp

				if verbosity:
					f_out.write('\n\n')

				if csv_verbosity:
					csv_out.write("\t".join(str_csv) + '\n')
				ex_id += 1

			odata['examples'] = example_jsons


	f_out.write('\n\nВСЕГО УНИКАЛЬНЫХ ПРИМЕРОВ = ' + str(len(examples_number)))
	f_out.close()
	csv_out.close()
