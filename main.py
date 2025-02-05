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
        # Utilisation du thème 'flatly'
        super().__init__(themename='flatly')
        self.title("Serious Game - Gestion de Patrimoine")
        self.geometry("1200x900")
        self.resizable(False, False)
        center_window(self, 1200, 900)
        self.configure(bg="#fffefd")  # Fond principal blanc cassé

        # Configuration globale des styles
        style = ttk.Style()
        style.theme_use('flatly')
        style.configure("TFrame", background="#fffefd")
        style.configure("TLabel", background="#fffefd", foreground="#29373e")
        style.configure("Card.TFrame", background="#fffefd", relief="raised", borderwidth=2)
        style.configure("Question.TLabel", background="#fffefd", foreground="#29373e", font=("Helvetica", 18))
        style.configure("Success.TButton", background="#d8e5ab", foreground="#29373e")
        style.configure("Primary.TButton", background="#29373e", foreground="#fffefd")
        style.configure("Info.TButton", background="#7a97b8", foreground="#fffefd")
        style.configure("Secondary.TButton", background="#7a97b8", foreground="#fffefd")
        style.configure("Danger.TButton", background="#29373e", foreground="#fffefd")
        # Style pour l'en-tête
        style.configure("Header.TFrame", background="#7a97b8")
        style.configure("Header.TLabel", background="#7a97b8", foreground="#fffefd", font=("Helvetica", 20, "bold"))
        # Styles pour le quiz
        style.configure("Quiz.TFrame", background="#fffefd")
        style.configure("Quiz.TLabel", background="#fffefd", foreground="#29373e", font=("Helvetica", 18))
        style.configure("Quiz.TRadiobutton", background="#fffefd", foreground="#29373e", font=("Helvetica", 14))
        style.configure("Quiz.TButton", background="#29373e", foreground="#fffefd")

        # Chargement des images depuis le dossier assets
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        logo_path = os.path.join(self.assets_dir, "logo.png")
        self.logo_photo = load_image_from_file(logo_path, (40, 40))
        self.budget_icon = load_image_from_file(os.path.join(self.assets_dir, "budget.png"), (30, 30))
        self.bonheur_icon = load_image_from_file(os.path.join(self.assets_dir, "bonheur.png"), (30, 30))
        self.epargne_icon = load_image_from_file(os.path.join(self.assets_dir, "epargne.png"), (30, 30))
        self.character_dir = os.path.join(self.assets_dir, "character")

        # Modification des jauges (remplacement de "loisirs" par "bonheur")
        self.gauges = {"budget": 50, "bonheur": 50, "epargne": 50}
        self.game_log = []
        self.checkpoint_state = None
        self.checkpoint_log_index = None

        # Chargement des fichiers JSON
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

        # Pour le quiz, sélection de 10 questions aléatoires
        self.current_quiz_list = []

        # Création d'un conteneur principal pour les frames
        self.container = ttk.Frame(self)
        self.container.pack(expand=True)

        # Création du menu de démarrage
        self.menu_frame = MenuFrame(parent=self.container, controller=self)
        self.menu_frame.grid(row=0, column=0, sticky="nsew")

        # Création des autres frames (jeu et quiz)
        self.frames = {}
        for F in (GameFrame, QuizFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Affichage de l'en-tête
        self.header_frame = ttk.Frame(self, style="Header.TFrame")
        self.header_frame.pack(side="top", fill="x")
        header_label = ttk.Label(self.header_frame, text="Serious Game - Gestion de Patrimoine", style="Header.TLabel")
        header_label.pack(pady=10)

        # (Le label d'instructions a été supprimé)
        # Bindings pour le jeu et la touche indice 'i'
        self.bind("<Left>", self.on_left_arrow)
        self.bind("<Right>", self.on_right_arrow)
        self.bind("<Return>", self.on_enter_key)
        self.bind("<i>", self.on_i_key)

        # Au démarrage, on affiche le menu
        self.show_frame("MenuFrame")

    def on_left_arrow(self, event):
        # Si nous sommes dans le jeu
        game_frame = self.frames.get("GameFrame")
        if game_frame and game_frame.winfo_ismapped():
            if "disabled" not in game_frame.next_button.state():
                game_frame.next_card()
            elif "disabled" not in game_frame.optionA_button.state():
                game_frame.choice("A")

    def on_right_arrow(self, event):
        game_frame = self.frames.get("GameFrame")
        if game_frame and game_frame.winfo_ismapped():
            if "disabled" not in game_frame.next_button.state():
                game_frame.next_card()
            elif "disabled" not in game_frame.optionB_button.state():
                game_frame.choice("B")

    def on_enter_key(self, event):
        if self.frames.get("GameFrame") and self.frames["GameFrame"].winfo_ismapped():
            if "disabled" not in self.frames["GameFrame"].next_button.state():
                self.frames["GameFrame"].next_card()
        elif self.frames.get("QuizFrame") and self.frames["QuizFrame"].winfo_ismapped():
            self.frames["QuizFrame"].submit_answer()

    def on_i_key(self, event):
        if self.frames.get("GameFrame") and self.frames["GameFrame"].winfo_ismapped():
            self.frames["GameFrame"].show_indice()

    def show_frame(self, frame_name):
        if frame_name in self.frames:
            self.frames[frame_name].tkraise()
        elif frame_name == "MenuFrame":
            self.menu_frame.tkraise()

    def update_gauges_display(self):
        self.frames["GameFrame"].update_gauges_label(
            self.gauges["budget"],
            self.gauges["bonheur"],
            self.gauges["epargne"]
        )

    def load_next_card(self):
        self.checkpoint_state = (self.gauges["budget"], self.gauges["bonheur"], self.gauges["epargne"])
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
        # Si le JSON utilise encore "loisirs", on ajoute cette valeur à "bonheur"
        self.gauges["bonheur"] += effects.get("loisirs", 0)
        # Si le JSON a été modifié pour utiliser "bonheur", on peut aussi récupérer directement l'effet "bonheur"
        if "bonheur" in effects:
            self.gauges["bonheur"] += effects.get("bonheur", 0)
        self.gauges["epargne"] += effects.get("epargne", 0)

        self.game_log.append({
            "situation": self.current_card.get("question", "Question non définie"),
            "choix": choix_text,
            "explanation": explanation
        })

        self.update_gauges_display()

        if self.gauges["budget"] <= 0 or self.gauges["bonheur"] <= 0 or self.gauges["epargne"] <= 0:
            messagebox.showinfo("Défaite", "Oh non ! Une de vos jauges est tombée à 0.")
            self.start_quiz()
        else:
            self.frames["GameFrame"].enable_next_button()

    def start_quiz(self):
        total_questions = min(10, len(self.quiz_questions))
        self.current_quiz_list = random.sample(self.quiz_questions, total_questions)
        self.current_quiz_index = 0
        self.quiz_answers = []
        self.frames["QuizFrame"].load_question(
            self.current_quiz_list[self.current_quiz_index],
            self.current_quiz_index + 1, total_questions
        )
        self.show_frame("QuizFrame")

    def process_quiz_answer(self, answer):
        self.quiz_answers.append(answer)
        self.current_quiz_index += 1
        total = len(self.current_quiz_list)
        if self.current_quiz_index < total:
            self.frames["QuizFrame"].load_question(
                self.current_quiz_list[self.current_quiz_index],
                self.current_quiz_index + 1, total
            )
        else:
            corrections = ""
            for i, q in enumerate(self.current_quiz_list):
                if self.quiz_answers[i] != q["answer"]:
                    corrections += f"Question {i+1}: {q.get('question', 'Question non définie')}\n"
                    corrections += f"Votre réponse: {self.quiz_answers[i]} | Réponse correcte: {q['answer']}\n"
                    corrections += f"Explication: {q.get('explanation', 'Aucune explication')}\n\n"
            if corrections:
                messagebox.showinfo("Quiz - Corrections", corrections)
                messagebox.showinfo("Quiz", "Fin de la partie.")
                self.destroy()
            else:
                messagebox.showinfo("Quiz", "Bravo, toutes les réponses sont correctes ! Vous reprenez la partie.")
                self.gauges["budget"], self.gauges["bonheur"], self.gauges["epargne"] = self.checkpoint_state
                self.game_log = self.game_log[:self.checkpoint_log_index]
                self.load_next_card()
                self.show_frame("GameFrame")

class MenuFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="TFrame")
        self.controller = controller
        # Titre du menu
        title = ttk.Label(self, text="Bienvenue dans le Serious Game", font=("Helvetica", 24, "bold"), style="TLabel")
        title.pack(pady=20)
        # Bouton Jouer
        play_button = ttk.Button(self, text="Jouer", command=self.start_game, bootstyle="Primary")
        play_button.pack(pady=10, ipadx=10, ipady=5)
        # Bouton Quitter
        quit_button = ttk.Button(self, text="Quitter", command=self.controller.destroy, bootstyle="Primary")
        quit_button.pack(pady=10, ipadx=10, ipady=5)

    def start_game(self):
        rules = (
            "Règles du jeu :\n"
            "- Vous devez gérer votre patrimoine en équilibrant votre Budget, votre Bonheur et votre Épargne.\n"
            "- Chaque décision aura un impact sur ces trois jauges.\n"
            "- Si l'une de vos jauges tombe à 0, vous passez au quiz de fin de partie.\n"
            "- Si vous répondez correctement aux 10 questions du quiz, vous reprenez votre partie depuis l'état précédent.\n"
            "- Utilisez les raccourcis :\n"
            "   • Flèche gauche (←) : Sélectionner l'option A / passer\n"
            "   • Flèche droite (→) : Sélectionner l'option B / passer\n"
            "   • Entrée : Valider ou passer\n"
            "   • 'i' : Afficher l'indice\n"
            "   • Dans le quiz, utilisez ↑/↓ pour naviguer et Entrée pour valider."
        )
        messagebox.showinfo("Règles", rules)
        # Démarre le jeu
        self.controller.load_next_card()
        self.controller.show_frame("GameFrame")

