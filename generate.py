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

Relation = lambda name, token, modifier, initializer:{'name': name, 'token':token,'mod':modifier,'init':initializer}
Input = lambda name, answer, distractors:{'name':name, 'answer':answer, 'distractors':distractors}
Association = lambda token, index:{'token':token,'index':index}

def getRelationByToken(relationName):
    """find and return the first relation containing the specified name"""
    for relation in RELATIONS:
        if(relation['token'] == relationName):
            return relation
    return None #possible failure here if expecting object- don't use dynamically

RELATIONS.append({
    'name': 'SUBJECT',
    'token':'PROPERNOUN', 
    'init':'SubjectModel {name} = JournalismController.selectRandom(subjectAccess.selectByNounType(Arrays.asList(new String[] {{"PROPERNAME"}}), Arrays.asList(Gender.values())))',
    'mod':'.getSubject()',
    'index':-1})
RELATIONS.append({
    'name': getRelationByToken('PROPERNOUN')['name'],
    'token':'LASTNAME', 
    'init': getRelationByToken('PROPERNOUN')['init'],
    'mod':'.getSubject_last_name()',
    'index':-1})
RELATIONS.append({
    'name': getRelationByToken('PROPERNOUN')['name'],
    'token':'PRONOUN',
    'init': getRelationByToken('PROPERNOUN')['init'],
    'mod':'.getPronoun()',
    'index':-1})

def generateOutput():
    print("Opening {file} for reading".format(file=FILENAME))
    inputFile = open(FILENAME, "r")
    setFlags(inputFlags, inputFile)
    
    print("Parsing Input...")
    strings, associations, inputs, answerStrings = gen(inputFile)

    print("Writing to {file}".format(file=OUTPUT))
    writeToFile(OUTPUT, strings, associations, inputs, answerStrings)

def writeToFile(outputName, strings, associations, inputs, answerStrings):
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
    #open output stream
    out = open("output/"+OUTPUT,"w+")
    #write java imports
    out.write(sd.imports)
    #write PTEID info
    ##out.write(sd.PTEID(MC_PTE_ID, OA_PTE_ID))
    #write class NAME
    out.write(sd.generateClassName(CLASSNAME))
    #instantiate DAOs
    #TODO only instantiate necessary DAOs
    out.write(sd.DAOs)
    #instantiate models
    out.write(instantiateModels(associations))
    #instantiate model strings
    out.write(instantiateModelStrings(associations))
    #write global lists
    out.write(sd.GLOBAL_LISTS)
    #write constructor
    out.write(sd.generateConstructorName(CLASSNAME))
    #generate varLists
    out.write(generateVariableLists(inputs))
    #initialize sentences
    out.write(generateSentences(strings, answerStrings))
    #end constructor
    out.write(sd.CONSTRUCTOR_END)
    #end class
    out.write(sd.generateMiddleFiller())
def instantiateModels(assocs):
    toRet = ""   
    indexed = []
    for assoc in assocs:
        if(assoc['index'] not in indexed):
            assocRelation = getRelationByToken(assoc['token'])
            toRet += "\n" + assocRelation['init'].format(name = assocRelation['name'] + assoc['index']) + ";"
            indexed.append(assoc['index'])
    print(toRet)
    return toRet

def instantiateModelStrings(assocs):
    toRet = ""
    for assoc in assocs:
        assocRelation = getRelationByToken(assoc['token'])
        toRet += "\nString " + assoc['token'] + assoc['index'] + " = " + assocRelation['name'] + assoc['index'] + assocRelation['mod'] + ";"
    print(toRet)
    return toRet

def generateVariableLists(inputs):
    toRet = ""
    for input in inputs:
        answerCount = len(input['answer'])
        toRet += """
    String {word}Answer = "";
    distractorIndex = 0;
    ArrayList<String> {word}List = new ArrayList<String>();
    chosen = rand.nextInt({num});
    """.format(word=input['name'], num = answerCount)
        for i in range(answerCount):
            toRet +="""
    if (chosen == {num}) {{
        {word}Answer = "{answer}\";""".format(num=i, word=input['name'], answer=input['answer'][i])
            for distractor in input['distractors'][i]:
                toRet += """
                {word}List.add("{distract}".trim());""".format(distract=distractor['text'], word=input['name'])
            toRet +="""
                varList.add({word}List);
            }}
            """.format(word=input['name'])
    return toRet
    
def generateSentences(strings, answerStrings):
    toRet = """
    ArrayList<String> sentenceList = new ArrayList<String>();
    ArrayList<Tuple> distractorList = new ArrayList<Tuple>();
    """
    for i, string in enumerate(answerStrings):
        toRet += """
        sentenceList.add("{sentence}");""".format(sentence=string)
        toRet += """
        distractorList.add(new Tuple("{sentence}",varList));""".format(sentence = strings[i])
    return toRet

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
    answerStrings = []
    
    strings = readStrings(inputFile)
    inputs = readInputs(inputFile)
    strings, associations, answerStrings = handleRelations(strings,inputs)

    return strings, associations, inputs, answerStrings

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
    answerStrings = []
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
        answerString = ""
        for i, token in enumerate(inputs):
            token = token['name']
            while('$'+token.upper() in string.upper()):
                answerString = re.sub('\\$' + token, tokenize(token, 'Answer'), string, flags=re.IGNORECASE)
                string = re.sub('\\$' + token, """%{i}$s""".format(i=i+1), string, flags=re.IGNORECASE)
        answerStrings.append(answerString)
        newStrings.append(string)
    return newStrings, associations, answerStrings

def tokenize(token,index):
    return '" + ' + token + index + '.trim() + "'

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
