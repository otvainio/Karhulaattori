import sys
import sympy
import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QGridLayout, QListWidget, QListWidgetItem,
    QLabel, QSplitter, QFrame, QTabWidget, QTextBrowser, QGroupBox
)

# Premium Nordic Dark Theme QSS Stylesheet
QSS_STYLESHEET = """
QMainWindow {
    background-color: #1e222b;
}

QTabWidget::pane {
    border: 1px solid #2e3440;
    background: #1e222b;
    border-radius: 12px;
}

QTabBar::tab {
    background: #242933;
    color: #eceff4;
    border: 1px solid #2e3440;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
    font-family: 'Segoe UI', sans-serif;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background: #2e3440;
    color: #88c0d0;
    border-bottom-color: #2e3440;
    font-weight: bold;
}

QTabBar::tab:hover {
    background: #3b4252;
}

/* Central Widget & Layouts */
QWidget#centralWidget {
    background-color: #1e222b;
}

/* Display Elements */
QFrame#displayFrame {
    background-color: #242933;
    border: 1px solid #2e3440;
    border-radius: 12px;
    padding: 10px;
}

QLineEdit#mainDisplay {
    background-color: transparent;
    border: none;
    color: #eceff4;
    font-size: 36px;
    font-weight: 500;
    font-family: 'Segoe UI', 'Outfit', sans-serif;
    qproperty-alignment: 'AlignRight | AlignVCenter';
}

QLabel#formulaDisplay {
    background-color: transparent;
    color: #81a1c1;
    font-size: 16px;
    font-family: 'Segoe UI', 'Outfit', sans-serif;
    qproperty-alignment: 'AlignRight | AlignVCenter';
}

/* Buttons Styling */
QPushButton {
    background-color: #2e3440;
    border: 1px solid #3b4252;
    border-radius: 10px;
    color: #eceff4;
    font-size: 16px;
    font-weight: 500;
    font-family: 'Segoe UI', sans-serif;
    min-height: 48px;
    min-width: 48px;
}

QPushButton:hover {
    background-color: #3b4252;
    border: 1px solid #4c566a;
}

QPushButton:pressed {
    background-color: #434c5e;
}

/* Operator Buttons styling */
QPushButton.operatorBtn {
    background-color: #3b4252;
    color: #88c0d0;
    font-size: 18px;
}

QPushButton.operatorBtn:hover {
    background-color: #434c5e;
    color: #8fbcbb;
}

/* Accent Buttons */
QPushButton.accentBtn {
    background-color: #d8dee9;
    color: #2e3440;
    font-weight: bold;
}

QPushButton.accentBtn:hover {
    background-color: #e5e9f0;
}

QPushButton.equalBtn {
    background-color: #88c0d0;
    color: #2e3440;
    font-weight: bold;
    font-size: 20px;
}

QPushButton.equalBtn:hover {
    background-color: #8fbcbb;
}

QPushButton.scientificBtn {
    background-color: #2b303c;
    color: #b48ead;
    font-size: 13px;
}

QPushButton.scientificBtn:hover {
    background-color: #353b4a;
}

QPushButton.symbolicBtn {
    background-color: #2f384c;
    color: #a3be8c;
    font-size: 13px;
}

QPushButton.symbolicBtn:hover {
    background-color: #3b4862;
}

/* Group Boxes & Containers */
QGroupBox {
    border: 1px solid #2e3440;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
    color: #81a1c1;
    font-size: 13px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}

/* Sidebar and History Styles */
QFrame#sidebarFrame {
    background-color: #242933;
    border: 1px solid #2e3440;
    border-radius: 12px;
    padding: 8px;
}

QLabel#sidebarTitle {
    color: #eceff4;
    font-weight: bold;
    font-size: 16px;
    padding: 4px;
}

QListWidget#historyList {
    background-color: transparent;
    border: none;
    color: #eceff4;
    font-size: 13px;
}

QListWidget#historyList::item {
    background-color: #2e3440;
    border-radius: 6px;
    padding: 8px;
    margin-bottom: 6px;
    color: #eceff4;
}

QListWidget#historyList::item:hover {
    background-color: #3b4252;
}

QListWidget#historyList::item:selected {
    background-color: #434c5e;
    border: 1px solid #88c0d0;
}

QPushButton#toggleSidebarBtn, QPushButton#toggleSciBtn {
    background-color: transparent;
    border: none;
    color: #81a1c1;
    font-size: 13px;
    text-decoration: underline;
    max-width: 120px;
    min-height: 25px;
}
"""

