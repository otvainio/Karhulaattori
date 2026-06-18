import sys
import json
import os
from datetime import datetime
import sympy
import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers 3D projection

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QGridLayout, QListWidget, QListWidgetItem,
    QLabel, QSplitter, QFrame, QTabWidget, QTextBrowser, QTextEdit, QGroupBox, QScrollArea,
    QComboBox
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

class LatexCanvas(FigureCanvas):
    """Renders a LaTeX string via matplotlib mathtext — no external LaTeX install needed."""
    def __init__(self, bg='#1e222b', height=100):
        self._fig = Figure(facecolor=bg)
        super().__init__(self._fig)
        self._ax = self._fig.add_axes([0, 0, 1, 1])
        self._ax.set_axis_off()
        self._ax.set_facecolor(bg)
        self._bg = bg
        self._current_latex = ""
        self.setFixedHeight(height)

    def render(self, latex_str):
        self._current_latex = latex_str
        self._ax.clear()
        self._ax.set_axis_off()
        self._ax.set_facecolor(self._bg)
        if latex_str:
            try:
                self._ax.text(
                    0.5, 0.5, r"$" + latex_str + r"$",
                    ha='center', va='center', fontsize=15,
                    color='#88c0d0', transform=self._ax.transAxes
                )
            except Exception:
                pass
        try:
            self._fig.canvas.draw_idle()
        except Exception:
            pass


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
        self._history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history.json')
        self._global_history = []
        self._load_history()

        self.setup_calculator_tab()
        self.setup_symbolic_tab()
        self.setup_linear_algebra_tab()
        self.setup_complex_tab()
        self.setup_calculus_tab()
        self.setup_statistics_tab()
        self.setup_3d_graphing_tab()
        self.setup_number_theory_tab()
        self.setup_analysis_tab()
        self.setup_history_tab()
        
        self.apply_styles()
        self.bind_shortcuts()
        self.update_displays()

    def apply_styles(self):
        self.setStyleSheet(QSS_STYLESHEET)

    def _copy_latex_btn(self, canvas):
        btn = QPushButton("Copy LaTeX")
        btn.setStyleSheet(
            "font-size: 11px; min-height: 22px; max-height: 24px; "
            "background-color: #2e3440; color: #81a1c1; "
            "border: 1px solid #3b4252; border-radius: 4px; padding: 0 8px;"
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: QApplication.clipboard().setText(canvas._current_latex))
        return btn

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
        self.tabs.addTab(sym_widget, "Symbolic Solver")
        
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
        self.sym_input_latex = LatexCanvas(height=80)
        ig_layout.addWidget(self.sym_input_latex)
        ig_layout.addWidget(self._copy_latex_btn(self.sym_input_latex), alignment=Qt.AlignmentFlag.AlignRight)
        self.f_x_input.textChanged.connect(self._preview_sym_input)
        left_layout.addWidget(input_group)
        self._preview_sym_input(self.f_x_input.text())
        
        # Action Grid for solvers
        actions_group = QGroupBox("Symbolic Operators")
        ag_layout = QGridLayout(actions_group)
        ag_layout.setSpacing(8)
        
        sym_ops = [
            ("Solve Equation(s)", "solve_eq"),
            ("Solve ODE",         "solve_ode"),
            ("Simplify Formula",  "simplify_eq"),
        ]
        
        for idx, (label, act) in enumerate(sym_ops):
            btn = QPushButton(label)
            btn.setStyleSheet("font-size: 13px; font-weight: bold; background-color: #2f384c; color: #a3be8c;")
            btn.clicked.connect(lambda checked, action=act: self.execute_symbolic_op(action))
            row = idx // 2
            col = idx % 2
            ag_layout.addWidget(btn, row, col)
            
        left_layout.addWidget(actions_group)

        # Polynomial, Trig & Log group
        extra_group = QGroupBox("Polynomial · Advanced Trig · Logarithms")
        eg_layout = QGridLayout(extra_group)
        eg_layout.setSpacing(8)

        extra_ops = [
            # Polynomial
            ("Expand",          "expand_poly"),
            ("Factor",          "factor_poly"),
            ("Partial Fractions","apart_poly"),
            ("Collect (x)",     "collect_poly"),
            # Advanced trig
            ("Trig Simplify",   "trig_simp"),
            ("Expand Trig",     "expand_trig"),
            ("Rewrite → exp",   "rewrite_exp"),
            ("Rewrite → cos",   "rewrite_cos"),
            # Logarithms
            ("Expand log",      "expand_log"),
            ("Combine log",     "combine_log"),
        ]

        for idx, (label, act) in enumerate(extra_ops):
            btn = QPushButton(label)
            btn.setStyleSheet(
                "font-size: 12px; font-weight: bold; "
                "background-color: #2a3045; color: #88c0d0; min-height: 36px;"
            )
            btn.clicked.connect(lambda checked, action=act: self.execute_symbolic_op(action))
            eg_layout.addWidget(btn, idx // 3, idx % 3)

        # "Evaluate log(b)" — log base input inline with the button
        log_eval_widget = QWidget()
        log_eval_layout = QHBoxLayout(log_eval_widget)
        log_eval_layout.setContentsMargins(0, 0, 0, 0)
        log_eval_layout.setSpacing(6)
        log_base_label = QLabel("log base b:")
        log_base_label.setStyleSheet("color: #88c0d0; font-size: 12px;")
        log_eval_layout.addWidget(log_base_label)
        self.log_base_input = QLineEdit("10")
        self.log_base_input.setFixedWidth(50)
        self.log_base_input.setStyleSheet(
            "background-color: #2e3440; color: #eceff4; "
            "border: 1px solid #3b4252; border-radius: 4px; padding: 3px;"
        )
        log_eval_layout.addWidget(self.log_base_input)
        eval_log_btn = QPushButton("Evaluate log(b)")
        eval_log_btn.setStyleSheet(
            "font-size: 12px; font-weight: bold; "
            "background-color: #2a3045; color: #88c0d0; min-height: 36px;"
        )
        eval_log_btn.clicked.connect(lambda: self.execute_symbolic_op("eval_log"))
        log_eval_layout.addWidget(eval_log_btn)
        next_row = (len(extra_ops) - 1) // 3 + 1
        eg_layout.addWidget(log_eval_widget, next_row, 0, 1, 3)

        left_layout.addWidget(extra_group)
        
        # Results View
        results_group = QGroupBox("Calculation Output")
        rg_layout = QVBoxLayout(results_group)
        self.sym_output = QTextBrowser()
        self.sym_output.setMaximumHeight(60)
        self.sym_output.setStyleSheet("""
            background-color: #242933;
            border: 1px solid #2e3440;
            border-radius: 8px;
            color: #a3be8c;
            font-family: 'Consolas', monospace;
            font-size: 13px;
        """)
        rg_layout.addWidget(self.sym_output)
        self.sym_result_latex = LatexCanvas(height=130)
        rg_layout.addWidget(self.sym_result_latex)
        rg_layout.addWidget(self._copy_latex_btn(self.sym_result_latex), alignment=Qt.AlignmentFlag.AlignRight)
        left_layout.addWidget(results_group)
        
        layout.addWidget(left_panel, 2)

        # Right Column - Visual Plot Area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        plot_group = QGroupBox("Interactive Graph")
        pg_layout = QVBoxLayout(plot_group)

        # Multi-function input
        func_label = QLabel("Functions to plot — one per line. Explicit: x**2+1  or  y=x**2  |  Implicit: x**2+y**2=25")
        func_label.setStyleSheet("color: #81a1c1; font-size: 11px;")
        func_label.setWordWrap(True)
        pg_layout.addWidget(func_label)

        self.plot_functions_input = QTextEdit("x**2 - 3*x + 2")
        self.plot_functions_input.setFixedHeight(62)
        self.plot_functions_input.setStyleSheet("""
            background-color: #242933;
            border: 1px solid #3b4252;
            border-radius: 6px;
            color: #eceff4;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            padding: 4px;
        """)
        pg_layout.addWidget(self.plot_functions_input)

        # Matplotlib Canvas
        self.canvas = FigureCanvas(Figure(facecolor='#1e222b'))
        self.ax = self.canvas.figure.subplots()
        self.ax.set_facecolor('#242933')
        self.ax.tick_params(colors='#eceff4')
        self.ax.grid(color='#2e3440', linestyle='--')
        pg_layout.addWidget(self.canvas)
        self._setup_graph_interaction()

        # Plot Range & Button
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("x from:"))
        self.x_min_input = QLineEdit("-10")
        self.x_min_input.setFixedWidth(50)
        self.x_min_input.setStyleSheet("background-color: #2e3440; color: #eceff4; border: 1px solid #3b4252; border-radius: 4px; padding: 3px;")
        control_layout.addWidget(self.x_min_input)
        control_layout.addWidget(QLabel("to:"))
        self.x_max_input = QLineEdit("10")
        self.x_max_input.setFixedWidth(50)
        self.x_max_input.setStyleSheet("background-color: #2e3440; color: #eceff4; border: 1px solid #3b4252; border-radius: 4px; padding: 3px;")
        control_layout.addWidget(self.x_max_input)
        control_layout.addWidget(QLabel("  y from:"))
        self.y_min_input = QLineEdit("-10")
        self.y_min_input.setFixedWidth(50)
        self.y_min_input.setStyleSheet("background-color: #2e3440; color: #eceff4; border: 1px solid #3b4252; border-radius: 4px; padding: 3px;")
        control_layout.addWidget(self.y_min_input)
        control_layout.addWidget(QLabel("to:"))
        self.y_max_input = QLineEdit("10")
        self.y_max_input.setFixedWidth(50)
        self.y_max_input.setStyleSheet("background-color: #2e3440; color: #eceff4; border: 1px solid #3b4252; border-radius: 4px; padding: 3px;")
        control_layout.addWidget(self.y_max_input)
        control_layout.addStretch()
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.setStyleSheet("background-color: #3b4252; color: #81a1c1; font-size: 12px; min-height: 35px; min-width: 85px;")
        reset_view_btn.clicked.connect(self._reset_graph_view)
        control_layout.addWidget(reset_view_btn)
        clear_graph_btn = QPushButton("Clear")
        clear_graph_btn.setStyleSheet("background-color: #3b4252; color: #bf616a; font-weight: bold; min-height: 35px; min-width: 65px;")
        clear_graph_btn.clicked.connect(self._clear_graph)
        control_layout.addWidget(clear_graph_btn)
        self.plot_btn = QPushButton("Plot")
        self.plot_btn.setStyleSheet("background-color: #88c0d0; color: #2e3440; font-weight: bold; min-height: 35px; min-width: 80px;")
        self.plot_btn.clicked.connect(self.plot_function)
        control_layout.addWidget(self.plot_btn)
        pg_layout.addLayout(control_layout)
        right_layout.addWidget(plot_group)

        # Intercepts & Intersections output
        intercepts_grp = QGroupBox("Intercepts & Intersections")
        igl = QVBoxLayout(intercepts_grp)
        self.intercepts_output = QTextBrowser()
        self.intercepts_output.setFixedHeight(80)
        self.intercepts_output.setStyleSheet("""
            background-color: #242933;
            border: 1px solid #2e3440;
            border-radius: 8px;
            color: #eceff4;
            font-family: 'Consolas', monospace;
            font-size: 12px;
        """)
        igl.addWidget(self.intercepts_output)
        right_layout.addWidget(intercepts_grp)

        layout.addWidget(right_panel, 3)

        # Initial Plot
        self.plot_function()

    def setup_linear_algebra_tab(self):
        la_widget = QWidget()
        self.tabs.addTab(la_widget, "Linear Algebra")

        outer = QHBoxLayout(la_widget)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        # ── LEFT: inputs ──────────────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)

        input_style = """
            background-color: #242933;
            border: 1px solid #3b4252;
            border-radius: 8px;
            color: #eceff4;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            padding: 6px;
        """

        # Matrix A
        grp_a = QGroupBox("Matrix A  (rows by ';', cols by spaces — e.g.  1 2; 3 4)")
        la = QVBoxLayout(grp_a)
        self.la_mat_a = QTextEdit("1 2; 3 4")
        self.la_mat_a.setFixedHeight(80)
        self.la_mat_a.setStyleSheet(input_style)
        la.addWidget(self.la_mat_a)
        left_layout.addWidget(grp_a)

        # Matrix B
        grp_b = QGroupBox("Matrix B")
        lb = QVBoxLayout(grp_b)
        self.la_mat_b = QTextEdit("5 6; 7 8")
        self.la_mat_b.setFixedHeight(80)
        self.la_mat_b.setStyleSheet(input_style)
        lb.addWidget(self.la_mat_b)
        left_layout.addWidget(grp_b)

        # Vector u
        grp_u = QGroupBox("Vector u  (space or comma separated, e.g.  1 2 3)")
        lu = QVBoxLayout(grp_u)
        self.la_vec_u = QLineEdit("1 2 3")
        self.la_vec_u.setStyleSheet(input_style)
        lu.addWidget(self.la_vec_u)
        left_layout.addWidget(grp_u)

        # Vector v
        grp_v = QGroupBox("Vector v")
        lv = QVBoxLayout(grp_v)
        self.la_vec_v = QLineEdit("4 5 6")
        self.la_vec_v.setStyleSheet(input_style)
        lv.addWidget(self.la_vec_v)
        left_layout.addWidget(grp_v)

        left_layout.addStretch()
        outer.addWidget(left, 2)

        # ── MIDDLE: operation buttons ──────────────────────────────────
        mid = QWidget()
        mid_layout = QVBoxLayout(mid)
        mid_layout.setSpacing(8)

        btn_style = "font-size: 12px; font-weight: bold; background-color: #2f384c; color: #a3be8c; min-height: 38px;"

        matrix_ops = [
            ("det(A)",       "det_a"),
            ("inv(A)",       "inv_a"),
            ("Transpose A",  "tra_a"),
            ("Eigenvalues A","eig_a"),
            ("A × B",        "mat_mul"),
            ("A + B",        "mat_add"),
            ("Rank A",       "rank_a"),
            ("Row Echelon A","rref_a"),
        ]
        vector_ops = [
            ("u · v (dot)",  "dot_uv"),
            ("u × v (cross)","cross_uv"),
            ("|u| (norm)",   "norm_u"),
            ("Angle(u,v)",   "angle_uv"),
            ("u + v",        "vec_add"),
            ("Projection u→v","proj_uv"),
        ]

        mat_grp = QGroupBox("Matrix Operations")
        mg_layout = QVBoxLayout(mat_grp)
        for label, act in matrix_ops:
            btn = QPushButton(label)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_la_op(a))
            mg_layout.addWidget(btn)
        mid_layout.addWidget(mat_grp)

        vec_grp = QGroupBox("Vector Operations")
        vg_layout = QVBoxLayout(vec_grp)
        for label, act in vector_ops:
            btn = QPushButton(label)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_la_op(a))
            vg_layout.addWidget(btn)
        mid_layout.addWidget(vec_grp)
        mid_layout.addStretch()

        outer.addWidget(mid, 1)

        # ── RIGHT: output ──────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        out_grp = QGroupBox("Result")
        og_layout = QVBoxLayout(out_grp)
        self.la_output = QTextBrowser()
        self.la_output.setMaximumHeight(60)
        self.la_output.setStyleSheet("""
            background-color: #242933;
            border: 1px solid #2e3440;
            border-radius: 8px;
            color: #a3be8c;
            font-family: 'Consolas', monospace;
            font-size: 13px;
        """)
        og_layout.addWidget(self.la_output)
        self.la_result_latex = LatexCanvas(height=130)
        og_layout.addWidget(self.la_result_latex)
        og_layout.addWidget(self._copy_latex_btn(self.la_result_latex), alignment=Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(out_grp)
        outer.addWidget(right, 2)

    # ── Linear Algebra execution ───────────────────────────────────────
    def _parse_matrix(self, text):
        """Parse a matrix from text.  Rows separated by ';', cols by spaces or commas."""
        rows = [r.strip() for r in text.strip().replace('\n', ';').split(';') if r.strip()]
        data = []
        for row in rows:
            cols = [c for c in row.replace(',', ' ').split() if c]
            data.append([sympy.sympify(c) for c in cols])
        return sympy.Matrix(data)

    def _parse_vector(self, text):
        """Parse a vector from a single line (space or comma separated)."""
        parts = [c for c in text.strip().replace(',', ' ').split() if c]
        return sympy.Matrix([sympy.sympify(p) for p in parts])

    def _la_render(self, label_html, latex_str):
        self.la_output.setHtml(label_html)
        self.la_result_latex.render(latex_str)

    def execute_la_op(self, action):
        try:
            if action in ("det_a", "inv_a", "tra_a", "eig_a", "rank_a", "rref_a"):
                A = self._parse_matrix(self.la_mat_a.toPlainText())

                if action == "det_a":
                    result = A.det()
                    self._la_render("<b>det(A)</b>", r"\det(A) = " + sympy.latex(result))

                elif action == "inv_a":
                    result = A.inv()
                    self._la_render("<b>A⁻¹</b>", r"A^{-1} = " + sympy.latex(result))

                elif action == "tra_a":
                    result = A.T
                    self._la_render("<b>Aᵀ</b>", r"A^T = " + sympy.latex(result))

                elif action == "eig_a":
                    evecs = A.eigenvects()
                    html = "<b>Eigenvalues &amp; vectors</b>"
                    self.la_output.setHtml(html)
                    parts = [
                        r"\lambda_{" + str(i+1) + r"} = " + sympy.latex(val)
                        for i, (val, _, _) in enumerate(evecs)
                    ]
                    self.la_result_latex.render(r",\quad ".join(parts))

                elif action == "rank_a":
                    result = A.rank()
                    self._la_render("<b>rank(A)</b>", r"\mathrm{rank}(A) = " + sympy.latex(result))

                elif action == "rref_a":
                    rref_mat, pivots = A.rref()
                    self._la_render(
                        f"<b>RREF</b> · pivots: {list(pivots)}",
                        sympy.latex(rref_mat)
                    )

            elif action in ("mat_mul", "mat_add"):
                A = self._parse_matrix(self.la_mat_a.toPlainText())
                B = self._parse_matrix(self.la_mat_b.toPlainText())
                if action == "mat_mul":
                    result = A * B
                    self._la_render("<b>A × B</b>", r"A \times B = " + sympy.latex(result))
                else:
                    result = A + B
                    self._la_render("<b>A + B</b>", r"A + B = " + sympy.latex(result))

            else:  # vector ops
                u = self._parse_vector(self.la_vec_u.text())
                v = self._parse_vector(self.la_vec_v.text())

                if action == "dot_uv":
                    result = u.dot(v)
                    self._la_render("<b>u · v</b>", r"\mathbf{u} \cdot \mathbf{v} = " + sympy.latex(result))

                elif action == "cross_uv":
                    result = u.cross(v)
                    self._la_render("<b>u × v</b>", r"\mathbf{u} \times \mathbf{v} = " + sympy.latex(result.T))

                elif action == "norm_u":
                    result = sympy.sqrt(u.dot(u))
                    self._la_render("<b>|u|</b>", r"|\mathbf{u}| = " + sympy.latex(result))

                elif action == "angle_uv":
                    cos_theta = u.dot(v) / (sympy.sqrt(u.dot(u)) * sympy.sqrt(v.dot(v)))
                    angle_rad = sympy.acos(sympy.simplify(cos_theta))
                    self._la_render(
                        f"<b>Angle (°):</b> {sympy.N(angle_rad * 180 / sympy.pi, 5)}",
                        r"\theta = " + sympy.latex(sympy.simplify(angle_rad))
                    )

                elif action == "vec_add":
                    result = u + v
                    self._la_render("<b>u + v</b>", r"\mathbf{u} + \mathbf{v} = " + sympy.latex(result.T))

                elif action == "proj_uv":
                    proj = (u.dot(v) / v.dot(v)) * v
                    self._la_render(
                        "<b>proj_v(u)</b>",
                        r"\mathrm{proj}_{\mathbf{v}}(\mathbf{u}) = " + sympy.latex(proj.T)
                    )

        except Exception as e:
            self.la_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {str(e)}")
            self.la_result_latex.render("")


    def _preview_sym_input(self, text):
        try:
            x = sympy.Symbol('x')
            expr = sympy.sympify(text.replace("=", "-(") + ")" if "=" in text else text)
            self.sym_input_latex.render(sympy.latex(expr))
        except Exception:
            self.sym_input_latex.render("")

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
        self._add_to_global_history("Calculator", "evaluate", calculation, f"= {result}")

    def history_item_clicked(self, item):
        result_val = item.data(Qt.ItemDataRole.UserRole)
        if result_val and result_val != "Error":
            self.current_input = result_val
            self.new_entry_started = True
            self.update_displays()

    def clear_history(self):
        self.history_list.clear()

    # Dedicated Symbolic Solver operations
    def _parse_ode(self, text):
        """Convert user ODE notation to a sympy Eq ready for dsolve.
        Supports y', y'', y (function of x).
        Example inputs:
          y'' + y = 0
          y' = y
          y'' - 3*y' + 2*y = 0
        """
        x = sympy.Symbol('x')
        y = sympy.Function('y')

        # Replace y'' with y(x).diff(x,2) and y' with y(x).diff(x)
        text = text.replace("y''", "y(x).diff(x,2)").replace("y'", "y(x).diff(x)")
        # Replace bare y (not followed by '(' to avoid touching y(x)) with y(x)
        import re
        text = re.sub(r'\by\b(?!\()', 'y(x)', text)

        if '=' in text:
            lhs_str, rhs_str = text.split('=', 1)
            lhs = sympy.sympify(lhs_str.strip(), locals={'x': x, 'y': y})
            rhs = sympy.sympify(rhs_str.strip(), locals={'x': x, 'y': y})
            return sympy.Eq(lhs, rhs), x, y
        else:
            expr = sympy.sympify(text.strip(), locals={'x': x, 'y': y})
            return sympy.Eq(expr, 0), x, y

    def execute_symbolic_op(self, action):
        func_str = self.f_x_input.text().strip()
        if not func_str:
            self.sym_output.setText("Error: empty input.")
            return

        def _set(label, latex_str):
            self.sym_output.setHtml(f"<b>{label}</b>")
            self.sym_result_latex.render(latex_str)
            self._add_to_global_history("Symbolic Solver", action, func_str, label)

        try:
            if action == "solve_ode":
                try:
                    ode_eq, x, y = self._parse_ode(func_str)
                    sol = sympy.dsolve(ode_eq, y(x))
                    _set("ODE solution", sympy.latex(sol))
                except Exception as e:
                    self.sym_output.setHtml(
                        f"<b>ODE failed:</b> {str(e)}<br>"
                        f"<i>e.g. y'' + y = 0</i>"
                    )
                    self.sym_result_latex.render("")
                return

            if "," in func_str:
                eqs_strs = func_str.split(",")
                eqs, syms = [], set()
                for eq_str in eqs_strs:
                    eq_str = eq_str.strip()
                    if not eq_str:
                        continue
                    if "=" in eq_str:
                        p = eq_str.split("=")
                        eq = sympy.sympify(p[0]) - sympy.sympify(p[1])
                    else:
                        eq = sympy.sympify(eq_str)
                    eqs.append(eq)
                    syms.update(eq.free_symbols)
                syms = sorted(list(syms), key=lambda s: s.name)
                if action == "solve_eq":
                    sol = sympy.solve(eqs, syms)
                    if isinstance(sol, dict):
                        latex_str = r",\quad ".join(
                            f"{sympy.latex(k)} = {sympy.latex(v)}" for k, v in sol.items()
                        )
                    else:
                        latex_str = sympy.latex(sol)
                    _set("System solution", latex_str)
                else:
                    raise ValueError("Calculus ops not supported on systems.")
                return

            x = sympy.Symbol('x')
            if "=" in func_str:
                p = func_str.split("=")
                expr = sympy.sympify(p[0]) - sympy.sympify(p[1])
            else:
                expr = sympy.sympify(func_str)

            if action == "solve_eq":
                roots = sympy.solve(expr, x)
                if not roots:
                    _set("No analytical roots found.", "")
                else:
                    latex_str = r",\quad ".join(
                        f"x_{{{i+1}}} = {sympy.latex(r)}" for i, r in enumerate(roots)
                    )
                    _set("Roots", latex_str)

            elif action == "derive_eq":
                res = sympy.diff(expr, x)
                _set("Derivative", r"f'(x) = " + sympy.latex(res))

            elif action == "integrate_eq":
                res = sympy.integrate(expr, x)
                _set("Integral", sympy.latex(res) + r" + C")

            elif action == "simplify_eq":
                res = sympy.simplify(expr)
                _set("Simplified", sympy.latex(res))

            elif action == "limit_0":
                res = sympy.limit(expr, x, 0)
                _set("Limit", r"\lim_{x \to 0} f(x) = " + sympy.latex(res))

            elif action == "taylor_eq":
                res = sympy.series(expr, x, 0, 5)
                _set("Taylor series", sympy.latex(res))

            elif action == "expand_poly":
                res = sympy.expand(expr)
                _set("Expanded", sympy.latex(res))

            elif action == "factor_poly":
                res = sympy.factor(expr)
                _set("Factored", sympy.latex(res))

            elif action == "apart_poly":
                res = sympy.apart(expr, x)
                _set("Partial fractions", sympy.latex(res))

            elif action == "collect_poly":
                res = sympy.collect(sympy.expand(expr), x)
                _set("Collected", sympy.latex(res))

            elif action == "trig_simp":
                res = sympy.trigsimp(expr)
                _set("Trig simplified", sympy.latex(res))

            elif action == "expand_trig":
                res = sympy.expand_trig(expr)
                _set("Expanded trig", sympy.latex(res))

            elif action == "rewrite_exp":
                res = sympy.simplify(expr.rewrite(sympy.exp))
                _set("In terms of exp", sympy.latex(res))

            elif action == "rewrite_cos":
                res = sympy.simplify(expr.rewrite(sympy.cos))
                _set("In terms of cos/sin", sympy.latex(res))

            elif action == "expand_log":
                res = sympy.expand_log(expr, force=True)
                _set("Expanded log", sympy.latex(res))

            elif action == "combine_log":
                res = sympy.logcombine(expr, force=True)
                _set("Combined logs", sympy.latex(res))

            elif action == "eval_log":
                try:
                    b = sympy.sympify(self.log_base_input.text())
                except Exception:
                    b = sympy.Integer(10)
                res = sympy.simplify(sympy.log(expr) / sympy.log(b))
                _set(f"log base {b}", r"\log_{" + sympy.latex(b) + r"} f(x) = " + sympy.latex(res))

        except Exception as e:
            self.sym_output.setText(f"Error: {str(e)}")
            self.sym_result_latex.render("")

    def _eval_expr(self, expr, x_vals):
        """Vectorized evaluation of a sympy expression over a numpy x array."""
        x = sympy.Symbol('x')
        f = sympy.lambdify(x, expr, modules=['numpy'])
        with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
            raw = f(x_vals)
        raw_arr = np.asarray(raw)
        # broadcast scalar (constant functions) to full length
        if raw_arr.ndim == 0:
            raw_arr = np.full(x_vals.shape, float(raw_arr.real if hasattr(raw_arr, 'real') else raw_arr))
            return raw_arr
        if raw_arr.shape != x_vals.shape:
            return np.full(x_vals.shape, np.nan)
        try:
            comp = raw_arr.astype(complex)
            result = np.where(np.abs(comp.imag) < 1e-9 * (1 + np.abs(comp.real)),
                              comp.real, np.nan).astype(float)
        except Exception:
            try:
                result = raw_arr.astype(float)
            except Exception:
                return np.full(x_vals.shape, np.nan)
        result[~np.isfinite(result)] = np.nan
        return result

    def _reset_graph_view(self):
        self.x_min_input.setText("-10")
        self.x_max_input.setText("10")
        self.y_min_input.setText("-10")
        self.y_max_input.setText("10")
        self.plot_function()

    def _clear_graph(self):
        self.plot_functions_input.clear()
        self.ax.clear()
        self.ax.set_facecolor('#242933')
        self.ax.tick_params(colors='#eceff4')
        for sp in self.ax.spines.values():
            sp.set_edgecolor('#4c566a')
        self.ax.grid(color='#2e3440', linestyle='--', alpha=0.6)
        self.ax.axhline(0, color='#4c566a', linewidth=1.0)
        self.ax.axvline(0, color='#4c566a', linewidth=1.0)
        self.canvas.draw()
        self.intercepts_output.setHtml('')

    def _setup_graph_interaction(self):
        """Attach pan (left-drag) and zoom (scroll wheel) to the main graph canvas."""
        self._graph_pan_start = None
        self._graph_pan_limits = None

        def _sync_range_inputs():
            xl = self.ax.get_xlim()
            yl = self.ax.get_ylim()
            self.x_min_input.setText(f"{xl[0]:.4g}")
            self.x_max_input.setText(f"{xl[1]:.4g}")
            self.y_min_input.setText(f"{yl[0]:.4g}")
            self.y_max_input.setText(f"{yl[1]:.4g}")

        def on_press(event):
            if event.button == 1 and event.inaxes == self.ax:
                self._graph_pan_start = (event.x, event.y)
                self._graph_pan_limits = (list(self.ax.get_xlim()), list(self.ax.get_ylim()))
                self.canvas.setCursor(Qt.CursorShape.ClosedHandCursor)

        def on_motion(event):
            if self._graph_pan_start is None:
                return
            px0, py0 = self._graph_pan_start
            xlim0, ylim0 = self._graph_pan_limits
            bbox = self.ax.get_window_extent()
            if bbox.width == 0 or bbox.height == 0:
                return
            dx = -(event.x - px0) * (xlim0[1] - xlim0[0]) / bbox.width
            dy = -(event.y - py0) * (ylim0[1] - ylim0[0]) / bbox.height
            self.ax.set_xlim(xlim0[0] + dx, xlim0[1] + dx)
            self.ax.set_ylim(ylim0[0] + dy, ylim0[1] + dy)
            self.canvas.draw_idle()

        def on_release(event):
            if self._graph_pan_start is not None:
                self._graph_pan_start = None
                self._graph_pan_limits = None
                _sync_range_inputs()
            self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)

        def on_scroll(event):
            if event.inaxes != self.ax or event.xdata is None:
                return
            factor = 0.85 if event.button == 'up' else 1.0 / 0.85
            cx, cy = event.xdata, event.ydata
            self.ax.set_xlim([cx + (x - cx) * factor for x in self.ax.get_xlim()])
            self.ax.set_ylim([cy + (y - cy) * factor for y in self.ax.get_ylim()])
            _sync_range_inputs()
            self.canvas.draw_idle()

        def on_enter_axes(event):
            if event.inaxes == self.ax:
                self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)

        def on_leave_axes(event):
            if self._graph_pan_start is None:
                self.canvas.setCursor(Qt.CursorShape.ArrowCursor)

        self.canvas.mpl_connect('button_press_event', on_press)
        self.canvas.mpl_connect('motion_notify_event', on_motion)
        self.canvas.mpl_connect('button_release_event', on_release)
        self.canvas.mpl_connect('scroll_event', on_scroll)
        self.canvas.mpl_connect('axes_enter_event', on_enter_axes)
        self.canvas.mpl_connect('axes_leave_event', on_leave_axes)

    def _parse_plot_entry(self, entry):
        """Parse a plot entry line. Returns (kind, data, label) or None.
        kind: 'explicit' | 'implicit' | 'vertical'
        """
        x, y = sympy.Symbol('x'), sympy.Symbol('y')
        entry = entry.strip()
        if not entry or entry.startswith('#'):
            return None
        try:
            if '=' in entry:
                lhs_str, rhs_str = entry.split('=', 1)
                lhs = sympy.sympify(lhs_str.strip())
                rhs = sympy.sympify(rhs_str.strip())
                implicit_expr = lhs - rhs
                if lhs == y and y not in rhs.free_symbols:
                    return ('explicit', rhs, entry)
                if lhs == x and y not in implicit_expr.free_symbols and x not in rhs.free_symbols:
                    try:
                        return ('vertical', float(rhs.evalf()), entry)
                    except Exception:
                        pass
                return ('implicit', implicit_expr, entry)
            else:
                expr = sympy.sympify(entry)
                if y in expr.free_symbols:
                    return ('implicit', expr, entry)
                return ('explicit', expr, entry)
        except Exception:
            return None

    def plot_function(self):
        raw = self.plot_functions_input.toPlainText()
        entries = [l.strip() for l in raw.splitlines() if l.strip() and not l.strip().startswith('#')]
        if not entries:
            return

        x_sym = sympy.Symbol('x')
        y_sym = sympy.Symbol('y')
        try:
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
        except ValueError:
            x_min, x_max = -10.0, 10.0
        try:
            y_min = float(self.y_min_input.text())
            y_max = float(self.y_max_input.text())
        except ValueError:
            y_min, y_max = -10.0, 10.0

        x_vals = np.linspace(x_min, x_max, 800)
        COLORS = ['#88c0d0', '#a3be8c', '#bf616a', '#ebcb8b', '#b48ead', '#d08770']

        self.ax.clear()
        self.ax.set_facecolor('#242933')
        self.ax.tick_params(colors='#eceff4')
        for sp in self.ax.spines.values():
            sp.set_edgecolor('#4c566a')
        self.ax.grid(color='#2e3440', linestyle='--', alpha=0.6)
        self.ax.axhline(0, color='#4c566a', linewidth=1.0)
        self.ax.axvline(0, color='#4c566a', linewidth=1.0)

        explicit_list = []   # (label, expr, color, y_arr)
        implicit_list = []   # (label, expr, color)
        intercept_parts = []

        for i, entry in enumerate(entries):
            parsed = self._parse_plot_entry(entry)
            if parsed is None:
                intercept_parts.append(f'<span style="color:#bf616a">Cannot parse: {entry}</span>')
                continue
            color = COLORS[i % len(COLORS)]
            kind, data, label = parsed

            if kind == 'explicit':
                expr = data
                # ── evaluate ─────────────────────────────────────────────
                try:
                    y_arr = self._eval_expr(expr, x_vals)
                except Exception as e:
                    intercept_parts.append(f'<span style="color:#bf616a">Eval error [{label}]: {e}</span>')
                    continue

                self.ax.plot(x_vals, y_arr, color=color, linewidth=2.5,
                             label=label, solid_capstyle='round')
                explicit_list.append((label, expr, color, y_arr))

                # ── x-intercepts ──────────────────────────────────────────
                x_roots = []
                try:
                    sym_roots = sympy.solve(expr, x_sym)
                    for r in sym_roots:
                        try:
                            if r.is_real:
                                rx = float(r)
                                if x_min <= rx <= x_max:
                                    x_roots.append(rx)
                        except Exception:
                            pass
                except Exception:
                    pass
                # numerical sign-change fallback
                if not x_roots:
                    mask = np.isfinite(y_arr)
                    if mask.sum() > 1:
                        yf, xf = y_arr[mask], x_vals[mask]
                        for si in np.where(np.diff(np.sign(yf)))[0]:
                            d = yf[si+1] - yf[si]
                            if d != 0:
                                x_roots.append(xf[si] - yf[si] * (xf[si+1] - xf[si]) / d)

                for rx in x_roots:
                    self.ax.plot(rx, 0, 'o', color=color, markersize=9, zorder=6,
                                 markeredgecolor='#eceff4', markeredgewidth=1)
                    self.ax.annotate(f'({rx:.4g}, 0)', (rx, 0),
                                     textcoords='offset points', xytext=(5, 8),
                                     color='#eceff4', fontsize=8,
                                     bbox=dict(boxstyle='round,pad=0.2', fc='#2e3440', alpha=0.85, ec='none'))
                if x_roots:
                    intercept_parts.append(
                        f'<span style="color:{color}">●</span> <b>{label}</b>'
                        f'  x-int: ' + ', '.join(f'({rx:.4g}, 0)' for rx in x_roots)
                    )

                # ── y-intercept ───────────────────────────────────────────
                try:
                    y0c = complex(expr.subs(x_sym, 0).evalf())
                    if abs(y0c.imag) < 1e-10 and np.isfinite(y0c.real):
                        ry = y0c.real
                        self.ax.plot(0, ry, 's', color=color, markersize=9, zorder=6,
                                     markeredgecolor='#eceff4', markeredgewidth=1)
                        self.ax.annotate(f'(0, {ry:.4g})', (0, ry),
                                         textcoords='offset points', xytext=(5, 8),
                                         color='#eceff4', fontsize=8,
                                         bbox=dict(boxstyle='round,pad=0.2', fc='#2e3440', alpha=0.85, ec='none'))
                        intercept_parts.append(
                            f'<span style="color:{color}">■</span> <b>{label}</b>'
                            f'  y-int: (0, {ry:.4g})'
                        )
                except Exception:
                    pass

            elif kind == 'implicit':
                expr = data
                try:
                    mx = np.linspace(x_min, x_max, 500)
                    my = np.linspace(y_min, y_max, 500)
                    X, Y = np.meshgrid(mx, my)
                    fn = sympy.lambdify((x_sym, y_sym), expr, modules=['numpy'])
                    with np.errstate(divide='ignore', invalid='ignore'):
                        Z = np.asarray(fn(X, Y), dtype=float)
                    if Z.shape != X.shape:
                        Z = np.broadcast_to(Z, X.shape).copy()
                    Z[~np.isfinite(Z)] = np.nan
                    self.ax.contour(X, Y, Z, levels=[0], colors=[color], linewidths=[2.5])
                    self.ax.plot([], [], color=color, linewidth=2.5, label=label)
                    implicit_list.append((label, expr, color))

                    def _sign_roots_1d(h, domain):
                        """Find sign-change roots in a 1-D array h over domain."""
                        roots = []
                        h = np.asarray(h, dtype=float)
                        h[~np.isfinite(h)] = np.nan
                        mask = np.isfinite(h)
                        if mask.sum() < 2:
                            return roots
                        hf, xf = h[mask], domain[mask]
                        for si in np.where(np.diff(np.sign(hf)))[0]:
                            d = hf[si+1] - hf[si]
                            if d != 0:
                                roots.append(float(xf[si] - hf[si] * (xf[si+1] - xf[si]) / d))
                        return roots

                    # ── x-intercepts of implicit curve: F(x, 0) = 0 ────────
                    xi_found = []
                    try:
                        for r in sympy.solve(expr.subs(y_sym, 0), x_sym):
                            try:
                                if r.is_real and x_min <= float(r) <= x_max:
                                    xi_found.append(float(r))
                            except Exception:
                                pass
                    except Exception:
                        pass
                    if not xi_found:
                        fn_x = sympy.lambdify(x_sym, expr.subs(y_sym, 0), modules=['numpy'])
                        with np.errstate(divide='ignore', invalid='ignore'):
                            xi_found = _sign_roots_1d(np.asarray(fn_x(x_vals), dtype=float), x_vals)
                    for rx in xi_found:
                        self.ax.plot(rx, 0, 'o', color=color, markersize=9, zorder=6,
                                     markeredgecolor='#eceff4', markeredgewidth=1)
                        self.ax.annotate(f'({rx:.4g}, 0)', (rx, 0),
                                         textcoords='offset points', xytext=(5, 8),
                                         color='#eceff4', fontsize=8,
                                         bbox=dict(boxstyle='round,pad=0.2', fc='#2e3440', alpha=0.85, ec='none'))
                    if xi_found:
                        intercept_parts.append(
                            f'<span style="color:{color}">●</span> <b>{label}</b>'
                            f'  x-int: ' + ', '.join(f'({rx:.4g}, 0)' for rx in xi_found)
                        )

                    # ── y-intercepts of implicit curve: F(0, y) = 0 ─────────
                    yi_found = []
                    try:
                        for r in sympy.solve(expr.subs(x_sym, 0), y_sym):
                            try:
                                if r.is_real and y_min <= float(r) <= y_max:
                                    yi_found.append(float(r))
                            except Exception:
                                pass
                    except Exception:
                        pass
                    if not yi_found:
                        fn_y = sympy.lambdify(y_sym, expr.subs(x_sym, 0), modules=['numpy'])
                        y_mesh = np.linspace(y_min, y_max, 800)
                        with np.errstate(divide='ignore', invalid='ignore'):
                            yi_found = _sign_roots_1d(np.asarray(fn_y(y_mesh), dtype=float), y_mesh)
                    for ry in yi_found:
                        self.ax.plot(0, ry, 's', color=color, markersize=9, zorder=6,
                                     markeredgecolor='#eceff4', markeredgewidth=1)
                        self.ax.annotate(f'(0, {ry:.4g})', (0, ry),
                                         textcoords='offset points', xytext=(5, 8),
                                         color='#eceff4', fontsize=8,
                                         bbox=dict(boxstyle='round,pad=0.2', fc='#2e3440', alpha=0.85, ec='none'))
                    if yi_found:
                        intercept_parts.append(
                            f'<span style="color:{color}">■</span> <b>{label}</b>'
                            f'  y-int: ' + ', '.join(f'(0, {ry:.4g})' for ry in yi_found)
                        )

                except Exception as e:
                    intercept_parts.append(f'<span style="color:#bf616a">Error [{label}]: {e}</span>')

            elif kind == 'vertical':
                self.ax.axvline(data, color=color, linewidth=2.5, label=label)

        # ── intersections between explicit pairs ──────────────────────────
        for a in range(len(explicit_list)):
            for b in range(a + 1, len(explicit_list)):
                lbl_a, expr_a, _, y_a = explicit_list[a]
                lbl_b, expr_b, _, y_b = explicit_list[b]
                pts = []

                try:
                    sym_pts = sympy.solve(expr_a - expr_b, x_sym)
                    for p in sym_pts:
                        try:
                            if p.is_real:
                                px = float(p)
                                if x_min <= px <= x_max:
                                    py = float(expr_a.subs(x_sym, p).evalf())
                                    if np.isfinite(py):
                                        pts.append((px, py))
                        except Exception:
                            pass
                except Exception:
                    pass

                # numerical fallback
                if not pts:
                    diff = y_a - y_b
                    mask = np.isfinite(diff)
                    if mask.sum() > 1:
                        df, xf, yaf = diff[mask], x_vals[mask], y_a[mask]
                        for si in np.where(np.diff(np.sign(df)))[0]:
                            d = df[si+1] - df[si]
                            if d != 0:
                                px = xf[si] - df[si] * (xf[si+1] - xf[si]) / d
                                py = float((yaf[si] + yaf[si+1]) / 2)
                                if np.isfinite(px) and np.isfinite(py):
                                    pts.append((px, py))

                for px, py in pts:
                    self.ax.plot(px, py, 'D', color='#ffffff', markersize=9, zorder=7,
                                 markeredgecolor='#4c566a', markeredgewidth=1)
                    self.ax.annotate(f'({px:.4g}, {py:.4g})', (px, py),
                                     textcoords='offset points', xytext=(5, 8),
                                     color='#eceff4', fontsize=8,
                                     bbox=dict(boxstyle='round,pad=0.2', fc='#2e3440', alpha=0.85, ec='none'))
                if pts:
                    intercept_parts.append(
                        f'<b>∩ {lbl_a} & {lbl_b}:</b> ' +
                        ', '.join(f'({px:.4g}, {py:.4g})' for px, py in pts)
                    )

        # ── intersections: explicit curve ∩ implicit curve ────────────────
        for lbl_e, expr_e, col_e, y_e in explicit_list:
            for lbl_i, expr_i, col_i in implicit_list:
                pts = []
                try:
                    fn_i = sympy.lambdify((x_sym, y_sym), expr_i, modules=['numpy'])
                    with np.errstate(divide='ignore', invalid='ignore'):
                        h = np.asarray(fn_i(x_vals, y_e), dtype=float)
                    h[~np.isfinite(h)] = np.nan
                    mask = np.isfinite(h)
                    if mask.sum() > 1:
                        hf, xf, yef = h[mask], x_vals[mask], y_e[mask]
                        for si in np.where(np.diff(np.sign(hf)))[0]:
                            d = hf[si+1] - hf[si]
                            if d != 0:
                                px = xf[si] - hf[si] * (xf[si+1] - xf[si]) / d
                                py = float((yef[si] + yef[si+1]) / 2)
                                if np.isfinite(px) and np.isfinite(py):
                                    pts.append((px, py))
                except Exception:
                    pass
                for px, py in pts:
                    self.ax.plot(px, py, 'D', color='#ffffff', markersize=9, zorder=7,
                                 markeredgecolor='#4c566a', markeredgewidth=1)
                    self.ax.annotate(f'({px:.4g}, {py:.4g})', (px, py),
                                     textcoords='offset points', xytext=(5, 8),
                                     color='#eceff4', fontsize=8,
                                     bbox=dict(boxstyle='round,pad=0.2', fc='#2e3440', alpha=0.85, ec='none'))
                if pts:
                    intercept_parts.append(
                        f'<b>∩ {lbl_e} & {lbl_i}:</b> ' +
                        ', '.join(f'({px:.4g}, {py:.4g})' for px, py in pts)
                    )

        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.legend(facecolor='#1e222b', edgecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
        self.canvas.draw()

        self.intercepts_output.setHtml(
            '<br>'.join(intercept_parts) if intercept_parts
            else '<i style="color:#4c566a">No intercepts found in current view.</i>'
        )


    # ── Complex Numbers Tab ─────────────────────────────────────────────────
    def setup_complex_tab(self):
        cx_widget = QWidget()
        self.tabs.addTab(cx_widget, "Complex Numbers")

        outer = QHBoxLayout(cx_widget)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        # ── LEFT: inputs + operations ────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)

        field_style = """
            background-color: #242933;
            border: 1px solid #3b4252;
            border-radius: 8px;
            color: #eceff4;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            padding: 6px;
        """

        # Input z1 / z2 (rectangular or polar)
        grp_z = QGroupBox("Complex Numbers  (use 'I' for imaginary unit — e.g.  3 + 4*I)")
        gz = QVBoxLayout(grp_z)
        self.cx_z1 = QLineEdit("3 + 4*I")
        self.cx_z1.setPlaceholderText("z₁  e.g.  3 + 4*I   or   2*exp(I*pi/3)")
        self.cx_z1.setStyleSheet(field_style)
        self.cx_z2 = QLineEdit("1 - 2*I")
        self.cx_z2.setPlaceholderText("z₂  e.g.  1 - 2*I")
        self.cx_z2.setStyleSheet(field_style)
        gz.addWidget(QLabel("z₁:"))
        gz.addWidget(self.cx_z1)
        gz.addWidget(QLabel("z₂:"))
        gz.addWidget(self.cx_z2)
        left_layout.addWidget(grp_z)

        # Polar -> Rect helper
        grp_polar = QGroupBox("Polar Input Helper  r e^(iθ)")
        gp = QGridLayout(grp_polar)
        gp.setSpacing(6)
        gp.addWidget(QLabel("r:"), 0, 0)
        self.cx_r = QLineEdit("5")
        self.cx_r.setStyleSheet(field_style)
        gp.addWidget(self.cx_r, 0, 1)
        gp.addWidget(QLabel("θ (rad):"), 1, 0)
        self.cx_theta = QLineEdit("pi/4")
        self.cx_theta.setStyleSheet(field_style)
        gp.addWidget(self.cx_theta, 1, 1)
        conv_btn = QPushButton("Polar → z₁")
        conv_btn.setStyleSheet("background-color: #3b4252; color: #88c0d0; font-weight: bold;")
        conv_btn.clicked.connect(self._polar_to_z1)
        gp.addWidget(conv_btn, 2, 0, 1, 2)
        left_layout.addWidget(grp_polar)

        # Operation buttons
        ops_grp = QGroupBox("Operations")
        og = QGridLayout(ops_grp)
        og.setSpacing(8)
        btn_style = "font-size: 12px; font-weight: bold; background-color: #2f384c; color: #a3be8c; min-height: 36px;"
        cx_ops = [
            ("z₁ + z₂",       "cx_add"),
            ("z₁ − z₂",       "cx_sub"),
            ("z₁ × z₂",       "cx_mul"),
            ("z₁ / z₂",       "cx_div"),
            ("|z₁| (modulus)","cx_mod"),
            ("arg(z₁) (angle)","cx_arg"),
            ("conj(z₁)",      "cx_conj"),
            ("z₁ⁿ (De Moivre)","cx_pow"),
            ("Polar Form z₁",  "cx_polar"),
            ("Euler e^(iθ)",   "cx_euler"),
            ("Re, Im parts",   "cx_parts"),
            ("z₁² (square)",   "cx_sq"),
        ]
        for idx, (label, act) in enumerate(cx_ops):
            btn = QPushButton(label)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_complex_op(a))
            og.addWidget(btn, idx // 2, idx % 2)
        left_layout.addWidget(ops_grp)

        # Power n input (for De Moivre)
        grp_n = QGroupBox("Power n  (for zⁿ)")
        gn = QHBoxLayout(grp_n)
        self.cx_n = QLineEdit("3")
        self.cx_n.setStyleSheet(field_style)
        gn.addWidget(self.cx_n)
        left_layout.addWidget(grp_n)

        left_layout.addStretch()
        outer.addWidget(left, 2)

        # ── RIGHT: output + Argand plane ─────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        out_grp = QGroupBox("Result")
        ogl = QVBoxLayout(out_grp)
        self.cx_output = QTextBrowser()
        self.cx_output.setMaximumHeight(60)
        self.cx_output.setStyleSheet("""
            background-color: #242933;
            border: 1px solid #2e3440;
            border-radius: 8px;
            color: #a3be8c;
            font-family: 'Consolas', monospace;
            font-size: 13px;
        """)
        ogl.addWidget(self.cx_output)
        self.cx_result_latex = LatexCanvas(height=120)
        ogl.addWidget(self.cx_result_latex)
        ogl.addWidget(self._copy_latex_btn(self.cx_result_latex), alignment=Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(out_grp)

        # Argand plane (canvas)
        argand_grp = QGroupBox("Argand Plane")
        agl = QVBoxLayout(argand_grp)
        self.cx_canvas = FigureCanvas(Figure(facecolor='#1e222b', figsize=(5, 4)))
        self.cx_ax = self.cx_canvas.figure.subplots()
        self._init_argand_axes()
        agl.addWidget(self.cx_canvas)

        plot_cx_btn = QPushButton("Plot z₁ and z₂ on Argand Plane")
        plot_cx_btn.setStyleSheet("background-color: #88c0d0; color: #2e3440; font-weight: bold; min-height: 34px;")
        plot_cx_btn.clicked.connect(self._plot_argand)
        agl.addWidget(plot_cx_btn)
        right_layout.addWidget(argand_grp)

        outer.addWidget(right, 3)

    def _init_argand_axes(self):
        ax = self.cx_ax
        ax.set_facecolor('#242933')
        ax.tick_params(colors='#eceff4')
        ax.grid(color='#2e3440', linestyle='--')
        ax.axhline(0, color='#4c566a', linewidth=1.2)
        ax.axvline(0, color='#4c566a', linewidth=1.2)
        ax.set_xlabel('Re', color='#81a1c1')
        ax.set_ylabel('Im', color='#81a1c1')
        ax.set_title('Argand Plane', color='#eceff4')
        self.cx_canvas.draw()

    def _polar_to_z1(self):
        try:
            r = sympy.sympify(self.cx_r.text())
            theta = sympy.sympify(self.cx_theta.text())
            z = r * sympy.exp(sympy.I * theta)
            z_rect = sympy.simplify(z.rewrite(sympy.cos))
            self.cx_z1.setText(str(sympy.expand(sympy.nsimplify(z_rect))))
        except Exception as e:
            self.cx_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {e}")

    def _plot_argand(self):
        try:
            z1 = sympy.sympify(self.cx_z1.text())
            z2 = sympy.sympify(self.cx_z2.text())
            ax = self.cx_ax
            ax.clear()
            self._init_argand_axes()

            def _draw_point(ax, z, label, color):
                re = float(sympy.re(z))
                im = float(sympy.im(z))
                ax.annotate("", xy=(re, im), xytext=(0, 0),
                            arrowprops=dict(arrowstyle='->', color=color, lw=2))
                ax.plot(re, im, 'o', color=color)
                ax.annotate(f" {label} = {re:.3g}+{im:.3g}j", (re, im),
                            color='#eceff4', fontsize=9)

            _draw_point(ax, z1, 'z₁', '#88c0d0')
            _draw_point(ax, z2, 'z₂', '#a3be8c')
            self.cx_canvas.draw()
        except Exception as e:
            self.cx_output.setHtml(f"<b style='color:#bf616a'>Plot Error:</b> {e}")

    def execute_complex_op(self, action):
        def _cx_latex(z):
            z = sympy.simplify(z)
            re = sympy.nsimplify(sympy.re(z), rational=False)
            im = sympy.nsimplify(sympy.im(z), rational=False)
            return sympy.latex(re) + " + " + sympy.latex(im) + r"i"

        def _set(label, latex_str):
            self.cx_output.setHtml(f"<b>{label}</b>")
            self.cx_result_latex.render(latex_str)
            self._add_to_global_history("Complex Numbers", action,
                                        f"z₁={self.cx_z1.text()}, z₂={self.cx_z2.text()}", label)

        try:
            z1 = sympy.sympify(self.cx_z1.text())
            z2 = sympy.sympify(self.cx_z2.text())

            if action == "cx_add":
                _set("z₁ + z₂", r"z_1 + z_2 = " + _cx_latex(z1 + z2))
            elif action == "cx_sub":
                _set("z₁ − z₂", r"z_1 - z_2 = " + _cx_latex(z1 - z2))
            elif action == "cx_mul":
                _set("z₁ × z₂", r"z_1 \cdot z_2 = " + _cx_latex(z1 * z2))
            elif action == "cx_div":
                _set("z₁ / z₂", r"\frac{z_1}{z_2} = " + _cx_latex(z1 / z2))
            elif action == "cx_mod":
                r = sympy.Abs(z1)
                _set(f"|z₁| ≈ {float(r):.6g}", r"|z_1| = " + sympy.latex(sympy.nsimplify(r, rational=False)))
            elif action == "cx_arg":
                r = sympy.arg(z1)
                _set(
                    f"arg(z₁) ≈ {float(r):.4g} rad  ({float(r)*180/3.14159265:.4g}°)",
                    r"\arg(z_1) = " + sympy.latex(sympy.nsimplify(r, rational=False))
                )
            elif action == "cx_conj":
                _set("conj(z₁)", r"\overline{z_1} = " + _cx_latex(sympy.conjugate(z1)))
            elif action == "cx_pow":
                n = sympy.sympify(self.cx_n.text())
                r = z1 ** n
                mod = sympy.Abs(z1) ** n
                theta_n = n * sympy.arg(z1)
                _set(
                    f"z₁ⁿ  (n = {n})",
                    r"z_1^{" + sympy.latex(n) + r"} = " + _cx_latex(r)
                )
            elif action == "cx_polar":
                z1s = sympy.simplify(z1)
                r_val = sympy.nsimplify(sympy.Abs(z1s), rational=False)
                theta_val = sympy.nsimplify(sympy.arg(z1s), rational=False)
                _set(
                    "Polar form",
                    sympy.latex(r_val) + r" \, e^{i \cdot " + sympy.latex(theta_val) + r"}"
                )
            elif action == "cx_euler":
                theta = sympy.sympify(self.cx_theta.text())
                r_val = sympy.sympify(self.cx_r.text())
                expanded = sympy.simplify(sympy.expand((r_val * sympy.exp(sympy.I * theta)).rewrite(sympy.cos)))
                _set(
                    "Euler's formula",
                    sympy.latex(r_val) + r" e^{i " + sympy.latex(theta) + r"} = " + sympy.latex(expanded)
                )
            elif action == "cx_parts":
                re_v = sympy.nsimplify(sympy.re(z1))
                im_v = sympy.nsimplify(sympy.im(z1))
                _set(
                    "Re / Im parts",
                    r"\operatorname{Re}(z_1) = " + sympy.latex(re_v) +
                    r",\quad \operatorname{Im}(z_1) = " + sympy.latex(im_v)
                )
            elif action == "cx_sq":
                _set("z₁²", r"z_1^2 = " + _cx_latex(z1 ** 2))

        except Exception as e:
            self.cx_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {str(e)}")
            self.cx_result_latex.render("")


    def setup_calculus_tab(self):
        calc_widget = QWidget()
        self.tabs.addTab(calc_widget, "Calculus")

        outer = QHBoxLayout(calc_widget)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        field_style = (
            "background-color: #242933; border: 1px solid #3b4252; "
            "border-radius: 8px; color: #eceff4; "
            "font-family: 'Consolas', monospace; font-size: 14px; padding: 6px;"
        )

        # ── LEFT: inputs + operations + output ───────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)

        # Expression input
        grp_input = QGroupBox("Expression  f(x)")
        gi = QVBoxLayout(grp_input)
        gi.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("f(x) ="))
        self.calc_expr = QLineEdit("x**3 - 3*x**2 + 2*x")
        self.calc_expr.setStyleSheet(field_style)
        self.calc_expr.textChanged.connect(self._update_calc_input_preview)
        row1.addWidget(self.calc_expr)
        gi.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Variable:"))
        self.calc_var = QLineEdit("x")
        self.calc_var.setFixedWidth(44)
        self.calc_var.setStyleSheet(field_style)
        row2.addWidget(self.calc_var)
        row2.addSpacing(16)
        row2.addWidget(QLabel("Point x₀ ="))
        self.calc_point = QLineEdit("0")
        self.calc_point.setFixedWidth(64)
        self.calc_point.setStyleSheet(field_style)
        row2.addWidget(self.calc_point)
        row2.addSpacing(16)
        row2.addWidget(QLabel("Order n:"))
        self.calc_order = QLineEdit("2")
        self.calc_order.setFixedWidth(44)
        self.calc_order.setStyleSheet(field_style)
        row2.addWidget(self.calc_order)
        row2.addSpacing(16)
        row2.addWidget(QLabel("a:"))
        self.calc_a = QLineEdit("0")
        self.calc_a.setFixedWidth(52)
        self.calc_a.setStyleSheet(field_style)
        row2.addWidget(self.calc_a)
        row2.addWidget(QLabel("b:"))
        self.calc_b = QLineEdit("1")
        self.calc_b.setFixedWidth(52)
        self.calc_b.setStyleSheet(field_style)
        row2.addWidget(self.calc_b)
        row2.addStretch()
        gi.addLayout(row2)
        left_layout.addWidget(grp_input)

        # Operation buttons
        ops_grp = QGroupBox("Operations")
        og = QGridLayout(ops_grp)
        og.setSpacing(8)
        btn_style = (
            "font-size: 12px; font-weight: bold; "
            "background-color: #2f384c; color: #a3be8c; min-height: 36px;"
        )
        calc_ops = [
            ("d/dx  Derivative",      "derivative"),
            ("dⁿ/dxⁿ  nth Deriv.",    "nth_derivative"),
            ("f'(x₀)  Eval Deriv.",   "eval_derivative"),
            ("∫ dx  Indefinite",      "indefinite_integral"),
            ("∫ₐᵇ dx  Definite",      "definite_integral"),
            ("lim x→x₀",             "limit"),
            ("lim x→x₀⁺  (right)",   "limit_right"),
            ("lim x→x₀⁻  (left)",    "limit_left"),
            ("Taylor Series",          "taylor"),
            ("Critical Points",        "critical_points"),
            ("Partial Fractions",      "partial_fractions"),
            ("Simplify",               "simplify"),
        ]
        for idx, (lbl, act) in enumerate(calc_ops):
            btn = QPushButton(lbl)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_calculus_op(a))
            og.addWidget(btn, idx // 2, idx % 2)

        left_layout.addWidget(ops_grp)

        # Output — below buttons, same pattern as symbolic tab
        out_grp = QGroupBox("Result")
        ogl = QVBoxLayout(out_grp)
        self.calc_output = QTextBrowser()
        self.calc_output.setMaximumHeight(60)
        self.calc_output.setStyleSheet(
            "background-color: #242933; border: 1px solid #2e3440; "
            "border-radius: 8px; color: #a3be8c; "
            "font-family: 'Consolas', monospace; font-size: 13px;"
        )
        ogl.addWidget(self.calc_output)
        self.calc_result_latex = LatexCanvas(height=130)
        ogl.addWidget(self.calc_result_latex)
        ogl.addWidget(self._copy_latex_btn(self.calc_result_latex), alignment=Qt.AlignmentFlag.AlignRight)
        left_layout.addWidget(out_grp)

        outer.addWidget(left, 2)

        # ── RIGHT: input LaTeX preview ────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        in_grp = QGroupBox("Input Preview")
        ig = QVBoxLayout(in_grp)
        self.calc_input_latex = LatexCanvas(height=120)
        ig.addWidget(self.calc_input_latex)
        ig.addWidget(self._copy_latex_btn(self.calc_input_latex), alignment=Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(in_grp)
        right_layout.addStretch()

        outer.addWidget(right, 3)

        self._update_calc_input_preview()

    def _update_calc_input_preview(self):
        try:
            v = self.calc_var.text().strip() or 'x'
            expr = sympy.sympify(self.calc_expr.text())
            self.calc_input_latex.render(r"f(" + v + r") = " + sympy.latex(expr))
        except Exception:
            pass

    def execute_calculus_op(self, action):
        try:
            v = self.calc_var.text().strip() or 'x'
            x = sympy.Symbol(v)
            expr = sympy.sympify(self.calc_expr.text())

            def _show(header, latex_str):
                self.calc_output.setHtml(f"<b>{header}</b>")
                self.calc_result_latex.render(latex_str)
                self._add_to_global_history("Calculus", action, self.calc_expr.text(), header)

            if action == "derivative":
                res = sympy.diff(expr, x)
                _show("d/d" + v + "  f(" + v + ")",
                      r"\frac{d}{d" + v + r"}\bigl(" + sympy.latex(expr) + r"\bigr) = " + sympy.latex(res))

            elif action == "nth_derivative":
                n = int(sympy.sympify(self.calc_order.text()))
                res = sympy.diff(expr, x, n)
                _show(f"d^{n}/d{v}^{n}  f({v})",
                      r"\frac{d^{" + str(n) + r"}}{d" + v + r"^{" + str(n) + r"}}"
                      r"\bigl(" + sympy.latex(expr) + r"\bigr) = " + sympy.latex(res))

            elif action == "eval_derivative":
                x0 = sympy.sympify(self.calc_point.text())
                res = sympy.diff(expr, x).subs(x, x0)
                res = sympy.nsimplify(res, rational=False)
                num_str = ""
                try:
                    num_str = f"  ≈ {float(res.evalf()):.6g}"
                except Exception:
                    pass
                _show(f"f'({x0}){num_str}",
                      r"f'\!\left(" + sympy.latex(x0) + r"\right) = " + sympy.latex(res))

            elif action == "indefinite_integral":
                res = sympy.integrate(expr, x)
                _show("∫ f(" + v + ") d" + v,
                      r"\int " + sympy.latex(expr) + r"\, d" + v + r" = " + sympy.latex(res) + r" + C")

            elif action == "definite_integral":
                a = sympy.sympify(self.calc_a.text())
                b = sympy.sympify(self.calc_b.text())
                res = sympy.integrate(expr, (x, a, b))
                res = sympy.nsimplify(res, rational=False)
                num_str = ""
                try:
                    num_str = f"  ≈ {float(res.evalf()):.6g}"
                except Exception:
                    pass
                _show(f"∫ f({v}) d{v}  from {a} to {b}{num_str}",
                      r"\int_{" + sympy.latex(a) + r"}^{" + sympy.latex(b) + r"} "
                      + sympy.latex(expr) + r"\, d" + v + r" = " + sympy.latex(res))

            elif action in ("limit", "limit_right", "limit_left"):
                x0 = sympy.sympify(self.calc_point.text())
                if action == "limit":
                    res = sympy.limit(expr, x, x0)
                    arrow = r"\to"
                    lbl = f"lim {v}→{x0}"
                elif action == "limit_right":
                    res = sympy.limit(expr, x, x0, '+')
                    arrow = r"\to^{+}"
                    lbl = f"lim {v}→{x0}⁺"
                else:
                    res = sympy.limit(expr, x, x0, '-')
                    arrow = r"\to^{-}"
                    lbl = f"lim {v}→{x0}⁻"
                res = sympy.nsimplify(res, rational=False)
                num_str = ""
                try:
                    num_str = f"  ≈ {float(res.evalf()):.6g}"
                except Exception:
                    pass
                _show(lbl + num_str,
                      r"\lim_{" + v + arrow + sympy.latex(x0) + r"}"
                      r"\bigl(" + sympy.latex(expr) + r"\bigr) = " + sympy.latex(res))

            elif action == "taylor":
                n = int(sympy.sympify(self.calc_order.text()))
                x0 = sympy.sympify(self.calc_point.text())
                series = sympy.series(expr, x, x0, n + 1)
                poly = series.removeO()
                _show(f"Taylor series around {v}={x0}, order {n}",
                      sympy.latex(expr) + r" \approx " + sympy.latex(sympy.expand(poly))
                      + r" + O\!\left((" + v + r"-" + sympy.latex(x0) + r")^{" + str(n + 1) + r"}\right)")

            elif action == "critical_points":
                deriv = sympy.diff(expr, x)
                crit = sympy.solve(deriv, x)
                second = sympy.diff(expr, x, 2)
                rows = []
                for p in crit:
                    try:
                        pc = complex(p.evalf())
                    except Exception:
                        continue
                    if abs(pc.imag) > 1e-9:
                        continue
                    fv = sympy.nsimplify(expr.subs(x, p), rational=False)
                    sd = second.subs(x, p)
                    try:
                        sd_f = float(sd.evalf())
                        kind = "local min" if sd_f > 0 else "local max" if sd_f < 0 else "inflection?"
                    except Exception:
                        kind = "unknown"
                    rows.append((p, fv, kind))
                if rows:
                    self.calc_output.setHtml(
                        "<b>Critical points:</b> " +
                        ";  ".join(f"{v}={sympy.latex(p)}  f={sympy.latex(fv)}  ({k})" for p, fv, k in rows)
                    )
                    latex_str = r"f'(" + v + r") = " + sympy.latex(deriv) + r" = 0"
                    for p, fv, k in rows:
                        latex_str += r",\quad " + v + r"=" + sympy.latex(p)
                    self.calc_result_latex.render(latex_str)
                else:
                    _show("No real critical points",
                          r"f'(" + v + r") = " + sympy.latex(deriv) + r" = 0 \Rightarrow \text{no real roots}")

            elif action == "partial_fractions":
                res = sympy.apart(expr, x)
                _show("Partial fractions",
                      sympy.latex(expr) + r" = " + sympy.latex(res))

            elif action == "simplify":
                res = sympy.simplify(expr)
                _show("Simplified",
                      sympy.latex(expr) + r" = " + sympy.latex(res))

        except Exception as e:
            self.calc_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {str(e)}")
            self.calc_result_latex.render("")


    def setup_statistics_tab(self):
        stat_widget = QWidget()
        self.tabs.addTab(stat_widget, "Statistics")

        outer = QHBoxLayout(stat_widget)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        field_style = (
            "background-color: #242933; border: 1px solid #3b4252; "
            "border-radius: 8px; color: #eceff4; "
            "font-family: 'Consolas', monospace; font-size: 13px; padding: 5px;"
        )
        btn_style = (
            "font-size: 12px; font-weight: bold; "
            "background-color: #2f384c; color: #a3be8c; min-height: 36px;"
        )

        # ── LEFT: data input + operations ────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)

        # Data input
        data_grp = QGroupBox("Data  (comma or space separated)")
        dg = QVBoxLayout(data_grp)
        self.stat_data_input = QTextEdit("2, 4, 4, 4, 5, 5, 7, 9")
        self.stat_data_input.setFixedHeight(56)
        self.stat_data_input.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
            "color: #eceff4; font-family: 'Consolas', monospace; font-size: 13px; padding: 4px;"
        )
        dg.addWidget(self.stat_data_input)
        left_layout.addWidget(data_grp)

        # Descriptive stats buttons
        desc_grp = QGroupBox("Descriptive Statistics")
        dsg = QGridLayout(desc_grp)
        dsg.setSpacing(8)
        desc_ops = [
            ("All Stats",    "all_stats"),
            ("Histogram",    "histogram"),
            ("Box Plot",     "boxplot"),
            ("Mean",         "mean"),
            ("Median",       "median"),
            ("Mode",         "mode"),
            ("Std Dev",      "std"),
            ("Variance",     "variance"),
            ("Min / Max",    "minmax"),
            ("Quartiles",    "quartiles"),
            ("Skewness",     "skewness"),
            ("Kurtosis",     "kurtosis"),
        ]
        for idx, (lbl, act) in enumerate(desc_ops):
            btn = QPushButton(lbl)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_stat_op(a))
            dsg.addWidget(btn, idx // 2, idx % 2)
        left_layout.addWidget(desc_grp)

        # Combinatorics
        comb_grp = QGroupBox("Combinatorics")
        cg = QGridLayout(comb_grp)
        cg.setSpacing(6)
        cg.addWidget(QLabel("n:"), 0, 0)
        self.stat_n = QLineEdit("10")
        self.stat_n.setFixedWidth(60)
        self.stat_n.setStyleSheet(field_style)
        cg.addWidget(self.stat_n, 0, 1)
        cg.addWidget(QLabel("r:"), 0, 2)
        self.stat_r = QLineEdit("3")
        self.stat_r.setFixedWidth(60)
        self.stat_r.setStyleSheet(field_style)
        cg.addWidget(self.stat_r, 0, 3)
        for idx, (lbl, act) in enumerate([("n! Factorial", "factorial"), ("nCr", "ncr"), ("nPr", "npr")]):
            btn = QPushButton(lbl)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_stat_op(a))
            cg.addWidget(btn, 1, idx)
        left_layout.addWidget(comb_grp)

        # Distributions
        dist_grp = QGroupBox("Probability Distributions")
        distg = QVBoxLayout(dist_grp)
        distg.setSpacing(6)

        dist_row = QHBoxLayout()
        dist_row.addWidget(QLabel("Distribution:"))
        self.stat_dist_combo = QComboBox()
        self.stat_dist_combo.addItems(["Normal", "Binomial", "Poisson", "t-distribution", "Chi-squared", "Exponential"])
        self.stat_dist_combo.setStyleSheet(
            "background-color: #242933; color: #eceff4; border: 1px solid #3b4252; "
            "border-radius: 6px; padding: 4px; font-size: 13px;"
        )
        dist_row.addWidget(self.stat_dist_combo)
        distg.addLayout(dist_row)

        params_row = QHBoxLayout()
        for lbl, attr, default in [("p1:", "stat_p1", "0"), ("p2:", "stat_p2", "1"), ("x:", "stat_x", "0")]:
            params_row.addWidget(QLabel(lbl))
            w = QLineEdit(default)
            w.setFixedWidth(64)
            w.setStyleSheet(field_style)
            setattr(self, attr, w)
            params_row.addWidget(w)
        params_row.addStretch()
        distg.addLayout(params_row)

        hint = QLabel("Normal: p1=μ p2=σ  |  Binomial: p1=n p2=p  |  Poisson/Exp: p1=λ  |  t/χ²: p1=df")
        hint.setStyleSheet("color: #4c566a; font-size: 10px;")
        hint.setWordWrap(True)
        distg.addWidget(hint)

        dist_btn_row = QGridLayout()
        dist_btn_row.setSpacing(8)
        for idx, (lbl, act) in enumerate([
            ("Plot PDF/PMF", "dist_pdf"), ("Plot CDF", "dist_cdf"),
            ("P(X ≤ x)",    "dist_prob"), ("Percentile → x", "dist_inv"),
        ]):
            btn = QPushButton(lbl)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_stat_op(a))
            dist_btn_row.addWidget(btn, idx // 2, idx % 2)
        distg.addLayout(dist_btn_row)
        left_layout.addWidget(dist_grp)
        left_layout.addStretch()
        outer.addWidget(left, 2)

        # ── RIGHT: plot canvas + text output ─────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        plot_grp = QGroupBox("Plot")
        pg = QVBoxLayout(plot_grp)
        self.stat_fig = Figure(facecolor='#1e222b')
        self.stat_canvas = FigureCanvas(self.stat_fig)
        self.stat_ax = self.stat_fig.subplots()
        self._init_stat_axes()
        pg.addWidget(self.stat_canvas)
        right_layout.addWidget(plot_grp, 1)

        self.stat_output = QTextBrowser()
        self.stat_output.setMaximumHeight(150)
        self.stat_output.setStyleSheet(
            "background-color: #242933; border: 1px solid #2e3440; border-radius: 8px; "
            "color: #a3be8c; font-family: 'Consolas', monospace; font-size: 13px; padding: 6px;"
        )
        right_layout.addWidget(self.stat_output)
        outer.addWidget(right, 3)

    def _init_stat_axes(self):
        ax = self.stat_ax
        ax.set_facecolor('#242933')
        ax.tick_params(colors='#eceff4')
        for spine in ax.spines.values():
            spine.set_edgecolor('#3b4252')
        ax.grid(color='#2e3440', linestyle='--', linewidth=0.7)
        self.stat_fig.tight_layout(pad=1.2)
        self.stat_canvas.draw()

    def _get_stat_data(self):
        raw = self.stat_data_input.toPlainText().strip()
        tokens = raw.replace(',', ' ').split()
        if not tokens:
            raise ValueError("No data entered")
        return np.array([float(t) for t in tokens])

    def _get_dist(self):
        from scipy import stats
        name = self.stat_dist_combo.currentText()
        p1 = float(self.stat_p1.text())
        p2_text = self.stat_p2.text().strip()
        p2 = float(p2_text) if p2_text else 1.0
        if name == "Normal":
            return stats.norm(loc=p1, scale=p2), f"N({p1}, {p2}²)"
        elif name == "Binomial":
            return stats.binom(n=int(p1), p=p2), f"Bin({int(p1)}, {p2})"
        elif name == "Poisson":
            return stats.poisson(mu=p1), f"Poisson({p1})"
        elif name == "t-distribution":
            return stats.t(df=p1), f"t({p1} df)"
        elif name == "Chi-squared":
            return stats.chi2(df=p1), f"χ²({p1} df)"
        elif name == "Exponential":
            return stats.expon(scale=1.0 / p1), f"Exp(λ={p1})"
        raise ValueError(f"Unknown distribution: {name}")

    def execute_stat_op(self, action):
        from scipy import stats as sp
        _stat_input = self.stat_data_input.toPlainText().strip()[:60]
        try:
            if action in ("all_stats", "histogram", "boxplot", "mean", "median", "mode",
                          "std", "variance", "minmax", "quartiles", "skewness", "kurtosis"):
                data = self._get_stat_data()
                n = len(data)
                mean = np.mean(data)
                median = np.median(data)
                mode_r = sp.mode(data, keepdims=True)
                mode_val = mode_r.mode[0]
                std = np.std(data, ddof=1)
                var = np.var(data, ddof=1)
                mn, mx = np.min(data), np.max(data)
                q1 = np.percentile(data, 25)
                q3 = np.percentile(data, 75)
                iqr = q3 - q1
                skew = sp.skew(data)
                kurt = sp.kurtosis(data)

                self.stat_ax.clear()
                self._init_stat_axes()

                if action == "histogram":
                    self.stat_ax.hist(data, bins='auto', color='#88c0d0', edgecolor='#1e222b', alpha=0.85)
                    self.stat_ax.set_title("Histogram", color='#eceff4')
                    self.stat_canvas.draw()
                    self.stat_output.setHtml(f"<b>n</b> = {n}")
                    return

                if action == "boxplot":
                    bp = self.stat_ax.boxplot(
                        data, patch_artist=True, vert=False,
                        boxprops=dict(facecolor='#3b4a6b', color='#88c0d0'),
                        medianprops=dict(color='#a3be8c', linewidth=2),
                        whiskerprops=dict(color='#88c0d0'),
                        capprops=dict(color='#88c0d0'),
                        flierprops=dict(markerfacecolor='#bf616a', marker='o', markersize=6),
                    )
                    self.stat_ax.set_title("Box Plot", color='#eceff4')
                    self.stat_canvas.draw()
                    self.stat_output.setHtml(
                        f"<b>Min</b> = {mn:.6g} &nbsp; <b>Q1</b> = {q1:.6g} &nbsp; "
                        f"<b>Median</b> = {median:.6g} &nbsp; <b>Q3</b> = {q3:.6g} &nbsp; "
                        f"<b>Max</b> = {mx:.6g}"
                    )
                    return

                if action == "all_stats":
                    self.stat_ax.hist(data, bins='auto', color='#88c0d0', edgecolor='#1e222b', alpha=0.75)
                    self.stat_ax.axvline(mean, color='#a3be8c', linestyle='--', linewidth=1.5, label=f'Mean={mean:.4g}')
                    self.stat_ax.axvline(median, color='#ebcb8b', linestyle=':', linewidth=1.5, label=f'Median={median:.4g}')
                    self.stat_ax.set_title("Data Distribution", color='#eceff4')
                    self.stat_ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
                    self.stat_canvas.draw()
                    self.stat_output.setHtml(
                        f"<b>n</b> = {n}<br>"
                        f"<b>Mean</b> = {mean:.6g} &nbsp;&nbsp; <b>Median</b> = {median:.6g} &nbsp;&nbsp; <b>Mode</b> = {mode_val:.6g}<br>"
                        f"<b>Std Dev</b> = {std:.6g} &nbsp;&nbsp; <b>Variance</b> = {var:.6g}<br>"
                        f"<b>Min</b> = {mn:.6g} &nbsp;&nbsp; <b>Max</b> = {mx:.6g} &nbsp;&nbsp; <b>Range</b> = {mx - mn:.6g}<br>"
                        f"<b>Q1</b> = {q1:.6g} &nbsp;&nbsp; <b>Q3</b> = {q3:.6g} &nbsp;&nbsp; <b>IQR</b> = {iqr:.6g}<br>"
                        f"<b>Skewness</b> = {skew:.6g} &nbsp;&nbsp; <b>Kurtosis</b> = {kurt:.6g}"
                    )
                    return

                text_map = {
                    "mean":     f"<b>Mean</b> = {mean:.8g}",
                    "median":   f"<b>Median</b> = {median:.8g}",
                    "mode":     f"<b>Mode</b> = {mode_val:.8g}",
                    "std":      f"<b>Std Dev (sample, ddof=1)</b> = {std:.8g}",
                    "variance": f"<b>Variance (sample, ddof=1)</b> = {var:.8g}",
                    "minmax":   f"<b>Min</b> = {mn:.6g}<br><b>Max</b> = {mx:.6g}<br><b>Range</b> = {mx - mn:.6g}",
                    "quartiles":f"<b>Q1</b> = {q1:.6g}<br><b>Median (Q2)</b> = {median:.6g}<br><b>Q3</b> = {q3:.6g}<br><b>IQR</b> = {iqr:.6g}",
                    "skewness": f"<b>Skewness</b> = {skew:.8g}",
                    "kurtosis": f"<b>Kurtosis (excess)</b> = {kurt:.8g}",
                }
                self.stat_output.setHtml(text_map[action])

            elif action in ("factorial", "ncr", "npr"):
                import math
                n = int(float(self.stat_n.text()))
                r = int(float(self.stat_r.text()))
                if action == "factorial":
                    self.stat_output.setHtml(f"<b>{n}!</b> = {math.factorial(n):,}")
                elif action == "ncr":
                    self.stat_output.setHtml(f"<b>C({n}, {r})</b> = {math.comb(n, r):,}")
                elif action == "npr":
                    self.stat_output.setHtml(f"<b>P({n}, {r})</b> = {math.perm(n, r):,}")

            elif action in ("dist_pdf", "dist_cdf", "dist_prob", "dist_inv"):
                dist, dist_name = self._get_dist()
                name = self.stat_dist_combo.currentText()
                is_discrete = name in ("Binomial", "Poisson")

                self.stat_ax.clear()
                self._init_stat_axes()

                if action == "dist_pdf":
                    if is_discrete:
                        lo, hi = int(dist.ppf(0.001)), int(dist.ppf(0.999)) + 1
                        xs = np.arange(lo, hi + 1)
                        self.stat_ax.bar(xs, dist.pmf(xs), color='#88c0d0', edgecolor='#1e222b', alpha=0.85)
                        self.stat_ax.set_title(f"PMF — {dist_name}", color='#eceff4')
                    else:
                        lo, hi = dist.ppf(0.001), dist.ppf(0.999)
                        xs = np.linspace(lo, hi, 500)
                        ys = dist.pdf(xs)
                        self.stat_ax.plot(xs, ys, color='#88c0d0', linewidth=2.5)
                        self.stat_ax.fill_between(xs, ys, alpha=0.2, color='#88c0d0')
                        self.stat_ax.set_title(f"PDF — {dist_name}", color='#eceff4')
                    self.stat_output.setHtml(
                        f"<b>{dist_name}</b><br>"
                        f"Mean = {dist.mean():.6g} &nbsp;&nbsp; Std = {dist.std():.6g} &nbsp;&nbsp; Var = {dist.var():.6g}"
                    )
                    self.stat_canvas.draw()

                elif action == "dist_cdf":
                    lo, hi = dist.ppf(0.001), dist.ppf(0.999)
                    if is_discrete:
                        xs = np.arange(int(lo), int(hi) + 2)
                    else:
                        xs = np.linspace(lo, hi, 500)
                    self.stat_ax.plot(xs, dist.cdf(xs), color='#a3be8c', linewidth=2.5)
                    self.stat_ax.set_ylim(0, 1.05)
                    self.stat_ax.set_title(f"CDF — {dist_name}", color='#eceff4')
                    self.stat_output.setHtml(f"<b>CDF — {dist_name}</b>")
                    self.stat_canvas.draw()

                elif action == "dist_prob":
                    x_val = float(self.stat_x.text())
                    prob = float(dist.cdf(x_val))
                    lo, hi = dist.ppf(0.001), dist.ppf(0.999)
                    if is_discrete:
                        xs = np.arange(int(lo), int(hi) + 2)
                        ys = dist.pmf(xs)
                        self.stat_ax.bar(xs, ys, color='#3b4a6b', edgecolor='#1e222b', alpha=0.7)
                        mask = xs <= x_val
                        self.stat_ax.bar(xs[mask], ys[mask], color='#88c0d0', edgecolor='#1e222b', alpha=0.9)
                    else:
                        xs = np.linspace(lo, hi, 500)
                        ys = dist.pdf(xs)
                        self.stat_ax.plot(xs, ys, color='#88c0d0', linewidth=2)
                        xs_shade = xs[xs <= x_val]
                        self.stat_ax.fill_between(xs_shade, dist.pdf(xs_shade), alpha=0.45, color='#88c0d0')
                    self.stat_ax.axvline(x_val, color='#bf616a', linestyle='--', linewidth=1.5)
                    self.stat_ax.set_title(f"P(X ≤ {x_val}) = {prob:.4g}  — {dist_name}", color='#eceff4')
                    self.stat_output.setHtml(
                        f"<b>P(X ≤ {x_val})</b> = {prob:.6g}<br>"
                        f"<b>P(X > {x_val})</b> = {1 - prob:.6g}"
                    )
                    self.stat_canvas.draw()

                elif action == "dist_inv":
                    p_val = float(self.stat_x.text())
                    if not 0 < p_val < 1:
                        raise ValueError("x must be a probability between 0 and 1")
                    x_val = float(dist.ppf(p_val))
                    self.stat_output.setHtml(
                        f"<b>P(X ≤ x) = {p_val}  →  x = {x_val:.8g}</b>"
                    )

            # Record non-plot actions to global history
            if action not in ("histogram", "boxplot", "dist_pdf", "dist_cdf", "dist_prob"):
                result_text = self.stat_output.toPlainText().strip()
                if result_text:
                    self._add_to_global_history("Statistics", action, _stat_input, result_text)

        except Exception as e:
            self.stat_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {str(e)}")


    def setup_3d_graphing_tab(self):
        tab = QWidget()
        self.tabs.addTab(tab, "3D Grapher")

        outer = QHBoxLayout(tab)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        field_style = (
            "background-color: #242933; border: 1px solid #3b4252; "
            "border-radius: 8px; color: #eceff4; "
            "font-family: 'Consolas', monospace; font-size: 13px; padding: 5px;"
        )
        btn_style = (
            "font-size: 12px; font-weight: bold; "
            "background-color: #2f384c; color: #a3be8c; min-height: 36px;"
        )

        # ── LEFT: controls ────────────────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)

        # Surface expression input
        surf_grp = QGroupBox("Expressions — one per line  (explicit or implicit)")
        sg = QVBoxLayout(surf_grp)
        sg.setSpacing(4)
        hint_s = QLabel(
            "Explicit:  sin(sqrt(x**2+y**2))  or  z=x**2-y**2\n"
            "Implicit:  x**2+y**2+z**2=4   or   x^2+y^2=z^2  (^ works too)"
        )
        hint_s.setStyleSheet("color: #4c566a; font-size: 10px;")
        hint_s.setWordWrap(True)
        sg.addWidget(hint_s)
        self.g3d_expr_input = QTextEdit("sin(sqrt(x**2 + y**2))")
        self.g3d_expr_input.setFixedHeight(68)
        self.g3d_expr_input.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
            "color: #eceff4; font-family: 'Consolas', monospace; font-size: 13px; padding: 4px;"
        )
        sg.addWidget(self.g3d_expr_input)
        left_layout.addWidget(surf_grp)

        # Range & resolution
        rng_grp = QGroupBox("Range & Resolution")
        rg = QGridLayout(rng_grp)
        rg.setSpacing(6)
        for row, axis in enumerate(('x', 'y', 'z')):
            rg.addWidget(QLabel(f"{axis} min:"), row, 0)
            w_min = QLineEdit("-5")
            w_min.setStyleSheet(field_style)
            rg.addWidget(w_min, row, 1)
            rg.addWidget(QLabel(f"{axis} max:"), row, 2)
            w_max = QLineEdit("5")
            w_max.setStyleSheet(field_style)
            rg.addWidget(w_max, row, 3)
            setattr(self, f"g3d_{axis}min", w_min)
            setattr(self, f"g3d_{axis}max", w_max)

        rg.addWidget(QLabel("Resolution:"), 3, 0)
        self.g3d_res = QComboBox()
        self.g3d_res.addItems(["50  (fast)", "75", "100  (detailed)"])
        self.g3d_res.setStyleSheet(
            "background-color: #242933; color: #eceff4; border: 1px solid #3b4252; "
            "border-radius: 6px; padding: 4px; font-size: 12px;"
        )
        rg.addWidget(self.g3d_res, 3, 1, 1, 3)
        left_layout.addWidget(rng_grp)

        # Colormap
        cmap_grp = QGroupBox("Appearance")
        cg = QHBoxLayout(cmap_grp)
        cg.addWidget(QLabel("Colormap:"))
        self.g3d_cmap = QComboBox()
        self.g3d_cmap.addItems(["viridis", "plasma", "coolwarm", "ocean", "magma", "inferno", "twilight", "RdBu"])
        self.g3d_cmap.setStyleSheet(
            "background-color: #242933; color: #eceff4; border: 1px solid #3b4252; "
            "border-radius: 6px; padding: 4px; font-size: 12px;"
        )
        cg.addWidget(self.g3d_cmap)
        left_layout.addWidget(cmap_grp)

        # Plot type buttons
        type_grp = QGroupBox("Plot Type")
        tg = QGridLayout(type_grp)
        tg.setSpacing(8)
        for idx, (lbl, act) in enumerate([
            ("Surface",            "surface"),
            ("Wireframe",          "wireframe"),
            ("Surface + Contour",  "surface_contour"),
            ("Filled Contour Map", "contourf"),
        ]):
            btn = QPushButton(lbl)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.plot_3d(a))
            tg.addWidget(btn, idx // 2, idx % 2)
        left_layout.addWidget(type_grp)

        # Parametric curve
        param_grp = QGroupBox("Parametric Curve  (x(t), y(t), z(t))")
        pg = QGridLayout(param_grp)
        pg.setSpacing(6)
        hint_p = QLabel("e.g. helix: x=cos(t) y=sin(t) z=t/(2*pi)  t: 0 → 4*pi")
        hint_p.setStyleSheet("color: #4c566a; font-size: 10px;")
        hint_p.setWordWrap(True)
        pg.addWidget(hint_p, 0, 0, 1, 2)
        for row, (lbl, attr, default) in enumerate([
            ("x(t) =", "g3d_xt", "cos(t)"),
            ("y(t) =", "g3d_yt", "sin(t)"),
            ("z(t) =", "g3d_zt", "t / (2*pi)"),
        ], start=1):
            pg.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(field_style)
            setattr(self, attr, w)
            pg.addWidget(w, row, 1)

        t_row = QHBoxLayout()
        t_row.addWidget(QLabel("t:"))
        self.g3d_tmin = QLineEdit("0")
        self.g3d_tmin.setFixedWidth(80)
        self.g3d_tmin.setStyleSheet(field_style)
        t_row.addWidget(self.g3d_tmin)
        t_row.addWidget(QLabel("to"))
        self.g3d_tmax = QLineEdit("4*pi")
        self.g3d_tmax.setFixedWidth(80)
        self.g3d_tmax.setStyleSheet(field_style)
        t_row.addWidget(self.g3d_tmax)
        t_row.addStretch()
        pg.addLayout(t_row, 4, 0, 1, 2)

        param_btn = QPushButton("Plot Parametric Curve")
        param_btn.setStyleSheet(btn_style)
        param_btn.clicked.connect(lambda: self.plot_3d("parametric"))
        pg.addWidget(param_btn, 5, 0, 1, 2)
        left_layout.addWidget(param_grp)

        # Clear + Reset View
        ctrl_row = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(btn_style)
        clear_btn.clicked.connect(self._clear_3d)
        reset_btn = QPushButton("Reset View")
        reset_btn.setStyleSheet(btn_style)
        reset_btn.clicked.connect(self._reset_3d_view)
        ctrl_row.addWidget(clear_btn)
        ctrl_row.addWidget(reset_btn)
        left_layout.addLayout(ctrl_row)

        left_layout.addStretch()
        outer.addWidget(left, 2)

        # ── RIGHT: 3D canvas + status ─────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self.g3d_fig = Figure(facecolor='#1e222b')
        self.g3d_canvas = FigureCanvas(self.g3d_fig)
        self.g3d_ax = self.g3d_fig.add_subplot(111, projection='3d')
        self._init_3d_axes()
        right_layout.addWidget(self.g3d_canvas, 1)

        self.g3d_output = QTextBrowser()
        self.g3d_output.setMaximumHeight(36)
        self.g3d_output.setStyleSheet(
            "background-color: #242933; border: 1px solid #2e3440; border-radius: 6px; "
            "color: #a3be8c; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px;"
        )
        right_layout.addWidget(self.g3d_output)
        outer.addWidget(right, 3)

    def _init_3d_axes(self):
        ax = self.g3d_ax
        ax.set_facecolor('#1e222b')
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor('#3b4252')
        ax.yaxis.pane.set_edgecolor('#3b4252')
        ax.zaxis.pane.set_edgecolor('#3b4252')
        ax.tick_params(colors='#81a1c1', labelsize=7)
        ax.set_xlabel('x', color='#81a1c1', labelpad=4)
        ax.set_ylabel('y', color='#81a1c1', labelpad=4)
        ax.set_zlabel('z', color='#81a1c1', labelpad=4)
        ax.grid(True, color='#2e3440', linewidth=0.5)
        self.g3d_fig.tight_layout(pad=0.5)
        self.g3d_canvas.draw()

    def _clear_3d(self):
        self.g3d_ax.clear()
        self._init_3d_axes()
        self.g3d_output.setHtml('')

    def _reset_3d_view(self):
        self.g3d_ax.view_init(elev=25, azim=-60)
        self.g3d_canvas.draw()

    def _parse_3d_entry(self, entry):
        """Return ('explicit', expr) or ('implicit', expr) where expr is the sympy expression.
        For explicit: expr is z = f(x,y).
        For implicit: expr is F(x,y,z) = 0 (LHS - RHS).
        Also handles ^ as ** and strips leading 'z =' for explicit."""
        x_s, y_s, z_s = sympy.Symbol('x'), sympy.Symbol('y'), sympy.Symbol('z')
        raw = entry.replace('^', '**').strip()
        if '=' in raw:
            lhs_str, rhs_str = raw.split('=', 1)
            lhs = sympy.sympify(lhs_str.strip())
            rhs = sympy.sympify(rhs_str.strip())
            full = lhs - rhs
            # Explicit if lhs is z and z not in rhs free symbols
            if lhs == z_s and z_s not in rhs.free_symbols:
                return ('explicit', rhs)
            return ('implicit', full)
        else:
            expr = sympy.sympify(raw)
            if z_s in expr.free_symbols:
                return ('implicit', expr)
            return ('explicit', expr)

    def plot_3d(self, plot_type):
        from skimage.measure import marching_cubes

        try:
            x_s, y_s, z_s = sympy.Symbol('x'), sympy.Symbol('y'), sympy.Symbol('z')
            cmap = self.g3d_cmap.currentText()
            res = int(self.g3d_res.currentText().split()[0])

            self.g3d_ax.clear()
            self._init_3d_axes()

            if plot_type == "parametric":
                t_sym = sympy.Symbol('t')
                t_min = float(sympy.sympify(self.g3d_tmin.text()).evalf())
                t_max = float(sympy.sympify(self.g3d_tmax.text()).evalf())
                t_vals = np.linspace(t_min, t_max, 600)
                funcs = [
                    sympy.lambdify(t_sym, sympy.sympify(self.g3d_xt.text().replace('^', '**')), 'numpy'),
                    sympy.lambdify(t_sym, sympy.sympify(self.g3d_yt.text().replace('^', '**')), 'numpy'),
                    sympy.lambdify(t_sym, sympy.sympify(self.g3d_zt.text().replace('^', '**')), 'numpy'),
                ]
                coords = []
                for f in funcs:
                    v = np.asarray(f(t_vals))
                    if v.ndim == 0:
                        v = np.full(t_vals.shape, float(v))
                    coords.append(v.astype(float))
                self.g3d_ax.plot(*coords, color='#88c0d0', linewidth=2)
                self.g3d_ax.set_title("Parametric Curve", color='#eceff4', pad=4)
                self.g3d_canvas.draw()
                self.g3d_output.setHtml("<b>Parametric curve plotted</b>")
                return

            x_min = float(sympy.sympify(self.g3d_xmin.text()).evalf())
            x_max = float(sympy.sympify(self.g3d_xmax.text()).evalf())
            y_min = float(sympy.sympify(self.g3d_ymin.text()).evalf())
            y_max = float(sympy.sympify(self.g3d_ymax.text()).evalf())
            z_min = float(sympy.sympify(self.g3d_zmin.text()).evalf())
            z_max = float(sympy.sympify(self.g3d_zmax.text()).evalf())

            entries = [
                ln.strip() for ln in self.g3d_expr_input.toPlainText().splitlines()
                if ln.strip() and not ln.strip().startswith('#')
            ]
            WIRE_COLORS = ['#88c0d0', '#a3be8c', '#bf616a', '#ebcb8b']
            plotted = 0
            alpha = 0.9 if len(entries) == 1 else 0.72

            for i, entry in enumerate(entries):
                try:
                    kind, expr = self._parse_3d_entry(entry)
                except Exception as e:
                    self.g3d_output.setHtml(f"<b style='color:#bf616a'>Parse error:</b> {e}")
                    continue

                try:
                    if kind == 'implicit':
                        # ── Marching-cubes path ───────────────────────────
                        x_v = np.linspace(x_min, x_max, res)
                        y_v = np.linspace(y_min, y_max, res)
                        z_v = np.linspace(z_min, z_max, res)
                        X3, Y3, Z3 = np.meshgrid(x_v, y_v, z_v, indexing='ij')
                        fn = sympy.lambdify((x_s, y_s, z_s), expr, modules=['numpy'])
                        with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
                            vol = np.asarray(fn(X3, Y3, Z3), dtype=float)
                        finite = np.isfinite(vol)
                        if not finite.any():
                            raise ValueError("Expression is NaN/Inf everywhere in range")
                        # Replace non-finite with a safe large value
                        fill = np.nanmax(np.abs(vol[finite])) * 2 + 1
                        vol[~finite] = fill

                        verts, faces, _, _ = marching_cubes(vol, level=0)
                        # Map grid indices → world coordinates
                        verts[:, 0] = x_min + verts[:, 0] * (x_max - x_min) / (res - 1)
                        verts[:, 1] = y_min + verts[:, 1] * (y_max - y_min) / (res - 1)
                        verts[:, 2] = z_min + verts[:, 2] * (z_max - z_min) / (res - 1)

                        self.g3d_ax.plot_trisurf(
                            verts[:, 0], verts[:, 1], verts[:, 2],
                            triangles=faces, cmap=cmap, alpha=alpha,
                            linewidth=0, antialiased=True
                        )

                    else:
                        # ── Explicit z = f(x,y) path ──────────────────────
                        x_v = np.linspace(x_min, x_max, res)
                        y_v = np.linspace(y_min, y_max, res)
                        X, Y = np.meshgrid(x_v, y_v)
                        fn = sympy.lambdify((x_s, y_s), expr, modules=['numpy'])
                        with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
                            raw = np.asarray(fn(X, Y), dtype=complex)
                        Z = np.where(np.abs(raw.imag) < 1e-9 * (1 + np.abs(raw.real)),
                                     raw.real, np.nan).astype(float)
                        Z[~np.isfinite(Z)] = np.nan

                        if plot_type == "surface":
                            self.g3d_ax.plot_surface(X, Y, Z, cmap=cmap, alpha=alpha,
                                                     linewidth=0, antialiased=True)
                        elif plot_type == "wireframe":
                            stride = max(1, res // 20)
                            self.g3d_ax.plot_wireframe(X, Y, Z,
                                                       color=WIRE_COLORS[i % len(WIRE_COLORS)],
                                                       linewidth=0.6, rstride=stride, cstride=stride)
                        elif plot_type == "surface_contour":
                            self.g3d_ax.plot_surface(X, Y, Z, cmap=cmap, alpha=0.75, linewidth=0)
                            z_off = np.nanmin(Z) - (np.nanmax(Z) - np.nanmin(Z)) * 0.15
                            self.g3d_ax.contourf(X, Y, Z, zdir='z', offset=z_off,
                                                 cmap=cmap, alpha=0.55, levels=14)
                        elif plot_type == "contourf":
                            self.g3d_ax.contourf(X, Y, Z, cmap=cmap, alpha=0.9, levels=18)
                            self.g3d_ax.contour(X, Y, Z, colors='#eceff4',
                                                alpha=0.25, linewidths=0.5, levels=18)

                except Exception as e:
                    self.g3d_output.setHtml(f"<b style='color:#bf616a'>Error [{entry}]:</b> {e}")
                    continue

                plotted += 1

            self.g3d_ax.set_title(
                ", ".join(entries[:2]) + ("…" if len(entries) > 2 else ""),
                color='#eceff4', fontsize=9, pad=4
            )
            self.g3d_canvas.draw()
            self.g3d_output.setHtml(
                f"<b>Plotted {plotted} surface(s)</b>  —  drag to rotate, scroll to zoom"
            )

        except Exception as e:
            self.g3d_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {str(e)}")


    def setup_number_theory_tab(self):
        nt_widget = QWidget()
        self.tabs.addTab(nt_widget, "Number Theory")

        outer = QHBoxLayout(nt_widget)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        field_style = (
            "background-color: #242933; border: 1px solid #3b4252; "
            "border-radius: 8px; color: #eceff4; "
            "font-family: 'Consolas', monospace; font-size: 14px; padding: 6px;"
        )
        btn_style = (
            "font-size: 12px; font-weight: bold; "
            "background-color: #2f384c; color: #a3be8c; min-height: 36px;"
        )

        # ── LEFT: inputs + buttons ────────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(10)

        inp_grp = QGroupBox("Inputs")
        ig = QGridLayout(inp_grp)
        ig.setSpacing(6)
        for row, (lbl, attr, default) in enumerate([
            ("n:", "nt_n", "360"),
            ("a:", "nt_a", "48"),
            ("b / m:", "nt_b", "18"),
        ]):
            ig.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(field_style)
            setattr(self, attr, w)
            ig.addWidget(w, row, 1)
        left_layout.addWidget(inp_grp)

        # Single-n operations
        single_grp = QGroupBox("Single Number  (n)")
        sg = QGridLayout(single_grp)
        sg.setSpacing(8)
        single_ops = [
            ("Is Prime?",        "is_prime"),
            ("Factorize",        "factorize"),
            ("Euler φ(n)",       "totient"),
            ("Divisors",         "divisors"),
            ("Divisor Count σ₀", "div_count"),
            ("Divisor Sum σ₁",   "div_sum"),
            ("Perfect/Abundant?","perfect"),
            ("Next Prime",       "next_prime"),
            ("nth Prime",        "nth_prime"),
            ("Fibonacci(n)",     "fibonacci"),
            ("Base Convert",     "base_convert"),
            ("Collatz",          "collatz"),
        ]
        for idx, (lbl, act) in enumerate(single_ops):
            btn = QPushButton(lbl)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_nt_op(a))
            sg.addWidget(btn, idx // 2, idx % 2)
        left_layout.addWidget(single_grp)

        # Two-number operations
        two_grp = QGroupBox("Two Numbers  (a,  b / m)")
        tg = QGridLayout(two_grp)
        tg.setSpacing(8)
        two_ops = [
            ("GCD(a, b)",        "gcd"),
            ("LCM(a, b)",        "lcm"),
            ("Extended GCD",     "ext_gcd"),
            ("a mod m",          "mod"),
            ("Mod Inverse a⁻¹",  "mod_inv"),
            ("aⁿ mod m",         "mod_pow"),
            ("Legendre (a/b)",   "legendre"),
            ("Jacobi (a/b)",     "jacobi"),
        ]
        for idx, (lbl, act) in enumerate(two_ops):
            btn = QPushButton(lbl)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_nt_op(a))
            tg.addWidget(btn, idx // 2, idx % 2)
        left_layout.addWidget(two_grp)

        # Sequences
        seq_grp = QGroupBox("Sequences  (up to n)")
        sqg = QGridLayout(seq_grp)
        sqg.setSpacing(8)
        for idx, (lbl, act) in enumerate([
            ("Primes ≤ n",        "primes_upto"),
            ("π(x) Plot",         "prime_pi_plot"),
        ]):
            btn = QPushButton(lbl)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, a=act: self.execute_nt_op(a))
            sqg.addWidget(btn, 0, idx)
        left_layout.addWidget(seq_grp)
        left_layout.addStretch()
        outer.addWidget(left, 2)

        # ── RIGHT: plot + text output ─────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.nt_fig = Figure(facecolor='#1e222b')
        self.nt_canvas = FigureCanvas(self.nt_fig)
        self.nt_canvas.setMaximumHeight(200)
        self.nt_ax = self.nt_fig.subplots()
        self._init_nt_axes()
        right_layout.addWidget(self.nt_canvas)

        out_grp = QGroupBox("Result")
        ogl = QVBoxLayout(out_grp)
        self.nt_output = QTextBrowser()
        self.nt_output.setStyleSheet(
            "background-color: #1e222b; border: 1px solid #2e3440; border-radius: 8px; "
            "color: #a3be8c; font-family: 'Consolas', monospace; font-size: 13px; padding: 8px;"
        )
        ogl.addWidget(self.nt_output)
        right_layout.addWidget(out_grp, 1)
        outer.addWidget(right, 3)

    def _init_nt_axes(self):
        ax = self.nt_ax
        ax.set_facecolor('#242933')
        ax.tick_params(colors='#eceff4', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#3b4252')
        ax.grid(color='#2e3440', linestyle='--', linewidth=0.7)
        self.nt_fig.tight_layout(pad=0.8)
        self.nt_canvas.draw()

    def execute_nt_op(self, action):
        import re as _re
        import math

        def _out(html):
            self.nt_output.setHtml(html)
            plain = _re.sub(r'<[^>]+>', '', html).strip()
            self._add_to_global_history("Number Theory", action,
                                        f"n={self.nt_n.text()} a={self.nt_a.text()} b={self.nt_b.text()}",
                                        plain[:200])

        def _ext_gcd(a, b):
            old_r, r = a, b
            old_s, s = 1, 0
            while r:
                q = old_r // r
                old_r, r = r, old_r - q * r
                old_s, s = s, old_s - q * s
            t = (old_r - old_s * a) // b if b else 0
            return old_s, t, old_r  # s, t, gcd  →  a*s + b*t = gcd

        try:
            n = int(sympy.sympify(self.nt_n.text()))
            a = int(sympy.sympify(self.nt_a.text()))
            b = int(sympy.sympify(self.nt_b.text()))

            # ── Single-n ops ──────────────────────────────────────────────
            if action == "is_prime":
                if sympy.isprime(n):
                    _out(f"<b style='color:#a3be8c'>{n:,} is PRIME ✓</b>")
                else:
                    factors = sympy.factorint(n)
                    smallest = min(factors)
                    _out(f"<b style='color:#bf616a'>{n:,} is NOT prime</b><br>"
                         f"Smallest factor: {smallest}<br>"
                         f"Factorization: {n:,} = " +
                         " × ".join(f"{p}^{e}" if e > 1 else str(p)
                                    for p, e in sorted(factors.items())))

            elif action == "factorize":
                factors = sympy.factorint(n)
                html_parts = [f"{p}<sup>{e}</sup>" if e > 1 else str(p)
                              for p, e in sorted(factors.items())]
                plain_parts = [f"{p}^{e}" if e > 1 else str(p)
                               for p, e in sorted(factors.items())]
                _out(f"<b>{n:,} = {'  ×  '.join(html_parts)}</b><br>"
                     f"{'  ×  '.join(plain_parts)}<br><br>"
                     f"Prime factors: {dict(sorted(factors.items()))}")

            elif action == "totient":
                phi = int(sympy.totient(n))
                _out(f"<b>φ({n:,}) = {phi:,}</b><br>"
                     f"{phi:,} integers in [1, {n:,}] are coprime to {n:,}")

            elif action == "divisors":
                divs = sympy.divisors(n)
                preview = ", ".join(f"{d:,}" for d in divs[:60])
                suffix = f" … ({len(divs)} total)" if len(divs) > 60 else ""
                _out(f"<b>Divisors of {n:,}  ({len(divs)} total):</b><br>{preview}{suffix}")

            elif action == "div_count":
                c = int(sympy.divisor_count(n))
                _out(f"<b>σ₀({n:,}) = {c}</b><br>{n:,} has {c} positive divisors")

            elif action == "div_sum":
                s = int(sympy.divisor_sigma(n, 1))
                proper = s - n
                _out(f"<b>σ₁({n:,}) = {s:,}</b><br>"
                     f"Sum of all divisors = {s:,}<br>"
                     f"Sum of proper divisors = {proper:,}")

            elif action == "perfect":
                s = int(sympy.divisor_sigma(n, 1))
                proper = s - n
                if proper == n:
                    _out(f"<b style='color:#a3be8c'>{n:,} is PERFECT</b><br>"
                         f"Sum of proper divisors = {proper:,} = n")
                elif proper > n:
                    _out(f"<b style='color:#ebcb8b'>{n:,} is ABUNDANT</b><br>"
                         f"Sum of proper divisors = {proper:,} > {n:,}<br>"
                         f"Excess = {proper - n:,}")
                else:
                    _out(f"<b style='color:#81a1c1'>{n:,} is DEFICIENT</b><br>"
                         f"Sum of proper divisors = {proper:,} < {n:,}<br>"
                         f"Deficiency = {n - proper:,}")

            elif action == "next_prime":
                p = sympy.nextprime(n)
                _out(f"<b>Next prime after {n:,} = {p:,}</b>")

            elif action == "nth_prime":
                if n > 1_000_000:
                    _out("<b style='color:#bf616a'>n too large (max 1 000 000)</b>")
                else:
                    p = sympy.prime(n)
                    _out(f"<b>Prime #{n:,} = {p:,}</b>")

            elif action == "fibonacci":
                if n > 10_000:
                    _out("<b style='color:#bf616a'>n too large for display (max 10 000)</b>")
                else:
                    f_val = int(sympy.fibonacci(n))
                    digits = len(str(f_val))
                    preview = f"{f_val:,}" if digits <= 60 else str(f_val)[:57] + "…"
                    _out(f"<b>F({n:,}) = {preview}</b><br>({digits} digits)")

            elif action == "base_convert":
                _out(
                    f"<b>{n:,} in different bases:</b><br><br>"
                    f"<b>Binary</b>   (base 2):   {bin(n)}<br>"
                    f"<b>Octal</b>    (base 8):   {oct(n)}<br>"
                    f"<b>Decimal</b>  (base 10): {n:,}<br>"
                    f"<b>Hex</b>      (base 16): {hex(n).upper()}"
                )

            elif action == "collatz":
                if n <= 0:
                    raise ValueError("n must be positive")
                seq = [n]
                x = n
                while x != 1 and len(seq) < 10_000:
                    x = x // 2 if x % 2 == 0 else 3 * x + 1
                    seq.append(x)
                peak = max(seq)
                steps = len(seq) - 1
                preview = " → ".join(map(str, seq[:20]))
                suffix = f" → … → 1  ({steps} steps)" if steps >= 20 else ""
                _out(f"<b>Collatz sequence from {n:,}:</b><br>"
                     f"Steps to reach 1: <b>{steps}</b><br>"
                     f"Peak value: <b>{peak:,}</b><br><br>"
                     f"{preview}{suffix}")
                # Plot
                self.nt_ax.clear()
                self._init_nt_axes()
                self.nt_ax.plot(seq, color='#88c0d0', linewidth=1.2)
                self.nt_ax.set_title(f"Collatz: n={n:,}  ({steps} steps)", color='#eceff4', fontsize=9)
                self.nt_canvas.draw()

            # ── Two-number ops ────────────────────────────────────────────
            elif action == "gcd":
                g = math.gcd(a, b)
                _out(f"<b>GCD({a:,}, {b:,}) = {g:,}</b>")

            elif action == "lcm":
                l = math.lcm(a, b)
                _out(f"<b>LCM({a:,}, {b:,}) = {l:,}</b>")

            elif action == "ext_gcd":
                s, t, g = _ext_gcd(a, b)
                _out(f"<b>Extended GCD({a:,}, {b:,})</b><br><br>"
                     f"GCD = <b>{g:,}</b><br>"
                     f"<b>{a:,}</b> × ({s}) + <b>{b:,}</b> × ({t}) = {g:,}<br>"
                     f"(Bézout coefficients:  s = {s},  t = {t})<br>"
                     f"Verify: {a*s + b*t} = {g}")

            elif action == "mod":
                r = a % b
                q = a // b
                _out(f"<b>{a:,} mod {b:,} = {r:,}</b><br>"
                     f"{a:,} = {b:,} × {q:,} + {r:,}")

            elif action == "mod_inv":
                g = math.gcd(a, b)
                if g != 1:
                    _out(f"<b style='color:#bf616a'>No inverse exists:</b> "
                         f"GCD({a}, {b}) = {g} ≠ 1")
                else:
                    inv = pow(a, -1, b)
                    _out(f"<b>{a:,}⁻¹ mod {b:,} = {inv:,}</b><br>"
                         f"Verify: {a:,} × {inv:,} mod {b:,} = {(a * inv) % b}")

            elif action == "mod_pow":
                # a^n mod b
                result = pow(a, n, b)
                _out(f"<b>{a:,}<sup>{n:,}</sup> mod {b:,} = {result:,}</b>")

            elif action == "legendre":
                if not sympy.isprime(b) or b == 2:
                    _out("<b style='color:#bf616a'>b must be an odd prime for the Legendre symbol</b>")
                else:
                    sym = int(sympy.legendre_symbol(a, b))
                    meaning = {
                        1:  f"{a} is a quadratic residue mod {b}",
                        -1: f"{a} is a quadratic non-residue mod {b}",
                        0:  f"{b} divides {a}",
                    }
                    _out(f"<b>({a}/{b}) = {sym}</b><br>{meaning.get(sym, '')}")

            elif action == "jacobi":
                if b % 2 == 0 or b < 1:
                    _out("<b style='color:#bf616a'>b must be a positive odd integer</b>")
                else:
                    sym = int(sympy.jacobi_symbol(a, b))
                    _out(f"<b>({a}/{b})_J = {sym}</b>  (Jacobi symbol)")

            # ── Sequences ─────────────────────────────────────────────────
            elif action in ("primes_upto", "prime_pi_plot"):
                limit = n
                if limit > 200_000:
                    _out("<b style='color:#bf616a'>n too large (max 200 000)</b>")
                    return
                primes = np.array(list(sympy.primerange(2, limit + 1)), dtype=np.int64)
                xs = np.arange(2, limit + 1)
                pi_vals = np.searchsorted(primes, xs, side='right')

                self.nt_ax.clear()
                self._init_nt_axes()
                self.nt_ax.plot(xs, pi_vals, color='#88c0d0', linewidth=1.5, label='π(x)')
                # x / ln(x) approximation
                with np.errstate(divide='ignore', invalid='ignore'):
                    approx = np.where(xs >= 2, xs / np.log(xs.astype(float)), 0)
                self.nt_ax.plot(xs, approx, color='#bf616a', linewidth=1,
                                linestyle='--', label='x / ln x')
                self.nt_ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=8)
                self.nt_ax.set_title(f"Prime counting π(x),  x ≤ {limit:,}",
                                     color='#eceff4', fontsize=9)
                self.nt_canvas.draw()

                if action == "primes_upto":
                    preview = ", ".join(f"{p:,}" for p in primes[:80])
                    suffix = f", …" if len(primes) > 80 else ""
                    _out(f"<b>Primes ≤ {limit:,}:  {len(primes):,} found</b><br><br>"
                         f"{preview}{suffix}")
                else:
                    import math as _math
                    _out(f"<b>π({limit:,}) = {len(primes):,}</b><br>"
                         f"x/ln(x) ≈ {limit / _math.log(limit):.1f}")

        except Exception as e:
            self.nt_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {str(e)}")

    # ══════════════════════════════════════════════════════════════════════
    # Analysis tab  (Fourier · Special Functions · Complex Mapping · FA)
    # ══════════════════════════════════════════════════════════════════════

    def setup_analysis_tab(self):
        w = QWidget()
        self.tabs.addTab(w, "Analysis")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(4, 4, 4, 4)
        self._an_tabs = QTabWidget()
        outer.addWidget(self._an_tabs)
        self._an_field = (
            "background-color: #242933; border: 1px solid #3b4252; "
            "border-radius: 8px; color: #eceff4; "
            "font-family: 'Consolas', monospace; font-size: 13px; padding: 5px;"
        )
        self._an_btn = (
            "font-size: 12px; font-weight: bold; "
            "background-color: #2f384c; color: #a3be8c; min-height: 34px;"
        )
        self._setup_fourier_subtab()
        self._setup_special_functions_subtab()
        self._setup_complex_mapping_subtab()
        self._setup_functional_analysis_subtab()

    # ── Fourier ────────────────────────────────────────────────────────────

    def _setup_fourier_subtab(self):
        tab = QWidget()
        self._an_tabs.addTab(tab, "Fourier")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        # Fourier series
        fs = QGroupBox("Fourier Series  of  f(x)  on  [−L, L]")
        fsg = QGridLayout(fs)
        fsg.setSpacing(6)
        fsg.addWidget(QLabel("f(x) ="), 0, 0)
        self.fs_expr = QLineEdit("x")
        self.fs_expr.setStyleSheet(self._an_field)
        fsg.addWidget(self.fs_expr, 0, 1)
        fsg.addWidget(QLabel("L ="), 1, 0)
        self.fs_L = QLineEdit("pi")
        self.fs_L.setStyleSheet(self._an_field)
        fsg.addWidget(self.fs_L, 1, 1)
        fsg.addWidget(QLabel("Terms N ="), 2, 0)
        self.fs_N = QLineEdit("8")
        self.fs_N.setStyleSheet(self._an_field)
        fsg.addWidget(self.fs_N, 2, 1)
        for lbl, act in [("Plot Approximation", "series"), ("Show Coefficients", "coeffs")]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._an_btn)
            btn.clicked.connect(lambda _, a=act: self._run_fourier(a))
            fsg.addWidget(btn, fsg.rowCount(), 0, 1, 2)
        ll.addWidget(fs)

        # FFT
        fft = QGroupBox("FFT  —  Discrete Signal")
        fftg = QVBoxLayout(fft)
        fftg.setSpacing(6)
        hint = QLabel("Signal samples (comma / space separated):")
        hint.setStyleSheet("color: #4c566a; font-size: 10px;")
        fftg.addWidget(hint)
        self.fft_data = QTextEdit("0,1,2,3,4,3,2,1,0,-1,-2,-3,-4,-3,-2,-1")
        self.fft_data.setFixedHeight(52)
        self.fft_data.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
            "color: #eceff4; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px;"
        )
        fftg.addWidget(self.fft_data)
        sr_row = QHBoxLayout()
        sr_row.addWidget(QLabel("Sample rate (Hz):"))
        self.fft_sr = QLineEdit("1")
        self.fft_sr.setFixedWidth(70)
        self.fft_sr.setStyleSheet(self._an_field)
        sr_row.addWidget(self.fft_sr)
        sr_row.addStretch()
        fftg.addLayout(sr_row)
        fft_btn = QPushButton("Compute FFT & Plot Spectrum")
        fft_btn.setStyleSheet(self._an_btn)
        fft_btn.clicked.connect(lambda: self._run_fourier("fft"))
        fftg.addWidget(fft_btn)
        ll.addWidget(fft)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.fourier_fig = Figure(facecolor='#1e222b')
        self.fourier_canvas = FigureCanvas(self.fourier_fig)
        rl.addWidget(self.fourier_canvas, 1)
        self.fourier_output = QTextBrowser()
        self.fourier_output.setMaximumHeight(90)
        self.fourier_output.setStyleSheet(
            "background-color: #1e222b; border: 1px solid #2e3440; border-radius: 6px; "
            "color: #a3be8c; font-family: 'Consolas', monospace; font-size: 12px; padding: 6px;"
        )
        rl.addWidget(self.fourier_output)
        outer.addWidget(right, 3)

    def _run_fourier(self, action):
        from scipy.integrate import quad as _quad
        try:
            if action in ("series", "coeffs"):
                x_sym = sympy.Symbol('x')
                expr = sympy.sympify(self.fs_expr.text())
                L = float(sympy.sympify(self.fs_L.text()).evalf())
                N = int(self.fs_N.text())
                f = sympy.lambdify(x_sym, expr, 'numpy')

                def safe_f(x):
                    with np.errstate(all='ignore'):
                        v = np.asarray(f(x), dtype=complex)
                    return np.where(np.isfinite(v.real), v.real, 0.0)

                a0 = (1/L) * _quad(safe_f, -L, L)[0]
                an = [0.0] + [(1/L) * _quad(lambda x, n=n: safe_f(x) * np.cos(n*np.pi*x/L), -L, L)[0] for n in range(1, N+1)]
                bn = [0.0] + [(1/L) * _quad(lambda x, n=n: safe_f(x) * np.sin(n*np.pi*x/L), -L, L)[0] for n in range(1, N+1)]

                xs = np.linspace(-L, L, 800)

                fig = self.fourier_fig
                fig.clear()
                if action == "series":
                    ax = fig.add_subplot(111)
                    ax.set_facecolor('#242933')
                    ax.tick_params(colors='#eceff4', labelsize=8)
                    ax.grid(color='#2e3440', linestyle='--', linewidth=0.6)
                    for sp in ax.spines.values(): sp.set_edgecolor('#3b4252')

                    S = np.full_like(xs, a0/2)
                    for n in range(1, N+1):
                        S += an[n]*np.cos(n*np.pi*xs/L) + bn[n]*np.sin(n*np.pi*xs/L)

                    ax.plot(xs, safe_f(xs), color='#eceff4', linewidth=1.5, label='f(x)', alpha=0.7)
                    ax.plot(xs, S, color='#88c0d0', linewidth=2, label=f'S_{N}(x)')
                    ax.axhline(0, color='#4c566a', linewidth=0.5)
                    ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
                    ax.set_title(f"Fourier series  N={N},  L={L:.4g}", color='#eceff4', fontsize=9)
                    self.fourier_output.setHtml(
                        f"<b>a₀ = {a0:.5g}</b><br>" +
                        "  ".join(f"a<sub>{n}</sub>={an[n]:.3g}" for n in range(1, min(N+1, 6))) + "<br>" +
                        "  ".join(f"b<sub>{n}</sub>={bn[n]:.3g}" for n in range(1, min(N+1, 6)))
                    )
                else:  # coeffs bar chart
                    ax1, ax2 = fig.subplots(2, 1)
                    for ax in (ax1, ax2):
                        ax.set_facecolor('#242933')
                        ax.tick_params(colors='#eceff4', labelsize=7)
                        ax.grid(color='#2e3440', linestyle='--', linewidth=0.5)
                        for sp in ax.spines.values(): sp.set_edgecolor('#3b4252')
                    ns = list(range(N+1))
                    ax1.bar(ns, an, color='#88c0d0', alpha=0.85)
                    ax1.set_title("aₙ coefficients", color='#eceff4', fontsize=9)
                    ax2.bar(ns, bn, color='#a3be8c', alpha=0.85)
                    ax2.set_title("bₙ coefficients", color='#eceff4', fontsize=9)
                    fig.tight_layout(pad=0.8)
                    self.fourier_output.setHtml(
                        f"<b>Coefficients a₀…a{N} and b₁…b{N}</b>"
                    )

            elif action == "fft":
                raw = self.fft_data.toPlainText().replace(',', ' ').split()
                signal = np.array([float(x) for x in raw])
                sr = float(self.fft_sr.text())
                N = len(signal)
                spectrum = np.fft.rfft(signal)
                freqs = np.fft.rfftfreq(N, d=1.0/sr)
                power = np.abs(spectrum)
                dom_idx = np.argmax(power[1:]) + 1
                dom_freq = freqs[dom_idx]

                fig = self.fourier_fig
                fig.clear()
                ax1, ax2 = fig.subplots(2, 1)
                for ax in (ax1, ax2):
                    ax.set_facecolor('#242933')
                    ax.tick_params(colors='#eceff4', labelsize=8)
                    ax.grid(color='#2e3440', linestyle='--', linewidth=0.6)
                    for sp in ax.spines.values(): sp.set_edgecolor('#3b4252')
                ax1.plot(signal, color='#88c0d0', linewidth=1.8, marker='o', markersize=3)
                ax1.set_title("Signal (time domain)", color='#eceff4', fontsize=9)
                ax2.bar(freqs, power, width=freqs[1]-freqs[0] if len(freqs)>1 else 1,
                        color='#a3be8c', alpha=0.85, align='edge')
                ax2.set_title("Frequency spectrum  |X(f)|", color='#eceff4', fontsize=9)
                ax2.set_xlabel("Frequency (Hz)", color='#81a1c1', fontsize=8)
                fig.tight_layout(pad=0.8)
                self.fourier_output.setHtml(
                    f"<b>N = {N} samples,  sr = {sr} Hz</b><br>"
                    f"Dominant frequency: <b>{dom_freq:.4g} Hz</b>  (|X| = {power[dom_idx]:.4g})"
                )

            self.fourier_canvas.draw()
            self._add_to_global_history("Analysis·Fourier", action,
                                        self.fs_expr.text(), self.fourier_output.toPlainText()[:150])
        except Exception as e:
            self.fourier_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {e}")

    # ── Special Functions ──────────────────────────────────────────────────

    def _setup_special_functions_subtab(self):
        tab = QWidget()
        self._an_tabs.addTab(tab, "Special Functions")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        sel_grp = QGroupBox("Function")
        sg = QGridLayout(sel_grp)
        sg.setSpacing(6)
        sg.addWidget(QLabel("Function:"), 0, 0)
        self.sf_combo = QComboBox()
        self.sf_combo.addItems([
            "Gamma  Γ(x)", "Digamma  ψ(x)", "Log-Gamma  ln Γ(x)",
            "Riemann Zeta  ζ(s)", "Error function  erf(x)", "Erfc(x)",
            "Bessel J_n(x)", "Bessel Y_n(x)", "Bessel I_n(x)", "Bessel K_n(x)",
            "Airy Ai(x)", "Airy Bi(x)",
            "Lambert W(x)", "Beta  B(x,n)",
        ])
        self.sf_combo.setStyleSheet(
            "background-color: #242933; color: #eceff4; border: 1px solid #3b4252; "
            "border-radius: 6px; padding: 4px; font-size: 12px;"
        )
        sg.addWidget(self.sf_combo, 0, 1)

        for row, (lbl, attr, default) in enumerate([
            ("x =",     "sf_x",    "2.5"),
            ("n / p2 =","sf_n",    "0"),
            ("x min:",  "sf_xmin", "-4"),
            ("x max:",  "sf_xmax", "6"),
        ], start=1):
            sg.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._an_field)
            setattr(self, attr, w)
            sg.addWidget(w, row, 1)

        for lbl, act in [("Evaluate at x", "eval"), ("Plot over range", "plot")]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._an_btn)
            btn.clicked.connect(lambda _, a=act: self._run_sf(a))
            sg.addWidget(btn, sg.rowCount(), 0, 1, 2)
        ll.addWidget(sel_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)
        self.sf_result_latex = LatexCanvas(height=90)
        rl.addWidget(self.sf_result_latex)
        rl.addWidget(self._copy_latex_btn(self.sf_result_latex), alignment=Qt.AlignmentFlag.AlignRight)
        self.sf_fig = Figure(facecolor='#1e222b')
        self.sf_canvas = FigureCanvas(self.sf_fig)
        self.sf_ax = self.sf_fig.subplots()
        self._init_sf_axes()
        rl.addWidget(self.sf_canvas, 1)
        outer.addWidget(right, 3)

    def _init_sf_axes(self):
        ax = self.sf_ax
        ax.set_facecolor('#242933')
        ax.tick_params(colors='#eceff4', labelsize=8)
        for sp in ax.spines.values(): sp.set_edgecolor('#3b4252')
        ax.grid(color='#2e3440', linestyle='--', linewidth=0.6)
        self.sf_fig.tight_layout(pad=0.8)
        self.sf_canvas.draw()

    def _run_sf(self, action):
        from scipy import special as sc
        import warnings
        try:
            name = self.sf_combo.currentText()
            x_val = float(sympy.sympify(self.sf_x.text()).evalf())
            n_val = float(sympy.sympify(self.sf_n.text()).evalf())
            x_min = float(sympy.sympify(self.sf_xmin.text()).evalf())
            x_max = float(sympy.sympify(self.sf_xmax.text()).evalf())

            # Map combo → (scipy eval fn, plot fn, latex name, needs_n)
            def _gamma(x, _):    return sc.gamma(x)
            def _digamma(x, _):  return sc.digamma(x)
            def _lgamma(x, _):   return sc.gammaln(x)
            def _zeta(x, _):     return sc.zeta(x)
            def _erf(x, _):      return sc.erf(x)
            def _erfc(x, _):     return sc.erfc(x)
            def _jv(x, n):       return sc.jv(n, x)
            def _yv(x, n):       return sc.yv(n, x)
            def _iv(x, n):       return sc.iv(n, x)
            def _kv(x, n):       return sc.kv(n, x)
            def _ai(x, _):       return sc.airy(x)[0]
            def _bi(x, _):       return sc.airy(x)[2]
            def _w(x, _):        return np.real(sc.lambertw(x))
            def _beta(x, n):     return sc.beta(x, n)

            fn_map = {
                "Gamma  Γ(x)":          (_gamma,  r"\Gamma(x)"),
                "Digamma  ψ(x)":        (_digamma, r"\psi(x)"),
                "Log-Gamma  ln Γ(x)":   (_lgamma,  r"\ln\Gamma(x)"),
                "Riemann Zeta  ζ(s)":   (_zeta,    r"\zeta(s)"),
                "Error function  erf(x)":(_erf,    r"\mathrm{erf}(x)"),
                "Erfc(x)":              (_erfc,    r"\mathrm{erfc}(x)"),
                "Bessel J_n(x)":        (_jv,      r"J_n(x)"),
                "Bessel Y_n(x)":        (_yv,      r"Y_n(x)"),
                "Bessel I_n(x)":        (_iv,      r"I_n(x)"),
                "Bessel K_n(x)":        (_kv,      r"K_n(x)"),
                "Airy Ai(x)":           (_ai,      r"\mathrm{Ai}(x)"),
                "Airy Bi(x)":           (_bi,      r"\mathrm{Bi}(x)"),
                "Lambert W(x)":         (_w,       r"W(x)"),
                "Beta  B(x,n)":         (_beta,    r"B(x,n)"),
            }
            fn, latex_name = fn_map[name]

            if action == "eval":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result = fn(x_val, n_val)
                self.sf_result_latex.render(
                    latex_name.replace("x", f"{x_val:.4g}").replace("n", f"{n_val:.4g}")
                    + r" = " + f"{float(np.real(result)):.8g}"
                )
                self._add_to_global_history("Analysis·Special", name,
                                            f"x={x_val}, n={n_val}", f"{float(np.real(result)):.8g}")

            elif action == "plot":
                xs = np.linspace(x_min, x_max, 600)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ys = np.asarray([fn(xi, n_val) for xi in xs], dtype=float)
                ys[~np.isfinite(ys)] = np.nan
                # Clip extreme values for display
                finite = ys[np.isfinite(ys)]
                if len(finite):
                    lo, hi = np.percentile(finite, 2), np.percentile(finite, 98)
                    ys = np.clip(ys, lo - abs(hi-lo), hi + abs(hi-lo))

                self.sf_ax.clear()
                self._init_sf_axes()
                n_label = f"(n={n_val:.4g})" if "Bessel" in name or "Beta" in name else ""
                self.sf_ax.plot(xs, ys, color='#88c0d0', linewidth=2)
                self.sf_ax.axhline(0, color='#4c566a', linewidth=0.8)
                self.sf_ax.axvline(0, color='#4c566a', linewidth=0.8)
                self.sf_ax.set_title(f"{name} {n_label}", color='#eceff4', fontsize=9)
                self.sf_ax.set_xlabel("x", color='#81a1c1', fontsize=8)
                self.sf_canvas.draw()
                self.sf_result_latex.render(latex_name + r"\text{ on } [" +
                                            f"{x_min:.4g}" + r",\," + f"{x_max:.4g}" + r"]")

        except Exception as e:
            self.sf_result_latex.render(r"\text{Error: }" + str(e)[:40])

    # ── Complex Mapping ────────────────────────────────────────────────────

    def _setup_complex_mapping_subtab(self):
        tab = QWidget()
        self._an_tabs.addTab(tab, "Complex Mapping")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        fn_grp = QGroupBox("Holomorphic function  f(z)")
        fg = QGridLayout(fn_grp)
        fg.setSpacing(6)
        hint = QLabel("Use z as variable.  Examples:  z**2   exp(z)   1/z   (z-1)/(z+1)   sin(z)")
        hint.setStyleSheet("color: #4c566a; font-size: 10px;")
        hint.setWordWrap(True)
        fg.addWidget(hint, 0, 0, 1, 2)
        fg.addWidget(QLabel("f(z) ="), 1, 0)
        self.cm_expr = QLineEdit("z**2")
        self.cm_expr.setStyleSheet(self._an_field)
        fg.addWidget(self.cm_expr, 1, 1)

        for row, (lbl, attr, default) in enumerate([
            ("Re min:", "cm_remin", "-2"), ("Re max:", "cm_remax", "2"),
            ("Im min:", "cm_immin", "-2"), ("Im max:", "cm_immax", "2"),
        ], start=2):
            fg.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setFixedWidth(64)
            w.setStyleSheet(self._an_field)
            setattr(self, attr, w)
            fg.addWidget(w, row, 1)

        fg.addWidget(QLabel("Resolution:"), 6, 0)
        self.cm_res = QComboBox()
        self.cm_res.addItems(["200  (fast)", "350", "500  (detailed)"])
        self.cm_res.setStyleSheet(
            "background-color: #242933; color: #eceff4; border: 1px solid #3b4252; "
            "border-radius: 6px; padding: 3px; font-size: 12px;"
        )
        fg.addWidget(self.cm_res, 6, 1)
        ll.addWidget(fn_grp)

        viz_grp = QGroupBox("Visualisation")
        vg = QGridLayout(viz_grp)
        vg.setSpacing(8)
        for idx, (lbl, act) in enumerate([
            ("Domain Colouring",  "domain"),
            ("Grid Mapping",      "grid"),
            ("Phase Portrait",    "phase"),
            ("Modulus Surface",   "modulus"),
        ]):
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._an_btn)
            btn.clicked.connect(lambda _, a=act: self._run_complex_map(a))
            vg.addWidget(btn, idx // 2, idx % 2)
        ll.addWidget(viz_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.cm_fig = Figure(facecolor='#1e222b')
        self.cm_canvas = FigureCanvas(self.cm_fig)
        rl.addWidget(self.cm_canvas, 1)
        self.cm_output = QTextBrowser()
        self.cm_output.setMaximumHeight(36)
        self.cm_output.setStyleSheet(
            "background-color: #1e222b; border: 1px solid #2e3440; border-radius: 6px; "
            "color: #a3be8c; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px;"
        )
        rl.addWidget(self.cm_output)
        outer.addWidget(right, 3)

    def _run_complex_map(self, viz):
        try:
            z_sym = sympy.Symbol('z')
            expr = sympy.sympify(self.cm_expr.text().replace('^', '**'))
            f = sympy.lambdify(z_sym, expr, modules=['numpy'])
            res = int(self.cm_res.currentText().split()[0])

            re_min = float(self.cm_remin.text()); re_max = float(self.cm_remax.text())
            im_min = float(self.cm_immin.text()); im_max = float(self.cm_immax.text())

            re_vals = np.linspace(re_min, re_max, res)
            im_vals = np.linspace(im_min, im_max, res)
            X, Y = np.meshgrid(re_vals, im_vals)
            Z = X + 1j * Y

            with np.errstate(all='ignore'):
                W = np.asarray(f(Z), dtype=complex)
            W[~np.isfinite(np.abs(W))] = np.nan

            self.cm_fig.clear()
            ax = self.cm_fig.add_subplot(111)
            ax.set_facecolor('#1e222b')
            ax.tick_params(colors='#eceff4', labelsize=8)
            for sp in ax.spines.values(): sp.set_edgecolor('#3b4252')

            if viz in ("domain", "phase"):
                from matplotlib.colors import hsv_to_rgb
                angle = np.angle(W)
                hue = (angle / (2 * np.pi)) % 1.0
                if viz == "domain":
                    # brightness encodes modulus (zeros dark, poles bright)
                    mod = np.abs(W)
                    val = 2/np.pi * np.arctan(np.where(np.isfinite(mod), mod, 0))
                    # Checkerboard isochromatic lines on |f|
                    k = np.floor(np.log2(mod + 1e-12))
                    val = val * (0.8 + 0.2 * (k % 2))
                else:
                    # Pure phase portrait — constant brightness
                    val = np.ones_like(hue) * 0.85
                sat = np.ones_like(hue) * 0.9
                hue = np.where(np.isfinite(hue), hue, 0)
                val = np.where(np.isfinite(val), val, 0)
                rgb = hsv_to_rgb(np.dstack([hue, sat, val]))
                ax.imshow(rgb, extent=[re_min, re_max, im_min, im_max],
                          origin='lower', aspect='auto', interpolation='bilinear')
                ax.set_xlabel("Re(z)", color='#81a1c1', fontsize=8)
                ax.set_ylabel("Im(z)", color='#81a1c1', fontsize=8)
                ax.set_title(
                    f"{'Domain colouring' if viz=='domain' else 'Phase portrait'}  f(z) = {self.cm_expr.text()}",
                    color='#eceff4', fontsize=9
                )

            elif viz == "grid":
                ax.set_facecolor('#242933')
                ax.grid(color='#2e3440', linestyle='--', linewidth=0.4)
                n_lines = 16
                # Vertical lines → blue family
                for re_v in np.linspace(re_min, re_max, n_lines):
                    im_v = np.linspace(im_min, im_max, 300)
                    z_line = re_v + 1j * im_v
                    with np.errstate(all='ignore'):
                        w_line = np.asarray(f(z_line), dtype=complex)
                    mask = np.isfinite(np.abs(w_line))
                    segs = np.where(np.diff(mask.astype(int)))[0]
                    starts = [0] + list(segs + 1)
                    ends = list(segs + 1) + [len(w_line)]
                    for s, e in zip(starts, ends):
                        if e - s > 1 and mask[s]:
                            ax.plot(w_line[s:e].real, w_line[s:e].imag, color='#88c0d0', linewidth=0.7, alpha=0.8)
                # Horizontal lines → green family
                for im_v in np.linspace(im_min, im_max, n_lines):
                    re_v = np.linspace(re_min, re_max, 300)
                    z_line = re_v + 1j * im_v
                    with np.errstate(all='ignore'):
                        w_line = np.asarray(f(z_line), dtype=complex)
                    mask = np.isfinite(np.abs(w_line))
                    segs = np.where(np.diff(mask.astype(int)))[0]
                    starts = [0] + list(segs + 1)
                    ends = list(segs + 1) + [len(w_line)]
                    for s, e in zip(starts, ends):
                        if e - s > 1 and mask[s]:
                            ax.plot(w_line[s:e].real, w_line[s:e].imag, color='#a3be8c', linewidth=0.7, alpha=0.8)
                ax.set_xlabel("Re(w)", color='#81a1c1', fontsize=8)
                ax.set_ylabel("Im(w)", color='#81a1c1', fontsize=8)
                ax.set_title(f"Grid mapping  f(z) = {self.cm_expr.text()}", color='#eceff4', fontsize=9)

            elif viz == "modulus":
                mod = np.abs(W)
                finite = np.isfinite(mod)
                if finite.any():
                    clip = np.nanpercentile(mod[finite], 98)
                    mod = np.clip(mod, 0, clip)
                ax.contourf(X, Y, mod, levels=40, cmap='viridis')
                ax.contour(X, Y, mod, levels=15, colors='white', linewidths=0.3, alpha=0.3)
                ax.set_xlabel("Re(z)", color='#81a1c1', fontsize=8)
                ax.set_ylabel("Im(z)", color='#81a1c1', fontsize=8)
                ax.set_title(f"|f(z)|  for  f(z) = {self.cm_expr.text()}", color='#eceff4', fontsize=9)

            self.cm_fig.tight_layout(pad=0.5)
            self.cm_canvas.draw()
            self.cm_output.setHtml(f"<b>f(z) = {self.cm_expr.text()}</b>  —  {viz}")
            self._add_to_global_history("Analysis·Complex", viz, f"f(z)={self.cm_expr.text()}", viz)

        except Exception as e:
            self.cm_output.setHtml(f"<b style='color:#bf616a'>Error:</b> {e}")

    # ── Functional Analysis ────────────────────────────────────────────────

    def _setup_functional_analysis_subtab(self):
        tab = QWidget()
        self._an_tabs.addTab(tab, "Functional Analysis")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        fn_grp = QGroupBox("Functions")
        fg = QGridLayout(fn_grp)
        fg.setSpacing(6)
        for row, (lbl, attr, default) in enumerate([
            ("f(x) =", "fa_f", "sin(x)"),
            ("g(x) =", "fa_g", "cos(x)"),
            ("a =",    "fa_a", "0"),
            ("b =",    "fa_b", "2*pi"),
            ("p =",    "fa_p", "2"),
        ]):
            fg.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._an_field)
            setattr(self, attr, w)
            fg.addWidget(w, row, 1)
        ll.addWidget(fn_grp)

        ops_grp = QGroupBox("Operations")
        og = QGridLayout(ops_grp)
        og.setSpacing(8)
        fa_ops = [
            ("||f||_p  Lp Norm",        "lp_norm"),
            ("||f||_∞  Sup Norm",        "sup_norm"),
            ("⟨f, g⟩  Inner Product",   "inner"),
            ("d(f,g)  L2 Distance",      "l2_dist"),
            ("Convolution  f ★ g",       "convolve"),
            ("Plot f and g",             "plot_both"),
        ]
        for idx, (lbl, act) in enumerate(fa_ops):
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._an_btn)
            btn.clicked.connect(lambda _, a=act: self._run_fa(a))
            og.addWidget(btn, idx // 2, idx % 2)
        ll.addWidget(ops_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)
        self.fa_result_latex = LatexCanvas(height=90)
        rl.addWidget(self.fa_result_latex)
        rl.addWidget(self._copy_latex_btn(self.fa_result_latex), alignment=Qt.AlignmentFlag.AlignRight)
        self.fa_fig = Figure(facecolor='#1e222b')
        self.fa_canvas = FigureCanvas(self.fa_fig)
        self.fa_ax = self.fa_fig.subplots()
        self._init_fa_axes()
        rl.addWidget(self.fa_canvas, 1)
        outer.addWidget(right, 3)

    def _init_fa_axes(self):
        ax = self.fa_ax
        ax.set_facecolor('#242933')
        ax.tick_params(colors='#eceff4', labelsize=8)
        for sp in ax.spines.values(): sp.set_edgecolor('#3b4252')
        ax.grid(color='#2e3440', linestyle='--', linewidth=0.6)
        self.fa_fig.tight_layout(pad=0.8)
        self.fa_canvas.draw()

    def _run_fa(self, action):
        from scipy.integrate import quad as _quad
        try:
            x_sym = sympy.Symbol('x')
            f_expr = sympy.sympify(self.fa_f.text())
            g_expr = sympy.sympify(self.fa_g.text())
            a = float(sympy.sympify(self.fa_a.text()).evalf())
            b = float(sympy.sympify(self.fa_b.text()).evalf())
            p = float(self.fa_p.text())

            f_num = sympy.lambdify(x_sym, f_expr, 'numpy')
            g_num = sympy.lambdify(x_sym, g_expr, 'numpy')

            def safe(fn, x):
                with np.errstate(all='ignore'):
                    v = np.asarray(fn(x), dtype=complex)
                return np.where(np.isfinite(v.real), v.real, 0.0)

            xs = np.linspace(a, b, 800)
            f_vals = safe(f_num, xs)
            g_vals = safe(g_num, xs)

            def _plot_refresh():
                self.fa_ax.clear()
                self._init_fa_axes()
                self.fa_ax.plot(xs, f_vals, color='#88c0d0', linewidth=2, label='f(x)')
                self.fa_ax.plot(xs, g_vals, color='#a3be8c', linewidth=2, label='g(x)', linestyle='--')
                self.fa_ax.axhline(0, color='#4c566a', linewidth=0.6)
                self.fa_ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
                self.fa_ax.set_title(f"[{a:.4g}, {b:.4g}]", color='#eceff4', fontsize=9)
                self.fa_canvas.draw()

            if action == "lp_norm":
                integrand = lambda x: abs(safe(f_num, np.array([x]))[0]) ** p
                val = _quad(integrand, a, b)[0] ** (1/p)
                self.fa_result_latex.render(
                    r"\|f\|_{" + f"{p:.4g}" + r"} = \left(\int_a^b |f|^p\,dx\right)^{1/p} = " + f"{val:.6g}"
                )
                _plot_refresh()
                self._add_to_global_history("Analysis·FA", "Lp norm", self.fa_f.text(), f"{val:.6g}")

            elif action == "sup_norm":
                val = np.max(np.abs(f_vals))
                self.fa_result_latex.render(
                    r"\|f\|_{\infty} = \sup_{x \in [a,b]} |f(x)| = " + f"{val:.6g}"
                )
                _plot_refresh()
                self.fa_ax.axhline(val, color='#bf616a', linestyle=':', linewidth=1.2, label=f'‖f‖∞={val:.4g}')
                self.fa_ax.axhline(-val, color='#bf616a', linestyle=':', linewidth=1.2)
                self.fa_ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
                self.fa_canvas.draw()
                self._add_to_global_history("Analysis·FA", "sup norm", self.fa_f.text(), f"{val:.6g}")

            elif action == "inner":
                integrand = lambda x: safe(f_num, np.array([x]))[0] * safe(g_num, np.array([x]))[0]
                val = _quad(integrand, a, b)[0]
                self.fa_result_latex.render(
                    r"\langle f,g \rangle = \int_a^b f(x)\,g(x)\,dx = " + f"{val:.6g}"
                )
                _plot_refresh()
                prod_vals = f_vals * g_vals
                self.fa_ax.fill_between(xs, prod_vals, alpha=0.25, color='#ebcb8b', label='f·g')
                self.fa_ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
                self.fa_canvas.draw()
                self._add_to_global_history("Analysis·FA", "inner product",
                                            f"{self.fa_f.text()}, {self.fa_g.text()}", f"{val:.6g}")

            elif action == "l2_dist":
                integrand = lambda x: (safe(f_num, np.array([x]))[0] - safe(g_num, np.array([x]))[0])**2
                val = _quad(integrand, a, b)[0] ** 0.5
                self.fa_result_latex.render(
                    r"d_{L^2}(f,g) = \|f-g\|_2 = " + f"{val:.6g}"
                )
                _plot_refresh()
                diff_vals = f_vals - g_vals
                ax2 = self.fa_ax.twinx()
                ax2.fill_between(xs, diff_vals, alpha=0.3, color='#bf616a', label='f−g')
                ax2.tick_params(colors='#bf616a', labelsize=7)
                ax2.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9, loc='upper right')
                self.fa_canvas.draw()
                self._add_to_global_history("Analysis·FA", "L2 distance",
                                            f"{self.fa_f.text()}, {self.fa_g.text()}", f"{val:.6g}")

            elif action == "convolve":
                dx = (b - a) / (len(xs) - 1)
                conv = np.convolve(f_vals, g_vals, mode='full') * dx
                t_conv = np.linspace(2*a, 2*b, len(conv))
                self.fa_ax.clear()
                self._init_fa_axes()
                self.fa_ax.plot(xs, f_vals, color='#88c0d0', linewidth=1.5, label='f(x)', alpha=0.6)
                self.fa_ax.plot(xs, g_vals, color='#a3be8c', linewidth=1.5, label='g(x)', alpha=0.6, linestyle='--')
                self.fa_ax.plot(t_conv, conv, color='#ebcb8b', linewidth=2, label='(f★g)(t)')
                self.fa_ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
                self.fa_ax.set_title("Convolution  (f★g)(t)", color='#eceff4', fontsize=9)
                self.fa_canvas.draw()
                self.fa_result_latex.render(r"(f \star g)(t) = \int f(\tau)\,g(t-\tau)\,d\tau")
                self._add_to_global_history("Analysis·FA", "convolution",
                                            f"{self.fa_f.text()}, {self.fa_g.text()}", "plotted")

            elif action == "plot_both":
                _plot_refresh()
                self.fa_result_latex.render(
                    r"f(x) = " + sympy.latex(f_expr) + r"\qquad g(x) = " + sympy.latex(g_expr)
                )

        except Exception as e:
            self.fa_result_latex.render(r"\text{Error: }" + str(e)[:40])

    # ── Global history ────────────────────────────────────────────────────

    def _load_history(self):
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    self._global_history = json.load(f)
        except Exception:
            self._global_history = []

    def _save_history(self):
        try:
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(self._global_history[-500:], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _add_to_global_history(self, tab, action, input_str, result_str):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tab": tab,
            "action": action,
            "input": str(input_str)[:200],
            "result": str(result_str)[:300],
        }
        self._global_history.insert(0, entry)
        self._global_history = self._global_history[:500]
        self._save_history()
        if hasattr(self, '_history_list_widget'):
            self._history_list_widget.insertItem(0, self._make_history_item(entry))

    def _make_history_item(self, entry):
        from PyQt6.QtWidgets import QListWidgetItem
        ts = entry["timestamp"][11:]  # just time HH:MM:SS
        text = f"[{ts}]  {entry['tab']}  ·  {entry['action']}\n  {entry['input'][:60]}  →  {entry['result'][:80]}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, entry)
        return item

    def setup_history_tab(self):
        hist_widget = QWidget()
        self.tabs.addTab(hist_widget, "History")

        layout = QVBoxLayout(hist_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Search bar
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Filter:"))
        self._history_search = QLineEdit()
        self._history_search.setPlaceholderText("Type to filter by tab, operation, or expression…")
        self._history_search.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
            "color: #eceff4; font-size: 13px; padding: 6px;"
        )
        self._history_search.textChanged.connect(self._filter_history)
        search_row.addWidget(self._history_search)
        layout.addLayout(search_row)

        # List
        self._history_list_widget = QListWidget()
        self._history_list_widget.setObjectName("historyList")
        self._history_list_widget.setStyleSheet("""
            QListWidget { background-color: #1e222b; border: 1px solid #2e3440;
                          border-radius: 8px; color: #eceff4; font-size: 12px; }
            QListWidget::item { background-color: #242933; border-radius: 6px;
                                margin: 2px 4px; padding: 6px 8px; }
            QListWidget::item:hover { background-color: #2e3440; }
            QListWidget::item:selected { background-color: #3b4a6b; color: #88c0d0; }
        """)
        self._history_list_widget.setSpacing(2)
        self._history_list_widget.itemDoubleClicked.connect(self._history_copy_result)

        for entry in self._global_history:
            self._history_list_widget.addItem(self._make_history_item(entry))

        layout.addWidget(self._history_list_widget, 1)

        hint = QLabel("Double-click an entry to copy the result to clipboard.")
        hint.setStyleSheet("color: #4c566a; font-size: 11px;")
        layout.addWidget(hint)

        # Buttons
        btn_row = QHBoxLayout()
        btn_style = (
            "font-size: 12px; font-weight: bold; min-height: 34px; "
            "background-color: #2e3440; color: #81a1c1; "
            "border: 1px solid #3b4252; border-radius: 8px; padding: 0 12px;"
        )
        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet(btn_style)
        clear_btn.clicked.connect(self._clear_global_history)
        export_btn = QPushButton("Export to .txt")
        export_btn.setStyleSheet(btn_style)
        export_btn.clicked.connect(self._export_history)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _history_copy_result(self, item):
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry:
            QApplication.clipboard().setText(entry.get("result", ""))

    def _filter_history(self, text):
        text = text.lower()
        for i in range(self._history_list_widget.count()):
            item = self._history_list_widget.item(i)
            entry = item.data(Qt.ItemDataRole.UserRole)
            visible = (
                not text or
                text in entry.get("tab", "").lower() or
                text in entry.get("action", "").lower() or
                text in entry.get("input", "").lower() or
                text in entry.get("result", "").lower()
            )
            item.setHidden(not visible)

    def _clear_global_history(self):
        self._global_history = []
        self._history_list_widget.clear()
        self._save_history()

    def _export_history(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history_export.txt')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for entry in self._global_history:
                    f.write(f"[{entry['timestamp']}]  {entry['tab']}  ·  {entry['action']}\n")
                    f.write(f"  Input:  {entry['input']}\n")
                    f.write(f"  Result: {entry['result']}\n\n")
            self._history_search.setPlaceholderText(f"Exported to {path}")
        except Exception as e:
            self._history_search.setPlaceholderText(f"Export failed: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    
    window = Karhulaattori()
    window.show()
    sys.exit(app.exec())
