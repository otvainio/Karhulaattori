import sys
import json
import math
import re
import os
from datetime import datetime
import sympy
import numpy as np
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers 3D projection
import networkx as nx
from scipy.integrate import quad as _quad, fixed_quad, solve_ivp
from scipy.interpolate import CubicSpline, interp1d
from scipy.optimize import brentq, curve_fit, fsolve
from scipy import stats as _stats, special as sc

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QGridLayout, QListWidget, QListWidgetItem,
    QLabel, QSplitter, QFrame, QTabWidget, QTextBrowser, QTextEdit, QGroupBox, QScrollArea,
    QComboBox, QCheckBox
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
    border: 1px solid #7b88a8;
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

/* Labels */
QLabel {
    color: #d8dee9;
    font-size: 12px;
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


def _user_data_dir() -> str:
    """Return a writable user-data directory, creating it if needed."""
    try:
        from platformdirs import user_data_dir
        d = user_data_dir("Karhulaattori", "Karhulaattori")
    except ImportError:
        d = os.path.join(os.path.expanduser("~"), ".karhulaattori")
    os.makedirs(d, exist_ok=True)
    return d


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
    _FIELD_STYLE = (
        "background-color: #242933; border: 1px solid #3b4252; "
        "border-radius: 8px; color: #eceff4; "
        "font-family: 'Consolas', monospace; font-size: 13px; padding: 5px;"
    )
    _BTN_STYLE = (
        "font-size: 12px; font-weight: bold; "
        "background-color: #2f384c; color: #a3be8c; min-height: 34px;"
    )
    _BTN_STYLE_SM = (
        "font-size: 12px; font-weight: bold; "
        "background-color: #2f384c; color: #a3be8c; min-height: 26px;"
    )
    _COMBO_STYLE = (
        "background-color: #242933; color: #eceff4; border: 1px solid #3b4252; "
        "border-radius: 6px; padding: 4px; font-size: 12px;"
    )

    @staticmethod
    def _err_html(e):
        return f"<b style='color:#bf616a'>Error:</b> {e}"

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
        self._history_file = os.path.join(_user_data_dir(), 'history.json')
        self._global_history = []
        self._load_history()

        self.setup_calculator_tab()
        self.setup_symbolic_tab()
        self.setup_geometry_tab()
        self.setup_linear_algebra_tab()
        self.setup_complex_tab()
        self.setup_calculus_tab()
        self.setup_de_tab()
        self.setup_statistics_tab()
        self.setup_3d_graphing_tab()
        self.setup_number_theory_tab()
        self.setup_analysis_tab()
        self.setup_numerical_tab()
        self.setup_graph_theory_tab()
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

    # ── Shared plot/widget helpers ─────────────────────────────────────────

    def _style_axes(self, ax, equal=False):
        ax.set_facecolor('#242933')
        ax.tick_params(colors='#eceff4', labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor('#3b4252')
        ax.grid(color='#2e3440', linestyle='--', linewidth=0.6)
        if equal:
            ax.set_aspect('equal', adjustable='datalim')

    def _make_output(self, layout, attr, max_h=120):
        tb = QTextBrowser()
        tb.setMaximumHeight(max_h)
        tb.setStyleSheet(
            "background-color: #1e222b; border: 1px solid #2e3440; border-radius: 6px; "
            "color: #a3be8c; font-family: 'Consolas', monospace; font-size: 12px; padding: 6px;"
        )
        setattr(self, attr, tb)
        layout.addWidget(tb)

    def _make_figure(self):
        fig = Figure(facecolor='#1e222b')
        return fig, FigureCanvas(fig)

    def _gt_get_graph(self):
        if self._gt_graph is None:
            self._gt_graph = self._gt_parse_graph()
        return self._gt_graph

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
            border: 1px solid #7b88a8;
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

    # ══════════════════════════════════════════════════════════════════════
    # Geometry tab  (Triangle · Conics · Shapes · Transformations)
    # ══════════════════════════════════════════════════════════════════════

    def setup_geometry_tab(self):
        w = QWidget()
        self.tabs.addTab(w, "Geometry")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(4, 4, 4, 4)
        self._geo_tabs = QTabWidget()
        outer.addWidget(self._geo_tabs)
        self._setup_geo_triangle()
        self._setup_geo_conics()
        self._setup_geo_shapes()
        self._setup_geo_transforms()

    # ── Triangle Solver ──────────────────────────────────────────────────────

    def _setup_geo_triangle(self):
        tab = QWidget()
        self._geo_tabs.addTab(tab, "Triangle")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("Known values  (leave unknowns blank)")
        g = QGridLayout(grp)
        g.setSpacing(6)
        hint = QLabel("Sides a, b, c  opposite to angles A, B, C (degrees).")
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        hint.setWordWrap(True)
        g.addWidget(hint, 0, 0, 1, 4)

        self._tri_fields = {}
        for col, name in enumerate(['a', 'b', 'c', 'A', 'B', 'C']):
            g.addWidget(QLabel(name + " ="), 1, col % 3 * 2)
            le = QLineEdit()
            le.setStyleSheet(self._FIELD_STYLE)
            le.setPlaceholderText("?")
            g.addWidget(le, 1 + col // 3, col % 3 * 2 + 1)
            self._tri_fields[name] = le

        # Presets
        preset_row = QHBoxLayout()
        for label, vals in [
            ("3-4-5", dict(a='3', b='4', c='5', A='', B='', C='')),
            ("Equilateral", dict(a='5', b='5', c='5', A='', B='', C='')),
            ("30-60-90", dict(a='1', b='', c='2', A='30', B='60', C='90')),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(self._BTN_STYLE_SM)
            btn.clicked.connect(lambda _, v=vals: [self._tri_fields[k].setText(v[k]) for k in v])
            preset_row.addWidget(btn)
        g.addLayout(preset_row, 4, 0, 1, 6)

        solve_btn = QPushButton("Solve Triangle")
        solve_btn.setStyleSheet(self._BTN_STYLE)
        solve_btn.clicked.connect(self._run_triangle)
        g.addWidget(solve_btn, 5, 0, 1, 6)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._geo_tri_fig, self._geo_tri_canvas = self._make_figure()
        rl.addWidget(self._geo_tri_canvas, 1)
        self._make_output(rl, '_geo_tri_out', 140)
        outer.addWidget(right, 3)

    def _run_triangle(self):
        try:
            def _get(name):
                t = self._tri_fields[name].text().strip()
                return float(t) if t else None

            a, b, c = _get('a'), _get('b'), _get('c')
            A, B, C = _get('A'), _get('B'), _get('C')

            # Convert angles to radians
            def r(deg): return math.radians(deg) if deg is not None else None
            Ar, Br, Cr = r(A), r(B), r(C)

            known_sides  = sum(x is not None for x in [a, b, c])
            known_angles = sum(x is not None for x in [A, B, C])

            # Fill missing angle if two angles known
            if known_angles == 2:
                if A is None: A = 180 - (B + C); Ar = r(A)
                elif B is None: B = 180 - (A + C); Br = r(B)
                else:          C = 180 - (A + B); Cr = r(C)
                known_angles = 3

            # SSS
            if known_sides == 3 and a and b and c:
                cos_A = (b**2 + c**2 - a**2) / (2*b*c)
                A = math.degrees(math.acos(max(-1, min(1, cos_A)))); Ar = r(A)
                cos_B = (a**2 + c**2 - b**2) / (2*a*c)
                B = math.degrees(math.acos(max(-1, min(1, cos_B)))); Br = r(B)
                C = 180 - A - B; Cr = r(C)
            # SAS
            elif known_sides == 2 and known_angles >= 1:
                if a and b and Cr:
                    c = math.sqrt(a**2 + b**2 - 2*a*b*math.cos(Cr))
                    cos_A = (b**2 + c**2 - a**2)/(2*b*c); A = math.degrees(math.acos(max(-1,min(1,cos_A)))); Ar=r(A)
                    B = 180 - A - C; Br = r(B)
                elif a and c and Br:
                    b = math.sqrt(a**2 + c**2 - 2*a*c*math.cos(Br))
                    cos_A = (b**2 + c**2 - a**2)/(2*b*c); A = math.degrees(math.acos(max(-1,min(1,cos_A)))); Ar=r(A)
                    C = 180 - A - B; Cr = r(C)
                elif b and c and Ar:
                    a = math.sqrt(b**2 + c**2 - 2*b*c*math.cos(Ar))
                    cos_B = (a**2 + c**2 - b**2)/(2*a*c); B = math.degrees(math.acos(max(-1,min(1,cos_B)))); Br=r(B)
                    C = 180 - A - B; Cr = r(C)
            # ASA / AAS — law of sines
            elif known_angles == 3 and known_sides >= 1:
                if a and Ar:
                    k = a / math.sin(Ar)
                elif b and Br:
                    k = b / math.sin(Br)
                else:
                    k = c / math.sin(Cr)
                if not a: a = k * math.sin(Ar)
                if not b: b = k * math.sin(Br)
                if not c: c = k * math.sin(Cr)

            if None in (a, b, c, A, B, C):
                raise ValueError("Not enough information to solve the triangle.")

            # Derived quantities
            s = (a + b + c) / 2
            area = math.sqrt(s*(s-a)*(s-b)*(s-c))
            R = (a * b * c) / (4 * area)   # circumradius
            r_in = area / s                  # inradius
            h_a = 2*area / a

            # Build triangle vertices: place c on x-axis, A at origin
            Bx, By = c, 0.0
            Cx = (a**2 - b**2 + c**2) / (2*c)
            Cy = math.sqrt(max(0, a**2 - (c - Cx)**2)) if a**2 - (c-Cx)**2 >= 0 else 0
            verts = np.array([[0,0],[Bx,By],[Cx,Cy],[0,0]])

            self._geo_tri_fig.clear()
            ax = self._geo_tri_fig.add_subplot(111)
            self._style_axes(ax, equal=True)
            ax.plot(verts[:,0], verts[:,1], color='#88c0d0', linewidth=2)
            ax.fill(verts[:-1,0], verts[:-1,1], alpha=0.12, color='#88c0d0')
            for (px,py), lbl in zip([(0,0),(Bx,By),(Cx,Cy)], ['A','B','C']):
                ax.annotate(lbl, (px,py), fontsize=11, color='#ebcb8b',
                            textcoords='offset points', xytext=(6,6))
            # Side labels
            for (p1,p2), lbl in zip([((0,0),(Cx,Cy)),((Bx,By),(Cx,Cy)),((0,0),(Bx,By))],
                                     [f'b={b:.4g}',f'a={a:.4g}',f'c={c:.4g}']):
                mx,my = (p1[0]+p2[0])/2,(p1[1]+p2[1])/2
                ax.annotate(lbl,(mx,my),fontsize=8,color='#a3be8c',
                            textcoords='offset points',xytext=(4,4))
            ax.set_title("Triangle", color='#eceff4', fontsize=9)
            self._geo_tri_fig.tight_layout(pad=0.6)
            self._geo_tri_canvas.draw_idle()

            self._geo_tri_out.setHtml(
                f"<b>Sides:</b>  a = {a:.6g},  b = {b:.6g},  c = {c:.6g}<br>"
                f"<b>Angles:</b> A = {A:.4g}°,  B = {B:.4g}°,  C = {C:.4g}°<br>"
                f"<b>Area</b> = {area:.6g} &nbsp;&nbsp; <b>Perimeter</b> = {a+b+c:.6g}<br>"
                f"<b>Circumradius R</b> = {R:.6g} &nbsp;&nbsp; <b>Inradius r</b> = {r_in:.6g}<br>"
                f"<b>Height h_a</b> = {h_a:.6g}"
            )
            self._add_to_global_history("Geometry·Triangle", "solve",
                                        f"a={a:.4g},b={b:.4g},c={c:.4g}",
                                        f"A={A:.3g}°,B={B:.3g}°,C={C:.3g}°,area={area:.4g}")
        except Exception as e:
            self._geo_tri_out.setHtml(self._err_html(e))

    # ── Conics ───────────────────────────────────────────────────────────────

    def _setup_geo_conics(self):
        tab = QWidget()
        self._geo_tabs.addTab(tab, "Conics")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("Conic Section")
        g = QGridLayout(grp)
        g.setSpacing(6)
        g.addWidget(QLabel("Type:"), 0, 0)
        self._geo_conic_type = QComboBox()
        self._geo_conic_type.addItems(["Circle", "Ellipse", "Parabola", "Hyperbola"])
        self._geo_conic_type.setStyleSheet(
            self._COMBO_STYLE
        )
        self._geo_conic_type.currentIndexChanged.connect(self._update_conic_hints)
        g.addWidget(self._geo_conic_type, 0, 1)

        self._conic_params = {}
        for row, (lbl, attr, default) in enumerate([
            ("h  (center x):", "_cp_h", "0"),
            ("k  (center y):", "_cp_k", "0"),
            ("a  (semi-major/focal):", "_cp_a", "3"),
            ("b  (semi-minor):", "_cp_b", "2"),
        ], start=1):
            g.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            self._conic_params[attr] = (g.itemAtPosition(row,0).widget(), w)
            g.addWidget(w, row, 1)

        self._conic_hint = QLabel("")
        self._conic_hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        self._conic_hint.setWordWrap(True)
        g.addWidget(self._conic_hint, 5, 0, 1, 2)

        plot_btn = QPushButton("Plot Conic")
        plot_btn.setStyleSheet(self._BTN_STYLE)
        plot_btn.clicked.connect(self._run_conic)
        g.addWidget(plot_btn, 6, 0, 1, 2)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._geo_con_fig, self._geo_con_canvas = self._make_figure()
        rl.addWidget(self._geo_con_canvas, 1)
        self._make_output(rl, '_geo_con_out', 120)
        outer.addWidget(right, 3)
        self._update_conic_hints()

    def _update_conic_hints(self):
        t = self._geo_conic_type.currentText()
        hints = {
            "Circle":    "Equation: (x-h)²+(y-k)²=a²   (b ignored)",
            "Ellipse":   "Equation: (x-h)²/a²+(y-k)²/b²=1   (a>b for horizontal)",
            "Parabola":  "Equation: y-k = (1/4p)(x-h)²   (a=focal length p, b ignored)",
            "Hyperbola": "Equation: (x-h)²/a²−(y-k)²/b²=1",
        }
        self._conic_hint.setText(hints.get(t, ""))

    def _run_conic(self):
        try:
            t = self._geo_conic_type.currentText()
            h = float(self._cp_h.text()); k = float(self._cp_k.text())
            a = float(self._cp_a.text()); b = float(self._cp_b.text())

            self._geo_con_fig.clear()
            ax = self._geo_con_fig.add_subplot(111)
            self._style_axes(ax, equal=True)
            ax.axhline(0, color='#7b88a8', linewidth=0.6)
            ax.axvline(0, color='#7b88a8', linewidth=0.6)

            info_lines = []

            if t == "Circle":
                th = np.linspace(0, 2*np.pi, 400)
                ax.plot(h + a*np.cos(th), k + a*np.sin(th), color='#88c0d0', linewidth=2)
                ax.plot(h, k, '+', color='#ebcb8b', markersize=10)
                info_lines = [
                    f"Circle:  (x−{h})² + (y−{k})² = {a}²",
                    f"Radius r = {a}",
                    f"Diameter = {2*a:.6g}",
                    f"Area = π·r² = {math.pi*a**2:.6g}",
                    f"Circumference = 2π·r = {2*math.pi*a:.6g}",
                ]

            elif t == "Ellipse":
                th = np.linspace(0, 2*np.pi, 400)
                ax.plot(h + a*np.cos(th), k + b*np.sin(th), color='#88c0d0', linewidth=2)
                ax.plot(h, k, '+', color='#ebcb8b', markersize=10)
                c_val = math.sqrt(abs(a**2 - b**2))
                e = c_val / a if a > 0 else 0
                area = math.pi * a * b
                # Foci
                if a >= b:
                    ax.plot([h-c_val, h+c_val], [k, k], 'o', color='#bf616a', markersize=6)
                else:
                    ax.plot([h, h], [k-c_val, k+c_val], 'o', color='#bf616a', markersize=6)
                info_lines = [
                    f"Ellipse:  (x−{h})²/{a}² + (y−{k})²/{b}² = 1",
                    f"Semi-major a={a},  semi-minor b={b}",
                    f"c = √|a²−b²| = {c_val:.6g}",
                    f"Eccentricity e = {e:.6g}",
                    f"Area = π·a·b = {area:.6g}",
                ]

            elif t == "Parabola":
                p = a  # focal parameter
                x_vals = np.linspace(h - 4*abs(p), h + 4*abs(p), 400)
                y_vals = k + (x_vals - h)**2 / (4*p)
                ax.plot(x_vals, y_vals, color='#88c0d0', linewidth=2)
                focus_y = k + p
                directrix_y = k - p
                ax.plot(h, focus_y, 'o', color='#bf616a', markersize=7, label=f'Focus ({h:.4g}, {focus_y:.4g})')
                ax.axhline(directrix_y, color='#ebcb8b', linestyle='--', linewidth=1,
                           label=f'Directrix y={directrix_y:.4g}')
                ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=8)
                info_lines = [
                    f"Parabola: y−{k} = (1/{4*p:.4g})(x−{h})²",
                    f"Focal length p = {p}",
                    f"Focus: ({h:.4g}, {focus_y:.4g})",
                    f"Directrix: y = {directrix_y:.4g}",
                    f"Vertex: ({h}, {k})",
                ]

            elif t == "Hyperbola":
                # Right branch
                t_vals = np.linspace(-np.pi/2 + 0.05, np.pi/2 - 0.05, 300)
                ax.plot(h + a/np.cos(t_vals), k + b*np.tan(t_vals), color='#88c0d0', linewidth=2)
                # Left branch
                ax.plot(h - a/np.cos(t_vals), k + b*np.tan(t_vals), color='#88c0d0', linewidth=2)
                c_val = math.sqrt(a**2 + b**2)
                e = c_val / a
                # Foci
                ax.plot([h-c_val, h+c_val], [k, k], 'o', color='#bf616a', markersize=6)
                # Asymptotes
                xl = np.array([h-4*a, h+4*a])
                ax.plot(xl, k + (b/a)*(xl-h), color='#7b88a8', linestyle=':', linewidth=1)
                ax.plot(xl, k - (b/a)*(xl-h), color='#7b88a8', linestyle=':', linewidth=1)
                info_lines = [
                    f"Hyperbola: (x−{h})²/{a}² − (y−{k})²/{b}² = 1",
                    f"c = √(a²+b²) = {c_val:.6g}",
                    f"Eccentricity e = {e:.6g}",
                    f"Asymptotes: y−{k} = ±({b}/{a})(x−{h})",
                    f"Foci: ({h-c_val:.4g},{k}), ({h+c_val:.4g},{k})",
                ]

            ax.set_title(f"{t}  (h={h}, k={k}, a={a}, b={b})", color='#eceff4', fontsize=9)
            self._geo_con_fig.tight_layout(pad=0.6)
            self._geo_con_canvas.draw_idle()
            self._geo_con_out.setHtml("<br>".join(f"<b>{l.split(':')[0]}:</b>{':'.join(l.split(':')[1:])}" if ':' in l else l for l in info_lines))
            self._add_to_global_history("Geometry·Conics", t, f"h={h},k={k},a={a},b={b}", info_lines[0])

        except Exception as e:
            self._geo_con_out.setHtml(self._err_html(e))

    # ── 2D Shapes ────────────────────────────────────────────────────────────

    def _setup_geo_shapes(self):
        tab = QWidget()
        self._geo_tabs.addTab(tab, "Shapes")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("Shape")
        g = QGridLayout(grp)
        g.setSpacing(6)
        g.addWidget(QLabel("Shape:"), 0, 0)
        self._geo_shape_type = QComboBox()
        self._geo_shape_type.addItems([
            "Circle", "Rectangle", "Square", "Triangle (equilateral)",
            "Regular Polygon", "Sector", "Annulus", "Trapezoid",
        ])
        self._geo_shape_type.setStyleSheet(
            self._COMBO_STYLE
        )
        g.addWidget(self._geo_shape_type, 0, 1)

        self._shape_params = []
        for row, (lbl, attr, default) in enumerate([
            ("p1  (r / width / side):", "_sp1", "4"),
            ("p2  (height / n-sides):", "_sp2", "3"),
            ("p3  (angle° / b1):",      "_sp3", "90"),
            ("p4  (b2 for trapezoid):", "_sp4", "6"),
        ], start=1):
            g.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            g.addWidget(w, row, 1)

        calc_btn = QPushButton("Calculate & Draw")
        calc_btn.setStyleSheet(self._BTN_STYLE)
        calc_btn.clicked.connect(self._run_shape)
        g.addWidget(calc_btn, 5, 0, 1, 2)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._geo_shp_fig, self._geo_shp_canvas = self._make_figure()
        rl.addWidget(self._geo_shp_canvas, 1)
        self._make_output(rl, '_geo_shp_out', 130)
        outer.addWidget(right, 3)

    def _run_shape(self):
        try:
            t  = self._geo_shape_type.currentText()
            p1 = float(self._sp1.text())
            p2 = float(self._sp2.text())
            p3 = float(self._sp3.text())
            p4 = float(self._sp4.text())

            self._geo_shp_fig.clear()
            ax = self._geo_shp_fig.add_subplot(111)
            self._style_axes(ax, equal=True)

            info = {}

            if t == "Circle":
                r = p1
                th = np.linspace(0, 2*np.pi, 400)
                ax.fill(r*np.cos(th), r*np.sin(th), alpha=0.18, color='#88c0d0')
                ax.plot(r*np.cos(th), r*np.sin(th), color='#88c0d0', linewidth=2)
                info = {"Radius": r, "Diameter": 2*r,
                        "Area": math.pi*r**2, "Circumference": 2*math.pi*r}

            elif t == "Rectangle":
                w, h = p1, p2
                rect = np.array([[0,0],[w,0],[w,h],[0,h],[0,0]])
                ax.fill(rect[:-1,0], rect[:-1,1], alpha=0.18, color='#88c0d0')
                ax.plot(rect[:,0], rect[:,1], color='#88c0d0', linewidth=2)
                diag = math.sqrt(w**2+h**2)
                info = {"Width": w, "Height": h, "Area": w*h,
                        "Perimeter": 2*(w+h), "Diagonal": diag}

            elif t == "Square":
                s = p1
                sq = np.array([[0,0],[s,0],[s,s],[0,s],[0,0]])
                ax.fill(sq[:-1,0], sq[:-1,1], alpha=0.18, color='#88c0d0')
                ax.plot(sq[:,0], sq[:,1], color='#88c0d0', linewidth=2)
                info = {"Side": s, "Area": s**2,
                        "Perimeter": 4*s, "Diagonal": s*math.sqrt(2)}

            elif t == "Triangle (equilateral)":
                s = p1
                h_tri = s * math.sqrt(3) / 2
                verts = np.array([[0,0],[s,0],[s/2,h_tri],[0,0]])
                ax.fill(verts[:-1,0], verts[:-1,1], alpha=0.18, color='#88c0d0')
                ax.plot(verts[:,0], verts[:,1], color='#88c0d0', linewidth=2)
                info = {"Side": s, "Height": h_tri,
                        "Area": math.sqrt(3)/4*s**2, "Perimeter": 3*s,
                        "Inradius": s/(2*math.sqrt(3)), "Circumradius": s/math.sqrt(3)}

            elif t == "Regular Polygon":
                s = p1; n = int(p2)
                R = s / (2 * math.sin(math.pi/n))
                angles = np.linspace(0, 2*np.pi, n+1) + math.pi/2
                xs_p = R * np.cos(angles); ys_p = R * np.sin(angles)
                ax.fill(xs_p[:-1], ys_p[:-1], alpha=0.18, color='#88c0d0')
                ax.plot(xs_p, ys_p, color='#88c0d0', linewidth=2)
                apothem = R * math.cos(math.pi/n)
                area = 0.5 * n * s * apothem
                info = {"Sides n": n, "Side length": s,
                        "Circumradius R": R, "Apothem": apothem,
                        "Perimeter": n*s, "Area": area,
                        "Interior angle °": (n-2)*180/n}

            elif t == "Sector":
                r = p1; angle_deg = p3
                angle_rad = math.radians(angle_deg)
                th = np.linspace(0, angle_rad, 300)
                xs_s = np.concatenate([[0], r*np.cos(th), [0]])
                ys_s = np.concatenate([[0], r*np.sin(th), [0]])
                ax.fill(xs_s, ys_s, alpha=0.18, color='#88c0d0')
                ax.plot(xs_s, ys_s, color='#88c0d0', linewidth=2)
                arc_len = r * angle_rad
                area = 0.5 * r**2 * angle_rad
                info = {"Radius": r, "Angle °": angle_deg,
                        "Arc length": arc_len, "Area": area,
                        "Chord length": 2*r*math.sin(angle_rad/2)}

            elif t == "Annulus":
                R_out, R_in = p1, p2
                th = np.linspace(0, 2*np.pi, 400)
                ax.fill(R_out*np.cos(th), R_out*np.sin(th), color='#88c0d0', alpha=0.25)
                ax.fill(R_in*np.cos(th), R_in*np.sin(th), color='#1e222b', alpha=1.0)
                ax.plot(R_out*np.cos(th), R_out*np.sin(th), color='#88c0d0', linewidth=2)
                ax.plot(R_in*np.cos(th), R_in*np.sin(th), color='#88c0d0', linewidth=2)
                info = {"Outer radius": R_out, "Inner radius": R_in,
                        "Area": math.pi*(R_out**2-R_in**2),
                        "Outer circ.": 2*math.pi*R_out,
                        "Inner circ.": 2*math.pi*R_in}

            elif t == "Trapezoid":
                b1, b2, h = p3, p4, p2
                offset = (b2 - b1) / 2
                verts = np.array([[0,0],[b1,0],[b1+offset,h],[-offset,h],[0,0]])
                ax.fill(verts[:-1,0], verts[:-1,1], alpha=0.18, color='#88c0d0')
                ax.plot(verts[:,0], verts[:,1], color='#88c0d0', linewidth=2)
                leg = math.sqrt(offset**2 + h**2)
                info = {"Base 1": b1, "Base 2": b2, "Height": h,
                        "Area": (b1+b2)*h/2,
                        "Perimeter": b1+b2+2*leg,
                        "Median": (b1+b2)/2}

            ax.set_title(t, color='#eceff4', fontsize=9)
            self._geo_shp_fig.tight_layout(pad=0.6)
            self._geo_shp_canvas.draw_idle()

            html = "".join(f"<b>{k}:</b> {v:.6g}<br>" if isinstance(v, float) else f"<b>{k}:</b> {v}<br>"
                           for k, v in info.items())
            self._geo_shp_out.setHtml(html)
            summary = "  ".join(f"{k}={v:.4g}" if isinstance(v, float) else f"{k}={v}" for k,v in info.items())
            self._add_to_global_history("Geometry·Shapes", t, "", summary[:200])

        except Exception as e:
            self._geo_shp_out.setHtml(self._err_html(e))

    # ── Transformations ───────────────────────────────────────────────────────

    def _setup_geo_transforms(self):
        tab = QWidget()
        self._geo_tabs.addTab(tab, "Transformations")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        shape_grp = QGroupBox("Shape  (vertices as  x1,y1; x2,y2; …)")
        sg = QGridLayout(shape_grp)
        sg.setSpacing(6)
        self._geo_xf_pts = QTextEdit("0,0; 3,0; 3,2; 0,2")
        self._geo_xf_pts.setFixedHeight(40)
        self._geo_xf_pts.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
            "color: #eceff4; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px;"
        )
        sg.addWidget(self._geo_xf_pts, 0, 0, 1, 2)
        # Presets
        preset_row = QHBoxLayout()
        for label, pts in [
            ("Square", "0,0; 1,0; 1,1; 0,1"),
            ("Triangle", "0,0; 2,0; 1,2"),
            ("Star", "0,2; 0.6,0.8; 2,0.6; 0.9,-0.2; 1.2,-1.6; 0,-0.6; -1.2,-1.6; -0.9,-0.2; -2,0.6; -0.6,0.8"),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(self._BTN_STYLE_SM)
            btn.clicked.connect(lambda _, p=pts: self._geo_xf_pts.setPlainText(p))
            preset_row.addWidget(btn)
        sg.addLayout(preset_row, 1, 0, 1, 2)
        ll.addWidget(shape_grp)

        xf_grp = QGroupBox("Transformation")
        xg = QGridLayout(xf_grp)
        xg.setSpacing(6)
        xg.addWidget(QLabel("Type:"), 0, 0)
        self._geo_xf_type = QComboBox()
        self._geo_xf_type.addItems([
            "Rotation", "Reflection", "Scaling", "Translation",
            "Shear", "Custom Matrix",
        ])
        self._geo_xf_type.setStyleSheet(
            self._COMBO_STYLE
        )
        xg.addWidget(self._geo_xf_type, 0, 1)

        for row, (lbl, attr, default) in enumerate([
            ("p1  (angle° / axis / sx / dx / shear):", "_xp1", "45"),
            ("p2  (sy for scale / dy for translation):", "_xp2", "1"),
            ("p3  (pivot x  or  0):", "_xp3", "0"),
            ("p4  (pivot y  or  0):", "_xp4", "0"),
            ("Matrix row 1  (a,b):", "_xp_m1", "0,-1"),
            ("Matrix row 2  (c,d):", "_xp_m2", "1,0"),
        ], start=1):
            xg.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            xg.addWidget(w, row, 1)

        apply_btn = QPushButton("Apply Transformation")
        apply_btn.setStyleSheet(self._BTN_STYLE)
        apply_btn.clicked.connect(self._run_transform)
        xg.addWidget(apply_btn, 7, 0, 1, 2)
        ll.addWidget(xf_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._geo_xf_fig, self._geo_xf_canvas = self._make_figure()
        rl.addWidget(self._geo_xf_canvas, 1)
        self._make_output(rl, '_geo_xf_out', 100)
        outer.addWidget(right, 3)

    def _parse_pts(self, text):
        pts = []
        for seg in text.replace('\n', ';').split(';'):
            seg = seg.strip()
            if not seg:
                continue
            parts = seg.replace(',', ' ').split()
            if len(parts) >= 2:
                pts.append([float(parts[0]), float(parts[1])])
        return np.array(pts)

    def _run_transform(self):
        try:
            pts = self._parse_pts(self._geo_xf_pts.toPlainText())
            if len(pts) < 2:
                raise ValueError("Need at least 2 vertices.")
            t  = self._geo_xf_type.currentText()
            p1 = float(self._xp1.text())
            p2 = float(self._xp2.text())
            p3 = float(self._xp3.text())
            p4 = float(self._xp4.text())

            pivot = np.array([p3, p4])
            centered = pts - pivot

            if t == "Rotation":
                theta = math.radians(p1)
                M = np.array([[math.cos(theta), -math.sin(theta)],
                               [math.sin(theta),  math.cos(theta)]])
                new_pts = (M @ centered.T).T + pivot
                desc = f"Rotation {p1}° about ({p3},{p4})"

            elif t == "Reflection":
                axis = int(p1) % 4  # 0=x-axis,1=y-axis,2=y=x,3=y=-x
                axes = {0: np.array([[1,0],[0,-1]]),
                        1: np.array([[-1,0],[0,1]]),
                        2: np.array([[0,1],[1,0]]),
                        3: np.array([[0,-1],[-1,0]])}
                M = axes[axis]
                new_pts = (M @ centered.T).T + pivot
                axis_names = {0:"x-axis",1:"y-axis",2:"y=x",3:"y=-x"}
                desc = f"Reflection about {axis_names[axis]}"

            elif t == "Scaling":
                sx, sy = p1, p2
                M = np.array([[sx,0],[0,sy]])
                new_pts = (M @ centered.T).T + pivot
                desc = f"Scale sx={sx}, sy={sy} about ({p3},{p4})"

            elif t == "Translation":
                dx, dy = p1, p2
                new_pts = pts + np.array([dx, dy])
                desc = f"Translation dx={dx}, dy={dy}"

            elif t == "Shear":
                kx = p1  # horizontal shear
                M = np.array([[1, kx],[0, 1]])
                new_pts = (M @ centered.T).T + pivot
                desc = f"Shear kx={kx}"

            elif t == "Custom Matrix":
                r1 = [float(x) for x in self._xp_m1.text().split(',')]
                r2 = [float(x) for x in self._xp_m2.text().split(',')]
                M = np.array([r1, r2])
                new_pts = (M @ centered.T).T + pivot
                det = float(np.linalg.det(M))
                desc = f"Matrix [[{r1[0]},{r1[1]}],[{r2[0]},{r2[1]}]]  det={det:.4g}"

            # Close polygons for drawing
            def close(p):
                return np.vstack([p, p[0]])

            self._geo_xf_fig.clear()
            ax = self._geo_xf_fig.add_subplot(111)
            self._style_axes(ax, equal=True)
            ax.axhline(0, color='#7b88a8', linewidth=0.5)
            ax.axvline(0, color='#7b88a8', linewidth=0.5)

            orig_c = close(pts)
            new_c  = close(new_pts)
            ax.fill(orig_c[:,0], orig_c[:,1], alpha=0.15, color='#88c0d0')
            ax.plot(orig_c[:,0], orig_c[:,1], color='#88c0d0', linewidth=2, label='Original')
            ax.fill(new_c[:,0], new_c[:,1], alpha=0.15, color='#a3be8c')
            ax.plot(new_c[:,0], new_c[:,1], color='#a3be8c', linewidth=2, linestyle='--', label='Transformed')

            # Draw arrows for a few corresponding vertices
            for o, n in zip(pts[:4], new_pts[:4]):
                ax.annotate("", xy=n, xytext=o,
                            arrowprops=dict(arrowstyle='->', color='#ebcb8b', lw=1.2))

            ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
            ax.set_title(desc, color='#eceff4', fontsize=9)
            self._geo_xf_fig.tight_layout(pad=0.6)
            self._geo_xf_canvas.draw_idle()

            self._geo_xf_out.setHtml(
                f"<b>{desc}</b><br>"
                f"Vertices: {len(pts)}  →  " +
                "  ".join(f"({x:.3g},{y:.3g})" for x,y in new_pts)
            )
            self._add_to_global_history("Geometry·Transforms", t,
                                        f"{len(pts)} pts", desc)

        except Exception as e:
            self._geo_xf_out.setHtml(self._err_html(e))

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
            self.la_output.setHtml(self._err_html(e))
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
            if not self.expression and 'x' not in self.current_input and '(' not in self.current_input:
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
            sp.set_edgecolor('#7b88a8')
        self.ax.grid(color='#2e3440', linestyle='--', alpha=0.6)
        self.ax.axhline(0, color='#7b88a8', linewidth=1.0)
        self.ax.axvline(0, color='#7b88a8', linewidth=1.0)
        self.canvas.draw_idle()
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
            sp.set_edgecolor('#7b88a8')
        self.ax.grid(color='#2e3440', linestyle='--', alpha=0.6)
        self.ax.axhline(0, color='#7b88a8', linewidth=1.0)
        self.ax.axvline(0, color='#7b88a8', linewidth=1.0)

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
                                 markeredgecolor='#7b88a8', markeredgewidth=1)
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
                                 markeredgecolor='#7b88a8', markeredgewidth=1)
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
        self.canvas.draw_idle()

        self.intercepts_output.setHtml(
            '<br>'.join(intercept_parts) if intercept_parts
            else '<i style="color:#7b88a8">No intercepts found in current view.</i>'
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
        self._style_axes(ax, equal=True)
        ax.axhline(0, color='#7b88a8', linewidth=1.2)
        ax.axvline(0, color='#7b88a8', linewidth=1.2)
        ax.set_xlabel('Re', color='#81a1c1')
        ax.set_ylabel('Im', color='#81a1c1')
        ax.set_title('Argand Plane', color='#eceff4')
        self.cx_canvas.draw_idle()

    def _polar_to_z1(self):
        try:
            r = sympy.sympify(self.cx_r.text())
            theta = sympy.sympify(self.cx_theta.text())
            z = r * sympy.exp(sympy.I * theta)
            z_rect = sympy.simplify(z.rewrite(sympy.cos))
            self.cx_z1.setText(str(sympy.expand(sympy.nsimplify(z_rect))))
        except Exception as e:
            self.cx_output.setHtml(self._err_html(e))

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
            self.cx_canvas.draw_idle()
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
            self.cx_output.setHtml(self._err_html(e))
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
        self.calc_input_latex = LatexCanvas(height=100)
        ig.addWidget(self.calc_input_latex)
        ig.addWidget(self._copy_latex_btn(self.calc_input_latex), alignment=Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(in_grp)

        plot_grp = QGroupBox("Plot")
        pg = QVBoxLayout(plot_grp)
        pg.setContentsMargins(4, 4, 4, 4)
        self.calc_fig, self.calc_canvas = self._make_figure()
        pg.addWidget(self.calc_canvas)
        right_layout.addWidget(plot_grp, 1)

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
                      r"\frac{d}{d" + v + r"}\left(" + sympy.latex(expr) + r"\right) = " + sympy.latex(res))
                x0 = sympy.sympify(self.calc_point.text())
                self._plot_calculus(action, expr, x, x0=x0)

            elif action == "nth_derivative":
                n = int(sympy.sympify(self.calc_order.text()))
                res = sympy.diff(expr, x, n)
                _show(f"d^{n}/d{v}^{n}  f({v})",
                      r"\frac{d^{" + str(n) + r"}}{d" + v + r"^{" + str(n) + r"}}"
                      r"\left(" + sympy.latex(expr) + r"\right) = " + sympy.latex(res))
                x0 = sympy.sympify(self.calc_point.text())
                self._plot_calculus(action, expr, x, x0=x0)

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
                self._plot_calculus(action, expr, x, x0=x0)

            elif action == "indefinite_integral":
                res = sympy.integrate(expr, x)
                _show("∫ f(" + v + ") d" + v,
                      r"\int " + sympy.latex(expr) + r"\, d" + v + r" = " + sympy.latex(res) + r" + C")
                self._plot_calculus(action, expr, x)

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
                self._plot_calculus(action, expr, x, a=a, b=b)

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
                      r"\left(" + sympy.latex(expr) + r"\right) = " + sympy.latex(res))

            elif action == "taylor":
                n = int(sympy.sympify(self.calc_order.text()))
                x0 = sympy.sympify(self.calc_point.text())
                series = sympy.series(expr, x, x0, n + 1)
                poly = series.removeO()
                _show(f"Taylor series around {v}={x0}, order {n}",
                      sympy.latex(expr) + r" \approx " + sympy.latex(sympy.expand(poly))
                      + r" + O\!\left((" + v + r"-" + sympy.latex(x0) + r")^{" + str(n + 1) + r"}\right)")
                self._plot_calculus(action, expr, x, x0=x0, n=n)

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
                self._plot_calculus(action, expr, x)

            elif action == "partial_fractions":
                res = sympy.apart(expr, x)
                _show("Partial fractions",
                      sympy.latex(expr) + r" = " + sympy.latex(res))

            elif action == "simplify":
                res = sympy.simplify(expr)
                _show("Simplified",
                      sympy.latex(expr) + r" = " + sympy.latex(res))

        except Exception as e:
            self.calc_output.setHtml(self._err_html(e))
            self.calc_result_latex.render("")

    def _plot_calculus(self, action, expr, x, x0=None, a=None, b=None, n=None):
        try:
            self._plot_calculus_inner(action, expr, x, x0=x0, a=a, b=b, n=n)
        except Exception:
            self.calc_canvas.draw_idle()

    def _plot_calculus_inner(self, action, expr, x, x0=None, a=None, b=None, n=None):
        if not self.calc_fig.axes:
            self.calc_fig.add_subplot(111)
        ax = self.calc_fig.axes[0]
        ax.clear()
        self._style_axes(ax)
        v = str(x)

        # Choose x range
        if action == "definite_integral" and a is not None and b is not None:
            fa, fb = float(a), float(b)
            margin = max((fb - fa) * 0.6, 1.5)
            xlo, xhi = fa - margin, fb + margin
        elif x0 is not None:
            x0f = float(x0)
            xlo, xhi = x0f - 4, x0f + 4
        else:
            xlo, xhi = -5, 5

        xs = np.linspace(xlo, xhi, 500)
        try:
            f_num = sympy.lambdify(x, expr, modules=['numpy'])
            ys = np.array(f_num(xs), dtype=float)
            # clip extreme values so the plot doesn't go crazy
            clip = max(np.nanpercentile(np.abs(ys[np.isfinite(ys)]), 95) * 4, 10) if np.any(np.isfinite(ys)) else 10
            ys = np.where(np.abs(ys) > clip, np.nan, ys)
        except Exception:
            self.calc_canvas.draw_idle()
            return

        ax.plot(xs, ys, color='#88c0d0', linewidth=2, label=f'f({v})', zorder=3)

        if action in ("derivative", "nth_derivative", "eval_derivative") and x0 is not None:
            x0f = float(x0)
            try:
                slope = float(sympy.diff(expr, x).subs(x, x0).evalf())
                y0    = float(expr.subs(x, x0).evalf())
                dx    = (xhi - xlo) * 0.25
                tx    = np.array([x0f - dx, x0f + dx])
                ax.plot(tx, slope * (tx - x0f) + y0,
                        color='#ebcb8b', linewidth=1.8, linestyle='--',
                        label=f"tangent  slope={slope:.4g}", zorder=4)
                ax.scatter([x0f], [y0], color='#bf616a', s=60, zorder=5)
            except Exception:
                pass

        elif action == "definite_integral" and a is not None and b is not None:
            fa, fb = float(a), float(b)
            xfill = np.linspace(fa, fb, 400)
            try:
                yfill = np.array(f_num(xfill), dtype=float)
                ax.fill_between(xfill, 0, yfill, alpha=0.40,
                                color='#a3be8c', label=f"∫ from {fa} to {fb}", zorder=2)
                ax.axvline(fa, color='#a3be8c', linewidth=1, linestyle=':')
                ax.axvline(fb, color='#a3be8c', linewidth=1, linestyle=':')
            except Exception:
                pass

        elif action == "taylor" and x0 is not None and n is not None:
            x0f = float(x0)
            try:
                poly = sympy.series(expr, x, x0, n + 1).removeO()
                p_num = sympy.lambdify(x, sympy.expand(poly), modules=['numpy'])
                yp = np.array(p_num(xs), dtype=float)
                yp = np.where(np.abs(yp) > clip * 2, np.nan, yp)
                ax.plot(xs, yp, color='#ebcb8b', linewidth=1.8, linestyle='--',
                        label=f"Taylor order {n}", zorder=4)
                ax.axvline(x0f, color='#616e88', linewidth=0.8, linestyle=':')
            except Exception:
                pass

        elif action == "critical_points":
            try:
                crits = sympy.solve(sympy.diff(expr, x), x)
                for cp in crits:
                    cpf = float(cp.evalf())
                    if not (xlo <= cpf <= xhi):
                        continue
                    ycp = float(expr.subs(x, cp).evalf())
                    ax.scatter([cpf], [ycp], color='#bf616a', s=70, zorder=5)
                    ax.annotate(f"x={cpf:.3g}", (cpf, ycp),
                                textcoords="offset points", xytext=(5, 5),
                                color='#d8dee9', fontsize=8)
            except Exception:
                pass

        ax.axhline(0, color='#4c566a', linewidth=0.7)
        ax.axvline(0, color='#4c566a', linewidth=0.7)
        ax.legend(fontsize=8, loc='best')
        self.calc_canvas.draw_idle()

    # ══════════════════════════════════════════════════════════════════════
    # Differential Equations tab
    # ══════════════════════════════════════════════════════════════════════

    def setup_de_tab(self):
        w = QWidget()
        self.tabs.addTab(w, "Diff. Equations")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(4, 4, 4, 4)
        self._de_tabs = QTabWidget()
        outer.addWidget(self._de_tabs)
        self._setup_de_symbolic()
        self._setup_de_numerical()
        self._setup_de_phase()
        self._setup_de_pde()

    # ── Symbolic ODE ───────────────────────────────────────────────────────

    def _setup_de_symbolic(self):
        tab = QWidget()
        self._de_tabs.addTab(tab, "Symbolic ODE")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("ODE  (y as function of x)")
        g = QGridLayout(grp)
        g.setSpacing(6)
        hint = QLabel("Use y' and y'' for derivatives.\nExamples:  y'' + y = 0    y' = y    y'' - 3*y' + 2*y = exp(x)")
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        hint.setWordWrap(True)
        g.addWidget(hint, 0, 0, 1, 2)
        g.addWidget(QLabel("ODE:"), 1, 0)
        self._de_sym_ode = QLineEdit("y'' + y = 0")
        self._de_sym_ode.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self._de_sym_ode, 1, 1)

        ic_hint = QLabel("Initial conditions  (optional, comma-separated):\nExamples:  y(0)=1   y(0)=1, y'(0)=0")
        ic_hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        ic_hint.setWordWrap(True)
        g.addWidget(ic_hint, 2, 0, 1, 2)
        g.addWidget(QLabel("ICs:"), 3, 0)
        self._de_sym_ics = QLineEdit("y(0)=1, y'(0)=0")
        self._de_sym_ics.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self._de_sym_ics, 3, 1)

        for lbl, act in [("Solve (general)", "general"), ("Solve with ICs", "particular")]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_de_symbolic(a))
            g.addWidget(btn, g.rowCount(), 0, 1, 2)

        presets = [
            ("Harmonic", "y'' + y = 0", "y(0)=1, y'(0)=0"),
            ("Damped",   "y'' + 0.5*y' + y = 0", "y(0)=2, y'(0)=0"),
            ("Forced",   "y'' + y = sin(x)", "y(0)=0, y'(0)=0"),
            ("Logistic", "y' = y*(1-y)", "y(0)=0.1"),
            ("Bessel",   "x**2*y'' + x*y' + (x**2-1)*y = 0", ""),
            ("Euler",    "x**2*y'' - 2*x*y' + 2*y = 0", "y(1)=1, y'(1)=0"),
        ]
        preset_row = QGridLayout()
        for idx, (lbl, ode, ics) in enumerate(presets):
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE_SM)
            btn.clicked.connect(lambda _, o=ode, i=ics: (
                self._de_sym_ode.setText(o), self._de_sym_ics.setText(i)))
            preset_row.addWidget(btn, idx//3, idx%3)
        g.addLayout(preset_row, g.rowCount(), 0, 1, 2)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._de_sym_latex = LatexCanvas(height=120)
        rl.addWidget(self._de_sym_latex)
        rl.addWidget(self._copy_latex_btn(self._de_sym_latex),
                     alignment=Qt.AlignmentFlag.AlignRight)
        self._de_sym_fig, self._de_sym_canvas = self._make_figure()
        rl.addWidget(self._de_sym_canvas, 1)
        self._make_output(rl, '_de_sym_out', 60)
        outer.addWidget(right, 3)

    def _run_de_symbolic(self, mode):
        try:
            x = sympy.Symbol('x')
            y = sympy.Function('y')
            ode_eq, x_s, y_f = self._parse_ode(self._de_sym_ode.text())

            if mode == "general":
                sol = sympy.dsolve(ode_eq, y_f(x_s))
                self._de_sym_latex.render(sympy.latex(sol))
                self._de_sym_out.setHtml("<b>General solution</b>")
                self._add_to_global_history("DE·Symbolic", "general",
                                            self._de_sym_ode.text(), str(sol)[:120])
                self._plot_de_sym_sol(sol, x_s)
            else:
                ics = self._parse_de_ics(self._de_sym_ics.text(), x_s, y_f)
                sol = sympy.dsolve(ode_eq, y_f(x_s), ics=ics if ics else None)
                self._de_sym_latex.render(sympy.latex(sol))
                self._de_sym_out.setHtml("<b>Particular solution</b>")
                self._add_to_global_history("DE·Symbolic", "particular",
                                            self._de_sym_ode.text(), str(sol)[:120])
                self._plot_de_sym_sol(sol, x_s)
        except Exception as e:
            self._de_sym_latex.render(r"\text{Error: }" + str(e)[:50])
            self._de_sym_out.setHtml(self._err_html(e))

    def _parse_de_ics(self, text, x_sym, y_func):
        """Parse 'y(0)=1, y'(0)=0' → dict for dsolve ics kwarg."""
        if not text.strip():
            return {}

        ics = {}
        x = x_sym; y = y_func
        for part in text.split(','):
            part = part.strip()
            if not part:
                continue
            m = re.match(r"y'?\(([^)]+)\)\s*=\s*(.+)", part)
            if not m:
                continue
            x_val = float(sympy.sympify(m.group(1)).evalf())
            rhs   = sympy.sympify(m.group(2))
            if "'" in part:
                ics[y(x).diff(x).subs(x, x_val)] = rhs
            else:
                ics[y(x_sym).subs(x_sym, x_val)] = rhs
        return ics

    def _plot_de_sym_sol(self, sol, x_sym):
        try:
            rhs = sol.rhs if hasattr(sol, 'rhs') else sol
            # Replace any free constants with numeric guesses for plotting
            free = rhs.free_symbols - {x_sym}
            sub = {s: 1 for s in free}
            rhs_num = rhs.subs(sub)
            f = sympy.lambdify(x_sym, rhs_num, 'numpy')
            xs = np.linspace(-2*np.pi, 2*np.pi, 600)
            with np.errstate(all='ignore'):
                ys = np.asarray(f(xs), dtype=complex).real
            ys[~np.isfinite(ys)] = np.nan
            if np.all(np.isnan(ys)):
                return
            self._de_sym_fig.clear()
            ax = self._de_sym_fig.add_subplot(111)
            self._style_axes(ax)
            ax.plot(xs, ys, color='#88c0d0', linewidth=2)
            ax.axhline(0, color='#7b88a8', linewidth=0.6)
            ax.set_title("Solution  y(x)", color='#eceff4', fontsize=9)
            self._de_sym_fig.tight_layout(pad=0.6)
            self._de_sym_canvas.draw_idle()
        except Exception:
            pass

    # ── Numerical IVP ─────────────────────────────────────────────────────

    def _setup_de_numerical(self):
        tab = QWidget()
        self._de_tabs.addTab(tab, "Numerical IVP")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("First-order system  dy/dt = f(t, y)")
        g = QGridLayout(grp)
        g.setSpacing(6)
        hint = QLabel(
            "Single ODE:  f(t, y) = -y + sin(t)\n"
            "System (comma-sep):  -y[1], y[0]   (SHO: dx/dt=v, dv/dt=-x)\n"
            "Use t and y (scalar) or y[0], y[1], … (vector)"
        )
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        hint.setWordWrap(True)
        g.addWidget(hint, 0, 0, 1, 2)

        g.addWidget(QLabel("f(t,y) ="), 1, 0)
        self._de_num_f = QLineEdit("-y + sin(t)")
        self._de_num_f.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self._de_num_f, 1, 1)

        for row, (lbl, attr, default) in enumerate([
            ("y₀  (comma-sep for system):", "_de_num_y0",  "1"),
            ("t₀ =", "_de_num_t0", "0"),
            ("t_end =", "_de_num_tf", "10"),
            ("Step h =",  "_de_num_h",  "0.1"),
        ], start=2):
            g.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            g.addWidget(w, row, 1)

        for lbl, act in [
            ("Euler",       "euler"),
            ("Heun (RK2)",  "heun"),
            ("RK4",         "rk4"),
            ("RK45 (scipy)","rk45"),
            ("DOP853",      "dop853"),
            ("Radau (stiff)","radau"),
            ("BDF (stiff)", "bdf"),
            ("Compare Euler/RK4/RK45", "compare"),
        ]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_de_numerical(a))
            g.addWidget(btn, g.rowCount(), 0, 1, 2)

        preset_row = QGridLayout()
        presets_num = [
            ("Decay",     "-0.5*y",       "2",    "0", "10", "0.2"),
            ("SHO",       "-y[1], y[0]",  "0,1",  "0", "20", "0.1"),
            ("Van der Pol","y[1], (1-y[0]**2)*y[1]-y[0]","0,2","0","30","0.05"),
            ("Lorenz x",  "y[1], -y[0]+y[1]*(1-y[0]**2)","1,0","0","40","0.02"),
        ]
        for idx, (lbl, f, y0, t0, tf, h) in enumerate(presets_num):
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE_SM)
            btn.clicked.connect(lambda _, fv=f, y0v=y0, t0v=t0, tfv=tf, hv=h: (
                self._de_num_f.setText(fv), self._de_num_y0.setText(y0v),
                self._de_num_t0.setText(t0v), self._de_num_tf.setText(tfv),
                self._de_num_h.setText(hv)))
            preset_row.addWidget(btn, idx//2, idx%2)
        g.addLayout(preset_row, g.rowCount(), 0, 1, 2)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._de_num_fig, self._de_num_canvas = self._make_figure()
        rl.addWidget(self._de_num_canvas, 1)
        self._make_output(rl, '_de_num_out', 80)
        outer.addWidget(right, 3)

    def _de_parse_rhs(self, expr_str, t_val, y_arr):
        """Evaluate f(t, y) string; supports scalar y or y[i] indexing."""

        s = expr_str.strip()
        # Build namespace
        ns = {
            't': t_val, 'y': y_arr[0] if len(y_arr)==1 else y_arr,
            **{f: getattr(np, f) for f in dir(np) if not f.startswith('_')},
            'pi': np.pi, 'e': np.e,
        }
        if ',' in s:
            parts = s.split(',')
            return np.array([float(eval(p.strip(), ns)) for p in parts])
        return np.array([float(eval(s, ns))])

    def _run_de_numerical(self, method):

        try:
            f_str = self._de_num_f.text()
            y0 = np.array([float(v) for v in self._de_num_y0.text().split(',')])
            t0 = float(self._de_num_t0.text())
            tf = float(self._de_num_tf.text())
            h  = float(self._de_num_h.text())

            def f_vec(t, y):
                return self._de_parse_rhs(f_str, t, np.asarray(y))

            scipy_methods = {
                'rk45': 'RK45', 'dop853': 'DOP853',
                'radau': 'Radau', 'bdf': 'BDF',
            }

            results = {}

            def _manual(stepper, name):
                ts = [t0]; ys = [y0.copy()]
                t_cur = t0; y_cur = y0.copy()
                while t_cur < tf - 1e-12:
                    h_actual = min(h, tf - t_cur)
                    y_cur = stepper(f_vec, t_cur, y_cur, h_actual)
                    t_cur += h_actual
                    ts.append(t_cur); ys.append(y_cur.copy())
                return np.array(ts), np.array(ys)

            def _euler_step(f, t, y, h):
                return y + h * f(t, y)

            def _heun_step(f, t, y, h):
                k1 = f(t, y)
                k2 = f(t + h, y + h*k1)
                return y + h/2 * (k1 + k2)

            def _rk4_step(f, t, y, h):
                k1 = f(t, y)
                k2 = f(t + h/2, y + h/2*k1)
                k3 = f(t + h/2, y + h/2*k2)
                k4 = f(t + h,   y + h*k3)
                return y + h/6 * (k1 + 2*k2 + 2*k3 + k4)

            if method == "compare":
                for name, stepper in [("Euler",_euler_step),("RK4",_rk4_step)]:
                    results[name] = _manual(stepper, name)
                sol = solve_ivp(f_vec, [t0, tf], y0, method='RK45',
                                max_step=h, dense_output=False)
                results["RK45"] = (sol.t, sol.y.T)
            elif method in scipy_methods:
                sol = solve_ivp(f_vec, [t0, tf], y0,
                                method=scipy_methods[method],
                                max_step=h, dense_output=False)
                results[method.upper()] = (sol.t, sol.y.T)
            elif method == "euler":
                results["Euler"] = _manual(_euler_step, "Euler")
            elif method == "heun":
                results["Heun"] = _manual(_heun_step, "Heun")
            elif method == "rk4":
                results["RK4"] = _manual(_rk4_step, "RK4")

            # Plot
            self._de_num_fig.clear()
            n_comp = len(y0)
            n_axes = n_comp + (1 if n_comp == 2 else 0)  # + phase plane if 2D
            axes = self._de_num_fig.subplots(1, n_axes) if n_axes > 1 else [self._de_num_fig.add_subplot(111)]

            colors = ['#88c0d0','#a3be8c','#ebcb8b','#bf616a']
            comp_labels = [f"y[{i}]" if n_comp > 1 else "y" for i in range(n_comp)]

            for ax in axes[:n_comp]:
                self._style_axes(ax)
            if n_comp == 2:
                self._de_axes(axes[2], equal=False)

            for cidx, (name, (ts, ys)) in enumerate(results.items()):
                col = colors[cidx % len(colors)]
                for comp in range(n_comp):
                    y_plot = ys[:, comp] if ys.ndim > 1 else ys
                    axes[comp].plot(ts, y_plot, color=col, linewidth=1.8,
                                    label=f"{name} {comp_labels[comp]}", alpha=0.9)
                if n_comp == 2 and len(results) == 1:
                    y0p = ys[:, 0]; y1p = ys[:, 1]
                    axes[2].plot(y0p, y1p, color='#a3be8c', linewidth=1.5, alpha=0.8)
                    axes[2].set_title("Phase plane", color='#eceff4', fontsize=8)
                    axes[2].set_xlabel(comp_labels[0], color='#81a1c1', fontsize=7)
                    axes[2].set_ylabel(comp_labels[1], color='#81a1c1', fontsize=7)

            for i, ax in enumerate(axes[:n_comp]):
                ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=7)
                ax.set_title(comp_labels[i], color='#eceff4', fontsize=8)
                ax.set_xlabel("t", color='#81a1c1', fontsize=7)

            self._de_num_fig.tight_layout(pad=0.6)
            self._de_num_canvas.draw_idle()

            first_name, (ts, ys) = list(results.items())[0]
            y_end = ys[-1] if ys.ndim == 1 else ys[-1]
            self._de_num_out.setHtml(
                f"<b>Method:</b> {first_name}  "
                f"<b>Steps:</b> {len(ts)-1}<br>"
                f"<b>y(t={ts[-1]:.4g})</b> = {np.round(y_end,6)}"
            )
            self._add_to_global_history("DE·Numerical", method, f_str,
                                        f"t_end={tf}, steps={len(ts)-1}")
        except Exception as e:
            self._de_num_out.setHtml(self._err_html(e))

    # ── Phase Portrait ─────────────────────────────────────────────────────

    def _setup_de_phase(self):
        tab = QWidget()
        self._de_tabs.addTab(tab, "Phase Portrait")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("Autonomous 2D system")
        g = QGridLayout(grp)
        g.setSpacing(6)
        hint = QLabel("dx/dt = f(x,y)    dy/dt = g(x,y)\nUse x and y as variables.")
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        g.addWidget(hint, 0, 0, 1, 2)

        g.addWidget(QLabel("f(x,y) ="), 1, 0)
        self._de_ph_f = QLineEdit("y")
        self._de_ph_f.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self._de_ph_f, 1, 1)

        g.addWidget(QLabel("g(x,y) ="), 2, 0)
        self._de_ph_g = QLineEdit("-x - 0.3*y")
        self._de_ph_g.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self._de_ph_g, 2, 1)

        for row, (lbl, attr, default) in enumerate([
            ("x min:", "_de_ph_xmin", "-4"),
            ("x max:", "_de_ph_xmax", "4"),
            ("y min:", "_de_ph_ymin", "-4"),
            ("y max:", "_de_ph_ymax", "4"),
            ("Trajectories n:", "_de_ph_n", "12"),
            ("t span:", "_de_ph_tf", "20"),
        ], start=3):
            g.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setFixedWidth(70)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            g.addWidget(w, row, 1)

        presets_ph = [
            ("Damped SHO",  "y", "-x-0.3*y", "-4","4","-4","4"),
            ("Centre",      "y", "-x",        "-3","3","-3","3"),
            ("Saddle",      "x", "-y",         "-3","3","-3","3"),
            ("Van der Pol", "y", "(1-x**2)*y-x","-4","4","-4","4"),
            ("Pendulum",    "y", "-sin(x)",    "-7","7","-4","4"),
            ("Lotka-Volterra","0.5*x-0.1*x*y", "-0.5*y+0.1*x*y", "0","10","0","10"),
        ]
        pg = QGridLayout()
        for idx, (lbl, f, g_str, x1,x2,y1,y2) in enumerate(presets_ph):
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE_SM)
            btn.clicked.connect(lambda _, fv=f, gv=g_str, x1v=x1,x2v=x2,y1v=y1,y2v=y2: (
                self._de_ph_f.setText(fv), self._de_ph_g.setText(gv),
                self._de_ph_xmin.setText(x1v), self._de_ph_xmax.setText(x2v),
                self._de_ph_ymin.setText(y1v), self._de_ph_ymax.setText(y2v)))
            pg.addWidget(btn, idx//3, idx%3)
        g.addLayout(pg, g.rowCount(), 0, 1, 2)

        for lbl, act in [("Vector Field + Trajectories", "full"),
                          ("Streamlines", "stream"),
                          ("Find Equilibria", "equil")]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_de_phase(a))
            g.addWidget(btn, g.rowCount(), 0, 1, 2)

        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._de_ph_fig, self._de_ph_canvas = self._make_figure()
        rl.addWidget(self._de_ph_canvas, 1)
        self._make_output(rl, '_de_ph_out', 90)
        outer.addWidget(right, 3)

    def _de_eval_field(self, expr_str, X, Y):
        ns = {
            'x': X, 'y': Y,
            **{f: getattr(np, f) for f in dir(np) if not f.startswith('_')},
            'pi': np.pi, 'e': np.e,
        }
        return np.asarray(eval(expr_str.strip(), ns), dtype=float)

    def _run_de_phase(self, mode):

        try:
            f_str = self._de_ph_f.text()
            g_str = self._de_ph_g.text()
            xmin = float(self._de_ph_xmin.text()); xmax = float(self._de_ph_xmax.text())
            ymin = float(self._de_ph_ymin.text()); ymax = float(self._de_ph_ymax.text())
            n_traj = int(self._de_ph_n.text())
            tf = float(self._de_ph_tf.text())

            xs = np.linspace(xmin, xmax, 22)
            ys = np.linspace(ymin, ymax, 22)
            X, Y = np.meshgrid(xs, ys)

            with np.errstate(all='ignore'):
                U = self._de_eval_field(f_str, X, Y)
                V = self._de_eval_field(g_str, X, Y)
            U[~np.isfinite(U)] = 0; V[~np.isfinite(V)] = 0

            self._de_ph_fig.clear()
            ax = self._de_ph_fig.add_subplot(111)
            self._style_axes(ax)
            ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
            ax.set_xlabel("x", color='#81a1c1', fontsize=8)
            ax.set_ylabel("y", color='#81a1c1', fontsize=8)

            if mode in ("full", "equil"):
                norm = np.sqrt(U**2 + V**2)
                norm[norm == 0] = 1
                ax.quiver(X, Y, U/norm, V/norm, norm,
                          cmap='cool', alpha=0.55, scale=28,
                          width=0.004, headwidth=4)

            if mode == "stream":
                speed = np.sqrt(U**2 + V**2)
                ax.streamplot(xs, ys, U, V,
                              color=speed, cmap='cool',
                              linewidth=1.2, density=1.4, arrowsize=1.4)

            if mode in ("full", "equil"):
                # Trajectories from grid of initial conditions
                ic_x = np.linspace(xmin, xmax, int(np.sqrt(n_traj))+1)
                ic_y = np.linspace(ymin, ymax, int(np.sqrt(n_traj))+1)
                def rhs(t, state):
                    xx, yy = state
                    with np.errstate(all='ignore'):
                        u = float(self._de_eval_field(f_str, np.array([[xx]]), np.array([[yy]]))[0,0])
                        v = float(self._de_eval_field(g_str, np.array([[xx]]), np.array([[yy]]))[0,0])
                    return [u, v]
                for x0 in ic_x:
                    for y0 in ic_y:
                        try:
                            sol = solve_ivp(rhs, [0, tf], [x0, y0],
                                            method='RK45', max_step=0.1,
                                            dense_output=False,
                                            events=lambda t,s: max(abs(s[0])-xmax*3, abs(s[1])-ymax*3))
                            xt, yt = sol.y
                            mask = (xt >= xmin) & (xt <= xmax) & (yt >= ymin) & (yt <= ymax)
                            if mask.sum() > 2:
                                ax.plot(xt[mask], yt[mask], color='#a3be8c',
                                        linewidth=0.8, alpha=0.55)
                        except Exception:
                            pass

            if mode == "equil":
                # Find equilibria numerically on a grid

                equil = []
                for x0 in np.linspace(xmin, xmax, 6):
                    for y0 in np.linspace(ymin, ymax, 6):
                        try:
                            def sys_eq(pt):
                                xx, yy = pt
                                u = float(self._de_eval_field(f_str, np.array([[xx]]), np.array([[yy]]))[0,0])
                                v = float(self._de_eval_field(g_str, np.array([[xx]]), np.array([[yy]]))[0,0])
                                return [u, v]
                            pt = fsolve(sys_eq, [x0, y0], full_output=False)
                            res = sys_eq(pt)
                            if abs(res[0]) < 1e-6 and abs(res[1]) < 1e-6:
                                # deduplicate
                                if not any(np.linalg.norm(np.array(pt)-np.array(e)) < 1e-4 for e in equil):
                                    equil.append(pt.tolist())
                        except Exception:
                            pass
                equil_html = ""
                for pt in equil:
                    ax.plot(pt[0], pt[1], 'o', color='#bf616a', markersize=8, zorder=5)
                    equil_html += f"({pt[0]:.4g}, {pt[1]:.4g})  "
                self._de_ph_out.setHtml(
                    f"<b>Equilibria found ({len(equil)}):</b> {equil_html}"
                )
            else:
                self._de_ph_out.setHtml(
                    f"<b>dx/dt = {f_str}</b><br>"
                    f"<b>dy/dt = {g_str}</b>"
                )

            ax.set_title(f"Phase portrait", color='#eceff4', fontsize=9)
            self._de_ph_fig.tight_layout(pad=0.4)
            self._de_ph_canvas.draw_idle()
            self._add_to_global_history("DE·Phase", mode, f"{f_str}, {g_str}", "")
        except Exception as e:
            self._de_ph_out.setHtml(self._err_html(e))

    # ── PDE ───────────────────────────────────────────────────────────────

    def _setup_de_pde(self):
        tab = QWidget()
        self._de_tabs.addTab(tab, "PDE")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("PDE  (finite difference)")
        g = QGridLayout(grp)
        g.setSpacing(6)

        g.addWidget(QLabel("Type:"), 0, 0)
        self._de_pde_type = QComboBox()
        self._de_pde_type.addItems([
            "Heat  uₜ = α·uₓₓ",
            "Wave  uₜₜ = c²·uₓₓ",
            "Laplace  uₓₓ + uyy = 0",
        ])
        self._de_pde_type.setStyleSheet(
            self._COMBO_STYLE
        )
        g.addWidget(self._de_pde_type, 0, 1)

        for row, (lbl, attr, default) in enumerate([
            ("α or c  (param):", "_de_pde_alpha", "0.5"),
            ("L  (domain [0,L]):", "_de_pde_L", "1.0"),
            ("T  (time span):", "_de_pde_T", "1.0"),
            ("Nx  (space steps):", "_de_pde_Nx", "50"),
            ("Nt  (time steps):", "_de_pde_Nt", "500"),
        ], start=1):
            g.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            g.addWidget(w, row, 1)

        g.addWidget(QLabel("Initial cond. u(x,0) ="), 6, 0)
        self._de_pde_ic = QLineEdit("sin(pi*x/L)")
        self._de_pde_ic.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self._de_pde_ic, 6, 1)

        g.addWidget(QLabel("Snapshots at t ="), 7, 0)
        self._de_pde_snaps = QLineEdit("0, 0.1, 0.3, 0.6, 1.0")
        self._de_pde_snaps.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self._de_pde_snaps, 7, 1)

        presets_pde = [
            ("Heat sin", "Heat  uₜ = α·uₓₓ", "0.5","1","1","50","500","sin(pi*x/L)","0,0.05,0.2,0.5,1.0"),
            ("Heat pulse","Heat  uₜ = α·uₓₓ","0.1","1","0.5","60","600","exp(-50*(x-0.5)**2)","0,0.02,0.1,0.3,0.5"),
            ("Wave",     "Wave  uₜₜ = c²·uₓₓ","1","1","2","60","600","sin(pi*x/L)","0,0.25,0.5,0.75,1.0"),
            ("Laplace",  "Laplace  uₓₓ + uyy = 0","","1","","30","","sin(pi*x/L)",""),
        ]
        pg = QGridLayout()
        for idx, (lbl, ptype, alpha, L, T, Nx, Nt, ic, snaps) in enumerate(presets_pde):
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE_SM)
            def _load(pt=ptype, a=alpha, lv=L, tv=T, nx=Nx, nt=Nt, icv=ic, sv=snaps):
                self._de_pde_type.setCurrentText(pt)
                if a: self._de_pde_alpha.setText(a)
                if lv: self._de_pde_L.setText(lv)
                if tv: self._de_pde_T.setText(tv)
                if nx: self._de_pde_Nx.setText(nx)
                if nt: self._de_pde_Nt.setText(nt)
                if icv: self._de_pde_ic.setText(icv)
                if sv: self._de_pde_snaps.setText(sv)
            btn.clicked.connect(_load)
            pg.addWidget(btn, idx//2, idx%2)
        g.addLayout(pg, g.rowCount(), 0, 1, 2)

        solve_btn = QPushButton("Solve PDE")
        solve_btn.setStyleSheet(self._BTN_STYLE)
        solve_btn.clicked.connect(self._run_de_pde)
        g.addWidget(solve_btn, g.rowCount(), 0, 1, 2)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._de_pde_fig, self._de_pde_canvas = self._make_figure()
        rl.addWidget(self._de_pde_canvas, 1)
        self._make_output(rl, '_de_pde_out', 70)
        outer.addWidget(right, 3)

    def _run_de_pde(self):
        try:
            ptype = self._de_pde_type.currentText()
            alpha = float(self._de_pde_alpha.text()) if self._de_pde_alpha.text() else 1.0
            L     = float(self._de_pde_L.text())
            Nx    = int(self._de_pde_Nx.text())
            ic_str= self._de_pde_ic.text()

            xs = np.linspace(0, L, Nx+1)
            dx = L / Nx

            ns = {'x': xs, 'L': L, 'pi': np.pi,
                  **{f: getattr(np, f) for f in dir(np) if not f.startswith('_')}}
            u0 = np.asarray(eval(ic_str, ns), dtype=float)
            if u0.shape != xs.shape:
                u0 = np.broadcast_to(u0, xs.shape).copy()

            snaps_t = [float(v.strip()) for v in self._de_pde_snaps.text().split(',') if v.strip()]

            self._de_pde_fig.clear()

            if "Heat" in ptype:
                Nt = int(self._de_pde_Nt.text())
                T  = float(self._de_pde_T.text())
                dt = T / Nt
                r  = alpha * dt / dx**2
                if r > 0.5:
                    self._de_pde_out.setHtml(
                        f"<b style='color:#ebcb8b'>Warning:</b> r={r:.3f} > 0.5 — "
                        "unstable (reduce dt or increase Nx)"
                    )
                u = u0.copy()
                snapshots = {0.0: u0.copy()}
                t_cur = 0.0
                for _ in range(Nt):
                    u_new = u.copy()
                    u_new[1:-1] = u[1:-1] + r*(u[2:] - 2*u[1:-1] + u[:-2])
                    u_new[0] = u_new[-1] = 0  # Dirichlet BC
                    u = u_new
                    t_cur += dt
                    for ts in snaps_t:
                        if abs(t_cur - ts) < dt/2 and ts not in snapshots:
                            snapshots[ts] = u.copy()

                ax = self._de_pde_fig.add_subplot(111)
                self._style_axes(ax)
                cmap = matplotlib.cm.get_cmap('cool')
                times_sorted = sorted(snapshots.keys())
                for i, t_s in enumerate(times_sorted):
                    color = cmap(i / max(len(times_sorted)-1, 1))
                    ax.plot(xs, snapshots[t_s], color=color, linewidth=1.8,
                            label=f"t={t_s:.3g}")
                ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=8)
                ax.set_title(f"Heat equation  α={alpha}  (FTCS)", color='#eceff4', fontsize=9)
                ax.set_xlabel("x", color='#81a1c1', fontsize=8)
                ax.set_ylabel("u(x,t)", color='#81a1c1', fontsize=8)
                self._de_pde_out.setHtml(f"<b>r = αΔt/Δx² = {r:.4g}</b>  "
                                          f"({'stable' if r<=0.5 else 'UNSTABLE'})")

            elif "Wave" in ptype:
                c  = alpha
                Nt = int(self._de_pde_Nt.text())
                T  = float(self._de_pde_T.text())
                dt = T / Nt
                r  = c * dt / dx
                u_prev = u0.copy()
                # First step: u(t=dt) using zero initial velocity
                u_cur = u_prev.copy()
                u_cur[1:-1] = (u_prev[1:-1]
                               + 0.5*r**2*(u_prev[2:]-2*u_prev[1:-1]+u_prev[:-2]))
                u_cur[0] = u_cur[-1] = 0
                snapshots = {0.0: u0.copy()}
                t_cur = dt
                for _ in range(Nt-1):
                    u_new = np.empty_like(u_cur)
                    u_new[1:-1] = (2*u_cur[1:-1] - u_prev[1:-1]
                                   + r**2*(u_cur[2:]-2*u_cur[1:-1]+u_cur[:-2]))
                    u_new[0] = u_new[-1] = 0
                    u_prev = u_cur; u_cur = u_new
                    t_cur += dt
                    for ts in snaps_t:
                        if abs(t_cur - ts) < dt*1.5 and ts not in snapshots:
                            snapshots[ts] = u_cur.copy()

                ax = self._de_pde_fig.add_subplot(111)
                self._style_axes(ax)
                cmap = matplotlib.cm.get_cmap('cool')
                times_sorted = sorted(snapshots.keys())
                for i, t_s in enumerate(times_sorted):
                    color = cmap(i / max(len(times_sorted)-1, 1))
                    ax.plot(xs, snapshots[t_s], color=color, linewidth=1.8,
                            label=f"t={t_s:.3g}")
                ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=8)
                ax.set_title(f"Wave equation  c={c}  (CFL={r:.3g})", color='#eceff4', fontsize=9)
                ax.set_xlabel("x", color='#81a1c1', fontsize=8)
                ax.set_ylabel("u(x,t)", color='#81a1c1', fontsize=8)
                self._de_pde_out.setHtml(f"<b>CFL = cΔt/Δx = {r:.4g}</b>  "
                                          f"({'stable' if r<=1 else 'UNSTABLE'})")

            elif "Laplace" in ptype:
                # 2D Laplace on [0,L]×[0,L] with u=sin(πx/L) on top, 0 elsewhere
                N = Nx
                u_lap = np.zeros((N+1, N+1))
                # Boundary: top edge u(x,L) = sin(πx/L)
                u_lap[-1, :] = np.sin(np.pi * xs / L)
                # Gauss-Seidel iteration
                for _ in range(2000):
                    u_old = u_lap.copy()
                    u_lap[1:-1, 1:-1] = 0.25*(
                        u_lap[2:,1:-1] + u_lap[:-2,1:-1] +
                        u_lap[1:-1,2:] + u_lap[1:-1,:-2])
                    if np.max(np.abs(u_lap - u_old)) < 1e-5:
                        break

                ax = self._de_pde_fig.add_subplot(111)
                ax.set_facecolor('#1e222b')
                im = ax.contourf(xs, xs, u_lap, levels=30, cmap='coolwarm')
                self._de_pde_fig.colorbar(im, ax=ax)
                ax.contour(xs, xs, u_lap, levels=10, colors='white', linewidths=0.4, alpha=0.5)
                ax.set_title("Laplace equation  (Gauss-Seidel)", color='#eceff4', fontsize=9)
                ax.set_xlabel("x", color='#81a1c1', fontsize=8)
                ax.set_ylabel("y", color='#81a1c1', fontsize=8)
                ax.tick_params(colors='#eceff4', labelsize=8)
                self._de_pde_out.setHtml("<b>Boundary:</b> u=sin(πx/L) on top, 0 elsewhere")

            self._de_pde_fig.tight_layout(pad=0.5)
            self._de_pde_canvas.draw_idle()
            self._add_to_global_history("DE·PDE", ptype.split()[0], ic_str, "solved")

        except Exception as e:
            self._de_pde_out.setHtml(self._err_html(e))

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
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
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
        self.stat_fig, self.stat_canvas = self._make_figure()
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
        self._style_axes(ax)
        self.stat_fig.tight_layout(pad=1.2)
        self.stat_canvas.draw_idle()

    def _get_stat_data(self):
        raw = self.stat_data_input.toPlainText().strip()
        tokens = raw.replace(',', ' ').split()
        if not tokens:
            raise ValueError("No data entered")
        return np.array([float(t) for t in tokens])

    def _get_dist(self):

        name = self.stat_dist_combo.currentText()
        p1 = float(self.stat_p1.text())
        p2_text = self.stat_p2.text().strip()
        p2 = float(p2_text) if p2_text else 1.0
        if name == "Normal":
            return _stats.norm(loc=p1, scale=p2), f"N({p1}, {p2}²)"
        elif name == "Binomial":
            return _stats.binom(n=int(p1), p=p2), f"Bin({int(p1)}, {p2})"
        elif name == "Poisson":
            return _stats.poisson(mu=p1), f"Poisson({p1})"
        elif name == "t-distribution":
            return _stats.t(df=p1), f"t({p1} df)"
        elif name == "Chi-squared":
            return _stats.chi2(df=p1), f"χ²({p1} df)"
        elif name == "Exponential":
            return _stats.expon(scale=1.0 / p1), f"Exp(λ={p1})"
        raise ValueError(f"Unknown distribution: {name}")

    def execute_stat_op(self, action):

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
                    self.stat_canvas.draw_idle()
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
                    self.stat_canvas.draw_idle()
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
                    self.stat_canvas.draw_idle()
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
                    self.stat_canvas.draw_idle()

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
                    self.stat_canvas.draw_idle()

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
                    self.stat_canvas.draw_idle()

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
            self.stat_output.setHtml(self._err_html(e))


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
        hint_s.setStyleSheet("color: #7b88a8; font-size: 10px;")
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
            self._COMBO_STYLE
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
            self._COMBO_STYLE
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
        hint_p.setStyleSheet("color: #7b88a8; font-size: 10px;")
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

        self.g3d_fig, self.g3d_canvas = self._make_figure()
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
        self.g3d_canvas.draw_idle()

    def _clear_3d(self):
        self.g3d_ax.clear()
        self._init_3d_axes()
        self.g3d_output.setHtml('')

    def _reset_3d_view(self):
        self.g3d_ax.view_init(elev=25, azim=-60)
        self.g3d_canvas.draw_idle()

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
                self.g3d_canvas.draw_idle()
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
            self.g3d_canvas.draw_idle()
            self.g3d_output.setHtml(
                f"<b>Plotted {plotted} surface(s)</b>  —  drag to rotate, scroll to zoom"
            )

        except Exception as e:
            self.g3d_output.setHtml(self._err_html(e))


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

        self.nt_fig, self.nt_canvas = self._make_figure()
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
        self._style_axes(ax)
        self.nt_fig.tight_layout(pad=0.8)
        self.nt_canvas.draw_idle()

    def execute_nt_op(self, action):



        def _out(html):
            self.nt_output.setHtml(html)
            plain = re.sub(r'<[^>]+>', '', html).strip()
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
                self.nt_canvas.draw_idle()

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
                self.nt_canvas.draw_idle()

                if action == "primes_upto":
                    preview = ", ".join(f"{p:,}" for p in primes[:80])
                    suffix = f", …" if len(primes) > 80 else ""
                    _out(f"<b>Primes ≤ {limit:,}:  {len(primes):,} found</b><br><br>"
                         f"{preview}{suffix}")
                else:

                    _out(f"<b>π({limit:,}) = {len(primes):,}</b><br>"
                         f"x/ln(x) ≈ {limit / math.log(limit):.1f}")

        except Exception as e:
            self.nt_output.setHtml(self._err_html(e))

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
        self._setup_fourier_subtab()
        self._setup_special_functions_subtab()
        self._setup_complex_mapping_subtab()
        self._setup_functional_analysis_subtab()
        self._setup_series_subtab()

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
        self.fs_expr.setStyleSheet(self._FIELD_STYLE)
        fsg.addWidget(self.fs_expr, 0, 1)
        fsg.addWidget(QLabel("L ="), 1, 0)
        self.fs_L = QLineEdit("pi")
        self.fs_L.setStyleSheet(self._FIELD_STYLE)
        fsg.addWidget(self.fs_L, 1, 1)
        fsg.addWidget(QLabel("Terms N ="), 2, 0)
        self.fs_N = QLineEdit("8")
        self.fs_N.setStyleSheet(self._FIELD_STYLE)
        fsg.addWidget(self.fs_N, 2, 1)
        for lbl, act in [("Plot Approximation", "series"), ("Show Coefficients", "coeffs")]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_fourier(a))
            fsg.addWidget(btn, fsg.rowCount(), 0, 1, 2)
        ll.addWidget(fs)

        # FFT
        fft = QGroupBox("FFT  —  Discrete Signal")
        fftg = QVBoxLayout(fft)
        fftg.setSpacing(6)
        hint = QLabel("Signal samples (comma / space separated):")
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
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
        self.fft_sr.setStyleSheet(self._FIELD_STYLE)
        sr_row.addWidget(self.fft_sr)
        sr_row.addStretch()
        fftg.addLayout(sr_row)
        fft_btn = QPushButton("Compute FFT & Plot Spectrum")
        fft_btn.setStyleSheet(self._BTN_STYLE)
        fft_btn.clicked.connect(lambda: self._run_fourier("fft"))
        fftg.addWidget(fft_btn)
        ll.addWidget(fft)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.fourier_fig, self.fourier_canvas = self._make_figure()
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
                    ax.axhline(0, color='#7b88a8', linewidth=0.5)
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

            self.fourier_canvas.draw_idle()
            self._add_to_global_history("Analysis·Fourier", action,
                                        self.fs_expr.text(), self.fourier_output.toPlainText()[:150])
        except Exception as e:
            self.fourier_output.setHtml(self._err_html(e))

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
            self._COMBO_STYLE
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
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            sg.addWidget(w, row, 1)

        for lbl, act in [("Evaluate at x", "eval"), ("Plot over range", "plot")]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
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
        self.sf_fig, self.sf_canvas = self._make_figure()
        self.sf_ax = self.sf_fig.subplots()
        self._init_sf_axes()
        rl.addWidget(self.sf_canvas, 1)
        outer.addWidget(right, 3)

    def _init_sf_axes(self):
        ax = self.sf_ax
        self._style_axes(ax)
        self.sf_fig.tight_layout(pad=0.8)
        self.sf_canvas.draw_idle()

    def _run_sf(self, action):

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
                self.sf_ax.axhline(0, color='#7b88a8', linewidth=0.8)
                self.sf_ax.axvline(0, color='#7b88a8', linewidth=0.8)
                self.sf_ax.set_title(f"{name} {n_label}", color='#eceff4', fontsize=9)
                self.sf_ax.set_xlabel("x", color='#81a1c1', fontsize=8)
                self.sf_canvas.draw_idle()
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
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        hint.setWordWrap(True)
        fg.addWidget(hint, 0, 0, 1, 2)
        fg.addWidget(QLabel("f(z) ="), 1, 0)
        self.cm_expr = QLineEdit("z**2")
        self.cm_expr.setStyleSheet(self._FIELD_STYLE)
        fg.addWidget(self.cm_expr, 1, 1)

        for row, (lbl, attr, default) in enumerate([
            ("Re min:", "cm_remin", "-2"), ("Re max:", "cm_remax", "2"),
            ("Im min:", "cm_immin", "-2"), ("Im max:", "cm_immax", "2"),
        ], start=2):
            fg.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setFixedWidth(64)
            w.setStyleSheet(self._FIELD_STYLE)
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
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_complex_map(a))
            vg.addWidget(btn, idx // 2, idx % 2)
        ll.addWidget(viz_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.cm_fig, self.cm_canvas = self._make_figure()
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
            self.cm_canvas.draw_idle()
            self.cm_output.setHtml(f"<b>f(z) = {self.cm_expr.text()}</b>  —  {viz}")
            self._add_to_global_history("Analysis·Complex", viz, f"f(z)={self.cm_expr.text()}", viz)

        except Exception as e:
            self.cm_output.setHtml(self._err_html(e))

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
            w.setStyleSheet(self._FIELD_STYLE)
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
            btn.setStyleSheet(self._BTN_STYLE)
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
        self.fa_fig, self.fa_canvas = self._make_figure()
        self.fa_ax = self.fa_fig.subplots()
        self._init_fa_axes()
        rl.addWidget(self.fa_canvas, 1)
        outer.addWidget(right, 3)

    def _init_fa_axes(self):
        ax = self.fa_ax
        self._style_axes(ax)
        self.fa_fig.tight_layout(pad=0.8)
        self.fa_canvas.draw_idle()

    def _run_fa(self, action):

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
                self.fa_ax.axhline(0, color='#7b88a8', linewidth=0.6)
                self.fa_ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
                self.fa_ax.set_title(f"[{a:.4g}, {b:.4g}]", color='#eceff4', fontsize=9)
                self.fa_canvas.draw_idle()

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
                self.fa_canvas.draw_idle()
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
                self.fa_canvas.draw_idle()
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
                self.fa_canvas.draw_idle()
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
                self.fa_canvas.draw_idle()
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

    # ══════════════════════════════════════════════════════════════════════
    # Analysis — Series & Sums subtab
    # ══════════════════════════════════════════════════════════════════════

    def _setup_series_subtab(self):
        tab = QWidget()
        self._an_tabs.addTab(tab, "Series & Sums")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(8)

        grp = QGroupBox("Series / Sum")
        g = QGridLayout(grp)
        g.setSpacing(6)
        for i, (lbl, attr, val) in enumerate([
            ("Term  a(n) =",      "sr_an",   "1/n**2"),
            ("From  n =",         "sr_from", "1"),
            ("To  n =",           "sr_to",   "oo"),
            ("Partial sums  N =", "sr_N",    "60"),
        ]):
            g.addWidget(QLabel(lbl), i, 0)
            f = QLineEdit(val)
            f.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, f)
            g.addWidget(f, i, 1)
        ll.addWidget(grp)

        for lbl, act in [
            ("Check Convergence", "convergence"),
            ("Compute Sum",       "sum"),
            ("Plot Partial Sums", "partial"),
            ("Common Series",     "common"),
        ]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_series(a))
            ll.addWidget(btn)

        ll.addStretch()
        outer.addWidget(left, 1)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setSpacing(6)
        self.sr_fig, self.sr_canvas = self._make_figure()
        self.sr_ax = self.sr_fig.add_subplot(111)
        self._style_axes(self.sr_ax)
        self.sr_fig.tight_layout(pad=0.8)
        rl.addWidget(self.sr_canvas, 1)
        self._make_output(rl, "sr_out", 200)
        self.sr_out.setOpenLinks(False)
        self.sr_out.anchorClicked.connect(self._sr_load_preset)
        outer.addWidget(right, 2)

    _SR_PRESETS = [
        ("Geometric  (1/2)ⁿ",        "(1/2)**n",             "0", "oo"),
        ("p-series  1/n²  (Basel)",   "1/n**2",               "1", "oo"),
        ("p-series  1/n³",            "1/n**3",               "1", "oo"),
        ("Harmonic  1/n  (diverges)", "1/n",                  "1", "oo"),
        ("Alt. harmonic  (−1)ⁿ⁺¹/n", "(-1)**(n+1)/n",        "1", "oo"),
        ("e  =  Σ 1/n!",              "1/factorial(n)",       "0", "oo"),
        ("Euler  Σ 1/n⁴",             "1/n**4",               "1", "oo"),
        ("Telescoping  1/(n(n+1))",   "1/(n*(n+1))",          "1", "oo"),
        ("Finite: n²  (1..10)",       "n**2",                 "1", "10"),
        ("Power: xⁿ/n! at x=1",      "1**n/factorial(n)",    "0", "oo"),
    ]

    def _sr_load_preset(self, url):
        idx = int(url.toString())
        _, an, frm, to = self._SR_PRESETS[idx]
        self.sr_an.setText(an)
        self.sr_from.setText(frm)
        self.sr_to.setText(to)
        self._run_series("sum")

    def _run_series(self, action):
        try:
            an_text = self.sr_an.text().strip()
            a_expr  = sympy.sympify(an_text)
            lower   = sympy.sympify(self.sr_from.text())
            upper   = sympy.sympify(self.sr_to.text())
            N       = max(2, int(self.sr_N.text()))

            # Derive the variable from the expression itself so subs/lambdify
            # always match — never create a symbol with different assumptions
            # and expect it to substitute into a plain-symbol expression.
            free = [s for s in a_expr.free_symbols if s.name == 'n']
            if not free:
                free = sorted(a_expr.free_symbols, key=str)
            n_sym  = free[0] if free else sympy.Symbol('n')
            # Continuous version for limit/integral tests
            n_cont = sympy.Symbol(n_sym.name, positive=True)

            if action == "convergence":
                html = f"<b>Series:</b> &Sigma; {an_text},  n = {lower} &hellip; {upper}<br><br>"
                # Use continuous symbol for all limit/integral computations.
                # Never wrap in sympy.Abs before limit — sympy often fails to simplify
                # Abs(1/n**3) to 0. Instead, compute the limit directly and use
                # Python abs() on the float result.
                a_cont = a_expr.subs(n_sym, n_cont)

                # Divergence test
                try:
                    lim_an = sympy.limit(a_cont, n_cont, sympy.oo)
                    L = abs(complex(lim_an.evalf()).real)
                    if L > 1e-12:
                        html += (f"<b style='color:#bf616a'>Diverges</b> — Divergence Test: "
                                 f"lim a(n) = {lim_an} &ne; 0<br>")
                        self.sr_out.setHtml(html)
                        return
                    html += f"Divergence Test: lim a(n) = {lim_an} &rarr; 0 &check;<br>"
                except Exception:
                    html += "Divergence Test: inconclusive<br>"

                # Ratio test
                try:
                    an1 = a_cont.subs(n_cont, n_cont + 1)
                    ratio_lim = sympy.limit(sympy.simplify(an1 / a_cont), n_cont, sympy.oo)
                    L = abs(complex(ratio_lim.evalf()).real)
                    verdict = ("<b style='color:#a3be8c'>Converges absolutely</b>" if L < 1
                               else "<b style='color:#bf616a'>Diverges</b>" if L > 1
                               else "Inconclusive (L = 1)")
                    html += f"Ratio Test: L = {ratio_lim} &rarr; |L| = {L:.6g} &rarr; {verdict}<br>"
                except Exception:
                    html += "Ratio Test: inconclusive<br>"

                # Root test
                try:
                    root_lim = sympy.limit(a_cont ** (sympy.Integer(1) / n_cont), n_cont, sympy.oo)
                    L = abs(complex(root_lim.evalf()).real)
                    verdict = ("<b style='color:#a3be8c'>Converges absolutely</b>" if L < 1
                               else "<b style='color:#bf616a'>Diverges</b>" if L > 1
                               else "Inconclusive (L = 1)")
                    html += f"Root Test: L = {root_lim} &rarr; |L| = {L:.6g} &rarr; {verdict}<br>"
                except Exception:
                    html += "Root Test: inconclusive<br>"

                # Integral test
                try:
                    lower_f = float(lower.evalf())
                    integ = sympy.integrate(a_cont, (n_cont, lower_f, sympy.oo))
                    try:
                        iv = float(integ.evalf())
                        if math.isfinite(iv):
                            html += (f"Integral Test: &int;a(n)dn = {sympy.nsimplify(integ)} = {iv:.6g}"
                                     f" &rarr; <b style='color:#a3be8c'>Converges</b><br>")
                        else:
                            html += f"Integral Test: &int;a(n)dn = &infin; &rarr; <b style='color:#bf616a'>Diverges</b><br>"
                    except Exception:
                        if integ.is_finite:
                            html += f"Integral Test: &int;a(n)dn = {integ} &rarr; <b style='color:#a3be8c'>Converges</b><br>"
                        elif integ == sympy.oo:
                            html += f"Integral Test: &int;a(n)dn = &infin; &rarr; <b style='color:#bf616a'>Diverges</b><br>"
                except Exception:
                    html += "Integral Test: inconclusive<br>"

                # Alternating series test (numeric sign check)
                try:
                    f_num = sympy.lambdify(n_sym, a_expr, 'math')
                    n0 = int(float(lower.evalf()))
                    vals = [float(f_num(int(k))) for k in range(n0, n0 + 14)]
                    signs = [v > 0 for v in vals if v != 0]
                    if all(signs[i] != signs[i+1] for i in range(len(signs)-1)):
                        abs_vals = [abs(v) for v in vals]
                        if all(abs_vals[i] >= abs_vals[i+1] for i in range(len(abs_vals)-1)) and abs_vals[-1] < abs_vals[0]:
                            html += ("Alternating Series Test: alternating, decreasing, &rarr; 0"
                                     " &rarr; <b style='color:#a3be8c'>Converges</b> (conditionally)<br>")
                except Exception:
                    pass

                self.sr_out.setHtml(html)

            elif action == "sum":
                result     = sympy.summation(a_expr, (n_sym, lower, upper))
                simplified = sympy.simplify(result)
                try:
                    num_val = float(simplified.evalf())
                    num_str = f"<br><b>Numerical:</b> {num_val:.12g}"
                except Exception:
                    num_str = ""
                html = (
                    f"<b>&Sigma; {an_text}</b>,  n = {lower} &hellip; {upper}<br><br>"
                    f"<b>Exact:</b> {simplified}{num_str}"
                )
                self.sr_out.setHtml(html)
                self._add_to_global_history("Analysis·Series", "sum", an_text, str(simplified))

            elif action == "partial":
                f_num = sympy.lambdify(n_sym, a_expr, 'math')
                n0    = int(float(lower.evalf()))
                indices = np.arange(n0, n0 + N)
                terms = []
                for k in indices:
                    try:
                        v = f_num(int(k))
                        terms.append(float(v.real if hasattr(v, 'real') else v))
                    except Exception:
                        terms.append(float(a_expr.subs(n_sym, int(k)).evalf()))
                terms = np.array(terms, dtype=float)
                partial = np.cumsum(terms)

                try:
                    exact = float(sympy.summation(a_expr, (n_sym, lower, sympy.oo)).evalf())
                    # Only show reference line if the result looks finite and plausible
                    # (sympy can return nonsense for divergent series)
                    has_exact = math.isfinite(exact) and abs(exact) < 1e15
                except Exception:
                    has_exact = False

                self.sr_fig.clear()
                ax = self.sr_fig.add_subplot(111)
                self._style_axes(ax)
                ax.plot(indices, partial, color='#88c0d0', linewidth=1.4,
                        marker='o', markersize=2, label='Sₙ')
                if has_exact:
                    ax.axhline(exact, color='#ebcb8b', linestyle='--', linewidth=1,
                               label=f'S = {exact:.6g}')
                ax.set_xlabel('n', color='#eceff4', fontsize=9)
                ax.set_ylabel('Partial sum  Sₙ', color='#eceff4', fontsize=9)
                ax.set_title(f'&Sigma; {an_text}', color='#eceff4', fontsize=9)
                ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
                self.sr_fig.tight_layout(pad=0.6)
                self.sr_canvas.draw_idle()

                self.sr_out.setHtml(
                    f"<b>S<sub>{N}</sub> &asymp; {partial[-1]:.12g}</b><br>"
                    f"Last term: a({indices[-1]}) &asymp; {terms[-1]:.4e}<br>"
                    + (f"Exact limit: {exact:.12g}" if has_exact else "")
                )

            elif action == "common":
                rows = "".join(
                    f"<tr><td style='padding:3px 8px'>{lbl}</td>"
                    f"<td style='padding:3px 4px'><a href='{i}' style='color:#88c0d0'>▶ Try</a></td></tr>"
                    for i, (lbl, *_) in enumerate(self._SR_PRESETS)
                )
                self.sr_out.setHtml(
                    "<b>Common Series</b> — click ▶ Try to load &amp; compute<br>"
                    f"<table>{rows}</table>"
                )

        except Exception as e:
            self.sr_out.setHtml(self._err_html(e))

    # ══════════════════════════════════════════════════════════════════════
    # Numerical Methods tab
    # ══════════════════════════════════════════════════════════════════════

    def setup_numerical_tab(self):
        w = QWidget()
        self.tabs.addTab(w, "Numerical")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(4, 4, 4, 4)
        self._nm_tabs = QTabWidget()
        outer.addWidget(self._nm_tabs)
        self._setup_nm_roots()
        self._setup_nm_integration()
        self._setup_nm_interpolation()
        self._setup_nm_fitting()

    # ── Root Finding ───────────────────────────────────────────────────────

    def _setup_nm_roots(self):
        tab = QWidget()
        self._nm_tabs.addTab(tab, "Root Finding")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("f(x) = 0")
        g = QGridLayout(grp)
        g.setSpacing(6)
        g.addWidget(QLabel("f(x) ="), 0, 0)
        self.nm_rf_f = QLineEdit("x**3 - x - 2")
        self.nm_rf_f.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self.nm_rf_f, 0, 1)

        params = [
            ("a  (left bracket):", "nm_rf_a",  "1"),
            ("b  (right bracket):", "nm_rf_b", "2"),
            ("x₀  (initial guess):", "nm_rf_x0","1.5"),
            ("Tolerance:", "nm_rf_tol",         "1e-9"),
            ("Max iterations:", "nm_rf_maxiter","100"),
        ]
        for row, (lbl, attr, default) in enumerate(params, start=1):
            g.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            g.addWidget(w, row, 1)

        methods = [
            ("Bisection",     "bisection"),
            ("Newton-Raphson","newton"),
            ("Secant",        "secant"),
            ("Regula Falsi",  "regula"),
            ("Brent's Method","brent"),
        ]
        for lbl, act in methods:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_rf(a))
            g.addWidget(btn, g.rowCount(), 0, 1, 2)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.nm_rf_fig, self.nm_rf_canvas = self._make_figure()
        rl.addWidget(self.nm_rf_canvas, 1)
        self._make_output(rl, "nm_rf_out", 110)
        outer.addWidget(right, 3)

    def _run_rf(self, method):
        try:
            x_sym = sympy.Symbol('x')
            f_expr = sympy.sympify(self.nm_rf_f.text())
            f_num  = sympy.lambdify(x_sym, f_expr, 'numpy')
            df_expr = sympy.diff(f_expr, x_sym)
            df_num  = sympy.lambdify(x_sym, df_expr, 'numpy')

            a   = float(sympy.sympify(self.nm_rf_a.text()).evalf())
            b   = float(sympy.sympify(self.nm_rf_b.text()).evalf())
            x0  = float(sympy.sympify(self.nm_rf_x0.text()).evalf())
            tol = float(self.nm_rf_tol.text())
            maxn= int(self.nm_rf_maxiter.text())

            history = []   # (iteration, x, f(x))
            root = None

            if method == "bisection":
                aa, bb = a, b
                for i in range(maxn):
                    mid = (aa + bb) / 2
                    fm  = f_num(mid)
                    history.append((i+1, mid, fm))
                    if abs(fm) < tol or (bb - aa)/2 < tol:
                        root = mid; break
                    if f_num(aa) * fm < 0:
                        bb = mid
                    else:
                        aa = mid
                else:
                    root = mid

            elif method == "newton":
                xi = x0
                for i in range(maxn):
                    fi  = f_num(xi)
                    dfi = df_num(xi)
                    if abs(dfi) < 1e-14:
                        break
                    xi_new = xi - fi / dfi
                    history.append((i+1, xi_new, f_num(xi_new)))
                    if abs(xi_new - xi) < tol:
                        root = xi_new; break
                    xi = xi_new
                else:
                    root = xi

            elif method == "secant":
                x_prev, xi = a, x0
                for i in range(maxn):
                    fp, fi = f_num(x_prev), f_num(xi)
                    if abs(fi - fp) < 1e-14:
                        break
                    xi_new = xi - fi * (xi - x_prev) / (fi - fp)
                    history.append((i+1, xi_new, f_num(xi_new)))
                    if abs(xi_new - xi) < tol:
                        root = xi_new; break
                    x_prev, xi = xi, xi_new
                else:
                    root = xi

            elif method == "regula":
                aa, bb = a, b
                for i in range(maxn):
                    fa, fb = f_num(aa), f_num(bb)
                    c = bb - fb * (bb - aa) / (fb - fa)
                    fc = f_num(c)
                    history.append((i+1, c, fc))
                    if abs(fc) < tol:
                        root = c; break
                    if fa * fc < 0:
                        bb = c
                    else:
                        aa = c
                else:
                    root = c

            elif method == "brent":

                root = brentq(f_num, a, b, xtol=tol, maxiter=maxn,
                              full_output=False)
                history = [(1, root, f_num(root))]

            # Plot
            margin = (b - a) * 0.3
            xs = np.linspace(a - margin, b + margin, 500)
            with np.errstate(all='ignore'):
                ys = np.asarray(f_num(xs), dtype=float)
            ys[~np.isfinite(ys)] = np.nan

            self.nm_rf_fig.clear()
            ax = self.nm_rf_fig.add_subplot(111)
            self._style_axes(ax)
            ax.plot(xs, ys, color='#88c0d0', linewidth=2, label='f(x)')
            ax.axhline(0, color='#7b88a8', linewidth=0.8)
            if root is not None:
                ax.axvline(root, color='#bf616a', linestyle='--', linewidth=1.2)
                ax.plot(root, f_num(root), 'o', color='#ebcb8b', markersize=8,
                        label=f'root ≈ {root:.8g}')
            # Shade bracket
            ax.axvspan(a, b, alpha=0.07, color='#a3be8c')
            ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
            ax.set_title(f"{method.capitalize()}  —  f(x) = {self.nm_rf_f.text()}",
                         color='#eceff4', fontsize=9)
            self.nm_rf_fig.tight_layout(pad=0.6)
            self.nm_rf_canvas.draw_idle()

            iters = len(history)
            root_str = f"{root:.10g}" if root is not None else "not found"
            fval_str = f"{f_num(root):.4e}" if root is not None else "—"
            self.nm_rf_out.setHtml(
                f"<b>Method:</b> {method} &nbsp; <b>Iterations:</b> {iters}<br>"
                f"<b>Root ≈</b> {root_str}<br>"
                f"<b>f(root) =</b> {fval_str}"
            )
            self._add_to_global_history("Numerical·Roots", method,
                                        self.nm_rf_f.text(), f"root≈{root_str}")

        except Exception as e:
            self.nm_rf_out.setHtml(self._err_html(e))

    # ── Numerical Integration ──────────────────────────────────────────────

    def _setup_nm_integration(self):
        tab = QWidget()
        self._nm_tabs.addTab(tab, "Integration")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("∫ f(x) dx  from a to b")
        g = QGridLayout(grp)
        g.setSpacing(6)
        g.addWidget(QLabel("f(x) ="), 0, 0)
        self.nm_int_f = QLineEdit("sin(x)**2")
        self.nm_int_f.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self.nm_int_f, 0, 1)

        for row, (lbl, attr, default) in enumerate([
            ("a =", "nm_int_a", "0"),
            ("b =", "nm_int_b", "pi"),
            ("n  (subintervals):", "nm_int_n", "100"),
        ], start=1):
            g.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            g.addWidget(w, row, 1)

        methods = [
            ("Trapezoidal Rule", "trap"),
            ("Simpson's Rule",   "simpson"),
            ("Gaussian Quadrature", "gauss"),
            ("Adaptive (scipy)",    "adaptive"),
            ("Compare All",         "compare"),
        ]
        for lbl, act in methods:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_nm_int(a))
            g.addWidget(btn, g.rowCount(), 0, 1, 2)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.nm_int_fig, self.nm_int_canvas = self._make_figure()
        rl.addWidget(self.nm_int_canvas, 1)
        self._make_output(rl, "nm_int_out", 110)
        outer.addWidget(right, 3)

    def _run_nm_int(self, method):

        try:
            x_sym = sympy.Symbol('x')
            f_expr = sympy.sympify(self.nm_int_f.text())
            f_num  = sympy.lambdify(x_sym, f_expr, 'numpy')
            a = float(sympy.sympify(self.nm_int_a.text()).evalf())
            b = float(sympy.sympify(self.nm_int_b.text()).evalf())
            n = int(self.nm_int_n.text())
            if n % 2 == 1:
                n += 1  # Simpson requires even

            xs = np.linspace(a, b, n + 1)
            with np.errstate(all='ignore'):
                ys = np.asarray(f_num(xs), dtype=float)

            def _trap():
                return np.trapz(ys, xs)

            def _simp():
                h = (b - a) / n
                return h/3 * (ys[0] + 4*np.sum(ys[1:-1:2]) + 2*np.sum(ys[2:-2:2]) + ys[-1])

            def _gauss():
                return fixed_quad(lambda x: np.asarray(f_num(x), dtype=float), a, b, n=min(n, 100))[0]

            def _adapt():
                return _quad(lambda x: float(np.asarray(f_num(np.array([x])), dtype=float)[0]), a, b)[0]

            results = {}
            if method == "compare":
                results = {
                    "Trapezoidal":   _trap(),
                    "Simpson's":     _simp(),
                    "Gauss":         _gauss(),
                    "Adaptive":      _adapt(),
                }
                exact_sym = sympy.integrate(f_expr, (x_sym, a, b))
                try:
                    exact = float(exact_sym.evalf())
                    results["Exact (sympy)"] = exact
                except Exception:
                    exact = None
            else:
                fn_map = {"trap": _trap, "simpson": _simp,
                          "gauss": _gauss, "adaptive": _adapt}
                results = {method: fn_map[method]()}

            # Plot
            xs_plot = np.linspace(a, b, 400)
            with np.errstate(all='ignore'):
                ys_plot = np.asarray(f_num(xs_plot), dtype=float)
            ys_plot[~np.isfinite(ys_plot)] = np.nan

            self.nm_int_fig.clear()
            ax = self.nm_int_fig.add_subplot(111)
            self._style_axes(ax)
            ax.plot(xs_plot, ys_plot, color='#88c0d0', linewidth=2, label='f(x)')
            ax.fill_between(xs_plot, ys_plot, alpha=0.18, color='#a3be8c')
            ax.axhline(0, color='#7b88a8', linewidth=0.6)

            if method in ("trap", "compare"):
                vis_n = min(n, 20)
                xs_v = np.linspace(a, b, vis_n + 1)
                ys_v = np.asarray(f_num(xs_v), dtype=float)
                ax.vlines(xs_v, 0, ys_v, colors='#ebcb8b', linewidth=0.8, alpha=0.6)
            elif method == "simpson":
                vis_n = min(n, 20)
                if vis_n % 2: vis_n += 1
                xs_v = np.linspace(a, b, vis_n + 1)
                ys_v = np.asarray(f_num(xs_v), dtype=float)
                ax.vlines(xs_v, 0, ys_v, colors='#b48ead', linewidth=0.8, alpha=0.6)

            ax.set_title(f"∫ f(x) dx  on [{a:.4g}, {b:.4g}]", color='#eceff4', fontsize=9)
            ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
            self.nm_int_fig.tight_layout(pad=0.6)
            self.nm_int_canvas.draw_idle()

            html = "<br>".join(
                f"<b>{k}:</b> {v:.10g}" for k, v in results.items()
            )
            self.nm_int_out.setHtml(html)
            primary_val = list(results.values())[0]
            self._add_to_global_history("Numerical·Integration", method,
                                        self.nm_int_f.text(), f"{primary_val:.8g}")

        except Exception as e:
            self.nm_int_out.setHtml(self._err_html(e))

    # ── Interpolation ──────────────────────────────────────────────────────

    def _setup_nm_interpolation(self):
        tab = QWidget()
        self._nm_tabs.addTab(tab, "Interpolation")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("Data Points")
        g = QGridLayout(grp)
        g.setSpacing(6)
        hint = QLabel("x values (comma/space separated):")
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        g.addWidget(hint, 0, 0, 1, 2)
        self.nm_ip_x = QTextEdit("0, 1, 2, 3, 4, 5")
        self.nm_ip_x.setFixedHeight(36)
        self.nm_ip_x.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
            "color: #eceff4; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px;"
        )
        g.addWidget(self.nm_ip_x, 1, 0, 1, 2)
        hint2 = QLabel("y values:")
        hint2.setStyleSheet("color: #7b88a8; font-size: 10px;")
        g.addWidget(hint2, 2, 0, 1, 2)
        self.nm_ip_y = QTextEdit("0, 1, 4, 9, 16, 25")
        self.nm_ip_y.setFixedHeight(36)
        self.nm_ip_y.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
            "color: #eceff4; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px;"
        )
        g.addWidget(self.nm_ip_y, 3, 0, 1, 2)

        g.addWidget(QLabel("Eval at x ="), 4, 0)
        self.nm_ip_eval = QLineEdit("2.5")
        self.nm_ip_eval.setStyleSheet(self._FIELD_STYLE)
        g.addWidget(self.nm_ip_eval, 4, 1)

        methods = [
            ("Lagrange Polynomial", "lagrange"),
            ("Newton Divided Diff.", "newton_dd"),
            ("Cubic Spline (natural)","cubic_spline"),
            ("Linear Spline",         "linear"),
        ]
        for lbl, act in methods:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_nm_interp(a))
            g.addWidget(btn, g.rowCount(), 0, 1, 2)
        ll.addWidget(grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.nm_ip_fig, self.nm_ip_canvas = self._make_figure()
        rl.addWidget(self.nm_ip_canvas, 1)
        self._make_output(rl, "nm_ip_out", 90)
        outer.addWidget(right, 3)

    def _run_nm_interp(self, method):

        try:
            def _parse(text):
                return np.array([float(v) for v in text.replace(',', ' ').split()])

            xs = _parse(self.nm_ip_x.toPlainText())
            ys = _parse(self.nm_ip_y.toPlainText())
            xe = float(self.nm_ip_eval.text())

            order = np.argsort(xs)
            xs, ys = xs[order], ys[order]

            x_plot = np.linspace(xs[0], xs[-1], 500)

            if method == "lagrange":
                def _lagrange(x_eval):
                    total = 0.0
                    for i in range(len(xs)):
                        term = ys[i]
                        for j in range(len(xs)):
                            if i != j:
                                term *= (x_eval - xs[j]) / (xs[i] - xs[j])
                        total += term
                    return total
                y_plot = np.array([_lagrange(xi) for xi in x_plot])
                y_eval = _lagrange(xe)

            elif method == "newton_dd":
                n = len(xs)
                dd = ys.copy().astype(float)
                coefs = [dd[0]]
                for lvl in range(1, n):
                    m = len(dd) - 1
                    dd = np.diff(dd) / (xs[lvl:lvl + m] - xs[:m])
                    coefs.append(dd[0])
                def _newton(x_eval):
                    val = coefs[-1]
                    for k in range(len(coefs)-2, -1, -1):
                        val = val * (x_eval - xs[k]) + coefs[k]
                    return val
                y_plot = np.array([_newton(xi) for xi in x_plot])
                y_eval = _newton(xe)

            elif method == "cubic_spline":
                cs = CubicSpline(xs, ys, bc_type='natural')
                y_plot = cs(x_plot)
                y_eval = float(cs(xe))

            elif method == "linear":
                li = interp1d(xs, ys, kind='linear', fill_value='extrapolate')
                y_plot = li(x_plot)
                y_eval = float(li(xe))

            # Clip runaway polynomial oscillations for display
            y_finite = y_plot[np.isfinite(y_plot)]
            if len(y_finite):
                lo = np.percentile(y_finite, 1); hi = np.percentile(y_finite, 99)
                pad = max(abs(hi - lo) * 0.5, 1)
                y_plot = np.clip(y_plot, lo - pad, hi + pad)

            self.nm_ip_fig.clear()
            ax = self.nm_ip_fig.add_subplot(111)
            self._style_axes(ax)
            ax.scatter(xs, ys, color='#ebcb8b', s=50, zorder=5, label='data')
            ax.plot(x_plot, y_plot, color='#88c0d0', linewidth=2,
                    label=method.replace('_', ' '))
            ax.axvline(xe, color='#b48ead', linestyle=':', linewidth=1)
            ax.plot(xe, y_eval, 's', color='#bf616a', markersize=8,
                    label=f'f({xe:.4g}) ≈ {y_eval:.6g}')
            ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
            ax.set_title(method.replace('_', ' ').title(), color='#eceff4', fontsize=9)
            self.nm_ip_fig.tight_layout(pad=0.6)
            self.nm_ip_canvas.draw_idle()

            self.nm_ip_out.setHtml(
                f"<b>Method:</b> {method.replace('_', ' ')}<br>"
                f"<b>Points:</b> {len(xs)}<br>"
                f"<b>f({xe:.4g}) ≈</b> {y_eval:.10g}"
            )
            self._add_to_global_history("Numerical·Interp", method,
                                        f"n={len(xs)}", f"f({xe})≈{y_eval:.6g}")

        except Exception as e:
            self.nm_ip_out.setHtml(self._err_html(e))

    # ── Curve Fitting ──────────────────────────────────────────────────────

    def _setup_nm_fitting(self):
        tab = QWidget()
        self._nm_tabs.addTab(tab, "Curve Fitting")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(10)

        grp = QGroupBox("Data")
        g = QGridLayout(grp)
        g.setSpacing(6)
        for row, (hint_text, attr, default) in enumerate([
            ("x values (comma/space):", "nm_fit_x", "1, 2, 3, 4, 5, 6, 7, 8"),
            ("y values:",               "nm_fit_y", "2.1, 3.9, 8.1, 16.0, 24.9, 36.1, 49.0, 63.8"),
        ]):
            hint = QLabel(hint_text)
            hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
            g.addWidget(hint, row*2, 0, 1, 2)
            te = QTextEdit(default)
            te.setFixedHeight(36)
            te.setStyleSheet(
                "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
                "color: #eceff4; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px;"
            )
            setattr(self, attr, te)
            g.addWidget(te, row*2+1, 0, 1, 2)
        ll.addWidget(grp)

        model_grp = QGroupBox("Model")
        mg = QGridLayout(model_grp)
        mg.setSpacing(8)

        mg.addWidget(QLabel("Polynomial degree:"), 0, 0)
        self.nm_fit_deg = QLineEdit("2")
        self.nm_fit_deg.setFixedWidth(50)
        self.nm_fit_deg.setStyleSheet(self._FIELD_STYLE)
        mg.addWidget(self.nm_fit_deg, 0, 1)

        mg.addWidget(QLabel("Custom f(x, …):"), 1, 0)
        self.nm_fit_custom = QLineEdit("a * exp(-b * x) + c")
        self.nm_fit_custom.setStyleSheet(self._FIELD_STYLE)
        mg.addWidget(self.nm_fit_custom, 1, 1)

        hint3 = QLabel("Parameters are any letters in the expression except x")
        hint3.setStyleSheet("color: #7b88a8; font-size: 10px;")
        hint3.setWordWrap(True)
        mg.addWidget(hint3, 2, 0, 1, 2)

        fitting_methods = [
            ("Polynomial Fit",        "poly"),
            ("Linear (OLS)",          "linear"),
            ("Exponential  a·eᵇˣ",   "exp"),
            ("Power Law  a·xᵇ",       "power"),
            ("Custom Model (curve_fit)","custom"),
        ]
        for lbl, act in fitting_methods:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_nm_fit(a))
            mg.addWidget(btn, mg.rowCount(), 0, 1, 2)
        ll.addWidget(model_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.nm_fit_fig, self.nm_fit_canvas = self._make_figure()
        rl.addWidget(self.nm_fit_canvas, 1)
        self._make_output(rl, "nm_fit_out", 120)
        outer.addWidget(right, 3)

    def _run_nm_fit(self, method):


        try:
            def _parse(text):
                return np.array([float(v) for v in text.replace(',', ' ').split()])

            xs = _parse(self.nm_fit_x.toPlainText())
            ys = _parse(self.nm_fit_y.toPlainText())
            x_plot = np.linspace(xs.min(), xs.max(), 400)

            self.nm_fit_fig.clear()
            ax = self.nm_fit_fig.add_subplot(111)
            self._style_axes(ax)
            ax.scatter(xs, ys, color='#ebcb8b', s=50, zorder=5, label='data')

            label = method
            r2_str = ""

            if method == "poly":
                deg = int(self.nm_fit_deg.text())
                coeffs = np.polyfit(xs, ys, deg)
                p = np.poly1d(coeffs)
                y_fit = p(x_plot)
                y_pred = p(xs)
                terms = [f"{c:+.4g}·x^{deg-i}" if (deg-i)>1
                         else (f"{c:+.4g}·x" if (deg-i)==1 else f"{c:+.4g}")
                         for i, c in enumerate(coeffs)]
                eq = "f(x) = " + " ".join(terms)
                label = f"poly deg {deg}"

            elif method == "linear":
                coeffs = np.polyfit(xs, ys, 1)
                p = np.poly1d(coeffs)
                y_fit = p(x_plot)
                y_pred = p(xs)
                eq = f"f(x) = {coeffs[0]:+.6g}·x {coeffs[1]:+.6g}"
                label = "linear"

            elif method == "exp":
                def _exp_model(x, a, b): return a * np.exp(b * x)
                popt, _ = curve_fit(_exp_model, xs, ys, p0=[1, 0.1], maxfev=10000)
                y_fit  = _exp_model(x_plot, *popt)
                y_pred = _exp_model(xs, *popt)
                eq = f"f(x) = {popt[0]:.6g}·exp({popt[1]:.6g}·x)"
                label = "exp fit"

            elif method == "power":
                # Need positive x and y
                mask = (xs > 0) & (ys > 0)
                lx, ly = np.log(xs[mask]), np.log(ys[mask])
                b, log_a = np.polyfit(lx, ly, 1)
                a = np.exp(log_a)
                y_fit  = a * x_plot**b
                y_pred = a * xs**b
                eq = f"f(x) = {a:.6g}·x^{b:.6g}"
                label = "power fit"

            elif method == "custom":
                raw = self.nm_fit_custom.text()
                param_names = sorted(set(re.findall(r'\b([a-wyzA-Z])\b', raw)) - {'x', 'e'})
                x_sym = sympy.Symbol('x')
                param_syms = [sympy.Symbol(p) for p in param_names]
                expr = sympy.sympify(raw)
                f_lam = sympy.lambdify([x_sym] + param_syms, expr, 'numpy')
                def _custom_model(x, *params):
                    return np.asarray(f_lam(x, *params), dtype=float)
                p0 = [1.0] * len(param_names)
                popt, pcov = curve_fit(_custom_model, xs, ys, p0=p0, maxfev=20000)
                y_fit  = _custom_model(x_plot, *popt)
                y_pred = _custom_model(xs, *popt)
                eq = "f(x) = " + raw + "  →  " + ", ".join(
                    f"{n}={v:.5g}" for n, v in zip(param_names, popt))
                label = "custom"

            # R² score
            ss_res = np.sum((ys - y_pred)**2)
            ss_tot = np.sum((ys - np.mean(ys))**2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float('nan')
            r2_str = f"R² = {r2:.6f}"

            ax.plot(x_plot, y_fit, color='#88c0d0', linewidth=2, label=label)
            ax.legend(facecolor='#2e3440', labelcolor='#eceff4', fontsize=9)
            ax.set_title(f"Curve fit  —  {label}", color='#eceff4', fontsize=9)
            self.nm_fit_fig.tight_layout(pad=0.6)
            self.nm_fit_canvas.draw_idle()

            self.nm_fit_out.setHtml(
                f"<b>Model:</b> {eq}<br>"
                f"<b>{r2_str}</b>"
            )
            self._add_to_global_history("Numerical·Fitting", method,
                                        f"n={len(xs)}", r2_str)

        except Exception as e:
            self.nm_fit_out.setHtml(self._err_html(e))

    # ══════════════════════════════════════════════════════════════════════
    # Graph Theory tab
    # ══════════════════════════════════════════════════════════════════════

    def setup_graph_theory_tab(self):
        w = QWidget()
        self.tabs.addTab(w, "Graph Theory")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(4, 4, 4, 4)
        self._gt_tabs = QTabWidget()
        outer.addWidget(self._gt_tabs)
        self._gt_graph = None
        self._setup_gt_editor()
        self._setup_gt_algorithms()
        self._setup_gt_mst_color()
        self._setup_gt_properties()

    # ── shared helpers ─────────────────────────────────────────────────────

    def _gt_parse_graph(self):
        """Parse edge list from _gt_edges QTextEdit → nx.Graph / nx.DiGraph."""

        directed = self._gt_directed.isChecked()
        weighted = self._gt_weighted.isChecked()
        G = nx.DiGraph() if directed else nx.Graph()
        text = self._gt_edges.toPlainText().strip()
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.replace(',', ' ').split()
            if len(parts) >= 2:
                u, v = parts[0], parts[1]
                w = float(parts[2]) if (weighted and len(parts) >= 3) else 1.0
                G.add_edge(u, v, weight=w)
        return G

    def _gt_draw(self, ax, G, node_colors=None, edge_colors=None,
                 labels=None, highlight_edges=None, title=""):

        layout_name = self._gt_layout.currentText()
        layouts = {
            "Spring":    nx.spring_layout,
            "Circular":  nx.circular_layout,
            "Shell":     nx.shell_layout,
            "Spectral":  nx.spectral_layout,
            "Kamada-Kawai": nx.kamada_kawai_layout,
            "Random":    nx.random_layout,
        }
        try:
            pos = layouts.get(layout_name, nx.spring_layout)(G, seed=42)
        except Exception:
            pos = nx.spring_layout(G, seed=42)

        ax.set_facecolor('#1a1e27')
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(False)

        n_colors = node_colors if node_colors else ['#5e81ac'] * len(G.nodes)
        e_colors = edge_colors if edge_colors else ['#7b88a8'] * len(G.edges)

        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=n_colors,
                               node_size=500, alpha=0.95)
        nx.draw_networkx_labels(G, pos, ax=ax,
                                font_color='#eceff4', font_size=9, font_weight='bold')

        arrows = isinstance(G, nx.DiGraph)
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color=e_colors,
                               width=1.8, alpha=0.75, arrows=arrows,
                               arrowsize=18, arrowstyle='->')

        if highlight_edges:
            nx.draw_networkx_edges(G, pos, edgelist=highlight_edges, ax=ax,
                                   edge_color='#ebcb8b', width=3.0, alpha=0.95,
                                   arrows=arrows, arrowsize=20, arrowstyle='->')

        if self._gt_weighted.isChecked():
            edge_labels = nx.get_edge_attributes(G, 'weight')
            edge_labels = {k: f"{v:.4g}" for k, v in edge_labels.items()}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                         font_color='#88c0d0', font_size=7)
        if title:
            ax.set_title(title, color='#eceff4', fontsize=9, pad=4)


    # ── Graph Editor ───────────────────────────────────────────────────────

    def _setup_gt_editor(self):
        tab = QWidget()
        self._gt_tabs.addTab(tab, "Graph")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(8)

        grp = QGroupBox("Edge List")
        gl = QVBoxLayout(grp)
        hint = QLabel("One edge per line:  u v  [weight]\nExample:  A B 3")
        hint.setStyleSheet("color: #7b88a8; font-size: 10px;")
        gl.addWidget(hint)
        self._gt_edges = QTextEdit("A B 1\nA C 4\nB C 2\nB D 5\nC D 1\nD E 3\nC E 2")
        self._gt_edges.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 8px; "
            "color: #eceff4; font-family: 'Consolas', monospace; font-size: 12px; padding: 4px;"
        )
        gl.addWidget(self._gt_edges)
        ll.addWidget(grp)

        opt_grp = QGroupBox("Options")
        og = QGridLayout(opt_grp)
        og.setSpacing(6)

        from PyQt6.QtWidgets import QCheckBox
        self._gt_directed = QCheckBox("Directed")
        self._gt_directed.setStyleSheet("color: #eceff4;")
        self._gt_weighted = QCheckBox("Weighted")
        self._gt_weighted.setChecked(True)
        self._gt_weighted.setStyleSheet("color: #eceff4;")
        og.addWidget(self._gt_directed, 0, 0)
        og.addWidget(self._gt_weighted, 0, 1)

        og.addWidget(QLabel("Layout:"), 1, 0)
        self._gt_layout = QComboBox()
        self._gt_layout.addItems(["Spring", "Circular", "Shell", "Spectral",
                                   "Kamada-Kawai", "Random"])
        self._gt_layout.setStyleSheet(
            "background-color: #242933; color: #eceff4; border: 1px solid #3b4252; "
            "border-radius: 6px; padding: 3px; font-size: 12px;"
        )
        og.addWidget(self._gt_layout, 1, 1)
        ll.addWidget(opt_grp)

        preset_grp = QGroupBox("Presets")
        pg = QGridLayout(preset_grp)
        presets = {
            "Petersen":  "0 1\n0 4\n0 5\n1 2\n1 6\n2 3\n2 7\n3 4\n3 8\n4 9\n5 7\n5 8\n6 8\n6 9\n7 9",
            "K5":        "A B\nA C\nA D\nA E\nB C\nB D\nB E\nC D\nC E\nD E",
            "K3,3":      "1 A\n1 B\n1 C\n2 A\n2 B\n2 C\n3 A\n3 B\n3 C",
            "Cycle C6":  "1 2\n2 3\n3 4\n4 5\n5 6\n6 1",
            "Tree":      "r A\nr B\nA C\nA D\nB E\nB F\nC G",
            "DAG":       "A B 2\nA C 3\nB D 1\nC D 4\nC E 2\nD F 5\nE F 1",
        }
        for idx, (label, edges) in enumerate(presets.items()):
            btn = QPushButton(label)
            btn.setStyleSheet(self._BTN_STYLE_SM)
            btn.clicked.connect(lambda _, e=edges: self._gt_edges.setPlainText(e))
            pg.addWidget(btn, idx // 3, idx % 3)
        ll.addWidget(preset_grp)

        draw_btn = QPushButton("Draw Graph")
        draw_btn.setStyleSheet(self._BTN_STYLE)
        draw_btn.clicked.connect(self._run_gt_draw)
        ll.addWidget(draw_btn)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._gt_fig = Figure(facecolor='#1a1e27')
        self._gt_canvas = FigureCanvas(self._gt_fig)
        rl.addWidget(self._gt_canvas, 1)
        self._make_output(rl, '_gt_draw_out', 90)
        outer.addWidget(right, 3)

    def _run_gt_draw(self):
        try:
            G = self._gt_parse_graph()
            self._gt_graph = G
    
            self._gt_fig.clear()
            ax = self._gt_fig.add_subplot(111)
            self._gt_draw(ax, G, title=f"Graph  —  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
            self._gt_fig.tight_layout(pad=0.3)
            self._gt_canvas.draw_idle()

            deg = dict(G.degree())
            deg_seq = sorted(deg.values(), reverse=True)
            density = nx.density(G)
            self._gt_draw_out.setHtml(
                f"<b>Nodes:</b> {G.number_of_nodes()}  "
                f"<b>Edges:</b> {G.number_of_edges()}<br>"
                f"<b>Degree sequence:</b> {deg_seq}<br>"
                f"<b>Density:</b> {density:.4g}"
            )
            self._add_to_global_history("GraphTheory", "draw",
                                        f"{G.number_of_nodes()}n,{G.number_of_edges()}e",
                                        f"density={density:.4g}")
        except Exception as e:
            self._gt_draw_out.setHtml(self._err_html(e))

    # ── Algorithms ─────────────────────────────────────────────────────────

    def _setup_gt_algorithms(self):
        tab = QWidget()
        self._gt_tabs.addTab(tab, "Algorithms")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(8)

        grp = QGroupBox("Parameters")
        g = QGridLayout(grp)
        g.setSpacing(6)
        for row, (lbl, attr, default) in enumerate([
            ("Source node:", "_gt_src", "A"),
            ("Target node:", "_gt_tgt", "F"),
        ]):
            g.addWidget(QLabel(lbl), row, 0)
            w = QLineEdit(default)
            w.setStyleSheet(self._FIELD_STYLE)
            setattr(self, attr, w)
            g.addWidget(w, row, 1)
        ll.addWidget(grp)

        algo_grp = QGroupBox("Algorithm")
        ag = QGridLayout(algo_grp)
        ag.setSpacing(8)
        algos = [
            ("BFS  (breadth-first)",   "bfs"),
            ("DFS  (depth-first)",      "dfs"),
            ("Dijkstra shortest path",  "dijkstra"),
            ("Bellman-Ford",            "bellman_ford"),
            ("Floyd-Warshall  (all-pairs)", "floyd"),
            ("Topological Sort  (DAG)", "topo_sort"),
        ]
        for idx, (lbl, act) in enumerate(algos):
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_gt_algo(a))
            ag.addWidget(btn, idx // 2, idx % 2)
        ll.addWidget(algo_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._gt_algo_fig = Figure(facecolor='#1a1e27')
        self._gt_algo_canvas = FigureCanvas(self._gt_algo_fig)
        rl.addWidget(self._gt_algo_canvas, 1)
        self._make_output(rl, '_gt_algo_out', 130)
        outer.addWidget(right, 3)

    def _run_gt_algo(self, algo):
        try:
            G = self._gt_get_graph()
    
            src = self._gt_src.text().strip()
            tgt = self._gt_tgt.text().strip()

            highlight = []
            node_colors = {n: '#5e81ac' for n in G.nodes}
            result_html = ""

            if algo == "bfs":
                _tree = nx.bfs_tree(G, src)
                order = list(_tree.nodes())
                highlight = list(_tree.edges())
                for i, n in enumerate(order):
                    node_colors[n] = f"#{min(0x5e+i*20,0xff):02x}81ac"
                result_html = (f"<b>BFS from {src}:</b><br>"
                               + " → ".join(order))

            elif algo == "dfs":
                _tree = nx.dfs_tree(G, src)
                order = list(_tree.nodes())
                highlight = list(_tree.edges())
                for i, n in enumerate(order):
                    node_colors[n] = f"#{min(0xa3+i*8,0xff):02x}be8c"
                result_html = (f"<b>DFS from {src}:</b><br>"
                               + " → ".join(order))

            elif algo == "dijkstra":
                length, path = nx.single_source_dijkstra(G, src, tgt,
                                                          weight='weight')
                highlight = list(zip(path, path[1:]))
                for n in path:
                    node_colors[n] = '#ebcb8b'
                result_html = (f"<b>Dijkstra  {src} → {tgt}</b><br>"
                               f"Path: {' → '.join(path)}<br>"
                               f"Total weight: <b>{length:.6g}</b>")

            elif algo == "bellman_ford":
                length, path = nx.single_source_bellman_ford(G, src, tgt,
                                                              weight='weight')
                highlight = list(zip(path, path[1:]))
                for n in path:
                    node_colors[n] = '#ebcb8b'
                result_html = (f"<b>Bellman-Ford  {src} → {tgt}</b><br>"
                               f"Path: {' → '.join(path)}<br>"
                               f"Total weight: <b>{length:.6g}</b>")

            elif algo == "floyd":
                lengths = dict(nx.all_pairs_dijkstra_path_length(G, weight='weight'))
                rows = []
                nodes = sorted(G.nodes())
                header = "From\\To  " + "  ".join(f"{n:>5}" for n in nodes)
                rows.append(header)
                for u in nodes:
                    row = f"{u:>5}    " + "  ".join(
                        f"{lengths[u].get(v, float('inf')):>5.2g}" for v in nodes)
                    rows.append(row)
                result_html = ("<b>All-pairs shortest paths:</b><br><pre style='font-size:10px;'>"
                               + "\n".join(rows) + "</pre>")

            elif algo == "topo_sort":
                UG = G if isinstance(G, nx.DiGraph) else nx.DiGraph(G)
                try:
                    order = list(nx.topological_sort(UG))
                    result_html = (f"<b>Topological order:</b><br>"
                                   + " → ".join(order))
                    for i, n in enumerate(order):
                        node_colors[n] = f"#{min(0x88+i*16,0xff):02x}c0d0"
                except nx.NetworkXUnfeasible:
                    result_html = "<b style='color:#bf616a'>Graph contains a cycle — no topological order.</b>"

            colors = [node_colors.get(n, '#5e81ac') for n in G.nodes]
            self._gt_algo_fig.clear()
            ax = self._gt_algo_fig.add_subplot(111)
            self._gt_draw(ax, G, node_colors=colors,
                          highlight_edges=highlight,
                          title=algo.replace('_', ' ').title())
            self._gt_algo_fig.tight_layout(pad=0.3)
            self._gt_algo_canvas.draw_idle()
            self._gt_algo_out.setHtml(result_html)
            self._add_to_global_history("GraphTheory", algo, f"{src}→{tgt}",
                                        result_html[:120].replace('<b>','').replace('</b>',''))

        except Exception as e:
            self._gt_algo_out.setHtml(self._err_html(e))

    # ── MST & Coloring ──────────────────────────────────────────────────────

    def _setup_gt_mst_color(self):
        tab = QWidget()
        self._gt_tabs.addTab(tab, "MST & Coloring")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(8)

        mst_grp = QGroupBox("Minimum Spanning Tree")
        mg = QGridLayout(mst_grp)
        mg.setSpacing(8)
        for lbl, act in [("Kruskal's MST", "kruskal"), ("Prim's MST", "prim"),
                          ("Maximum ST", "max_st")]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_gt_mst(a))
            mg.addWidget(btn, mg.rowCount(), 0, 1, 2)
        ll.addWidget(mst_grp)

        col_grp = QGroupBox("Graph Coloring")
        cg = QGridLayout(col_grp)
        cg.setSpacing(8)
        for lbl, act in [("Greedy Coloring", "greedy"),
                          ("Largest-First", "largest_first"),
                          ("DSATUR heuristic", "dsatur")]:
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_gt_color(a))
            cg.addWidget(btn, cg.rowCount(), 0, 1, 2)
        ll.addWidget(col_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._gt_mst_fig = Figure(facecolor='#1a1e27')
        self._gt_mst_canvas = FigureCanvas(self._gt_mst_fig)
        rl.addWidget(self._gt_mst_canvas, 1)
        self._make_output(rl, '_gt_mst_out', 110)
        outer.addWidget(right, 3)

    def _run_gt_mst(self, method):
        try:
            G = self._gt_get_graph()
    
            UG = G.to_undirected() if isinstance(G, nx.DiGraph) else G

            if method == "max_st":
                T = nx.maximum_spanning_tree(UG, weight='weight', algorithm='kruskal')
                label = "Maximum Spanning Tree"
            elif method == "prim":
                T = nx.minimum_spanning_tree(UG, weight='weight', algorithm='prim')
                label = "MST  (Prim)"
            else:
                T = nx.minimum_spanning_tree(UG, weight='weight', algorithm='kruskal')
                label = "MST  (Kruskal)"

            total_w = sum(d.get('weight', 1) for _, _, d in T.edges(data=True))
            mst_edges = list(T.edges())

            self._gt_mst_fig.clear()
            ax = self._gt_mst_fig.add_subplot(111)
            self._gt_draw(ax, UG, highlight_edges=mst_edges, title=label)
            self._gt_mst_fig.tight_layout(pad=0.3)
            self._gt_mst_canvas.draw_idle()

            edge_list = "  ".join(f"{u}-{v}" for u,v in mst_edges)
            self._gt_mst_out.setHtml(
                f"<b>{label}</b><br>"
                f"Edges ({T.number_of_edges()}): {edge_list}<br>"
                f"Total weight: <b>{total_w:.6g}</b>"
            )
            self._add_to_global_history("GraphTheory", method, "", f"total_w={total_w:.4g}")
        except Exception as e:
            self._gt_mst_out.setHtml(self._err_html(e))

    def _run_gt_color(self, strategy):
        try:
            G = self._gt_get_graph()
    
            UG = G.to_undirected() if isinstance(G, nx.DiGraph) else G

            strat_map = {
                "greedy":       "largest_first",
                "largest_first":"largest_first",
                "dsatur":       "DSATUR",
            }
            coloring = nx.coloring.greedy_color(UG, strategy=strat_map[strategy])
            num_colors = max(coloring.values()) + 1

            palette = ['#bf616a','#ebcb8b','#a3be8c','#88c0d0',
                       '#5e81ac','#b48ead','#d08770','#81a1c1']
            node_colors = [palette[coloring[n] % len(palette)] for n in UG.nodes]

            self._gt_mst_fig.clear()
            ax = self._gt_mst_fig.add_subplot(111)
            self._gt_draw(ax, UG, node_colors=node_colors,
                          title=f"Coloring  ({num_colors} colors)")
            self._gt_mst_fig.tight_layout(pad=0.3)
            self._gt_mst_canvas.draw_idle()

            groups = {}
            for node, color in coloring.items():
                groups.setdefault(color, []).append(str(node))
            color_html = "  ".join(f"<b>C{c}:</b> {','.join(ns)}" for c, ns in sorted(groups.items()))
            self._gt_mst_out.setHtml(
                f"<b>Chromatic number χ ≤ {num_colors}</b><br>{color_html}"
            )
            self._add_to_global_history("GraphTheory", f"coloring-{strategy}", "",
                                        f"χ≤{num_colors}")
        except Exception as e:
            self._gt_mst_out.setHtml(self._err_html(e))

    # ── Properties ─────────────────────────────────────────────────────────

    def _setup_gt_properties(self):
        tab = QWidget()
        self._gt_tabs.addTab(tab, "Properties")
        outer = QHBoxLayout(tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setSpacing(8)

        prop_grp = QGroupBox("Graph Properties")
        pg = QGridLayout(prop_grp)
        pg.setSpacing(8)
        props = [
            ("Basic Info",           "basic"),
            ("Degree Sequence",      "degree"),
            ("Connected Components", "components"),
            ("Is Bipartite?",        "bipartite"),
            ("Eulerian Path/Circuit","eulerian"),
            ("Adjacency Matrix",     "adj_matrix"),
            ("Centrality (degree)",  "centrality_deg"),
            ("Centrality (betweenness)", "centrality_bet"),
        ]
        for idx, (lbl, act) in enumerate(props):
            btn = QPushButton(lbl)
            btn.setStyleSheet(self._BTN_STYLE)
            btn.clicked.connect(lambda _, a=act: self._run_gt_props(a))
            pg.addWidget(btn, idx // 2, idx % 2)
        ll.addWidget(prop_grp)
        ll.addStretch()
        outer.addWidget(left, 2)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self._gt_prop_fig = Figure(facecolor='#1a1e27')
        self._gt_prop_canvas = FigureCanvas(self._gt_prop_fig)
        rl.addWidget(self._gt_prop_canvas, 1)
        self._make_output(rl, '_gt_prop_out', 160)
        outer.addWidget(right, 3)

    def _run_gt_props(self, prop):
        try:
            G = self._gt_get_graph()
    
            UG = G.to_undirected() if isinstance(G, nx.DiGraph) else G

            node_colors = ['#5e81ac'] * len(G.nodes)
            result_html = ""

            if prop == "basic":
                n, m = G.number_of_nodes(), G.number_of_edges()
                directed = isinstance(G, nx.DiGraph)
                connected = nx.is_connected(UG)
                result_html = (
                    f"<b>Nodes:</b> {n}  <b>Edges:</b> {m}<br>"
                    f"<b>Directed:</b> {directed}<br>"
                    f"<b>Density:</b> {nx.density(G):.4g}<br>"
                    f"<b>Self-loops:</b> {nx.number_of_selfloops(G)}<br>"
                    f"<b>Connected:</b> {connected}<br>"
                    + (f"<b>Diameter:</b> {nx.diameter(UG)}<br>" if connected else "")
                    + (f"<b>Radius:</b> {nx.radius(UG)}" if connected else "")
                )

            elif prop == "degree":
                deg = sorted(G.degree(), key=lambda x: -x[1])
                max_d = max(d for _, d in deg)
                palette = ['#5e81ac','#88c0d0','#a3be8c','#ebcb8b','#bf616a']
                node_colors = [palette[min(d // max(1, max_d // 4), 4)]
                               for n, d in sorted(G.degree(), key=lambda x: list(G.nodes).index(x[0]))]
                seq = sorted([d for _, d in G.degree()], reverse=True)
                rows = "".join(f"<b>{n}:</b> {d}  " for n, d in deg)
                result_html = (f"<b>Degree sequence:</b> {seq}<br>"
                               f"<b>Min deg:</b> {min(seq)}  "
                               f"<b>Max deg:</b> {max(seq)}  "
                               f"<b>Avg deg:</b> {sum(seq)/len(seq):.3g}<br>"
                               f"<br>{rows}")

            elif prop == "components":
                comps = list(nx.connected_components(UG))
                comps.sort(key=len, reverse=True)
                palette = ['#5e81ac','#a3be8c','#ebcb8b','#bf616a','#b48ead','#88c0d0']
                comp_map = {n: i for i, c in enumerate(comps) for n in c}
                node_colors = [palette[comp_map.get(n,0) % len(palette)] for n in G.nodes]
                rows = "".join(f"<b>C{i+1} ({len(c)} nodes):</b> {', '.join(sorted(c))}<br>"
                               for i, c in enumerate(comps))
                result_html = f"<b>Connected components:</b> {len(comps)}<br>" + rows

            elif prop == "bipartite":
                is_bip = nx.is_bipartite(UG)
                if is_bip:
                    sets = nx.bipartite.sets(UG)
                    node_colors = ['#88c0d0' if n in sets[0] else '#a3be8c' for n in G.nodes]
                    result_html = (f"<b>Bipartite: Yes</b><br>"
                                   f"Set X: {', '.join(sorted(str(n) for n in sets[0]))}<br>"
                                   f"Set Y: {', '.join(sorted(str(n) for n in sets[1]))}")
                else:
                    result_html = "<b>Bipartite: No</b>"

            elif prop == "eulerian":
                has_circuit = nx.is_eulerian(UG)
                has_path = nx.has_eulerian_path(UG)
                if has_circuit:
                    path = list(nx.eulerian_circuit(UG))
                    hl = path
                    result_html = (f"<b>Eulerian circuit exists</b><br>"
                                   f"{'  →  '.join(str(u) for u,v in path) + '  →  ' + str(path[0][0])}")
                elif has_path:
                    path = list(nx.eulerian_path(UG))
                    hl = path
                    result_html = (f"<b>Eulerian path exists</b><br>"
                                   f"{'  →  '.join(str(u) for u,v in path) + '  →  ' + str(path[-1][1])}")
                else:
                    odd_deg = [n for n, d in UG.degree() if d % 2 == 1]
                    result_html = (f"<b>No Eulerian path or circuit</b><br>"
                                   f"Odd-degree nodes: {odd_deg}")

            elif prop == "adj_matrix":
                nodes = sorted(G.nodes())
                A = nx.to_numpy_array(G, nodelist=nodes)
                header = "     " + "  ".join(f"{n:>4}" for n in nodes)
                rows = [header]
                for i, n in enumerate(nodes):
                    row = f"{n:>4}: " + "  ".join(f"{int(A[i,j]):>4}" if A[i,j]==int(A[i,j])
                                                   else f"{A[i,j]:>4.2g}" for j in range(len(nodes)))
                    rows.append(row)
                result_html = ("<b>Adjacency matrix:</b><br>"
                               "<pre style='font-size:9px;'>" + "\n".join(rows) + "</pre>")

            elif prop == "centrality_deg":
                cent = nx.degree_centrality(G)
                cent_sorted = sorted(cent.items(), key=lambda x: -x[1])
                max_c = max(cent.values()) if cent else 1
                palette = ['#7b88a8','#5e81ac','#88c0d0','#ebcb8b','#bf616a']
                node_colors = [palette[min(int(cent.get(n, 0) / max_c * 4), 4)] for n in G.nodes]
                rows = "  ".join(f"<b>{n}:</b>{v:.3f}" for n, v in cent_sorted)
                result_html = f"<b>Degree centrality:</b><br>{rows}"

            elif prop == "centrality_bet":
                cent = nx.betweenness_centrality(G, weight='weight', normalized=True)
                cent_sorted = sorted(cent.items(), key=lambda x: -x[1])
                max_c = max(cent.values()) if cent else 1
                palette = ['#7b88a8','#5e81ac','#88c0d0','#ebcb8b','#bf616a']
                node_colors = [palette[min(int(cent.get(n, 0) / max(max_c,1e-9) * 4), 4)] for n in G.nodes]
                rows = "  ".join(f"<b>{n}:</b>{v:.3f}" for n, v in cent_sorted)
                result_html = f"<b>Betweenness centrality:</b><br>{rows}"

            self._gt_prop_fig.clear()
            ax = self._gt_prop_fig.add_subplot(111)
            self._gt_draw(ax, G, node_colors=node_colors,
                          title=prop.replace('_', ' ').title())
            self._gt_prop_fig.tight_layout(pad=0.3)
            self._gt_prop_canvas.draw_idle()
            self._gt_prop_out.setHtml(result_html)
            self._add_to_global_history("GraphTheory", prop, "",
                                        result_html[:100].replace('<b>','').replace('</b>',''))

        except Exception as e:
            self._gt_prop_out.setHtml(self._err_html(e))

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
        hint.setStyleSheet("color: #7b88a8; font-size: 11px;")
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
        path = os.path.join(_user_data_dir(), 'history_export.txt')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for entry in self._global_history:
                    f.write(f"[{entry['timestamp']}]  {entry['tab']}  ·  {entry['action']}\n")
                    f.write(f"  Input:  {entry['input']}\n")
                    f.write(f"  Result: {entry['result']}\n\n")
            self._history_search.setPlaceholderText(f"Exported to {path}")
        except Exception as e:
            self._history_search.setPlaceholderText(f"Export failed: {e}")


def main() -> None:
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    window = Karhulaattori()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
