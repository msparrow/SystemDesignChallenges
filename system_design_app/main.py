import os
import sys
import json
import google.generativeai as genai
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGridLayout, QListWidget

# Add your Gemini API key here
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Load Canonical Solutions from JSON file
with open('/Users/matthewsparrow/MyProjects/SystemDesignChallenges/system_design_app/canonical_solutions.json', 'r') as f:
    CANONICAL_SOLUTIONS = json.load(f)

# Multi-Dimensional Qualitative Scoring Rubric
SCORING_RUBRIC = """
**1. Requirement Analysis & Scoping:**
- 0 (Not Attempted): The user gave a blank answer or a non-sensical answer.
- 1 (Not Acceptable): Fails to identify basic functional or non-functional requirements.
- 2 (Needs Improvement): Identifies some requirements but misses key aspects like scalability or latency.
- 3 (Acceptable): Clearly defines functional and non-functional requirements and reasonable scope.
- 4 (Exceptional): Provides a detailed and nuanced understanding of the requirements, including edge cases and trade-offs.

**2. High-Level Architecture:**
- 0 (Not Attempted): The user gave a blank answer or a non-sensical answer.
- 1 (Not Acceptable): Proposes a non-viable or overly simplistic architecture.
- 2 (Needs Improvement): The architecture has major flaws or omits critical components.
- 3 (Acceptable): A solid, workable architecture with all necessary components.
- 4 (Exceptional): A well-reasoned architecture that makes clever trade-offs and shows a deep understanding of system design principles.

**3. Component Deep-Dive:**
- 0 (Not Attempted): The user gave a blank answer or a non-sensical answer.
- 1 (Not Acceptable): Fails to break down the system into logical components.
- 2 (Needs Improvement): Components are poorly defined or have unclear responsibilities.
- 3 (Acceptable): Components are well-defined with clear responsibilities.
- 4 (Exceptional): Provides a detailed design for each component, including APIs and data models.

**4. Scalability & Bottleneck Analysis:**
- 0 (Not Attempted): The user gave a blank answer or a non-sensical answer.
- 1 (Not Acceptable): Does not address scalability or potential bottlenecks.
- 2 (Needs Improvement): Identifies some scalability issues but offers weak or ineffective solutions.
- 3 (Acceptable): Identifies major bottlenecks and proposes reasonable solutions.
- 4 (Exceptional): A thorough analysis of scalability challenges with creative and effective solutions.
"""

