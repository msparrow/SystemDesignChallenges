import os
import sys
import json
import google.generativeai as genai
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QGridLayout, QListWidget, QDialog, QLineEdit, QListWidgetItem, QLineEdit
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# --- Constants ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# Use absolute path for reliability
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SOLUTIONS_FILE = os.path.join(APP_DIR, 'canonical_solutions.json')
RESPONSES_FILE = os.path.join(APP_DIR, 'user_responses.json')
GLOSSARY_FILE = os.path.join(APP_DIR, 'glossary.json')


# --- Load Data ---
with open(SOLUTIONS_FILE, 'r') as f:
    CANONICAL_SOLUTIONS = json.load(f)

with open(GLOSSARY_FILE, 'r') as f:
    GLOSSARY_DATA = json.load(f)

# --- Scoring Rubric ---
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

class GeminiWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_key, user_solution, canonical_solution):
        super().__init__()
        self.api_key = api_key
        self.user_solution = user_solution
        self.canonical_solution = canonical_solution
        self.prompt = f"""
        Analyze the following user solution for a system design problem.
        Compare it against the provided canonical solution and score it based on the rubric.
        If a section's content is '[USER LEFT THIS SECTION BLANK]', it means the user did not attempt it and it must be scored 0.

        User Solution:
        {self.user_solution}

        Canonical Solution:
        {self.canonical_solution}

        Scoring Rubric:
        {SCORING_RUBRIC}

        For each of the four sections, provide a score (0-4) and a brief, one-paragraph justification for that score. Return the output in the following format:
        Requirements Score: [0-4] - [Justification]
        Architecture Score: [0-4] - [Justification]
        Components Score: [0-4] - [Justification]
        Scalability Score: [0-4] - [Justification]

        Finally, end with a 2-3 sentence summary of the overall score out of 16. Explain whether the user did a good job and how they would have performed in a real interview based on this answer.
        """

    def _call_gemini_api(self):
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content(self.prompt, request_options={'timeout': 10})
        return response.text

    def run(self):
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._call_gemini_api)
        try:
            result = future.result(timeout=6.5)
            self.finished.emit(result)
        except TimeoutError:
            self.error.emit("Request timed out after 6 seconds.")
        except Exception as e:
            self.error.emit(str(e))

class GlossaryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Glossary")
        self.resize(900, 600)  # Set a larger default size
        self.main_layout = QVBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_concepts)
        self.main_layout.addWidget(self.search_bar)

        self.content_layout = QHBoxLayout()
        self.concept_list = QListWidget()
        self.concept_list.currentItemChanged.connect(self.display_concept)
        self.content_layout.addWidget(self.concept_list)

        self.concept_display = QTextEdit()
        self.concept_display.setReadOnly(True)
        self.content_layout.addWidget(self.concept_display)

        self.main_layout.addLayout(self.content_layout)
        self.setLayout(self.main_layout)
        self.load_concepts()

    def load_concepts(self):
        for section, concepts in GLOSSARY_DATA.items():
            section_item = QListWidgetItem(f"--- {section} ---")
            font = section_item.font()
            font.setBold(True)
            section_item.setFont(font)
            section_item.setFlags(section_item.flags() & ~Qt.ItemIsSelectable)
            self.concept_list.addItem(section_item)
            for concept in concepts.keys():
                self.concept_list.addItem(concept)

    def filter_concepts(self, text):
        for i in range(self.concept_list.count()):
            item = self.concept_list.item(i)
            is_section = item.text().startswith('---')
            if is_section:
                item.setHidden(False) # Always show sections
            else:
                item.setHidden(text.lower() not in item.text().lower())

    def display_concept(self, current, previous):
        if current is not None and not current.text().startswith('---'):
            section_item = self.find_section_item(current)
            if section_item:
                section = section_item.text().strip('--- ')
                concept = current.text()
                self.concept_display.setText(GLOSSARY_DATA[section][concept])
        else:
            self.concept_display.clear()

    def find_section_item(self, item):
        index = self.concept_list.row(item)
        while index >= 0:
            current_item = self.concept_list.item(index)
            if current_item.text().startswith('---'):
                return current_item
            index -= 1
        return None

