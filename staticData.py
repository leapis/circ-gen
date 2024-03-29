imports ="""//autogenerated
package edu.rutgers.elearning.component.journalism.pte;

import java.util.Random;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;

import edu.rutgers.elearning.component.journalism.dao.*;
import edu.rutgers.elearning.component.pte.ProblemTemplateEngine;
import edu.rutgers.elearning.component.questions.GeneratedQuestion;
import edu.rutgers.elearning.component.questions.QuestionAnswer;
import edu.rutgers.elearning.component.questions.RegexQuestion;
import edu.rutgers.elearning.util.math.SigfigNumber;
import edu.rutgers.elearning.component.journalism.model.*;
import edu.rutgers.elearning.component.journalism.model.SubjectModel.Gender;
import edu.rutgers.elearning.component.journalism.pte.JournalismController;
import edu.rutgers.elearning.component.questions.MultipleChoiceQuestion;
"""

GLOBAL_LISTS = """
	ArrayList<String> values = new ArrayList<String>();
	ArrayList<String> distractors = new ArrayList<String>();
	ArrayList<ArrayList<String>> varList = new ArrayList<ArrayList<String>>();
	String chosenSentenceAnswer;
	Tuple chosenSentenceDistractor;
"""

DAOs ="""
SubjectDAO subjectAccess = new SubjectDAO();
Random rand = new Random();
"""
def generateClassName(name):
    return """
public class {name} extends ProblemTemplateEngine {{
""".format(name=name)

def generateConstructorName(name):
    return """
public {name}(int problemtemplate_id, int[] criticalskill_ids, int debugmode, QuestionType type) {{
\tsuper(problemtemplate_id, criticalskill_ids, debugmode, type);
\tint distractorIndex, chosen;
""".format(name=name)

CONSTRUCTOR_END = """
		int sentenceIndex = rand.nextInt(sentenceList.size());
		chosenSentenceAnswer = JournalismController.capitalizeString(sentenceList.get(sentenceIndex));
		chosenSentenceDistractor = distractorList.get(sentenceIndex);
	}
"""

def generateMiddleFiller():
    return """

/**
	 * Formats the answers from a SigfigNumber into a
	 * QuestionAnswer object. Answers passed to this method
	 * can either be correct or incorrect answers.
	 *
	 * @param answer - The answer to be displayed 
	 * @param correct - true if this is the correct answer, otherwise false
	 * @return QuestionAnswer - Answer to be displayed to the user as one
	 * 		   of the multiple choice options
	 */
	protected QuestionAnswer formatAnswer(String answer, boolean correct) {
		QuestionAnswer qa = null;
		distractors.add(answer);
		qa = new QuestionAnswer(answer.toString(), answer, false, correct);
		
		return qa;
	}

	/**
	 * Populates the multiple choice answers, typically
	 * one correct answer and four incorrect answers. If
	 * five answers are not defined, this method will generate
	 * answers similar to the correct answer.
	 *
	 * @return List&lt;QuestionAnswer&gt; - the answers to be displayed
	 * 		   to the users.
	 */
	public List<QuestionAnswer> getMultipleChoiceAnswers() {
		ArrayList<QuestionAnswer> answers = new ArrayList<QuestionAnswer>();
		values.add(chosenSentenceAnswer);
		answers.add(formatAnswer(chosenSentenceAnswer, true));
		while(answers.size() < chosenSentenceDistractor.getLimit() && answers.size() < answer_count) {
			String candidate = JournalismController.capitalizeString(chosenSentenceDistractor.buildString());
			boolean good = true;
			for(int i = 0; i < values.size(); i++)
				if(candidate.contentEquals(values.get(i)))
					good = false;
			if(good == true) {
				values.add(candidate);
				answers.add(formatAnswer(candidate, false));
			}
		}
		return answers;
	}

	/**
	 * Used to generate the question text displayed.
	 *
	 * @return question - String question, this will be
	 * 		   displayed to the user
	 */
	public String getQuestionText() {
		if (type == QuestionType.OPENANSWER)
            return JournalismController.capitalizeString(chosenSentenceDistractor.buildString());
		else
			return "Select the best choice from the answers below:";
        }

	@Override
	/**
	 * Serves the question to the user. Depending on
	 * the type variable, this method will either
	 * serve a multiple choice question or an open
	 * answer question.
	 *
	 * @return GeneratedQuestion - object used to display
	 * 		   a multiple choice or open answer question
	 */
	public GeneratedQuestion serveQuestion() {
		GeneratedQuestion gq = null;
		RegexQuestion rq = new RegexQuestion();
		if (type == QuestionType.OPENANSWER) {
			chosenSentenceAnswer = JournalismController.regexPrep(chosenSentenceAnswer);
			rq.setRegex_accept(chosenSentenceAnswer);
			//gq.setRegex_reject(null);
			gq = rq;
		}
		else if (type == QuestionType.MULTIPLECHOICE) {
			MultipleChoiceQuestion mcq = new MultipleChoiceQuestion();
			mcq.setAnswers(getMultipleChoiceAnswers());
			mcq.prepareAnswers(answer_count, debugmode);
			gq = mcq;
		}
		if (gq != null) {
			gq.setQuestion_text(getQuestionText());
			gq.loadMetadata(problemtemplate_id);
			//gq.setDifficulty(difficulty);
			// TODO add critical 
		}
		return gq;
	}

	public String storeDistractors() {
		HashMap<String, Object> dataMap = new HashMap<String, Object>();
		int index = 0;
		String alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
		//use distractor values of A, B, C, D
		if(values.size() > alphabet.length()) {
			System.out.println("More than 26 distractors, can't keep up with naming");
		}
		for(String s : values) {
			dataMap.put("distractor " + alphabet.charAt(index),s);
			index++;
		}

		//not sure how to deal with this yet

		return dataMap.toString();
	}

	/**
	 * This method is for the 2018 Math Placement Exam.
	 * This method is to store the question data for a reporting
	 * service. This method will return a listing of all variables
	 * in this PTE
	 *
	 * @return String the version
	 */
	public String storeVersion()
	{
		HashMap<String, Object> dataMap = new HashMap<String, Object>();
		//dataMap.put();
		//TODO: this

		return dataMap.toString();
	}

	@Override
	public String getDebugInfo() {
		// TODO Auto-generated method stub
		// how do we get the debug info?
		// I'm not really sure what's in here
		return null;
	}

}

"""

def generateVersion(name):
    return """

    """

def generateEnd():
    return """

    """