class Karhulaattori(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Karhulaattori - Premium Math Solver")
        self.setMinimumSize(780, 680)
        self.resize(850, 720)
        
        # State variables
        self.expression = ""
        self.current_input = "0"
        self.new_entry_started = True
        
        # Setup Tabbed Layout
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tabs setup
        self.setup_calculator_tab()
        self.setup_symbolic_tab()
        
        self.apply_styles()
        self.bind_shortcuts()
        self.update_displays()

    def apply_styles(self):
        self.setStyleSheet(QSS_STYLESHEET)

    def setup_calculator_tab(self):
        calc_widget = QWidget()
        self.tabs.addTab(calc_widget, "Calculator")
        
        tab_layout = QHBoxLayout(calc_widget)
        tab_layout.setContentsMargins(8, 8, 8, 8)
        tab_layout.setSpacing(10)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        tab_layout.addWidget(self.splitter)
        
        # Left Panel (Layout)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # Display
        display_frame = QFrame()
        display_frame.setObjectName("displayFrame")
        display_layout = QVBoxLayout(display_frame)
        display_layout.setContentsMargins(10, 10, 10, 10)
        display_layout.setSpacing(4)
        
        self.formula_label = QLabel("")
        self.formula_label.setObjectName("formulaDisplay")
        display_layout.addWidget(self.formula_label)
        
        self.display_input = QLineEdit("0")
        self.display_input.setObjectName("mainDisplay")
        self.display_input.setReadOnly(True)
        display_layout.addWidget(self.display_input)
        left_layout.addWidget(display_frame)
        
        # Variable x input row
        self.x_input_frame = QFrame()
        self.x_input_frame.setVisible(False)
        x_input_layout = QHBoxLayout(self.x_input_frame)
        x_input_layout.setContentsMargins(8, 2, 8, 2)
        
        x_label = QLabel("Variable x value:")
        x_label.setStyleSheet("color: #a3be8c; font-size: 13px; font-weight: bold;")
        x_input_layout.addWidget(x_label)
        
        self.x_value_input = QLineEdit("5")
        self.x_value_input.setStyleSheet("""
            background-color: #2e3440;
            border: 1px solid #4c566a;
            border-radius: 6px;
            color: #eceff4;
            font-size: 13px;
            padding: 4px;
            max-width: 80px;
        """)
        x_input_layout.addWidget(self.x_value_input)
        x_input_layout.addStretch()
        left_layout.addWidget(self.x_input_frame)
        
        # Options Row
        toggles_layout = QHBoxLayout()
        self.toggle_sci_btn = QPushButton("Scientific Mode")
        self.toggle_sci_btn.setObjectName("toggleSciBtn")
        self.toggle_sci_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_sci_btn.clicked.connect(self.toggle_scientific)
        toggles_layout.addWidget(self.toggle_sci_btn)
        
        toggles_layout.addStretch()
        
        self.toggle_sidebar_btn = QPushButton("Show History")
        self.toggle_sidebar_btn.setObjectName("toggleSidebarBtn")
        self.toggle_sidebar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        toggles_layout.addWidget(self.toggle_sidebar_btn)
        left_layout.addLayout(toggles_layout)
        
        # Buttons Widget
        self.buttons_widget = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_widget)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(6)
        
        # Scientific grid
        self.sci_panel = QFrame()
        self.sci_panel.setVisible(False)
        sci_grid = QGridLayout(self.sci_panel)
        sci_grid.setContentsMargins(0, 0, 0, 0)
        sci_grid.setSpacing(6)
        
        sci_buttons = [
            ('x²', 'pow2', 'scientificBtn'), ('xʸ', 'pow_y', 'scientificBtn'), ('√', 'sqrt', 'scientificBtn'), ('π', 'pi', 'scientificBtn'), ('e', 'e', 'scientificBtn'),
            ('sin', 'sin', 'scientificBtn'), ('cos', 'cos', 'scientificBtn'), ('tan', 'tan', 'scientificBtn'), ('(', 'lpar', 'scientificBtn'), (')', 'rpar', 'scientificBtn'),
            ('x', 'var_x', 'symbolicBtn'), ('d/dx', 'diff', 'symbolicBtn'), ('∫dx', 'integrate', 'symbolicBtn'), ('simplify', 'simplify', 'symbolicBtn'), ('solve=0', 'solve', 'symbolicBtn')
        ]
        
        for idx, (label, action, style_class) in enumerate(sci_buttons):
            btn = QPushButton(label)
            btn.setProperty("class", style_class)
            btn.clicked.connect(lambda checked, act=action, val=label: self.handle_action(act, val))
            row = idx // 5
            col = idx % 5
            sci_grid.addWidget(btn, row, col)
            
        self.buttons_layout.addWidget(self.sci_panel)
        
        # Core Grid
        core_grid_widget = QWidget()
        core_grid = QGridLayout(core_grid_widget)
        core_grid.setContentsMargins(0, 0, 0, 0)
        core_grid.setSpacing(6)
        
        buttons = [
            ('C', 'clear', 0, 0, 1, 1, 'accentBtn'),
            ('CE', 'clear_entry', 0, 1, 1, 1, 'accentBtn'),
            ('%', 'percent', 0, 2, 1, 1, 'operatorBtn'),
            ('÷', 'divide', 0, 3, 1, 1, 'operatorBtn'),
            
            ('7', 'num_7', 1, 0, 1, 1, ''),
            ('8', 'num_8', 1, 1, 1, 1, ''),
            ('9', 'num_9', 1, 2, 1, 1, ''),
            ('×', 'multiply', 1, 3, 1, 1, 'operatorBtn'),
            
            ('4', 'num_4', 2, 0, 1, 1, ''),
            ('5', 'num_5', 2, 1, 1, 1, ''),
            ('6', 'num_6', 2, 2, 1, 1, ''),
            ('-', 'subtract', 2, 3, 1, 1, 'operatorBtn'),
            
            ('1', 'num_1', 3, 0, 1, 1, ''),
            ('2', 'num_2', 3, 1, 1, 1, ''),
            ('3', 'num_3', 3, 2, 1, 1, ''),
            ('+', 'add', 3, 3, 1, 1, 'operatorBtn'),
            
            ('+/-', 'negate', 4, 0, 1, 1, ''),
            ('0', 'num_0', 4, 1, 1, 1, ''),
            ('.', 'decimal', 4, 2, 1, 1, ''),
            ('=', 'equals', 4, 3, 1, 1, 'equalBtn')
        ]
        
        for label, action, row, col, rspan, cspan, style_class in buttons:
            btn = QPushButton(label)
            if style_class:
                btn.setProperty("class", style_class)
            btn.clicked.connect(lambda checked, act=action, val=label: self.handle_action(act, val))
            core_grid.addWidget(btn, row, col, rspan, cspan)
            
        self.buttons_layout.addWidget(core_grid_widget)
        left_layout.addWidget(self.buttons_widget)
        self.splitter.addWidget(left_container)
        
        # History Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebarFrame")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(6, 6, 6, 6)
        
        sidebar_header = QHBoxLayout()
        title = QLabel("History")
        title.setObjectName("sidebarTitle")
        sidebar_header.addWidget(title)
        sidebar_header.addStretch()
        
        clear_hist_btn = QPushButton("Clear")
        clear_hist_btn.setStyleSheet("font-size: 11px; min-height: 22px; max-width: 50px; background-color: #3b4252; border: none;")
        clear_hist_btn.clicked.connect(self.clear_history)
        sidebar_header.addWidget(clear_hist_btn)
        sidebar_layout.addLayout(sidebar_header)
        
        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.itemDoubleClicked.connect(self.history_item_clicked)
        sidebar_layout.addWidget(self.history_list)
        
        self.splitter.addWidget(self.sidebar)
        self.sidebar.setVisible(False)
        self.splitter.setSizes([500, 250])

    def setup_symbolic_tab(self):
        sym_widget = QWidget()
        self.tabs.addTab(sym_widget, "Symbolic Solver & Grapher")
        
        layout = QHBoxLayout(sym_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Left Column - Function Input & Solvers
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        input_group = QGroupBox("Define Function f(x)")
        ig_layout = QVBoxLayout(input_group)
        self.f_x_input = QLineEdit("x**2 - 3*x + 2")
        self.f_x_input.setStyleSheet("""
            background-color: #242933;
            border: 1px solid #3b4252;
            border-radius: 8px;
            color: #eceff4;
            font-size: 16px;
            font-family: 'Consolas', monospace;
            padding: 8px;
        """)
        ig_layout.addWidget(self.f_x_input)
        left_layout.addWidget(input_group)
        
        # Action Grid for solvers
        actions_group = QGroupBox("Symbolic Operators")
        ag_layout = QGridLayout(actions_group)
        ag_layout.setSpacing(8)
        
        sym_ops = [
            ("Solve f(x) = 0", "solve_eq"),
            ("Derivative (d/dx)", "derive_eq"),
            ("Integral (∫dx)", "integrate_eq"),
            ("Simplify Formula", "simplify_eq"),
            ("Limit x -> 0", "limit_0"),
            ("Taylor Expansion", "taylor_eq")
        ]
        
        for idx, (label, act) in enumerate(sym_ops):
            btn = QPushButton(label)
            btn.setStyleSheet("font-size: 13px; font-weight: bold; background-color: #2f384c; color: #a3be8c;")
            btn.clicked.connect(lambda checked, action=act: self.execute_symbolic_op(action))
            row = idx // 2
            col = idx % 2
            ag_layout.addWidget(btn, row, col)
            
        left_layout.addWidget(actions_group)
        
        # Results View
        results_group = QGroupBox("Calculation Output")
        rg_layout = QVBoxLayout(results_group)
        self.sym_output = QTextBrowser()
        self.sym_output.setStyleSheet("""
            background-color: #242933;
            border: 1px solid #2e3440;
            border-radius: 8px;
            color: #a3be8c;
            font-family: 'Consolas', monospace;
            font-size: 14px;
        """)
        rg_layout.addWidget(self.sym_output)
        left_layout.addWidget(results_group)
        
        layout.addWidget(left_panel, 2)
        
        # Right Column - Visual Plot Area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        plot_group = QGroupBox("Interactive Graph")
        pg_layout = QVBoxLayout(plot_group)
        
        # Matplotlib Canvas Setup
        self.canvas = FigureCanvas(Figure(facecolor='#1e222b'))
        self.ax = self.canvas.figure.subplots()
        self.ax.set_facecolor('#242933')
        self.ax.tick_params(colors='#eceff4')
        self.ax.grid(color='#2e3440', linestyle='--')
        
        pg_layout.addWidget(self.canvas)
        
        # Plot Range Options & Button
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Range x from:"))
        self.x_min_input = QLineEdit("-10")
        self.x_min_input.setFixedWidth(50)
        self.x_min_input.setStyleSheet("background-color: #2e3440; color: #eceff4; border: 1px solid #3b4252; border-radius: 4px; padding: 3px;")
        control_layout.addWidget(self.x_min_input)
        
        control_layout.addWidget(QLabel("to:"))
        self.x_max_input = QLineEdit("10")
        self.x_max_input.setFixedWidth(50)
        self.x_max_input.setStyleSheet("background-color: #2e3440; color: #eceff4; border: 1px solid #3b4252; border-radius: 4px; padding: 3px;")
        control_layout.addWidget(self.x_max_input)
        
        control_layout.addStretch()
        
        self.plot_btn = QPushButton("Plot Function")
        self.plot_btn.setStyleSheet("background-color: #88c0d0; color: #2e3440; font-weight: bold; min-height: 35px; min-width: 120px;")
        self.plot_btn.clicked.connect(self.plot_function)
        control_layout.addWidget(self.plot_btn)
        
        pg_layout.addLayout(control_layout)
        right_layout.addWidget(plot_group)
        
        layout.addWidget(right_panel, 3)
        
        # Initial Plot
        self.plot_function()

    def bind_shortcuts(self):
        # Digits & decimal
        for char in "0123456789.x":
            sc = QShortcut(QKeySequence(char), self)
            sc.activated.connect(lambda c=char: self.handle_digit(c))
            
        # Operators
        ops = {
            '+': ('add', '+'),
            '-': ('subtract', '-'),
            '*': ('multiply', '×'),
            '/': ('divide', '÷'),
            '%': ('percent', '%'),
            '=': ('equals', '='),
            '\r': ('equals', '='),
            '\n': ('equals', '='),
        }
        for key, (action, val) in ops.items():
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda a=action, v=val: self.handle_action(a, v))
            
        # Clear
        sc_clear = QShortcut(QKeySequence("Esc"), self)
        sc_clear.activated.connect(lambda: self.handle_action("clear", "C"))
        
        sc_back = QShortcut(QKeySequence("Backspace"), self)
        sc_back.activated.connect(lambda: self.handle_action("clear_entry", "CE"))

    def toggle_scientific(self):
        visible = self.sci_panel.isVisible()
        self.sci_panel.setVisible(not visible)
        self.x_input_frame.setVisible(not visible)
        self.toggle_sci_btn.setText("Standard Mode" if not visible else "Scientific Mode")

    def toggle_sidebar(self):
        visible = self.sidebar.isVisible()
        self.sidebar.setVisible(not visible)
        self.toggle_sidebar_btn.setText("Hide History" if not visible else "Show History")

    def update_displays(self):
        self.display_input.setText(self.current_input)
        self.formula_label.setText(self.expression)

    def handle_digit(self, char):
        if self.new_entry_started:
            if char == '.':
                self.current_input = "0."
            else:
                self.current_input = char
            self.new_entry_started = False
        else:
            if char == '.' and '.' in self.current_input:
                return
            if self.current_input == "0" and char != '.':
                self.current_input = char
            else:
                self.current_input += char
        self.update_displays()

    def handle_action(self, action, val):
        if action.startswith("num_"):
            digit = action.split("_")[1]
            self.handle_digit(digit)
            return
            
        if action == "decimal":
            self.handle_digit(".")
            return
            
        if action == "var_x":
            self.handle_digit("x")
            return
            
        if action == "clear":
            self.expression = ""
            self.current_input = "0"
            self.new_entry_started = True
            
        elif action == "clear_entry":
            self.current_input = "0"
            self.new_entry_started = True
            
        elif action == "negate":
            if self.current_input != "0":
                if self.current_input.startswith("-"):
                    self.current_input = self.current_input[1:]
                else:
                    self.current_input = "-" + self.current_input
                    
        elif action in ["add", "subtract", "multiply", "divide"]:
            op_map = {"add": "+", "subtract": "-", "multiply": "*", "divide": "/"}
            if self.new_entry_started and self.expression and self.expression[-1] in ["+", "-", "*", "/"]:
                self.expression = self.expression[:-1] + op_map[action]
            else:
                self.expression += f" {self.current_input} {op_map[action]}"
            self.new_entry_started = True
            
        elif action == "percent":
            try:
                expr_str = f"({self.current_input}) / 100"
                result = sympy.sympify(expr_str)
                self.current_input = self.format_number(result)
            except Exception:
                self.current_input = "Error"
                
        elif action == "equals":
            if not self.expression and 'x' not in self.current_input:
                return
            
            full_expr = f"{self.expression} {self.current_input}".strip()
            try:
                eval_expr = full_expr.replace("×", "*").replace("÷", "/")
                x = sympy.Symbol('x')
                
                if "=" in eval_expr:
                    parts = eval_expr.split("=")
                    sym_expr = sympy.sympify(parts[0]) - sympy.sympify(parts[1])
                    result_val = sympy.solve(sym_expr, x)
                else:
                    sym_expr = sympy.sympify(eval_expr)
                    if x in sym_expr.free_symbols:
                        x_val_str = self.x_value_input.text().strip()
                        x_val = sympy.sympify(x_val_str)
                        result_val = sym_expr.subs(x, x_val).evalf()
                    else:
                        result_val = sym_expr.evalf()
                
                formatted_res = self.format_number(result_val)
                readable_expr = full_expr.replace("*", "×").replace("/", "÷").strip()
                self.add_history_item(readable_expr, formatted_res)
                
                self.current_input = formatted_res
                self.expression = ""
                self.new_entry_started = True
            except Exception:
                self.current_input = "Error"
                self.new_entry_started = True
                
        # Scientific Operations
        elif action == "pow2":
            self.current_input = f"({self.current_input})**2"
            self.new_entry_started = False
            
        elif action == "pow_y":
            self.expression += f" ({self.current_input})**"
            self.new_entry_started = True
            
        elif action == "sqrt":
            self.current_input = f"sqrt({self.current_input})"
            self.new_entry_started = False
            
        elif action == "pi":
            self.current_input = "pi"
            self.new_entry_started = False
            
        elif action == "e":
            self.current_input = "E"
            self.new_entry_started = False
            
        elif action in ["sin", "cos", "tan"]:
            self.current_input = f"{action}({self.current_input})"
            self.new_entry_started = False
            
        elif action == "lpar":
            if self.new_entry_started or self.current_input == "0":
                self.expression += " ("
            else:
                self.expression += f" {self.current_input} * ("
            self.new_entry_started = True
            self.current_input = "0"
            
        elif action == "rpar":
            self.expression += f" {self.current_input} )"
            self.new_entry_started = True
            self.current_input = "0"
            
        elif action in ["diff", "integrate", "simplify", "solve"]:
            # Quick route symbolic operations from the main calculator
            full_expr = f"{self.expression} {self.current_input}".strip()
            try:
                eval_expr = full_expr.replace("×", "*").replace("÷", "/")
                x = sympy.Symbol('x')
                
                if "=" in eval_expr:
                    parts = eval_expr.split("=")
                    sym_expr = sympy.sympify(parts[0]) - sympy.sympify(parts[1])
                else:
                    sym_expr = sympy.sympify(eval_expr)
                
                if action == "diff":
                    result = sympy.diff(sym_expr, x)
                    readable_op = f"d/dx({eval_expr})"
                elif action == "integrate":
                    result = sympy.integrate(sym_expr, x)
                    readable_op = f"∫({eval_expr})dx"
                elif action == "simplify":
                    result = sympy.simplify(sym_expr)
                    readable_op = f"simplify({eval_expr})"
                elif action == "solve":
                    result = sympy.solve(sym_expr, x)
                    readable_op = f"solve({eval_expr})"
                    
                formatted_res = str(result)
                self.add_history_item(readable_op, formatted_res)
                self.current_input = formatted_res
                self.expression = ""
                self.new_entry_started = True
            except Exception:
                self.current_input = "Error"
                self.new_entry_started = True
                
        self.update_displays()

    def format_number(self, value):
        try:
            if isinstance(value, (sympy.Float, sympy.Integer)):
                val_float = float(value)
                if val_float.is_integer():
                    return str(int(val_float))
                if abs(val_float) > 1e12 or (abs(val_float) < 1e-6 and val_float != 0):
                    return f"{val_float:.6e}"
                return f"{val_float:.8g}"
            return str(value)
        except Exception:
            return str(value)

    def add_history_item(self, calculation, result):
        item_text = f"{calculation}\n= {result}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, result)
        self.history_list.insertItem(0, item)

    def history_item_clicked(self, item):
        result_val = item.data(Qt.ItemDataRole.UserRole)
        if result_val and result_val != "Error":
            self.current_input = result_val
            self.new_entry_started = True
            self.update_displays()

    def clear_history(self):
        self.history_list.clear()

    # Dedicated Symbolic Solver operations
    def execute_symbolic_op(self, action):
        func_str = self.f_x_input.text().strip()
        if not func_str:
            self.sym_output.setText("Error: Function f(x) is empty.")
            return
            
        try:
            # Check for system of equations (separated by commas)
            if "," in func_str:
                eqs_strs = func_str.split(",")
                eqs = []
                symbols = set()
                for eq_str in eqs_strs:
                    eq_str = eq_str.strip()
                    if not eq_str:
                        continue
                    if "=" in eq_str:
                        parts = eq_str.split("=")
                        eq = sympy.sympify(parts[0]) - sympy.sympify(parts[1])
                    else:
                        eq = sympy.sympify(eq_str)
                    eqs.append(eq)
                    symbols.update(eq.free_symbols)
                
                symbols = sorted(list(symbols), key=lambda s: s.name)
                output_html = "<b>System of Equations:</b><br>"
                for eq in eqs:
                    output_html += f"{eq} = 0<br>"
                output_html += "<br>"
                
                if action == "solve_eq":
                    sol = sympy.solve(eqs, symbols)
                    output_html += "<b>Solutions:</b><br>"
                    if not sol:
                        output_html += "No solutions found."
                    else:
                        if isinstance(sol, dict):
                            for var, val in sol.items():
                                output_html += f"{var} = {val}<br>"
                        elif isinstance(sol, list):
                            for idx, s in enumerate(sol):
                                if isinstance(s, tuple):
                                    term = ", ".join(f"{symbols[i]} = {val}" for i, val in enumerate(s))
                                    output_html += f"Set {idx+1}: {term}<br>"
                                else:
                                    output_html += f"Set {idx+1}: {s}<br>"
                        else:
                            output_html += f"{sol}<br>"
                    self.sym_output.setHtml(output_html)
                    return
                else:
                    raise ValueError("Calculus operations are not supported on systems of equations.")

            # Single equation or expression
            x = sympy.Symbol('x')
            if "=" in func_str:
                parts = func_str.split("=")
                expr = sympy.sympify(parts[0]) - sympy.sympify(parts[1])
                output_html = f"<b>Equation:</b> {parts[0]} = {parts[1]}<br><br>"
            else:
                expr = sympy.sympify(func_str)
                output_html = f"<b>Function:</b> f(x) = {expr}<br><br>"
            
            if action == "solve_eq":
                roots = sympy.solve(expr, x)
                output_html += "<b>Solutions for x:</b><br>"
                if not roots:
                    output_html += "No analytical roots found."
                else:
                    for i, root in enumerate(roots):
                        output_html += f"x<sub>{i+1}</sub> = {root}<br>"
                        
            elif action == "derive_eq":
                deriv = sympy.diff(expr, x)
                output_html += f"<b>Derivative f'(x):</b><br>{deriv}"
                
            elif action == "integrate_eq":
                integral = sympy.integrate(expr, x)
                output_html += f"<b>Indefinite Integral ∫f(x)dx:</b><br>{integral} + C"
                
            elif action == "simplify_eq":
                simp = sympy.simplify(expr)
                output_html += f"<b>Simplified Formula:</b><br>{simp}"
                
            elif action == "limit_0":
                lim = sympy.limit(expr, x, 0)
                output_html += f"<b>Limit as x → 0:</b><br>{lim}"
                
            elif action == "taylor_eq":
                series = sympy.series(expr, x, 0, 5)
                output_html += f"<b>Taylor Series (x=0, up to O(x^5)):</b><br>{series}"
                
            self.sym_output.setHtml(output_html)
        except Exception as e:
            self.sym_output.setText(f"Error executing operation:\n{str(e)}")

    def plot_function(self):
        func_str = self.f_x_input.text().strip()
        try:
            # Handle systems of equations or equation plotting
            if "," in func_str:
                self.sym_output.setText("Plotting is not supported for systems of equations.")
                return
                
            x = sympy.Symbol('x')
            if "=" in func_str:
                parts = func_str.split("=")
                expr = sympy.sympify(parts[0]) - sympy.sympify(parts[1])
            else:
                expr = sympy.sympify(func_str)
            
            # Make numeric function via numpy
            f_num = sympy.lambdify(x, expr, "numpy")
            
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
            
            # Draw values
            x_vals = np.linspace(x_min, x_max, 400)
            
            # Wrap function execution to avoid crash on division-by-zero or complex numbers
            y_vals = []
            for val in x_vals:
                try:
                    res = f_num(val)
                    if isinstance(res, complex) or np.isnan(res) or np.isinf(res):
                        y_vals.append(None)
                    else:
                        y_vals.append(float(res))
                except Exception:
                    y_vals.append(None)
                    
            y_vals = np.array(y_vals, dtype=float)
            
            # Redraw canvas
            self.ax.clear()
            self.ax.set_facecolor('#242933')
            self.ax.grid(color='#2e3440', linestyle='--')
            
            # Plot the line
            self.ax.plot(x_vals, y_vals, color='#88c0d0', linewidth=2.5, label=f"y = {expr}")
            
            # Draw horizontal/vertical zero lines
            self.ax.axhline(0, color='#3b4252', linewidth=1.2)
            self.ax.axvline(0, color='#3b4252', linewidth=1.2)
            
            self.ax.legend(facecolor='#1e222b', edgecolor='#2e3440', labelcolor='#eceff4')
            self.ax.tick_params(colors='#eceff4')
            
            self.canvas.draw()
        except Exception as e:
            self.sym_output.setText(f"Plotting Error:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    
    window = Karhulaattori()
    window.show()
    sys.exit(app.exec())
