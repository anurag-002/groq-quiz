from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
import random
from groq import Groq
import sys

# --- CONFIG ---
GROQ_API_KEY = "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"
MODEL = "llama3-8b-8192"
NUM_OPTIONS = 4
TOTAL_QUESTIONS = 10

Window.clearcolor = (1, 1, 1, 1)
BLUE = get_color_from_hex('#3692D6')
client = Groq(api_key=GROQ_API_KEY)
used_questions = []

# Category prompts
QUIZ_PROMPTS = [
    "Create a fun Bollywood or Hollywood trivia question. Use recent movies, actors, or Netflix series. Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Ask a question related to trending tech, new gadgets, viral apps or Insta/YouTube culture. Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Ask a sports-related question (cricket, football, Olympics, or famous players like Kohli or Messi). Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Generate a question from Indian history, cultural traditions, or national festivals. Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Create a science or climate-based quiz question — inventions, discoveries, or environment. Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Ask a current affairs or recent events question (India or international). Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Create a quiz question around music trends, viral songs, K-pop, or TikTok dances. Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Make a question about world geography, tourist spots, or capital cities. Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Create a fun fashion or lifestyle question — style trends, brands, or Gen-Z culture. Format:\nQuestion: ...\nOptions: ...\nAnswer: ...",
    "Ask a question about viral memes, internet slang, or trending X (Twitter) posts. Format:\nQuestion: ...\nOptions: ...\nAnswer: ..."
]

def get_unique_groq_question():
    attempts = 0
    max_attempts = 10

    while attempts < max_attempts:
        prompt = random.choice(QUIZ_PROMPTS)

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9
        )

        output = response.choices[0].message.content.strip()

        try:
            q_text = output.split("Question:")[1].split("Options:")[0].strip()
            options = output.split("Options:")[1].split("Answer:")[0].strip().split(",")
            answer = output.split("Answer:")[1].strip()

            if len(options) == NUM_OPTIONS and q_text not in used_questions:
                used_questions.append(q_text)
                return {"question": q_text, "options": [opt.strip() for opt in options], "answer": answer}
        except Exception as e:
            print("Error parsing Groq response:", e)
            attempts += 1

    return {
        "question": "Fallback Question: What is the capital of France?",
        "options": ["Berlin", "Madrid", "Paris", "Lisbon"],
        "answer": "Paris"
    }

class QuizLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)

        self.question_count = 0
        self.score = 0

        self.logo = Image(source='groq-logo.png', size_hint=(1, 0.3))
        self.add_widget(self.logo)

        self.question_label = Label(
            text="Loading...",
            halign="center",
            valign="middle",
            color=(0, 0, 0, 1),
            font_size='20sp',
            size_hint=(1, None)
        )
        self.question_label.bind(width=self.update_text_size)
        self.question_label.bind(texture_size=self.update_label_height)
        self.add_widget(self.question_label)

        self.buttons = []
        for _ in range(NUM_OPTIONS):
            btn = Button(
                text="",
                size_hint=(1, None),
                height=50,
                background_color=BLUE,
                color=(1, 1, 1, 1),
                font_size='16sp'
            )
            btn.bind(on_release=self.check_answer)
            self.buttons.append(btn)
            self.add_widget(btn)

        self.load_question()

    def update_text_size(self, instance, width):
        instance.text_size = (width, None)

    def update_label_height(self, instance, size):
        instance.height = size[1]

    def load_question(self):
        if self.question_count >= TOTAL_QUESTIONS:
            self.show_final_popup()
            return

        self.disable_buttons(True)
        self.question_label.text = "Fetching new question..."

        q = get_unique_groq_question()
        self.current_question = q
        self.question_label.text = q["question"]

        random.shuffle(q["options"])
        for i in range(NUM_OPTIONS):
            self.buttons[i].text = q["options"][i]
            self.buttons[i].disabled = False
            self.buttons[i].background_color = BLUE

    def check_answer(self, instance):
        correct = self.current_question["answer"]
        selected = instance.text
        self.question_count += 1

        if selected == correct:
            instance.background_color = (0, 1, 0, 1)  # Green
            self.score += 10
            message = f"✅ Correct!\nScore: {self.score}"
        else:
            instance.background_color = (1, 0, 0, 1)  # Red
            self.score -= 2
            message = f"❌ Wrong! Correct: {correct}\nScore: {self.score}"

        self.disable_buttons(True)
        self.show_next_popup(message)

    def disable_buttons(self, value):
        for btn in self.buttons:
            btn.disabled = value

    def show_next_popup(self, message):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        label = Label(text=message, font_size='18sp', color=(0, 0, 0, 1), halign='center')
        label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))

        next_btn = Button(
            text='Next',
            size_hint=(1, None),
            height=40,
            background_color=BLUE,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(label)
        layout.add_widget(next_btn)

        popup = Popup(title='Groq Quiz', content=layout,
                      size_hint=(0.8, 0.4), auto_dismiss=False)

        next_btn.bind(on_release=lambda x: (popup.dismiss(), self.load_question()))
        popup.open()

    def show_final_popup(self):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        label = Label(text=f"🎯 Quiz Completed!\nYour Final Score: {self.score}", font_size='20sp', color=(0, 0, 0, 1), halign='center')
        label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))

        quit_btn = Button(
            text='Quit',
            size_hint=(1, None),
            height=50,
            background_color=(1, 0, 0, 1),  # Red
            color=(1, 1, 1, 1),
            font_size='18sp'
        )
        quit_btn.bind(on_release=lambda x: sys.exit(0))

        layout.add_widget(label)
        layout.add_widget(quit_btn)

        popup = Popup(title='Quiz Finished', content=layout,
                      size_hint=(0.8, 0.5), auto_dismiss=False)
        popup.open()

class QuizApp(App):
    def build(self):
        return QuizLayout()

if __name__ == '__main__':
    QuizApp().run()
