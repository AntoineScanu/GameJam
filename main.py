import os
import random
import json
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

def load_image_from_file(path, size):
    """
    Charge une image depuis un fichier, la redimensionne et renvoie un objet PhotoImage.
    """
    try:
        image = Image.open(path)
        image = image.resize(size, resample=Image.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Erreur lors du chargement de l'image depuis {path}: {e}")
        return None

def get_random_character_image(character_dir, size):
    """
    Parcourt le dossier 'character' et renvoie une image (PhotoImage) choisie aléatoirement.
    """
    try:
        files = [f for f in os.listdir(character_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if not files:
            return None
        chosen_file = random.choice(files)
        path = os.path.join(character_dir, chosen_file)
        return load_image_from_file(path, size)
    except Exception as e:
        print(f"Erreur lors de la sélection d'une image de personnage: {e}")
        return None

def center_window(window, width, height):
    """
    Centre la fenêtre sur l'écran en utilisant les dimensions passées.
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

class SeriousGame(ttk.Window):
    def __init__(self):
        # Utilisation du thème 'flatly' pour un style moderne
        super().__init__(themename='flatly')
        self.title("Serious Game - Gestion de Patrimoine")
        self.geometry("1200x900")
        self.resizable(False, False)
        center_window(self, 1200, 900)
        self.configure(bg="#f0f8ff")

        # Dossier assets et chargement du logo (pour le bouton indice)
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        logo_path = os.path.join(self.assets_dir, "logo.png")
        self.logo_photo = load_image_from_file(logo_path, (40, 40))

        # Dossier des images de personnage
        self.character_dir = os.path.join(self.assets_dir, "character")

        # État initial du jeu
        self.gauges = {"budget": 50, "loisirs": 50, "epargne": 50}
        self.game_log = []
        self.checkpoint_state = None
        self.checkpoint_log_index = None

        # Chargement des données JSON
        try:
            with open("cards.json", "r", encoding="utf-8") as f:
                self.cards = json.load(f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger cards.json: {e}")
            self.destroy()

        try:
            with open("quiz.json", "r", encoding="utf-8") as f:
                self.quiz_questions = json.load(f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger quiz.json: {e}")
            self.destroy()

        # Conteneur principal pour les frames (centré)
        self.container = ttk.Frame(self)
        self.container.pack(expand=True)

        # Création des frames de jeu et de quiz
        self.frames = {}
        for F in (GameFrame, QuizFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # En-tête (titre du jeu)
        self.header_frame = ttk.Frame(self, bootstyle="info")
        self.header_frame.pack(side="top", fill="x")
        header_label = ttk.Label(self.header_frame, text="Serious Game - Gestion de Patrimoine", font=("Helvetica", 20, "bold"))
        header_label.pack(pady=10)

        # Label d'instructions pour les raccourcis clavier
        self.shortcuts_label = ttk.Label(self, text="Raccourcis: Pour le jeu → ← pour choisir, Entrée ou flèche pour passer; Pour le quiz ↑/↓ pour naviguer, Entrée pour valider", font=("Helvetica", 12))
        self.shortcuts_label.pack(side="bottom", pady=5)

        # Lier les touches fléchées et Entrée (pour la partie jeu)
        self.bind("<Left>", self.on_left_arrow)
        self.bind("<Right>", self.on_right_arrow)
        self.bind("<Return>", self.on_enter_key)

        # Démarrage sur la frame de jeu
        self.show_frame("GameFrame")
        self.load_next_card()

    def on_left_arrow(self, event):
        # Pour la partie jeu, si la frame de jeu est visible
        game_frame = self.frames["GameFrame"]
        if game_frame.winfo_ismapped():
            # Si le bouton "Suivant" est activé, passer à la question suivante
            if "disabled" not in game_frame.next_button.state():
                game_frame.next_card()
            # Sinon, sélectionner l'option A
            elif "disabled" not in game_frame.optionA_button.state():
                game_frame.choice("A")

    def on_right_arrow(self, event):
        # Pour la partie jeu, idem pour l'option B
        game_frame = self.frames["GameFrame"]
        if game_frame.winfo_ismapped():
            if "disabled" not in game_frame.next_button.state():
                game_frame.next_card()
            elif "disabled" not in game_frame.optionB_button.state():
                game_frame.choice("B")

    def on_enter_key(self, event):
        # Dans la partie jeu, si le bouton "Suivant" est activé, passer à la question suivante
        if self.frames["GameFrame"].winfo_ismapped():
            if "disabled" not in self.frames["GameFrame"].next_button.state():
                self.frames["GameFrame"].next_card()
        # Dans le quiz, la touche Entrée valide la réponse (le quiz gère ses propres flèches)
        elif self.frames["QuizFrame"].winfo_ismapped():
            self.frames["QuizFrame"].submit_answer()

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()

    def update_gauges_display(self):
        gauges_text = f"Budget: {self.gauges['budget']} | Loisirs: {self.gauges['loisirs']} | Épargne: {self.gauges['epargne']}"
        self.frames["GameFrame"].update_gauges_label(gauges_text)

    def load_next_card(self):
        self.checkpoint_state = (self.gauges["budget"], self.gauges["loisirs"], self.gauges["epargne"])
        self.checkpoint_log_index = len(self.game_log)
        self.current_card = random.choice(self.cards)
        self.frames["GameFrame"].set_card(self.current_card)
        self.update_gauges_display()

    def apply_choice(self, choice):
        if choice == "A":
            effects = self.current_card["optionA"]["effects"]
            explanation = self.current_card["optionA"]["explanation"]
            choix_text = self.current_card["optionA"]["text"]
        elif choice == "B":
            effects = self.current_card["optionB"]["effects"]
            explanation = self.current_card["optionB"]["explanation"]
            choix_text = self.current_card["optionB"]["text"]
        else:
            return

        self.gauges["budget"] += effects.get("budget", 0)
        self.gauges["loisirs"] += effects.get("loisirs", 0)
        self.gauges["epargne"] += effects.get("epargne", 0)

        self.game_log.append({
            "situation": self.current_card.get("question", "Question non définie"),
            "choix": choix_text,
            "explication": explanation
        })

        self.frames["GameFrame"].show_explanation(explanation)
        self.update_gauges_display()

        if self.gauges["budget"] <= 0 or self.gauges["loisirs"] <= 0 or self.gauges["epargne"] <= 0:
            messagebox.showinfo("Défaite", "Oh non ! Une de vos jauges est tombée à 0.")
            self.start_quiz()
        else:
            self.frames["GameFrame"].enable_next_button()

    def start_quiz(self):
        self.current_quiz_index = 0
        self.quiz_answers = []
        self.frames["QuizFrame"].load_question(self.quiz_questions[self.current_quiz_index])
        self.show_frame("QuizFrame")

    def process_quiz_answer(self, answer):
        self.quiz_answers.append(answer)
        self.current_quiz_index += 1
        if self.current_quiz_index < len(self.quiz_questions):
            self.frames["QuizFrame"].load_question(self.quiz_questions[self.current_quiz_index])
        else:
            correct = all(self.quiz_answers[i] == self.quiz_questions[i]["answer"] for i in range(len(self.quiz_questions)))
            if correct:
                messagebox.showinfo("Quiz", "Bravo, toutes les réponses sont correctes ! Vous reprenez la partie.")
                self.gauges["budget"], self.gauges["loisirs"], self.gauges["epargne"] = self.checkpoint_state
                self.game_log = self.game_log[:self.checkpoint_log_index]
                self.load_next_card()
                self.show_frame("GameFrame")
            else:
                corrections = "Correction du quiz:\n\n"
                for idx, q in enumerate(self.quiz_questions):
                    user_answer = self.quiz_answers[idx] if idx < len(self.quiz_answers) else "Non répondu"
                    correct_answer = q["answer"]
                    corrections += f"Q{idx+1}: {q.get('question', 'Question non définie')}\nVotre réponse: {user_answer} | Réponse correcte: {correct_answer}\n\n"
                messagebox.showinfo("Quiz - Corrections", corrections)
                messagebox.showinfo("Quiz", "Fin de la partie.")
                self.destroy()

class GameFrame(ttk.Frame):
    def __init__(self, parent, controller):
        # Style pour la carte
        style = ttk.Style()
        style.configure("Card.TFrame", background="white", relief="raised", borderwidth=2)
        # Style pour le label de la question
        style.configure("Question.TLabel", background="white", foreground="black", font=("Helvetica", 18))
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller

        self.gauges_label = ttk.Label(self, text="", font=("Helvetica", 16, "bold"), bootstyle="info")
        self.gauges_label.pack(pady=10)

        self.card_frame = ttk.Frame(self, style="Card.TFrame")
        self.card_frame.pack(pady=20, padx=20)

        self.character_label = ttk.Label(self.card_frame)
        self.character_label.pack(side="left", padx=10, pady=10)

        self.question_label = ttk.Label(self.card_frame, text="", wraplength=500, style="Question.TLabel")
        self.question_label.pack(side="left", padx=10, pady=10)

        self.explanation_label = ttk.Label(self, text="", wraplength=700, font=("Helvetica", 14, "italic"), foreground="blue")
        self.explanation_label.pack(pady=10)

        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.pack(pady=10)

        # Pour l'option A, la flèche gauche précède le texte
        self.optionA_button = ttk.Button(
            self.buttons_frame,
            text="",
            width=25,
            command=lambda: self.choice("A"),
            bootstyle="success"
        )
        self.optionA_button.grid(row=0, column=0, padx=20, pady=10)
        # Pour l'option B, le texte est suivi de la flèche droite
        self.optionB_button = ttk.Button(
            self.buttons_frame,
            text="",
            width=25,
            command=lambda: self.choice("B"),
            bootstyle="danger"
        )
        self.optionB_button.grid(row=0, column=1, padx=20, pady=10)

        if controller.logo_photo:
            self.indice_button = ttk.Button(self, text="Indice du conseiller", image=controller.logo_photo,
                                            compound="left", command=self.show_indice, bootstyle="info")
        else:
            self.indice_button = ttk.Button(self, text="Indice du conseiller", command=self.show_indice, bootstyle="info")
        self.indice_button.pack(pady=10)

        self.next_button = ttk.Button(self, text="Suivant", command=self.next_card, state="disabled",
                                       width=30, bootstyle="primary")
        self.next_button.pack(pady=10)

        self.quit_button = ttk.Button(self, text="Quitter", command=self.controller.destroy, bootstyle="secondary")
        self.quit_button.pack(pady=10)

    def update_gauges_label(self, text):
        self.gauges_label.config(text=text)

    def set_card(self, card):
        self.current_card = card
        self.question_label.config(text=card.get("question", "Question non définie"))
        self.explanation_label.config(text="")
        self.next_button.config(state="disabled")
        self.optionA_button.config(state="normal", text=f"← {card['optionA'].get('text', 'Option A')}")
        self.optionB_button.config(state="normal", text=f"{card['optionB'].get('text', 'Option B')} →")
        char_image = get_random_character_image(self.controller.character_dir, (150, 150))
        if char_image:
            self.character_label.config(image=char_image)
            self.character_label.image = char_image
        else:
            self.character_label.config(text="Personnage", image="")

    def show_indice(self):
        if hasattr(self, "current_card"):
            indice = self.current_card.get("hint", "Pas d'indice disponible.")
            messagebox.showinfo("Indice du conseiller", indice)

    def choice(self, option):
        self.optionA_button.config(state="disabled")
        self.optionB_button.config(state="disabled")
        self.controller.apply_choice(option)

    def show_explanation(self, explanation):
        self.explanation_label.config(text=explanation)

    def enable_next_button(self):
        self.next_button.config(state="normal")

    def next_card(self):
        self.controller.load_next_card()

class QuizFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="warning")
        self.controller = controller
        self.var_answer = tk.StringVar()

        self.title_label = ttk.Label(self, text="Quiz Éducatif", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=20)

        self.question_label = ttk.Label(self, text="", wraplength=700, font=("Helvetica", 18))
        self.question_label.pack(pady=20)

        self.options_frame = ttk.Frame(self)
        self.options_frame.pack(pady=10)

        self.radio_buttons = {}
        for option in ["A", "B", "C", "D"]:
            rb = ttk.Radiobutton(self.options_frame, text="", variable=self.var_answer, value=option, bootstyle="success")
            rb.pack(anchor="w", padx=20, pady=5)
            self.radio_buttons[option] = rb

        self.submit_button = ttk.Button(self, text="Valider", command=self.submit_answer, bootstyle="primary")
        self.submit_button.pack(pady=20)

        self.quit_button = ttk.Button(self, text="Quitter", command=self.controller.destroy, bootstyle="secondary")
        self.quit_button.pack(pady=10)

        # Bindings pour naviguer avec les flèches dans le quiz
        self.bind("<Up>", self.on_up_arrow)
        self.bind("<Down>", self.on_down_arrow)

    def load_question(self, question):
        self.focus_set()  # Assure que la frame capte les événements clavier
        self.current_question = question
        self.question_label.config(text=question.get("question", "Question non définie"))
        self.var_answer.set("")
        options = question.get("options", {})
        for option in ["A", "B", "C", "D"]:
            text = options.get(option, "")
            self.radio_buttons[option].config(text=f"{option}: {text}")

    def on_up_arrow(self, event):
        options = ["A", "B", "C", "D"]
        current = self.var_answer.get()
        if current not in options:
            new_index = 0
        else:
            idx = options.index(current)
            new_index = (idx - 1) % len(options)
        self.var_answer.set(options[new_index])

    def on_down_arrow(self, event):
        options = ["A", "B", "C", "D"]
        current = self.var_answer.get()
        if current not in options:
            new_index = 0
        else:
            idx = options.index(current)
            new_index = (idx + 1) % len(options)
        self.var_answer.set(options[new_index])

    def submit_answer(self):
        answer = self.var_answer.get()
        if not answer:
            messagebox.showwarning("Attention", "Veuillez sélectionner une réponse.")
            return
        self.controller.process_quiz_answer(answer)

if __name__ == "__main__":
    app = SeriousGame()
    app.mainloop()
