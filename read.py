from flags import flags
import json
import re
import staticData as sd
import sys

CLASSNAME = "DefaultTestName"
if(sys.argv[2]):
    CLASSNAME = sys.argv[2]
HEADERLEN = 2
ignoredChars = ["\n","+"]
replacedChars = [{'old':"\u2019", 'new':"'"}]
allowCorrectAsDistractor = True

#turn to enums?
dynamicTokens = {'LASTNAME':'SUBJECT', 'PROPERNAME':'SUBJECT', 'PRONOUN':'SUBJECT'}
dynamicRelation = {'LASTNAME':'.getSubject_last_name()', 'PROPERNAME':'.getSubject()', 'PRONOUN':'.getPronoun()'}
dynamicCalls  = {
                    'SUBJECT' : 'SubjectModel {name} = JournalismController.selectRandom(subjectAccess.selectByNounType(Arrays.asList(new String[] {{"PROPERNAME"}}), Arrays.asList(Gender.values())))'
                }

print("Input Analysis:")

def readInput(filename):
    inputFile = open(filename,"r")
    fileFlags = readHeader(inputFile)
    inputs = {}
    distractors = {}
    answers = {}
    dynamics = {}
    strings = []
    if(fileFlags == [flags.NONE]):
        strings,dynamics = interface(readStrings(inputFile))
        inputs, distractors, answers = readInputs(inputFile)
        writeFile(filename, inputs, distractors, strings, answers, dynamics)
    print("interfacing: " + str(interface(strings)))
def readHeader(inputFile):
    headerString = inputFile.readline()
    fileFlags = []
    for header in headerString.split(" "):
        if(header[0] != "-"):
            fileFlags.append(flags.ERROR)
        else:
            if(header[1] == "n"):
                fileFlags.append(flags.NONE)
            else:
                fileFlags.append(flags.ERROR)
    return fileFlags

def readStrings(inputFile):
    inputFile.seek(HEADERLEN)
    strings = []
    currentString = inputFile.readline()
    while("#" not in currentString):
        for character in ignoredChars:
            currentString = sanitize(currentString.replace(character,"").strip())
        if(currentString != ''):
            strings.append(currentString)
        currentString = inputFile.readline()
    return strings

def findInputs(inputFile):
    inputFile.seek(HEADERLEN)
    for num, line in enumerate(inputFile, 1):
        if('#' in line):
            return(num)
    return -1

def readInputs(inputFile):
    inputs = {}
    distractors = {}
    answers = {}
    presidingInput = ""
    correctAnswer = ""
    currentInput = inputFile.readline()
    while('@' not in currentInput):
        for character in ignoredChars:
            currentInput = sanitize(currentInput.replace(character,"").strip())
        if(currentInput != ''):
            if(currentInput[0] == "$"):
                presidingInput = currentInput[1:].replace("=","").strip()
                inputs[presidingInput] = []
                distractors[presidingInput] = []
                answers[presidingInput] = {}
            elif(currentInput[:2] == "::"):
                correctAnswer = currentInput.replace("::",'').strip()
                inputs[presidingInput].append(correctAnswer)
                distractors[presidingInput].append(correctAnswer)
                answers[presidingInput][correctAnswer] = []
                if(allowCorrectAsDistractor):
                    answers[presidingInput][correctAnswer].append(correctAnswer)
            else:
                inputPhrase, distractor = currentInput.split(";")
                assert(distractor is not list)
                if(inputPhrase.strip() not in inputs[presidingInput]):
                    inputs[presidingInput].append(inputPhrase.strip())
                    distractors[presidingInput].append(distractor.strip())
                    answers[presidingInput][correctAnswer].append(inputPhrase.strip())
        currentInput = inputFile.readline()
    return inputs, distractors, answers

def readAnswers(inputFile):
    answers = {}
    currentAnswer = inputFile.readline()
    while('~' not in currentAnswer):
        for character in ignoredChars:
            currentAnswer = currentAnswer.replace(character,"").strip()
        if(currentAnswer != ''):
            currentAnswer = currentAnswer.replace(" OR", ",")
            answerName, answerBody = currentAnswer[1:].split("=")
            answerName = answerName.strip()
            answers[answerName] = []
            for name in answerBody.split(","):
                answers[answerName].append(name.strip())
        currentAnswer = inputFile.readline()
    return answers

