# quiz_module.py
import tkinter as tk          # GUI 창, 버튼, 라벨, 입력창 등 위젯을 만드는 라이브러리
from tkinter import ttk       # 진행 바(Progressbar) 같은 위젯을 사용하기 위한 모듈
import random                 # 문제 순서를 무작위로 섞기 위한 모듈

# ════════════════════════════════════════════════════════════════
# 퀴즈 데이터 및 채점 로직 모듈
# ════════════════════════════════════════════════════════════════

# 방향 예측 문제 6개를 딕셔너리 리스트로 저장
# 각 딕셔너리의 키: type(유형), q(문제), c(선택지 리스트), a(정답 인덱스), exp(해설)
QUIZ_QUESTIONS = [
    {"type":"Q vs Kc",                                                         # 문제 유형
     "q":"N₂+3H₂⇌2NH₃\n\nQ=0.02   Kc=0.05\n\n평형 이동 방향은?",              # 문제 텍스트
     "c":["▶ 정반응","◀ 역반응","● 변화없음"],                                    # 선택지 3개
     "a":0,                                                                    # 정답 인덱스 (0=정반응)
     "exp":"Q(0.02) < Kc(0.05) → 생성물 부족 → 정반응"},                        # 해설

    {"type":"Q vs Kc",
     "q":"어떤 반응에서\n\nQ=8.3   Kc=2.1\n\n평형 이동 방향은?",
     "c":["▶ 정반응","◀ 역반응","● 변화없음"],
     "a":1,                                                                    # 정답 인덱스 (1=역반응)
     "exp":"Q(8.3) > Kc(2.1) → 생성물 과잉 → 역반응"},

    {"type":"온도 변화",
     "q":"N₂+3H₂⇌2NH₃  ΔH=-92kJ (발열)\n\n온도를 높이면?",
     "c":["▶ 정반응 (NH₃↑)","◀ 역반응 (NH₃↓)","● 변화없음"],
     "a":1,
     "exp":"발열 반응 + 온도↑ → 열 흡수 방향(역반응)으로 이동"},

    {"type":"온도 변화",
     "q":"N₂+O₂⇌2NO  ΔH=+181kJ (흡열)\n\n온도를 높이면?",
     "c":["▶ 정반응 (NO↑)","◀ 역반응 (NO↓)","● 변화없음"],
     "a":0,
     "exp":"흡열 반응 + 온도↑ → 열 흡수 방향(정반응)으로 이동"},

    {"type":"압력 변화",
     "q":"N₂+3H₂⇌2NH₃\n반응물 계수합: 4  생성물 계수합: 2\n\n압력을 높이면?",
     "c":["▶ 정반응 (NH₃↑)","◀ 역반응 (N₂·H₂↑)","● 변화없음"],
     "a":0,
     "exp":"압력↑ → 분자 수 감소 방향 / 계수합 4>2 → 정반응"},

    {"type":"농도 변화",
     "q":"N₂+3H₂⇌2NH₃\n\n평형 상태에서 N₂를 추가하면?",
     "c":["▶ 정반응 (NH₃↑)","◀ 역반응 (NH₃↓)","● 변화없음"],
     "a":0,
     "exp":"반응물(N₂) 추가 → N₂ 소모 방향(정반응)으로 이동"},
]

# Kc 계산 문제의 원본 데이터
# 정답은 코드에서 calculate_kc()가 직접 계산하여 생성
KC_PROBLEMS = [
    {"rxn":"N₂+3H₂⇌2NH₃",                                  # 반응식 문자열 (화면 표시용)
     "r":[("N2",1),("H2",3)],                               # 반응물 리스트: (물질명, 계수)
     "p":[("NH3",2)],                                       # 생성물 리스트: (물질명, 계수)
     "c":{"N2":0.5,"H2":1.5,"NH3":0.8},                    # 평형 농도 딕셔너리 (단위: M)
     "formula":"Kc = [NH₃]² / ([N₂]×[H₂]³)"},             # 화면에 보여줄 공식 문자열

    {"rxn":"H₂+I₂⇌2HI",
     "r":[("H2",1),("I2",1)],
     "p":[("HI",2)],
     "c":{"H2":0.5,"I2":0.5,"HI":2.0},
     "formula":"Kc = [HI]² / ([H₂]×[I₂])"},
]