class SystemDesignApp(QWidget):
    def __init__(self):
        super().__init__()
        self.questions = list(CANONICAL_SOLUTIONS.keys())
        self.initUI()

    def initUI(self):
        self.setWindowTitle('System Design Interview Practice')
        self.main_layout = QHBoxLayout()

        # Left side: Question List
        self.question_list = QListWidget()
        self.question_list.addItems(self.questions)
        self.question_list.setCurrentRow(0)
        self.question_list.currentItemChanged.connect(self.question_changed)
        self.main_layout.addWidget(self.question_list, 1)

        # Right side: Main Content
        self.right_layout = QVBoxLayout()
        self.question_label = QLabel(self.questions[0])
        self.right_layout.addWidget(self.question_label)

        # Text Input Fields
        self.grid_layout = QGridLayout()
        self.requirements_input = QTextEdit()
        self.architecture_input = QTextEdit()
        self.components_input = QTextEdit()
        self.scalability_input = QTextEdit()
        self.grid_layout.addWidget(QLabel('Requirement Analysis & Scoping:'), 0, 0)
        self.grid_layout.addWidget(self.requirements_input, 0, 1)
        self.grid_layout.addWidget(QLabel('High-Level Architecture:'), 1, 0)
        self.grid_layout.addWidget(self.architecture_input, 1, 1)
        self.grid_layout.addWidget(QLabel('Component Deep-Dive:'), 2, 0)
        self.grid_layout.addWidget(self.components_input, 2, 1)
        self.grid_layout.addWidget(QLabel('Scalability & Bottleneck Analysis:'), 3, 0)
        self.grid_layout.addWidget(self.scalability_input, 3, 1)
        self.right_layout.addLayout(self.grid_layout)

        # Analyze Button
        self.analyze_button = QPushButton('Grade Solution')
        self.analyze_button.clicked.connect(self.analyze_solution)
        self.right_layout.addWidget(self.analyze_button)

        # Result Display Labels
        self.results_layout = QGridLayout()
        self.requirements_score_label = QLabel('Requirements Score:')
        self.architecture_score_label = QLabel('Architecture Score:')
        self.components_score_label = QLabel('Components Score:')
        self.scalability_score_label = QLabel('Scalability Score:')
        self.overall_score_label = QLabel('Overall Score:')
        self.grade_label = QLabel('Grade:')
        self.results_layout.addWidget(self.requirements_score_label, 0, 0)
        self.results_layout.addWidget(self.architecture_score_label, 1, 0)
        self.results_layout.addWidget(self.components_score_label, 2, 0)
        self.results_layout.addWidget(self.scalability_score_label, 3, 0)
        self.results_layout.addWidget(self.overall_score_label, 4, 0)
        self.results_layout.addWidget(self.grade_label, 5, 0)
        self.right_layout.addLayout(self.results_layout)

        # Analysis Output Window
        self.analysis_output = QTextEdit()
        self.analysis_output.setReadOnly(True)
        self.right_layout.addWidget(self.analysis_output)

        self.main_layout.addLayout(self.right_layout, 3)
        self.setLayout(self.main_layout)

    def question_changed(self, current, previous):
        if current is not None:
            self.question_label.setText(current.text())
            self.clear_inputs_and_results()

    def clear_inputs_and_results(self):
        self.requirements_input.clear()
        self.architecture_input.clear()
        self.components_input.clear()
        self.scalability_input.clear()
        self.requirements_score_label.setText('Requirements Score:')
        self.architecture_score_label.setText('Architecture Score:')
        self.components_score_label.setText('Components Score:')
        self.scalability_score_label.setText('Scalability Score:')
        self.overall_score_label.setText('Overall Score:')
        self.grade_label.setText('Grade:')
        self.analysis_output.clear()

    def analyze_solution(self):
        requirements_text = self.requirements_input.toPlainText().strip()
        architecture_text = self.architecture_input.toPlainText().strip()
        components_text = self.components_input.toPlainText().strip()
        scalability_text = self.scalability_input.toPlainText().strip()

        user_solution = f"""
        Requirement Analysis & Scoping:
        {requirements_text if requirements_text else '[USER LEFT THIS SECTION BLANK]'}

        High-Level Architecture:
        {architecture_text if architecture_text else '[USER LEFT THIS SECTION BLANK]'}

        Component Deep-Dive:
        {components_text if components_text else '[USER LEFT THIS SECTION BLANK]'}

        Scalability & Bottleneck Analysis:
        {scalability_text if scalability_text else '[USER LEFT THIS SECTION BLANK]'}
        """
        
        current_question = self.question_list.currentItem().text()
        canonical_solution = CANONICAL_SOLUTIONS.get(current_question, "No canonical solution found for this question.")

        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            response = model.generate_content(f"""
            Analyze the following user solution for a system design problem.
            Compare it against the provided canonical solution and score it based on the rubric.
            If a section's content is '[USER LEFT THIS SECTION BLANK]', it means the user did not attempt it and it must be scored 0.
            Return only the scores for each section and the overall score.

            User Solution:
            {user_solution}

            Canonical Solution:
            {canonical_solution}

            Scoring Rubric:
            {SCORING_RUBRIC}

            For each of the four sections, provide a score (0-4) and a brief, one-paragraph justification for that score. Return the output in the following format:
            Requirements Score: [0-4] - [Justification]
            Architecture Score: [0-4] - [Justification]
            Components Score: [0-4] - [Justification]
            Scalability Score: [0-4] - [Justification]
            """)

            self.display_scores(response.text)

        except Exception as e:
            self.requirements_score_label.setText(f"Error: {e}")

    def display_scores(self, analysis_result):
        self.analysis_output.setText(analysis_result)

        scores = {}
        for line in analysis_result.strip().split('\n'):
            if ":" in line:
                key, value_part = line.split(":", 1)
                # Extract only the number from the value part
                score_str = value_part.strip().split(' ')[0]
                try:
                    scores[key.strip()] = int(score_str)
                except ValueError:
                    pass # Ignore lines where the score is not an integer

        requirements_score = scores.get('Requirements Score', 0)
        architecture_score = scores.get('Architecture Score', 0)
        components_score = scores.get('Components Score', 0)
        scalability_score = scores.get('Scalability Score', 0)

        self.requirements_score_label.setText(f'Requirements Score: {requirements_score}')
        self.architecture_score_label.setText(f'Architecture Score: {architecture_score}')
        self.components_score_label.setText(f'Components Score: {components_score}')
        self.scalability_score_label.setText(f'Scalability Score: {scalability_score}')

        overall_score = requirements_score + architecture_score + components_score + scalability_score
        self.overall_score_label.setText(f'Overall Score: {overall_score} / 16')

        grade = self.calculate_grade(overall_score)
        self.grade_label.setText(f'Grade: {grade}')

        self.analysis_output.setText(analysis_result)

    def calculate_grade(self, score):
        percentage = (score / 16) * 100
        if percentage >= 95:
            return 'A+'
        elif percentage >= 85:
            return 'A'
        elif percentage >= 75:
            return 'B'
        elif percentage >= 65:
            return 'C'
        elif percentage >= 55:
            return 'C-'
        elif percentage >= 45:
            return 'D'
        else:
            return 'F'


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SystemDesignApp()
    ex.show()
    sys.exit(app.exec_())