def writeFile(filename, inputs, distractors, strings, answers, dynamics):
    name,ext = filename.split(".",1) #not a good solution
    print("inputs: " + str(inputs))
    print("distractors: " + str(distractors))
    print("strings: " + str(strings))
    print("answers: " + str(answers))
    out = open("output/"+filename,"w+")
    out.write(sd.imports)
    out.write(sd.generateClassName(CLASSNAME))
    out.write(sd.DAOs)
    out.write("String chosenSentenceAnswer, chosenSentenceDistractor;\n")
    dynamicsList = []
    dynamicsIndexList = []
    for dynamic in dynamics:
        if(dynamic not in dynamicsList):
            if(dynamic['index'] not in dynamicsIndexList):
                out.write(dynamicCalls[dynamicTokens[dynamic['token']]].format(name=dynamicTokens[dynamic['token']]+dynamic['index']) + ";\n")
                dynamicsIndexList.append(dynamic['index'])
            out.write("String " + dynamic['token']+dynamic['index'] + " = " + dynamicTokens[dynamic['token']]+dynamic['index']+dynamicRelation[dynamic['token']] + ";\n")
            dynamicsList.append(dynamic)
    out.write(sd.generateConstructorName(CLASSNAME))
    out.write("\tint distractorIndex, chosen;")
    for varName in inputs.keys():
        i = 0
        out.write(
"""
String {word}Answer, {word}Distractor;
{word}Answer = {word}Distractor = "";
distractorIndex = 0;
ArrayList<String> {word}List = new ArrayList<String>();
""".format(word=varName))
        out.write("""chosen = rand.nextInt({num});\n""".format(num=len(answers[varName].keys())))
        for answer in answers[varName].keys():
            out.write("""if(chosen=={i}){{\n""".format(i=i))
            out.write("""\t{word}List = new ArrayList<String>();\n""".format(word=varName))
            for distractor in answers[varName][answer]:
                out.write("""\t{word}List.add("{wrongAnswer}");\n""".format(word=varName, wrongAnswer=distractor))
            out.write(
"""
\t{word}Answer = "{answer}";
\tdistractorIndex = rand.nextInt({word}List.size());
\t{word}Distractor = {word}List.get(distractorIndex);
""".format(word=varName,answer=answer))
            out.write("}\n")
            i += 1
    out.write("""
ArrayList<String> sentenceList = new ArrayList<String>();
ArrayList<String> distractorList = new ArrayList<String>();
            """)
    for sentence in strings:
        distractor = sentence
        for varName in inputs.keys():
            sentence = sentence.replace("$"+varName,'" + ' + varName +'Answer + "')
            distractor = distractor.replace("$"+varName,'" + ' + varName +'Distractor + "')
        out.write('\nsentenceList.add("' + sentence + '");')
        out.write('\ndistractorList.add("' + distractor + '");')
    out.write("""\nint sentenceIndex = rand.nextInt(sentenceList.size());
chosenSentenceAnswer = sentenceList.get(sentenceIndex);
chosenSentenceDistractor = distractorList.get(sentenceIndex);""")
    out.write("\n}")
    out.write(sd.generateMiddleFiller())
def sanitize(word):
    for characters in replacedChars:
         word = word.replace(characters['old'], characters['new'])
    word = re.sub(' +', ' ', word)
    return word

def interface(strings):
    dynamics = []
    newStrings = []
    for string in strings:
        for token in dynamicTokens.keys():
            while("$" + token in string.upper()):
                temp, end, *rest = re.split("\$"+token,string,flags=re.IGNORECASE)
                index = end[0]
                string = re.sub("\$"+token + index,tokenize(token,index), string,1,flags=re.IGNORECASE)
                print("detected token in string: " + string)
                dynamics.append({'token':token,'index': index})
        newStrings.append(string)
    return newStrings, dynamics

def tokenize(token,index):
    return '" + ' + token + index + '.strip() + "'

def jformat(word):
    print("nothing")

if(sys.argv[1]):
    readInput(sys.argv[1])
else:
    readInput("test.txt")
#readInput("./test.txt")