class LeChatelierQuizManager:

    """
    르샤틀리에 퀴즈 탭을 관리하는 클래스

    클래스를 사용한 이유:
    1. 점수(score), 문제 번호(idx), 위젯(btns 등) 같은 변수를
       show_question, check_answer, _show_final 등 여러 함수가
       self를 통해 공유해야 하기 때문이다.
    2. 퀴즈 관련 함수 13개를 하나의 단위로 묶어 관리하기 위해서이다.
    3. 팀원 A의 main_ui.py에서 LeChatelierQuizManager(tab_quiz)
       한 줄로 퀴즈 탭 전체를 호출할 수 있도록 하기 위해서이다.
    """

    def __init__(self, parent_frame):
        self.parent   = parent_frame   # 퀴즈 탭 프레임을 인스턴스 변수로 저장
        self.score    = 0              # 맞힌 문제 수 (초기값 0)
        self.total    = 0              # 지금까지 푼 문제 수 (초기값 0)
        self.idx      = 0              # 현재 문제 번호 (0번부터 시작)
        self.answered = False          # 현재 문제에 이미 답했는지 여부 (중복 클릭 방지)

        kc = self.build_kc_questions()                              # Kc 계산 문제 2개 자동 생성
        self.questions = random.sample(                             # 전체 문제를 무작위 순서로 섞어서 저장
            QUIZ_QUESTIONS + kc,                                    # 방향 예측(6개) + Kc 계산(2개) 합치기
            len(QUIZ_QUESTIONS) + len(kc)                           # 전체 문제 수만큼 샘플링 = 전체 섞기
        )

        self._build_ui()       # UI 위젯 생성
        self.show_question()   # 첫 번째 문제 화면에 표시


    # ── Kc 계산 핵심 함수 ────────────────────────────────────

    def calculate_kc(self, reactants, products, conc):
        """Kc 계산 공식: [생성물]^계수의 곱 / [반응물]^계수의 곱"""
        numerator = 1.0                              # 분자 초기값
        for name, coeff in products:                 # 생성물 리스트를 하나씩 순회
            numerator *= conc[name] ** coeff         # 해당 물질 농도를 계수만큼 거듭제곱하여 분자에 곱함

        denominator = 1.0                            # 분모 초기값
        for name, coeff in reactants:                # 반응물 리스트를 하나씩 순회
            denominator *= conc[name] ** coeff       # 해당 물질 농도를 계수만큼 거듭제곱하여 분모에 곱함

        return round(numerator / denominator, 4)     # Kc = 분자/분모, 소수점 4자리로 반올림 후 반환

    def build_kc_questions(self):
        """KC_PROBLEMS 데이터로 Kc 계산 문제를 자동 생성하는 함수"""
        result = []                                              # 생성된 문제를 담을 빈 리스트
        for prob in KC_PROBLEMS:                                 # 문제 원본 데이터를 하나씩 처리
            kc = self.calculate_kc(prob["r"], prob["p"], prob["c"])  # 공식을 적용해 정답 Kc 계산
            conc_str = "  ".join(                                # 농도 표시 문자열 생성
                f"[{k}]={v}M" for k, v in prob["c"].items()     # 예: "[N2]=0.5M  [H2]=1.5M  [NH3]=0.8M"
            )
            result.append({                                      # 완성된 문제 딕셔너리를 리스트에 추가
                "type": "Kc 계산",                               # 문제 유형
                "q":    f"{prob['rxn']}\n평형 농도: {conc_str}\n{prob['formula']}\n\nKc 값을 직접 입력하세요.",
                "c":    [],      # 선택지 없음 (직접 입력 방식)
                "a":    None,    # 정답 인덱스 없음 (수치 비교 방식)
                "kc":   kc,      # calculate_kc()로 계산한 정답 Kc 값
                "exp":  f"{prob['formula']}\n= {kc}",            # 해설: 공식 + 계산된 정답
            })
        return result            # 생성된 Kc 문제 리스트 반환


    # ── UI 구성 ──────────────────────────────────────────────

    def _build_ui(self):
        """퀴즈 탭에 필요한 모든 위젯을 생성하는 함수"""
        F = ("맑은 고딕", 10)    # 자주 쓰는 폰트를 변수로 저장

        # ── 상단: 점수 라벨 + 문제 번호 라벨 ─────────────────
        top = tk.Frame(self.parent, bg="white")          # 점수와 번호를 담을 가로 프레임
        top.pack(fill="x", padx=12, pady=8)              # 화면 상단에 가로로 채워 배치
        self.lbl_score = tk.Label(top,                   # 점수를 표시하는 라벨
            text="점수: 0 / 0", bg="white", fg="#8e44ad",
            font=("맑은 고딕",11,"bold"))
        self.lbl_score.pack(side="left")                 # 왼쪽에 배치
        self.lbl_prog = tk.Label(top,                    # 현재 문제 번호를 표시하는 라벨
            text=f"1 / {len(self.questions)}", bg="white", fg="gray", font=F)
        self.lbl_prog.pack(side="right")                 # 오른쪽에 배치

        # ── 진행 바 ───────────────────────────────────────────
        self.prog_var = tk.DoubleVar()                   # 진행 바와 연결할 숫자 변수
        ttk.Progressbar(self.parent,                     # 진행 바 위젯 생성
            variable=self.prog_var,                      # 위에서 만든 변수와 연결
            maximum=len(self.questions),                 # 최대값 = 전체 문제 수
            length=460).pack(pady=4)                     # 가로 460px, 위아래 여백 4px

        # ── 문제 유형 배지 + 문제 텍스트 ─────────────────────
        self.lbl_type = tk.Label(self.parent,            # 문제 유형을 색깔 배지로 표시하는 라벨
            text="", bg="#8e44ad", fg="white",
            font=("맑은 고딕",9,"bold"), padx=10, pady=3)
        self.lbl_type.pack()                             # 화면에 배치 (문제마다 색이 바뀜)
        self.lbl_q = tk.Label(self.parent,               # 문제 내용을 표시하는 라벨
            text="", bg="#f4f6f8", fg="#2c3e50",
            font=("맑은 고딕",12), justify="center",     # 텍스트 가운데 정렬
            wraplength=500,                              # 500px 넘으면 자동 줄바꿈
            padx=20, pady=16)
        self.lbl_q.pack(fill="x", padx=20, pady=8)      # 좌우 20px 여백으로 배치

        # ── 선택지 버튼 3개 (방향 예측 문제용) ───────────────
        self.btn_frame = tk.Frame(self.parent, bg="white")   # 버튼 3개를 담을 프레임
        self.btn_frame.pack(pady=6)
        self.btns = []                                   # 버튼 객체를 저장할 빈 리스트
        for i, col in enumerate(["#27ae60","#e74c3c","#7f8c8d"]):  # 초록/빨강/회색 순으로 반복
            b = tk.Button(self.btn_frame,                # 선택지 버튼 생성
                text="", bg=col, fg="white",
                font=("맑은 고딕",10,"bold"),
                width=14, pady=6, relief="flat",
                command=lambda x=i: self.check_answer(x))  # 클릭 시 check_answer(i) 호출
            b.grid(row=0, column=i, padx=8)             # 가로로 나란히 배치
            self.btns.append(b)                          # 리스트에 추가 (나중에 색 변경할 때 사용)
        self.btn_colors = ["#27ae60","#e74c3c","#7f8c8d"]   # 버튼 원래 색 저장 (초기화용)

        # ── 직접 입력 영역 (Kc 계산 문제용) ──────────────────
        self.inp_frame = tk.Frame(self.parent, bg="white")  # 입력창을 담을 프레임 (처음엔 숨김)
        tk.Label(self.inp_frame,                         # "Kc =" 라벨
            text="Kc =", bg="white", fg="#d35400",
            font=("맑은 고딕",12,"bold")).pack(side="left")
        self.entry = tk.Entry(self.inp_frame,            # 사용자가 Kc 값을 직접 입력하는 창
            width=12, font=("맑은 고딕",12), justify="center")
        self.entry.pack(side="left", padx=6)             # 라벨 오른쪽에 배치
        self.entry.bind("<Return>",                      # Enter 키를 누르면
            lambda e: self.submit_kc())                  # submit_kc() 함수 호출
        self.btn_submit = tk.Button(self.inp_frame,      # "제출" 버튼 생성
            text="제출", bg="#d35400", fg="white",
            font=("맑은 고딕",10,"bold"),
            padx=14, pady=4, relief="flat",
            command=self.submit_kc)                      # 클릭 시 submit_kc() 호출
        self.btn_submit.pack(side="left")                # 입력창 오른쪽에 배치

        # ── 결과·해설 라벨 (정답 제출 후에만 표시) ───────────
        self.lbl_result = tk.Label(self.parent,          # "✅ 정답" 또는 "❌ 오답" 표시 라벨
            text="", bg="#eafaf1", fg="#1e8449",
            font=("맑은 고딕",10,"bold"), padx=14, pady=6)
        self.lbl_explain = tk.Label(self.parent,         # 해설 텍스트 표시 라벨
            text="", bg="#eafaf1", fg="#2c3e50",
            font=("맑은 고딕",10), justify="left",
            wraplength=500, padx=14, pady=6)

        # ── 다음 문제·처음부터 버튼 ──────────────────────────
        self.btn_next = tk.Button(self.parent,           # "다음 문제 →" 버튼
            text="다음 문제 →", bg="#2980b9", fg="white",
            font=("맑은 고딕",10,"bold"),
            padx=16, pady=5, relief="flat",
            command=self.next_question)                  # 클릭 시 next_question() 호출
        self.btn_restart = tk.Button(self.parent,        # "↺ 처음부터" 버튼 (퀴즈 끝난 후 표시)
            text="↺ 처음부터", bg="#95a5a6", fg="white",
            font=("맑은 고딕",10,"bold"),
            padx=14, pady=5, relief="flat",
            command=self.restart)                        # 클릭 시 restart() 호출


    # ── 퀴즈 진행 로직 ───────────────────────────────────────

    def show_question(self):
        """현재 문제를 화면에 표시. 문제 유형에 따라 입력 방식을 전환한다."""
        if self.idx >= len(self.questions):  # 문제 번호가 전체 수 이상이면 (모든 문제 완료)
            self._show_final()               # 최종 결과 화면으로 이동
            return                           # 함수 종료

        q = self.questions[self.idx]         # 현재 문제 딕셔너리를 q에 저장

        # 문제 유형별 배지 색상 딕셔너리에서 색을 꺼내 배지에 적용
        self.lbl_type.config(
            text=f"  {q['type']}  ",
            bg={"Q vs Kc":"#8e44ad",         # Q vs Kc → 보라
                "온도 변화":"#c0392b",         # 온도 변화 → 빨강
                "압력 변화":"#2471a3",         # 압력 변화 → 파랑
                "농도 변화":"#1e8449",         # 농도 변화 → 초록
                "Kc 계산" :"#d35400"          # Kc 계산 → 주황
               }.get(q["type"],"#555"))       # 해당 없으면 회색

        self.lbl_q.config(text=q["q"])                   # 문제 내용 업데이트
        self.lbl_prog.config(text=f"{self.idx+1} / {len(self.questions)}")  # 진행 번호 업데이트
        self.prog_var.set(self.idx)                       # 진행 바를 현재 문제 번호만큼 채움

        for w in [self.lbl_result, self.lbl_explain,      # 결과 카드·다음 버튼·처음부터 버튼을
                  self.btn_next, self.btn_restart]:        # 모두 화면에서 숨김 (새 문제 시작)
            w.pack_forget()
        self.answered = False                             # 답변 상태를 "아직 안 풀었음"으로 초기화

        if q["type"] == "Kc 계산":            # Kc 계산 문제이면
            self.btn_frame.pack_forget()       # 선택지 버튼 영역 숨김
            self.inp_frame.pack(pady=8)        # 직접 입력 영역 표시
            self.entry.config(state="normal")  # 입력창 활성화
            self.entry.delete(0, tk.END)       # 이전 입력값 삭제
            self.btn_submit.config(state="normal")  # 제출 버튼 활성화
            self.entry.focus()                 # 커서를 입력창으로 이동
        else:                                  # 방향 예측 문제이면
            self.inp_frame.pack_forget()       # 직접 입력 영역 숨김
            self.btn_frame.pack(pady=6)        # 선택지 버튼 영역 표시
            for i, btn in enumerate(self.btns):             # 버튼 3개를 반복하며
                btn.config(text=q["c"][i],                  # 이번 문제의 선택지 텍스트 적용
                           bg=self.btn_colors[i],           # 원래 색으로 복원
                           state="normal")                  # 클릭 가능하게 활성화

    def check_answer(self, selected):
        """선택지 버튼 채점 — 방향 예측 문제에서 호출"""
        if self.answered: return             # 이미 답변했으면 중복 처리 방지 후 종료
        self.answered = True                 # 답변 완료 표시

        q     = self.questions[self.idx]     # 현재 문제 딕셔너리
        is_ok = (selected == q["a"])         # 선택한 인덱스와 정답 인덱스 비교

        self._update_score(is_ok)            # 점수 업데이트 함수 호출

        for i, btn in enumerate(self.btns):                         # 버튼 3개 반복
            btn.config(state="disabled")                            # 모든 버튼 비활성화
            if i == q["a"]:                                         # 정답 버튼이면
                btn.config(bg="#1a5276")                            # 진한 파랑으로 강조
            elif i == selected and not is_ok:                       # 내가 고른 오답 버튼이면
                btn.config(bg="#7b241c")                            # 진한 빨강으로 강조

        verdict = "✅ 정답!" if is_ok else f"❌ 오답  (정답: {q['c'][q['a']]})"  # 결과 메시지 생성
        self._show_result(is_ok, verdict, q["exp"])                 # 결과 카드 표시

    def submit_kc(self):
        """입력값 채점 — Kc 계산 문제에서 호출"""
        if self.answered: return             # 이미 답변했으면 중복 처리 방지

        try:
            user_val = float(self.entry.get())   # 입력창의 문자열을 실수(float)로 변환 시도
        except ValueError:                       # 변환 실패 시 (숫자가 아닌 값 입력)
            self.lbl_result.config(text="⚠ 숫자를 입력해주세요.", fg="#e74c3c", bg="white")
            self.lbl_result.pack(pady=4)         # 경고 메시지 표시
            return                               # 채점하지 않고 종료

        self.answered = True                     # 답변 완료 표시
        self.entry.config(state="disabled")      # 입력창 비활성화 (수정 불가)
        self.btn_submit.config(state="disabled") # 제출 버튼 비활성화

        q          = self.questions[self.idx]    # 현재 문제 딕셔너리
        correct_kc = q["kc"]                     # build_kc_questions()에서 계산된 정답 Kc
        tolerance  = max(correct_kc * 0.01, 0.001)           # 오차 허용 범위: 정답의 ±1% (최소 0.001)
        is_ok      = abs(user_val - correct_kc) <= tolerance  # 오차 범위 내이면 정답으로 처리

        self._update_score(is_ok)                # 점수 업데이트
        verdict = f"✅ 정답! (입력값: {user_val})" if is_ok else \
                  f"❌ 오답  (입력: {user_val} / 정답: {correct_kc})"  # 결과 메시지 생성
        self._show_result(is_ok, verdict, q["exp"])  # 결과 카드 표시

    def _update_score(self, is_ok):
        """점수 계산 및 점수 라벨 갱신 (공통 함수)"""
        self.total += 1                              # 푼 문제 수 1 증가
        if is_ok: self.score += 1                   # 정답이면 맞힌 수도 1 증가
        pct = int(self.score / self.total * 100)     # 정답률(%) 계산: 맞힌 수 / 푼 수 × 100
        self.lbl_score.config(                       # 점수 라벨 텍스트 갱신
            text=f"점수: {self.score} / {self.total}  ({pct}%)")

    def _show_result(self, is_ok, verdict, explanation):
        """결과·해설 라벨 표시 및 다음 문제 버튼 노출 (공통 함수)"""
        bg = "#eafaf1" if is_ok else "#fdedec"   # 정답이면 초록 배경, 오답이면 빨간 배경
        fg = "#1e8449" if is_ok else "#922b21"   # 정답이면 초록 글씨, 오답이면 빨간 글씨
        self.lbl_result.config(text=verdict, bg=bg, fg=fg)   # 결과 라벨 색·텍스트 적용
        self.lbl_explain.config(text=explanation, bg=bg)     # 해설 라벨 색·텍스트 적용
        self.lbl_result.pack(padx=20, pady=(8,0), fill="x")  # 결과 라벨을 화면에 표시
        self.lbl_explain.pack(padx=20, pady=(0,4), fill="x") # 해설 라벨을 화면에 표시
        next_txt = "결과 보기 →" if self.idx >= len(self.questions)-1 else "다음 문제 →"
        # 마지막 문제이면 "결과 보기", 아니면 "다음 문제"로 버튼 텍스트 설정
        self.btn_next.config(text=next_txt)
        self.btn_next.pack(pady=6)               # 다음 문제 버튼을 화면에 표시

    def next_question(self):
        """다음 문제로 이동"""
        self.idx += 1            # 문제 번호를 1 증가
        self.show_question()     # 다음 문제를 화면에 표시

    def restart(self):
        """퀴즈를 처음부터 다시 시작"""
        kc = self.build_kc_questions()           # Kc 계산 문제 다시 생성
        self.questions = random.sample(          # 전체 문제를 다시 무작위로 섞기
            QUIZ_QUESTIONS + kc,
            len(QUIZ_QUESTIONS) + len(kc))
        self.score = self.total = self.idx = 0   # 점수·푼 수·문제 번호 모두 0으로 초기화
        self.lbl_score.config(text="점수: 0 / 0") # 점수 라벨 초기화
        self.prog_var.set(0)                     # 진행 바를 처음으로 되돌림
        self.show_question()                     # 첫 번째 문제 표시

    def _show_final(self):
        """모든 문제를 다 풀었을 때 최종 결과를 표시하는 함수"""
        total = len(self.questions)                              # 전체 문제 수
        pct   = int(self.score / total * 100) if total else 0   # 최종 정답률(%) 계산

        if pct >= 80:                            # 80점 이상이면
            msg, col = "🏆 마스터!", "#1a5276"   # 트로피 메시지, 진한 파랑
        elif pct >= 60:                          # 60점 이상이면
            msg, col = "👍 좋아요!", "#1e8449"   # 엄지 메시지, 초록
        else:                                    # 60점 미만이면
            msg, col = "📚 복습 필요", "#922b21" # 책 메시지, 빨강

        self.btn_frame.pack_forget()             # 선택지 버튼 영역 숨김
        self.inp_frame.pack_forget()             # 입력 영역 숨김
        self.lbl_type.config(text="  퀴즈 완료!  ", bg=col)    # 배지를 "퀴즈 완료!"로 변경
        self.lbl_q.config(                       # 문제 카드에 최종 결과 표시
            text=f"{msg}\n\n최종 점수: {self.score} / {total}  ({pct}%)",
            fg=col)
        self.lbl_prog.config(text=f"완료 {total}/{total}")      # 진행 번호 업데이트
        self.prog_var.set(total)                 # 진행 바를 끝까지 채움
        for w in [self.lbl_result, self.lbl_explain, self.btn_next]:  # 결과·해설·다음 버튼
            w.pack_forget()                      # 화면에서 숨김
        self.btn_restart.pack(pady=12)           # "처음부터" 버튼을 화면에 표시