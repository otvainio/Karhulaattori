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
    QLabel, QSplitter, QFrame, QTabWidget, QTextBrowser, QTextEdit, QGroupBox, QScrollArea
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
        self.setup_calculator_tab()
        self.setup_symbolic_tab()
        self.setup_linear_algebra_tab()
        self.setup_complex_tab()
        
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
            ("Solve ODE", "solve_ode"),
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    
    window = Karhulaattori()
    window.show()
    sys.exit(app.exec())