class GameFrame(ttk.Frame):
    def __init__(self, parent, controller):
        style = ttk.Style()
        style.configure("Card.TFrame", background="#fffefd", relief="raised", borderwidth=2)
        style.configure("Question.TLabel", background="#fffefd", foreground="#29373e", font=("Helvetica", 18))
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller

        # Création d'un frame pour les jauges avec icônes
        self.gauges_frame = ttk.Frame(self)
        self.gauges_frame.pack(pady=10)
        self.budget_label = ttk.Label(self.gauges_frame, text="", image=self.controller.budget_icon, compound="left", style="Question.TLabel")
        self.budget_label.pack(side="left", padx=10)
        self.bonheur_label = ttk.Label(self.gauges_frame, text="", image=self.controller.bonheur_icon, compound="left", style="Question.TLabel")
        self.bonheur_label.pack(side="left", padx=10)
        self.epargne_label = ttk.Label(self.gauges_frame, text="", image=self.controller.epargne_icon, compound="left", style="Question.TLabel")
        self.epargne_label.pack(side="left", padx=10)

        self.card_frame = ttk.Frame(self, style="Card.TFrame")
        self.card_frame.pack(pady=20, padx=20)

        self.character_label = ttk.Label(self.card_frame)
        self.character_label.pack(side="left", padx=10, pady=10)

        self.question_label = ttk.Label(self.card_frame, text="", wraplength=500, style="Question.TLabel")
        self.question_label.pack(side="left", padx=10, pady=10)

        # Suppression du label d'explication ; remplacé par le bouton raccourcis
        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.pack(pady=10)

        self.optionA_button = ttk.Button(
            self.buttons_frame,
            text="",
            width=25,
            command=lambda: self.choice("A"),
            bootstyle="success"
        )
        self.optionA_button.grid(row=0, column=0, padx=20, pady=10)
        self.optionB_button = ttk.Button(
            self.buttons_frame,
            text="",
            width=25,
            command=lambda: self.choice("B"),
            bootstyle="danger"
        )
        self.optionB_button.grid(row=0, column=1, padx=20, pady=10)

        if controller.logo_photo:
            self.indice_button = ttk.Button(
                self,
                text="Indice du conseiller (i)",
                image=controller.logo_photo,
                compound="left",
                command=self.show_indice,
                bootstyle="info"
            )
        else:
            self.indice_button = ttk.Button(
                self,
                text="Indice du conseiller (i)",
                command=self.show_indice,
                bootstyle="info"
            )
        self.indice_button.pack(pady=10)

        self.shortcuts_button = ttk.Button(
            self,
            text="Afficher les raccourcis",
            command=self.show_shortcuts,
            bootstyle="info"
        )
        self.shortcuts_button.pack(pady=10)

        self.next_button = ttk.Button(self, text="Suivant", command=self.next_card, state="disabled",
                                       width=30, bootstyle="primary")
        self.next_button.pack(pady=10)

        self.quit_button = ttk.Button(self, text="Quitter", command=self.controller.destroy, bootstyle="Primary")
        self.quit_button.pack(pady=10)

    def update_gauges_label(self, budget, bonheur, epargne):
        self.budget_label.config(text=f"Budget: {budget}")
        self.bonheur_label.config(text=f"Bonheur: {bonheur}")
        self.epargne_label.config(text=f"Épargne: {epargne}")

    def set_card(self, card):
        self.current_card = card
        self.question_label.config(text=card.get("question", "Question non définie"))
        self.next_button.config(state="disabled")
        self.optionA_button.config(state="normal", text=f"(←) {card['optionA'].get('text', 'Option A')}")
        self.optionB_button.config(state="normal", text=f"{card['optionB'].get('text', 'Option B')} (→)")
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

    def show_shortcuts(self):
        shortcuts = (
            "Raccourcis :\n"
            "- 'i' : Afficher l'indice\n"
            "- Flèche gauche (←) : Sélectionner l'option A ou passer\n"
            "- Flèche droite (→) : Sélectionner l'option B ou passer\n"
            "- Entrée : Valider la réponse (quiz) ou passer à la question suivante (jeu)\n"
            "- Flèches haut (↑)/bas (↓) dans le quiz : Naviguer entre les options"
        )
        messagebox.showinfo("Raccourcis", shortcuts)

    def choice(self, option):
        self.optionA_button.config(state="disabled")
        self.optionB_button.config(state="disabled")
        self.controller.apply_choice(option)

    def enable_next_button(self):
        self.next_button.config(state="normal")

    def next_card(self):
        self.controller.load_next_card()

class QuizFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, style="Quiz.TFrame")
        self.controller = controller
        self.var_answer = tk.StringVar()

        self.progress_label = ttk.Label(self, text="", style="Quiz.TLabel")
        self.progress_label.pack(pady=(10, 0))

        self.title_label = ttk.Label(self, text="Quiz Éducatif", style="Quiz.TLabel")
        self.title_label.pack(pady=10)

        self.question_label = ttk.Label(self, text="", wraplength=700, style="Quiz.TLabel")
        self.question_label.pack(pady=10)

        self.options_frame = ttk.Frame(self, style="Quiz.TFrame")
        self.options_frame.pack(pady=10)

        self.radio_buttons = {}
        for option in ["A", "B", "C", "D"]:
            rb = ttk.Radiobutton(self.options_frame, text="", variable=self.var_answer, value=option, style="Quiz.TRadiobutton")
            rb.pack(anchor="w", padx=20, pady=5)
            self.radio_buttons[option] = rb

        self.submit_button = ttk.Button(self, text="Valider", command=self.submit_answer, style="Quiz.TButton")
        self.submit_button.pack(pady=10)

        self.quit_button = ttk.Button(self, text="Quitter", command=self.controller.destroy, style="Quiz.TButton")
        self.quit_button.pack(pady=10)

        # Bindings pour naviguer dans le quiz avec Entrée, Up et Down
        self.bind("<Return>", lambda event: self.submit_answer())
        self.bind("<Up>", self.on_up_arrow)
        self.bind("<Down>", self.on_down_arrow)
        self.focus_set()

    def load_question(self, question, current_num, total):
        self.focus_set()  # S'assurer que la frame capte les événements clavier
        self.current_question = question
        self.progress_label.config(text=f"Question {current_num}/{total}")
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
