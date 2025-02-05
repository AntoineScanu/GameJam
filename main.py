import tkinter as tk
from tkinter import messagebox
import json
import random


class SeriousGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Serious Game - Gestion de Patrimoine")
        self.geometry("800x600")

        # État du jeu
        self.gauges = {"budget": 50, "loisirs": 50, "epargne": 50}
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

        # Création d'un conteneur pour les frames
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        # Dictionnaire pour stocker les frames (Game et Quiz)
        self.frames = {}
        for F in (GameFrame, QuizFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # On démarre sur le GameFrame
        self.show_frame("GameFrame")
        self.load_next_card()

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()

    def update_gauges_display(self):
        self.frames["GameFrame"].update_gauges_label(
            f"Budget: {self.gauges['budget']} | Loisirs: {self.gauges['loisirs']} | Épargne: {self.gauges['epargne']}"
        )

    def load_next_card(self):
        # Sauvegarde du point de reprise (checkpoint) avant de jouer une nouvelle carte
        self.checkpoint_state = (self.gauges["budget"], self.gauges["loisirs"], self.gauges["epargne"])
        self.checkpoint_log_index = len(self.game_log)
        self.current_card = random.choice(self.cards)
        self.frames["GameFrame"].set_card(self.current_card)
        self.update_gauges_display()

    def apply_choice(self, choice):
        # Appliquer les effets selon le choix (A ou B)
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

        # Mise à jour des jauges
        self.gauges["budget"] += effects.get("budget", 0)
        self.gauges["loisirs"] += effects.get("loisirs", 0)
        self.gauges["epargne"] += effects.get("epargne", 0)

        # Enregistrement de la décision
        self.game_log.append({
            "situation": self.current_card["question"],
            "choix": choix_text,
            "explication": explanation
        })

        # Affichage de l'explication dans la GameFrame
        self.frames["GameFrame"].show_explanation(explanation)
        self.update_gauges_display()

        # Vérification de la condition de défaite (si une jauge est ≤ 0)
        if self.gauges["budget"] <= 0 or self.gauges["loisirs"] <= 0 or self.gauges["epargne"] <= 0:
            messagebox.showinfo("Défaite", "Oh non ! Une de vos jauges est tombée à 0.")
            self.show_game_log()
            self.start_quiz()
        else:
            # Autoriser le passage à la carte suivante
            self.frames["GameFrame"].enable_next_button()

    def show_game_log(self):
        # Affichage de l'historique des décisions
        log_text = "Récapitulatif de vos décisions :\n"
        for entry in self.game_log:
            log_text += f"- {entry['situation']}\n   Choix: {entry['choix']}\n   Explication: {entry['explication']}\n"
        messagebox.showinfo("Historique", log_text)

    def start_quiz(self):
        # Initialisation des variables du quiz et passage au QuizFrame
        self.current_quiz_index = 0
        self.quiz_answers = []  # stockera les réponses de l'utilisateur
        self.frames["QuizFrame"].load_question(self.quiz_questions[self.current_quiz_index])
        self.show_frame("QuizFrame")

    def process_quiz_answer(self, answer):
        # Enregistrer la réponse de l'utilisateur pour la question en cours
        self.quiz_answers.append(answer)
        self.current_quiz_index += 1
        if self.current_quiz_index < len(self.quiz_questions):
            self.frames["QuizFrame"].load_question(self.quiz_questions[self.current_quiz_index])
        else:
            # Fin du quiz, évaluation des réponses
            correct = True
            for idx, q in enumerate(self.quiz_questions):
                if self.quiz_answers[idx] != q["answer"]:
                    correct = False
                    break
            if correct:
                messagebox.showinfo("Quiz", "Bravo, toutes les réponses sont correctes ! Vous reprenez la partie.")
                # Restauration du point de reprise
                self.gauges["budget"], self.gauges["loisirs"], self.gauges["epargne"] = self.checkpoint_state
                self.game_log = self.game_log[:self.checkpoint_log_index]
                self.load_next_card()
                self.show_frame("GameFrame")
            else:
                messagebox.showinfo("Quiz", "Certaines réponses étaient incorrectes. Fin de la partie.")
                self.destroy()


class GameFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Label pour afficher l'état des jauges
        self.gauges_label = tk.Label(self, text="", font=("Helvetica", 14))
        self.gauges_label.pack(pady=10)

        # Label pour afficher la question/situation
        self.question_label = tk.Label(self, text="", wraplength=700, font=("Helvetica", 16))
        self.question_label.pack(pady=20)

        # Label pour afficher l'explication après un choix
        self.explanation_label = tk.Label(self, text="", wraplength=700, font=("Helvetica", 12), fg="blue")
        self.explanation_label.pack(pady=10)

        # Cadre pour les boutons des options
        self.buttons_frame = tk.Frame(self)
        self.buttons_frame.pack(pady=20)

        self.optionA_button = tk.Button(self.buttons_frame, text="Option A", width=20,
                                        command=lambda: self.choice("A"))
        self.optionA_button.grid(row=0, column=0, padx=10)
        self.optionB_button = tk.Button(self.buttons_frame, text="Option B", width=20,
                                        command=lambda: self.choice("B"))
        self.optionB_button.grid(row=0, column=1, padx=10)

        # Bouton pour obtenir un indice
        self.indice_button = tk.Button(self, text="Indice", command=self.show_indice)
        self.indice_button.pack(pady=10)

        # Bouton pour passer à la carte suivante (désactivé tant qu'aucun choix n'est validé)
        self.next_button = tk.Button(self, text="Suivant", command=self.next_card, state="disabled")
        self.next_button.pack(pady=10)

        # Bouton pour quitter
        self.quit_button = tk.Button(self, text="Quitter", command=self.controller.destroy)
        self.quit_button.pack(pady=10)

    def update_gauges_label(self, text):
        self.gauges_label.config(text=text)

    def set_card(self, card):
        self.current_card = card
        self.question_label.config(text=card["question"])
        self.explanation_label.config(text="")
        self.next_button.config(state="disabled")
        self.optionA_button.config(state="normal")
        self.optionB_button.config(state="normal")

    def show_indice(self):
        if hasattr(self, "current_card"):
            indice = self.current_card.get("hint", "Pas d'indice disponible.")
            messagebox.showinfo("Indice du conseiller financier", indice)

    def choice(self, option):
        # Désactiver les boutons des options après un choix
        self.optionA_button.config(state="disabled")
        self.optionB_button.config(state="disabled")
        self.controller.apply_choice(option)

    def show_explanation(self, explanation):
        self.explanation_label.config(text=explanation)

    def enable_next_button(self):
        self.next_button.config(state="normal")

    def next_card(self):
        self.controller.load_next_card()


class QuizFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_question = None
        self.var_answer = tk.StringVar()

        self.question_label = tk.Label(self, text="", wraplength=700, font=("Helvetica", 16))
        self.question_label.pack(pady=20)

        self.options_frame = tk.Frame(self)
        self.options_frame.pack(pady=10)

        self.radio_buttons = {}
        for option in ["A", "B", "C", "D"]:
            rb = tk.Radiobutton(self.options_frame, text="", variable=self.var_answer, value=option,
                                font=("Helvetica", 14))
            rb.pack(anchor="w")
            self.radio_buttons[option] = rb

        self.submit_button = tk.Button(self, text="Valider", command=self.submit_answer)
        self.submit_button.pack(pady=20)

    def load_question(self, question):
        self.current_question = question
        self.question_label.config(text=question["question"])
        self.var_answer.set(None)
        options = question["options"]
        for option in ["A", "B", "C", "D"]:
            text = options.get(option, "")
            self.radio_buttons[option].config(text=f"{option}: {text}")

    def submit_answer(self):
        answer = self.var_answer.get()
        if not answer:
            messagebox.showwarning("Attention", "Veuillez sélectionner une réponse.")
            return
        self.controller.process_quiz_answer(answer)


if __name__ == "__main__":
    app = SeriousGame()
    app.mainloop()
