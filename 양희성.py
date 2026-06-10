import tkinter as tk
from tkinter import ttk
from 김효석 import LeChatelierEngine
from 천우진 import LeChatelierQuizManager

class LeChatelierSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("화학 평형 이동 시뮬레이터 (르샤틀리에의 원리)")
        self.root.geometry("1020x750")
        self.root.configure(bg="#f5f6fa")

        self.engine = LeChatelierEngine()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        tab_sim  = tk.Frame(self.notebook, bg="#f5f6fa")
        tab_quiz = tk.Frame(self.notebook, bg="white")

        self.notebook.add(tab_sim,  text="  🔬  시뮬레이터  ")
        self.notebook.add(tab_quiz, text="  📝  퀴즈 모드   ")

        self.setup_ui(tab_sim)
        
        self.quiz_manager = LeChatelierQuizManager(tab_quiz)
        
        self.load_default_reaction()

    def setup_ui(self, parent):
        input_frame = tk.LabelFrame(parent, text=" 1. 반응식 및 엔탈피(ΔH) 조건 설정 ",
                                    bg="#f5f6fa", font=("맑은 고딕", 11, "bold"))
        input_frame.pack(fill="x", padx=15, pady=(15, 5))

        tk.Label(input_frame, text="입력 예시: N2 + 3H2 <=> 2NH3  (우측에서 열역학 엔탈피 부호를 직접 선택하세요)",
                 bg="#f5f6fa", fg="#7f8c8d", font=("맑은 고딕", 9)).grid(row=0, column=0, columnspan=5, sticky="w", padx=10, pady=2)

        tk.Label(input_frame, text="반응식:", bg="#f5f6fa", font=("맑은 고딕", 10)).grid(row=1, column=0, padx=(10, 2), pady=5)

        self.entry_reaction = tk.Entry(input_frame, width=35, font=("맑은 고딕", 10))
        self.entry_reaction.grid(row=1, column=1, padx=5, pady=5)

        self.var_deltah = tk.StringVar(value="exothermic") 
        dh_frame = tk.Frame(input_frame, bg="#f5f6fa")
        dh_frame.grid(row=1, column=2, padx=10, pady=5)
        
        rb_exo = tk.Radiobutton(dh_frame, text="ΔH < 0 (발열)", variable=self.var_deltah, 
                                value="exothermic", bg="#f5f6fa", font=("맑은 고딕", 9, "bold"), fg="#e74c3c",
                                command=self.trigger_simulation)
        rb_endo = tk.Radiobutton(dh_frame, text="ΔH > 0 (흡열)", variable=self.var_deltah, 
                                 value="endothermic", bg="#f5f6fa", font=("맑은 고딕", 9, "bold"), fg="#2980b9",
                                 command=self.trigger_simulation)
        rb_exo.pack(side="left", padx=5)
        rb_endo.pack(side="left", padx=5)

        tk.Button(input_frame, text="반응식 적용", command=self.parse_reaction,
                  bg="#3498db", fg="white", font=("맑은 고딕", 9, "bold")).grid(row=1, column=3, padx=5, pady=5)

        self.con_input_frame = tk.Frame(input_frame, bg="#f5f6fa")
        self.con_input_frame.grid(row=2, column=0, columnspan=5, sticky="w", padx=10, pady=5)

        control_frame = tk.LabelFrame(parent, text=" 2. 외부 조건 변화 조절 (르샤틀리에 조작) ",
                                      bg="#f5f6fa", font=("맑은 고딕", 11, "bold"))
        control_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(control_frame, text="온도 조절:", bg="#f5f6fa", font=("맑은 고딕", 10)).grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.scale_temp = ttk.Scale(control_frame, from_=-5, to=5, orient="horizontal", length=300, command=self.trigger_simulation)
        self.scale_temp.grid(row=0, column=1, padx=5, pady=5)
        self.lbl_temp = tk.Label(control_frame, text="기본 상태 (25.00 ℃)", bg="#f5f6fa", fg="#2c3e50", font=("맑은 고딕", 9, "bold"), width=25, anchor="w")
        self.lbl_temp.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        tk.Label(control_frame, text="용기 부피 압축(압력):", bg="#f5f6fa", font=("맑은 고딕", 10)).grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.scale_pres = ttk.Scale(control_frame, from_=-5, to=5, orient="horizontal", length=300, command=self.trigger_simulation)
        self.scale_pres.grid(row=1, column=1, padx=5, pady=5)
        self.lbl_pres = tk.Label(control_frame, text="기본 상태 (1.00 atm)", bg="#f5f6fa", fg="#2c3e50", font=("맑은 고딕", 9, "bold"), width=25, anchor="w")
        self.lbl_pres.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        tk.Label(control_frame, text="특정 물질 가변 조작:", bg="#f5f6fa", font=("맑은 고딕", 10)).grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.combo_chemical = ttk.Combobox(control_frame, state="readonly", width=10)
        self.combo_chemical.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.combo_chemical.bind("<<ComboboxSelected>>", lambda e: self.trigger_simulation())

        self.scale_chem = ttk.Scale(control_frame, from_=-2, to=2, orient="horizontal", length=180, command=self.trigger_simulation)
        self.scale_chem.grid(row=2, column=1, sticky="e", padx=(120, 5), pady=5)

        self.lbl_chem = tk.Label(control_frame, text="변화 없음 (0.00 M)", bg="#f5f6fa", fg="#2c3e50", font=("맑은 고딕", 9, "bold"), width=25, anchor="w")
        self.lbl_chem.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        tk.Button(control_frame, text="조건 초기화", command=self.reset_sliders,
                  bg="#95a5a6", fg="white", font=("맑은 고딕", 9, "bold")).grid(row=0, column=3, rowspan=3, padx=20, pady=5, ipady=10)

        display_frame = tk.Frame(parent, bg="#f5f6fa")
        display_frame.pack(fill="both", expand=True, padx=15, pady=5)

        vessel_box = tk.LabelFrame(display_frame, text=" 3. 실제 반응 용기 내부 (농도 시각화) ", bg="white", font=("맑은 고딕", 11, "bold"))
        vessel_box.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)

        self.canvas = tk.Canvas(vessel_box, bg="#1e272e", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        report_box = tk.LabelFrame(display_frame, text=" 4. 평형 이동 분석 결과 ", bg="white", font=("맑은 고딕", 11, "bold"), width=280)
        report_box.pack(side="right", fill="both", padx=(5, 0), pady=5)

        self.lbl_status = tk.Label(report_box, text="평형 상태 확인 중...", bg="white", fg="#2980b9", font=("맑은 고딕", 12, "bold"), justify="center")
        self.lbl_status.pack(fill="x", padx=10, pady=15)

        self.txt_report = tk.Text(report_box, bg="#f8f9fa", bd=0, font=("맑은 고딕", 10), spacing1=3)
        self.txt_report.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def load_default_reaction(self):
        self.entry_reaction.insert(0, "N2 + 3H2 <=> 2NH3")
        self.parse_reaction()

    def parse_reaction(self):
        self.engine.parse_reaction_logic(self.entry_reaction.get(), self.combo_chemical, self.con_input_frame)
        self.reset_sliders()

    def reset_sliders(self):
        self.engine.is_updating = True 
        self.scale_temp.set(0)
        self.scale_pres.set(0)
        self.scale_chem.set(0)
        self.engine.is_updating = False 
        self.trigger_simulation()

    def trigger_simulation(self, *args):
        self.engine.calculate_equilibrium_shift(
            self.scale_temp.get(), self.scale_pres.get(), self.scale_chem.get(),
            self.combo_chemical.get(), self.var_deltah.get(),
            self.lbl_temp, self.lbl_pres, self.lbl_chem, self.lbl_status, self.txt_report, self.canvas
        )

if __name__ == "__main__":
    root = tk.Tk()
    app  = LeChatelierSimulator(root)
    root.update()
    app.trigger_simulation()
    root.mainloop()