class SystemDesignApp(QWidget):
    def __init__(self):
        super().__init__()
        self.questions = list(CANONICAL_SOLUTIONS.keys())
        self.user_responses = self.load_or_create_responses()
        self.worker = None
        self.initUI()
        self.init_autosave_timer()
        # Load the first question's content
        self.question_list.setCurrentRow(0)


    def initUI(self):
        self.setWindowTitle('System Design Interview Practice')
        self.main_layout = QHBoxLayout()

        # Left side: Question List
        self.question_list = QListWidget()
        self.question_list.addItems(self.questions)
        self.question_list.currentItemChanged.connect(self.question_changed)
        self.main_layout.addWidget(self.question_list, 1)

        # Right side: Main Content
        self.right_layout = QVBoxLayout()

        # Top bar with Glossary button
        self.top_bar_layout = QHBoxLayout()
        self.top_bar_layout.addStretch(1)
        self.glossary_button = QPushButton("Glossary")
        self.glossary_button.clicked.connect(self.open_glossary)
        self.glossary_button.setFixedWidth(100)
        self.top_bar_layout.addWidget(self.glossary_button)
        self.right_layout.addLayout(self.top_bar_layout)

        self.question_label = QLabel()
        self.right_layout.addWidget(self.question_label)

        # Add the grade label
        self.grade_label = QLabel("Current Grade: 0/16")
        self.right_layout.addWidget(self.grade_label)

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
        self.analyze_button.clicked.connect(self.start_analysis)
        self.right_layout.addWidget(self.analyze_button)

        # Result Display
        self.analysis_output = QTextEdit()
        self.analysis_output.setReadOnly(True)
        self.right_layout.addWidget(self.analysis_output)

        self.main_layout.addLayout(self.right_layout, 3)
        self.setLayout(self.main_layout)

    def open_glossary(self):
        dialog = GlossaryDialog(self)
        dialog.exec_()

    def init_autosave_timer(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save_current_responses)
        self.autosave_timer.start(5000)

    def load_or_create_responses(self):
        try:
            with open(RESPONSES_FILE, 'r') as f:
                responses = json.load(f)
                # Ensure all questions exist in the file and have a grade
                for q in self.questions:
                    if q not in responses:
                        responses[q] = {"requirements": "", "architecture": "", "components": "", "scalability": "", "current_grade": 0}
                    elif "current_grade" not in responses[q]:
                        responses[q]["current_grade"] = 0
                return responses
        except (FileNotFoundError, json.JSONDecodeError):
            responses = {q: {"requirements": "", "architecture": "", "components": "", "scalability": "", "current_grade": 0} for q in self.questions}
            with open(RESPONSES_FILE, 'w') as f:
                json.dump(responses, f, indent=2)
            return responses

    def save_current_responses(self, item=None):
        if item is None:
            item = self.question_list.currentItem()

        if not item:
            return

        question_text = item.text()
        grade = self.user_responses.get(question_text, {}).get("current_grade", 0)
        self.user_responses[question_text] = {
            "requirements": self.requirements_input.toPlainText(),
            "architecture": self.architecture_input.toPlainText(),
            "components": self.components_input.toPlainText(),
            "scalability": self.scalability_input.toPlainText(),
            "current_grade": grade
        }
        with open(RESPONSES_FILE, 'w') as f:
            json.dump(self.user_responses, f, indent=2)

    def question_changed(self, current, previous):
        # Save the responses for the question we are leaving
        if previous is not None:
            self.save_current_responses(item=previous)

        # Load the responses for the new question
        if current is not None:
            question_text = current.text()
            self.question_label.setText(question_text)
            self.load_responses_for_question(question_text)
            self.analysis_output.clear()
            grade = self.user_responses.get(question_text, {}).get("current_grade", 0)
            self.grade_label.setText(f"Current Grade: {grade}/16")

    def load_responses_for_question(self, question):
        responses = self.user_responses.get(question, {})
        self.requirements_input.setText(responses.get("requirements", ""))
        self.architecture_input.setText(responses.get("architecture", ""))
        self.components_input.setText(responses.get("components", ""))
        self.scalability_input.setText(responses.get("scalability", ""))

    def start_analysis(self):
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("Grading...")
        self.save_current_responses()

        current_question = self.question_list.currentItem().text()
        responses = self.user_responses.get(current_question, {})
        
        user_solution = f"""
        Requirement Analysis & Scoping:
        {responses.get('requirements', '').strip() or '[USER LEFT THIS SECTION BLANK]'}

        High-Level Architecture:
        {responses.get('architecture', '').strip() or '[USER LEFT THIS SECTION BLANK]'}

        Component Deep-Dive:
        {responses.get('components', '').strip() or '[USER LEFT THIS SECTION BLANK]'}

        Scalability & Bottleneck Analysis:
        {responses.get('scalability', '').strip() or '[USER LEFT THIS SECTION BLANK]'}
        """

        canonical_solution = CANONICAL_SOLUTIONS.get(current_question, "")
        self.worker = GeminiWorker(GEMINI_API_KEY, user_solution, canonical_solution)
        self.worker.finished.connect(self.display_scores)
        self.worker.error.connect(self.display_error)
        self.worker.start()

    def display_scores(self, analysis_result):
        self.analysis_output.setText(analysis_result)
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("Grade Solution")

        # Parse the score and update the grade
        total_score = self.parse_and_update_grade(analysis_result)
        current_question = self.question_list.currentItem().text()
        self.user_responses[current_question]["current_grade"] = total_score
        self.save_current_responses()  # Save immediately after grading
        self.grade_label.setText(f"Current Grade: {total_score}/16")

    def parse_and_update_grade(self, analysis_result):
        total_score = 0
        try:
            lines = analysis_result.strip().split('\n')
            for line in lines:
                if ":" in line:
                    score_str = line.split(':')[1].strip().split(' ')[0]
                    total_score += int(score_str)
        except (ValueError, IndexError):
            # Handle cases where parsing fails
            pass
        return total_score

    def display_error(self, error_message):
        self.analysis_output.setText(f"An error occurred: {error_message}")
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("Grade Solution")

    def closeEvent(self, event):
        self.save_current_responses()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SystemDesignApp()
    ex.show()
    sys.exit(app.exec_())