#시뮬레이션 엔진 구현(1302 김효석)
import tkinter as tk #GUI 창 만들기 위한 tkinter 라이브러리 임포트
from tkinter import messagebox #에러나 경고 팝업 띄우기 위한 모듈 임포트
import re #화학반응식 문자열에서 계수와 알파벳 분리하기 위한 re 모듈 임포트

#르샤틀리에 계산 엔진 클래스--------------------------------------------------------------------------------------------------------------------
class LeChatelierEngine: 
    #LeChatelierngine 클래스 초기화될 때 실행되는 생성자함수
    def __init__(self): 
        self.reactants = [] #(반응물 물질명, 계수) 튜플 형태로 저장할 리스트
        self.products  = [] #(생성물 물질명, 계수) 튜플 형태로 저장할 리스트
        self.concentrations = {} #평형 이동 후 각 물질의 농도 저장할 딕셔너리
        self.entry_molarities = {} #초기 농도 입력창 개체들을 물질별 저장할 딕셔너리
        self.is_updating = False #슬라이더 초기화 시 무한루프 방지 플래그 변수

    #입력받은 화학반응식에서 계수와 화학종 분리 추출하는 알고리즘----------------------------------------------------------------------------------
    def parse_reaction_logic(self, raw_text, combo_chemical, con_input_frame):
        raw_text = raw_text.replace(" ", "") #입력 문자열에서 공백 제거
        if "<=>" not in raw_text: #입력 문자열에서 가역반응 기호(<=>)없다면 에러 팝업창 움, 함수 종료
            messagebox.showerror("오류", "올바른 가역 반응식 기호 '<=>'를 포함해 주세요.")
            return False
        #예상치 못한 에러 대비 예외 처리--------------------------------------------------------------------------------------------------------
        try: 
            left_side, right_side = raw_text.split("<=>") #<=> 기준 왼쪽과 오른쪽 문자열 분리

            #'+'기호로 연결된 화학식 문자열 쪼개서 계수, 이름 추출
            def parse_chemicals(s):
                result = [] #분리 결과 담을 임시 리스트
                for p in s.split("+"): #각 항 '+' 기준 분리
                    if not p: continue #빈 문자열이면 무시하고 다음으로
                    m = re.match(r"(\d*)([A-Za-z0-9]+)", p) #re 모듈 통해 정규표현식으로 앞의 숫자(계수)와 뒤의 알파벳+숫자(물질명) 매칭
                    if m: #매칭 성공 시 실행
                        coeff = int(m.group(1)) if m.group(1) else 1 #앞에 숫자가 있으면 정수로, 없으면 1(계수) 저장
                        result.append((m.group(2), coeff)) #(물질명, 계수) 형태로 리스트에 추가
                return result #분석 완료 화학종 리스트 반환

            self.reactants = parse_chemicals(left_side) #왼쪽 문자열을 해석하여 반응물 리스트에 저장
            self.products  = parse_chemicals(right_side) #오른쪽 문자열을 해석하여 반응물 리스트에 저장
            all_chems      = [n for n, _ in self.reactants + self.products] #반응물, 생성물 물질명만 모아서 리스트 생성

            combo_chemical['values'] = all_chems #메인 파일의 농도 조작용 콤보박스 목록에 추출한 물질 이름 주입
            if all_chems: combo_chemical.current(0) #목록에 물질이 존재하면 첫 번째 물질을 기본 선택 상태로 지정

            for w in con_input_frame.winfo_children(): w.destroy() #새로운 반응식이 들어왔으므로 기존에 생성되어 있던 농도 입력창 UI 삭제


            self.entry_molarities = {} #입력창 객체 새로 매핑하기 위해 딕셔너리 초기화
            tk.Label(con_input_frame, text="초기 평형 농도(M) →", bg="#f5f6fa", font=("맑은 고딕", 9, "bold")).pack(side="left")

            default_mols = {"N2": 1.0, "H2": 3.0, "NH3": 0.5} #초기 세팅값(NH3 합성 반응) 시 미리 초기 몰농도 지정
            #분석된 화학 물질 돌면서 화면에 입력창 생성------------------------------------------------------------------------------------------
            for name in all_chems:
                tk.Label(con_input_frame, text=f"{name}:", bg="#f5f6fa").pack(side="left", padx=(5, 2)) #물질 이름 라벨
                ent = tk.Entry(con_input_frame, width=5) #입력창
                ent.insert(0, str(default_mols.get(name, 1.0))) #사전 입력값(N2, H2, NH3) 입력 시 그 값 출력, 이외의 물질은 1.0
                ent.pack(side="left", padx=2) #입력창 가로 방향
                self.entry_molarities[name] = ent #메인 파일에서 결과값 가져갈 수 있게 딕셔너리에 입력창 객체 등록

            return True
        except Exception as e:
            messagebox.showerror("파싱 오류", f"반응식을 해석할 수 없습니다.\n({e})") #에러 팝업
            return False

    #사용자가 입력한 슬라이더 수치 받아서 르샤틀리에 법칙 따른 농도 변동량 계산--------------------------------------------------------------------
    def calculate_equilibrium_shift(self, t_val, p_val, c_val, target, dh_state, lbl_temp, lbl_pres, lbl_chem, lbl_status, txt_report, canvas):
        #입력 값 추출-------------------------------------------------------------------------------------------------------------------------
        if self.is_updating or not self.reactants: return #입력 없을 시 건너뛰기
        try:
            base_concen = {n: float(e.get()) for n, e in self.entry_molarities.items()} #초기 농도 문자열 float으로 변환해 딕셔너리 저장
        except ValueError:  #숫자 이외 값 입력 시 에러 방지하기 위해 계산 과정 강제 종료
            return

        #발열/흡열
        is_exo = (dh_state == "exothermic") #발열 반응 선택 시 True, 흡열 반응 선택시 False 저장

        #온도
        temp_calc = t_val * 20.0  #온도 슬라이더 수치 기존 +-5의 값을 +-100℃로 변환
        if abs(t_val) > 0.1: #슬라이더 수치 고온 시 빨간색 텍스트, 저온 시 파란색 텍스트
            lbl_temp.config(text=f"고온 (+{temp_calc:.2f} ℃)" if t_val > 0 else f"저온 ({temp_calc:.2f} ℃)", fg="#e74c3c" if t_val > 0 else "#2980b9")
        else: #슬라이더 수치 거의 0이면 기본 상온 텍스트
            lbl_temp.config(text="기본 상태 (25.00 ℃)", fg="#2c3e50")

        #압력
        pres_calc = 1.0 + (p_val * 0.4) #압력 슬라이더 수치 실제 기압으로 환산
        if abs(p_val) > 0.1: #슬라이더 수치 고압 시 초록색 텍스트, 저압 시 주황색 텍스트
            lbl_pres.config(text=f"부피 압축 ({pres_calc:.2f} atm)" if p_val > 0 else f"부피 확장 ({pres_calc:.2f} atm)", fg="#27ae60" if p_val > 0 else "#d35400")
        else: #슬라이더 수치 거의 0이면 기본 상압 텍스트
            lbl_pres.config(text="기본 상태 (1.00 atm)", fg="#2c3e50")

        #농도 변화
        if abs(c_val) > 0.1 and target: #농도 변화 물질 선택, 슬라이더 조작 시 보라색
            lbl_chem.config(text=f"{target} 투입 (+{c_val:.2f} M)" if c_val > 0 else f"{target} 제거 ({c_val:.2f} M)", fg="#8e44ad")
        else: #아니면 변화 없음 상태
            lbl_chem.config(text="변화 없음 (0.00 M)", fg="#2c3e50")

        #르샤틀리에 원리 적용------------------------------------------------------------------------------------------------------------------
        dx = 0.0 #최종 반응 징해도 변수(dx>0 시 정반응 우세, dx<0 시 역반응 우세)
        report_text = "" #최종 출력 메세지

        #온도 변화에 따른 르사틀리에 원리 적용
        if abs(t_val) > 0.1: #온도 변했다면
            direction = -1 if is_exo else 1 #발열 반응이면 온도 높였을 때 역반응, 흡열 반응이면 온도 높였을 때 정반응
            dx += t_val * 0.15 * direction #최종 계수에 0.15만큼 반영
            #평형 이동 원리 설명 텍스트
            report_text += (
                f"• [온도 변화 ({temp_calc:+.1f}℃)]:\n  [ΔH {'<' if is_exo else '>'} 0]인 상태에서 계의 온도를 {'높이면' if t_val > 0 else '낮추면'}, "
                f"외력을 상쇄하는 열역학적 평형 이동 방향인 "
                f"{'역' if direction * t_val < 0 else '정'}반응 우세 방향으로 반응이 진행됩니다.\n\n"
            )

        #압력 변화에 따른 르샤틀리에 원리 적용
        if abs(p_val) > 0.1: #압력 변했다면
            r_sum = sum(c for _, c in self.reactants) #반응물 계수 총합
            p_sum = sum(c for _, c in self.products) #생성물 계수 총합
            dx   += p_val * 0.12 * (r_sum - p_sum) #최종 계수에 반응물, 생성물 계수 차이, 압력 변화 고려해서 반영
            #평형 이동 원리 설명 텍스트
            report_text += (
                f"• [압력 변화 ({pres_calc:.2f} atm)]:\n  반응물 계수합({r_sum}) vs 생성물 계수합({p_sum})\n"
                f"  압력이 {'증가함에 따라 기체 분자 수가 감소하는' if p_val > 0 else '감소함에 따라 기체 분자 수가 증가하는'} 방향인 "
                f"{'정반응' if (r_sum > p_sum and p_val > 0) or (r_sum < p_sum and p_val < 0) else '역반응'} 우세 방향으로 평형 이동.\n\n"
            )

        #농도 변화에 따른 르샤틀리에 원리 적용
        if abs(c_val) > 0.1 and target: #농도 변했다면
            is_reactant = any(n == target for n, _ in self.reactants) #조작 물질 생성물인지 반응물인지 판단
            direction   = 1 if is_reactant else -1 #반응물이면 1, 생성물이면 -1
            dx += c_val * 0.25 * direction #최종 계수에 반영
            #평형 이동 원리 설명 텍스트
            report_text += (
                f"• [농도 변화]: {target} 물질을 {f'{c_val:+.2f}M 만큼 변동'}\n"
                f"  → 외부 변화를 방해하기 위해 {target}를 {'소모' if c_val > 0 else '생성'}하는 방향으로 계가 유도됩니다.\n\n"
            )

        #최종 평형 이동 계산-------------------------------------------------------------------------------------------------------------------
        self.concentrations = base_concen.copy() #초기 평형 농도 복사
        if abs(c_val) > 0.1 and target: #임의로 물질 주입하거나 뺀 외력을 그래프 데이터에 먼저 반영
            self.concentrations[target] = max(0.01, self.concentrations[target] + c_val * 0.6) #하한선 0.01M로 제한
        for name, coeff in self.reactants:
            self.concentrations[name] = max(0.02, self.concentrations[name] - coeff * dx) #반응물 최종 농도 계산(기존 농도-반응 농도) (최저 0.02M)
        for name, coeff in self.products:
            self.concentrations[name] = max(0.02, self.concentrations[name] + coeff * dx) #생성물 최종 농도 계산(기존 농도+반응 농도) (최저 0.02M)

        if dx > 0.02: #최종 평형 계수 0.02보다 크면 정반응 우세 예측
            lbl_status.config(text="▶  정반응 우세 평형 이동 완료", fg="#2ecc71")
        elif dx < -0.02: #최종 평형 계수 -0.02보다 작으면 역반응 우세 예측
            lbl_status.config(text="◀  역반응 우세 평형 이동 완료", fg="#e74c3c")
        else: #최종 평형 계수 0에 가까우면 평형 유지
            lbl_status.config(text="●  화학 평형 상태 유지", fg="#2980b9")

        txt_report.delete("1.0", tk.END) #평형 이동 분석 텍스트 초기화
        txt_report.insert("1.0", report_text if report_text else "상단의 조작 바(온도, 압력, 농도)를 자유롭게 움직여 실시간 수치 변화와 화학 평형 이동 현상을 관찰해보세요.")

        self.draw_vessel(p_val, canvas) #피스톤 용기 UI 호출

    #피스톤 용기 UI 렌더링---------------------------------------------------------------------------------------------------------------------
    def draw_vessel(self, p_val, canvas):
        canvas.delete("all") #이전 프레임 잔상 삭제
        W = canvas.winfo_width() #현재 가동 캔버스 창 가로 픽셀 길이
        H = canvas.winfo_height() #현재 가동 캔버스 창 세로 픽셀 길이
        if W <= 1 or H <= 1: W, H = 560, 320 #프로그램이 막 켜져서 크기 제대로 못 잡았다면 기본해상도 지정

        #압력 슬라이더 수치에 따라 피스톤의 세로 위치 계산
        top_y = 40 + (p_val * 15 if p_val > 0 else p_val * 10)
        bot_y = H - 50
        lx, rx = 60, W - 60

        #기본 UI 디자인
        canvas.create_rectangle(lx, top_y, rx, bot_y, outline="#7f8c8d", width=4)
        canvas.create_line(lx, top_y, rx, top_y, fill="#e74c3c", width=8)
        canvas.create_rectangle((lx + rx) / 2 - 10, 10, (lx + rx) / 2 + 10, top_y, fill="#e74c3c", outline="")

        total_items = len(self.concentrations) #용기 내부 표현해야할 화학종 개수 파악
        if total_items == 0: return #표현할 화학종 없으면 종료

        #일부 화학종 미리 지정, 나머지는 예비 색상 리스트에서
        colors = {"N2": "#3498db", "H2": "#1abc9c", "NH3": "#e74c3c", "O2": "#f1c40f", "CO2": "#9b59b6"}
        default_colors = ["#34495e", "#16a085", "#d35400", "#27ae60", "#7f8c8d"]

        vessel_width = rx - lx #실린더 내부 순수 가로폭 계산
        bar_gap   = 15 #막대그래프간 좌우 간격
        bar_width = (vessel_width - (bar_gap * (total_items + 1))) / total_items #(가로폭-전체 여백)/화학종 수로 막대그래프 최적의 가로폭 계산

        #계산 완료 물질 하나씩 렌더링-----------------------------------------------------------------------------------------------------------
        for idx, (name, val) in enumerate(self.concentrations.items()):
            b_left  = lx + bar_gap + idx * (bar_width + bar_gap) #그래프 왼쪽 시작 x축 좌표
            b_right = b_left + bar_width #그래프 오른쪽 끝 x축 좌표
            max_h   = bot_y - top_y - 20 #피스톤 위치에 따라 내부 공간 쓸 수 있는 세로 높이 계산
            bar_h   = min(max_h, (val / 5.0) * max_h) #농도 비례해 막대그래프 세로 높이 계산
            b_top   = bot_y - bar_h #상단 y축 좌표
            color   = colors.get(name, default_colors[idx % len(default_colors)]) #색상 지정

            canvas.create_rectangle(b_left, b_top, b_right, bot_y, fill=color, outline="#ecf0f1", width=1)
            canvas.create_text((b_left + b_right) / 2, bot_y + 20, text=name, fill="white", font=("맑은 고딕", 10, "bold"))
            canvas.create_text((b_left + b_right) / 2, b_top - 15, text=f"{val:.2f}M", fill="#ecf0f1", font=("Consolas", 9))