from flags import flags
import staticData as sd
import defaults
#from relations import Relation

import json
import re
import sys

FILENAME    = sys.argv[1] or defaults.FILENAME
CLASSNAME   = sys.argv[2] or defaults.CLASSNAME
OUTPUT      = sys.argv[3] or defaults.OUTPUT
HEADERLEN   = defaults.HEADERLEN
IGNORE      = defaults.IGNORE #characters to ignore in input
REPLACE     = defaults.REPLACE #characters to replace (generally unicode)
inputFlags  = defaults.INPUTFLAGS
settings    = {
        'ANSWER_AS_DISTRACTOR':True
        }
RELATIONS   = []

Relation = lambda token, modifier, initializer:{'token':token,'mod':modifier,'init':initializer}
Input = lambda name, answer, distractors:{'name':name, 'answer':answer, 'distractors':distractors}
Association = lambda token, index:{'token':token,'index':index}

def getRelationByToken(relationName):
    """find and return the first relation containing the specified name"""
    for relation in RELATIONS:
        if(relation['token'] == relationName):
            return relation
    return None #possible failure here if expecting object- don't use dynamically

RELATIONS.append({
    'token':'PROPERNOUN', 
    'init':'SubjectModel {name} = JournalismController.selectRandom(subjectAccess.selectByNounType(Arrays.asList(new String[] {{"PROPERNAME"}}), Arrays.asList(Gender.values())))',
    'mod':'.getSubject()','index':-1})
RELATIONS.append({
    'token':'LASTNAME', 
    'init':getRelationByToken('PROPERNOUN')['init'],
    'mod':'.getSubject_last_name()',
    'index':-1})
RELATIONS.append({
    'token':'PRONOUN',
    'init':getRelationByToken('PROPERNOUN')['init'],
    'mod':'.getPronoun()',
    'index':-1})

def generateOutput():
    print("Opening {file} for reading".format(file=FILENAME))
    inputFile = open(FILENAME, "r")
    setFlags(inputFlags, inputFile)
    
    print("Parsing Input...")
    strings, associations, inputs = gen(inputFile)

    print("Writing to {file}".format(file=OUTPUT))
    writeToFile(OUTPUT, strings, associations, inputs)

def writeToFile(outputName, strings, associations, inputs):
    print("writing to {o}".format(o=outputName))
    print("Strings:")
    for string in strings:
        print(string)
    print("Assocs:")
    for association in associations:
        print(association)
    print("inputs:")
    for input in inputs:
        print(input)

def setFlags(inputFlags, inputFile):
    """Reads header and sets global variables based on flags"""
    header = inputFile.readline()
    for flag in header.split():
        if(flag[0] != '-'):
            raise Exception("Invalid Header")
        switch = {
                'n':flags.NONE,
                'na':flags.NO_ANSWER_AS_DISTRACTOR
        }
        thisFlag = switch.get(flag[1:],flags.ERROR)
        inputFlags.append(thisFlag) #is this needed?
        if(thisFlag == flags.ERROR):
            raise Exception("Invalid Header")
        elif(thisFlag == flags.NO_ANSWER_AS_DISTRACTOR):
            settings['ANSWER_AS_DISTRACTOR'] = False

def gen(inputFile):
    strings = []
    associations = []
    inputs = []
    
    strings = readStrings(inputFile)
    inputs = readInputs(inputFile)
    strings, associations = handleRelations(strings,inputs)

    return strings, associations, inputs

def readStrings(inputFile):
    """generate string, relation, and answer data from the input file"""
    inputFile.seek(HEADERLEN)
    strings = []
    currentLine = inputFile.readline()
    while('#' not in currentLine):
        for character in IGNORE:
            currentLine = currentLine.replace(character, "")
        for character in REPLACE:
            currentLine = currentLine.replace(character['old'], character['new'])
        if(currentLine != ''):
            strings.append(sanitize(currentLine)) #should be okay to sanitize here
        currentLine = inputFile.readline()
    return strings

def readInputs(inputFile):
    inputLine = inputFile.readline()
    inputs = []
    while('@' not in inputLine):
        if(inputLine == ''):
            inputLine = inputFile.readline()
            continue
        if(inputLine[0] == '$'):
            inputLine = inputLine[1:].replace('=','')
            inputs.append(Input(sanitize(inputLine),[],[]))
        elif(inputLine[:2] == '::'):
            inputs[-1]['answer'].append(sanitize(inputLine[2:]))
            inputs[-1]['distractors'].append([])
            inputs = addAnswerAsDistractor(inputs,sanitize(inputLine[2:]))
        else:
            inputLine, info = sanitize(inputLine).split(';')
            inputs[-1]['distractors'][-1].append({'text':inputLine,'info':info})
        inputLine = inputFile.readline()
    return inputs

def addAnswerAsDistractor(inputs, string):
    if(settings['ANSWER_AS_DISTRACTOR']):
        inputs[-1]['distractors'][-1].append({'text':string,'info':'IS_ANSWER'})
    return inputs

def handleRelations(strings,inputs):
    newStrings = []
    associations = []
    for string in strings:
        for relation in RELATIONS:
            token = relation['token']
            while('$'+token in string.upper()):
                temp, end, *rest = re.split('\$'+token,string,flags=re.IGNORECASE)
                index=end[0] #assuming they only go up to 9
                string = re.sub('\$'+token+index,tokenize(token,index),string)
                if(Association(token,index) not in associations):
                    associations.append(Association(token,index))
        for token in inputs:
            token = token['name']
            while('$'+token.upper() in string.upper()):
                string = re.sub('\\$' + token, tokenize(token,''), string, flags=re.IGNORECASE)
        newStrings.append(string)
    return newStrings, associations

def tokenize(token,index):
    return '" + ' + token + index + '.strip() + "'
            
def sanitize(word):
    """return a sanitized sentence (all good characters, no extra whitespace)"""
    for character in IGNORE:
        word.replace(character, "")
    for character in REPLACE:
        word.replace(character['old'], character['new'])
    word = re.sub('\s+',' ', word)
    if(word[-1] == ' '):
        word = word[:-1]
    return word


generateOutput()
