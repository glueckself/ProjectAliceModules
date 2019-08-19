import os
import glob
import json
import re
from src.validation import validation
from src.dialogTemplate import dialogTemplate
from snips_nlu_parsers import get_all_builtin_entities
from unidecode import unidecode

class dialogValidation(validation):
	
	@property
	def JsonSchema(self) -> dict:
		with open(os.path.join(self.dir_path, 'schemas/dialog-schema.json') ) as json_file:
			return json.load(json_file)
	
	@property
	def JsonFiles(self) -> list:
		return glob.glob( os.path.join(self.modulePath, 'dialogTemplate/*.json') )

	# check whether the slot is a integrated one from snips
	def is_builtin(self, slot: str) -> bool:
		return slot in get_all_builtin_entities()
		
	def installerJsonFiles(self, modulePath: str) -> list:
		return glob.glob( os.path.join(modulePath, '*.install'))


	def searchModule(self, moduleName: str) -> str:
		for module in glob.glob(self.base_path + '/PublishedModules/*/*'):
			if os.path.basename(module) == moduleName:
				return module

	def getRequiredModules(self, modulePath: str = None) -> set:
		modulePath = modulePath or self.modulePath
		modules = {modulePath}
		for installer in self.installerJsonFiles(modulePath):
			data = self.validateSyntax(installer)
			if data and 'module' in data['conditions']:
				for module in data['conditions']['module']:
					if module['name'] != self.moduleName:
						path = self.searchModule(module['name'])
						pathSet = {path} if path else set()
						modules = modules.union(pathSet, self.getRequiredModules(path))
		return modules
	
	def getCoreModules(self) -> list:
		return glob.glob(self.base_path + '/PublishedModules/ProjectAlice/*')

	def getAllSlots(self, language: str) -> dict:
		modules = self.getRequiredModules().union(set(self.getCoreModules()))
		all_slots = {}
		for module in modules:
			# get data and check whether it is valid
			path = os.path.join(module, 'dialogTemplate', language)
			if os.path.isfile(path):
				data = self.validateSyntax(path)
				all_slots.update(dialogTemplate(data).slots)
		return all_slots

	def searchMissingSlotValues(self, values: list, allSlots: dict) -> list:
		found = []
		for value in values:
			uValue = unidecode(value).lower()
			for slot in allSlots['values']:
				allValues = [unidecode(slot['value']).lower()]
				if allSlots['useSynonyms'] and 'synonyms' in slot:
					allValues.extend([unidecode(x).lower() for x in slot['synonyms']])

				if (uValue in allValues or allSlots['automaticallyExtensible']):
					found.append(value)
		return [x for x in values if x not in found]

	def validateIntentSlots(self) -> None:
		all_slots = {}
		# get slots from all json files of a module
		for file in self.JsonFiles:
			all_slots[file] = self.getAllSlots(os.path.basename(file))

		# check whether the same slots appear in all files
		for file in self.JsonFiles:
			jsonPath = self.validModule['utterances'][self.filename(file)]
			# get data and check whether it is valid
			data = self.validateSyntax(file)
			for intentName, slots in dialogTemplate(data).utteranceSlots.items():
				for slot, values in slots.items():
					if not self.is_builtin(slot):
						if not slot in all_slots[file]:
							self.error = 1
							if intentName in jsonPath:
								jsonPath['missingSlots'][intentName].append(slot)
							else:
								jsonPath['missingSlots'][intentName] = [slot]
						else:
							missingValues = self.searchMissingSlotValues(values, all_slots[file][slot])
							if missingValues:
								self.error = 1
								jsonPath['missingSlotValue'][intentName][slot] = missingValues

	def validateSlots(self) -> None:
		all_slots = {}
		# get slots from all json files of a module
		for file in self.JsonFiles:
			# get data and check whether it is valid
			data = self.validateSyntax(file)
			all_slots.update(dialogTemplate(data).slots)

		# check whether the same slots appear in all files
		for file in self.JsonFiles:
			# get data and check whether it is valid
			data = self.validateSyntax(file)
			missingSlots = self.validModule['slots'][self.filename(file)]
			missingSlots = [k for k, v in all_slots.items() if k not in dialogTemplate(data).slots]
			if missingSlots:
				self.error = 1

	def searchDuplicateUtterances(self) -> None:
		for file in self.JsonFiles:
			jsonPath = self.validModule['utterances'][self.filename(file)]['duplicates']
			# get data and check whether it is valid
			data = self.validateSyntax(file)
			for intentName, shortUtterances in dialogTemplate(data).shortUtterances.items():
				for shortUtterance, utterances in shortUtterances.items():
					if len(utterances) > 1:
						# Will be added again when duplicates do not improve the performance anymore
						#self.error = 1
						jsonPath[intentName][shortUtterance] = utterances

	def validate(self) -> bool:
		self.validateSchema()
		self.validateSlots()
		self.searchDuplicateUtterances()
		self.validateIntentSlots()
		return self.error