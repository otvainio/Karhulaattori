import sys
import math
import sympy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QGridLayout, QListWidget, QListWidgetItem,
    QLabel, QSplitter, QFrame
)

# Premium Nordic Dark Theme QSS Stylesheet
QSS_STYLESHEET = """
QMainWindow {
    background-color: #1e222b;
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
    font-size: 18px;
    font-weight: 500;
    font-family: 'Segoe UI', 'Outfit', sans-serif;
    min-height: 50px;
    min-width: 50px;
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
    font-size: 20px;
}

QPushButton.operatorBtn:hover {
    background-color: #434c5e;
    color: #8fbcbb;
}

/* Accent Buttons (Equals, Clear) */
QPushButton.accentBtn {
    background-color: #d8dee9;
    color: #2e3440;
    font-weight: bold;
}

QPushButton.accentBtn:hover {
    background-color: #e5e9f0;
}

QPushButton.accentBtn:pressed {
    background-color: #eceff4;
}

QPushButton.equalBtn {
    background-color: #88c0d0;
    color: #2e3440;
    font-weight: bold;
    font-size: 22px;
}

QPushButton.equalBtn:hover {
    background-color: #8fbcbb;
}

QPushButton.equalBtn:pressed {
    background-color: #a3be8c;
}

QPushButton.scientificBtn {
    background-color: #2b303c;
    color: #b48ead;
    font-size: 14px;
}

QPushButton.scientificBtn:hover {
    background-color: #353b4a;
}

QPushButton.symbolicBtn {
    background-color: #2f384c;
    color: #a3be8c;
    font-size: 14px;
}

QPushButton.symbolicBtn:hover {
    background-color: #3b4862;
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
    font-size: 14px;
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

/* Control Panel Toggle Button */
QPushButton#toggleSidebarBtn, QPushButton#toggleSciBtn {
    background-color: transparent;
    border: none;
    color: #81a1c1;
    font-size: 14px;
    text-decoration: underline;
    max-width: 120px;
    min-height: 25px;
}

QPushButton#toggleSidebarBtn:hover, QPushButton#toggleSciBtn:hover {
    color: #88c0d0;
}
"""

class Karhulaattori(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Karhulaattori - Premium Calculator")
        self.setMinimumSize(460, 640)
        self.resize(540, 720)
        
        # State variables
        self.expression = ""
        self.current_input = "0"
        self.new_entry_started = True
        
        # Build UI
        self.setup_ui()
        self.apply_styles()
        self.bind_shortcuts()
        self.update_displays()

    def setup_ui(self):
        # Central widget and layout
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Splitter to allow resizing the sidebar
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left Side (Calculator Display & Buttons)
        self.calc_container = QWidget()
        calc_layout = QVBoxLayout(self.calc_container)
        calc_layout.setContentsMargins(0, 0, 0, 0)
        calc_layout.setSpacing(10)
        self.splitter.addWidget(self.calc_container)
        
        # Displays Frame
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
        
        calc_layout.addWidget(display_frame)
        
        # Variable x input row (Toggles visibility with Scientific Mode)
        self.x_input_frame = QFrame()
        self.x_input_frame.setObjectName("xInputFrame")
        self.x_input_frame.setVisible(False)
        x_input_layout = QHBoxLayout(self.x_input_frame)
        x_input_layout.setContentsMargins(8, 2, 8, 2)
        
        x_label = QLabel("Variable x value:")
        x_label.setStyleSheet("color: #a3be8c; font-size: 14px; font-weight: bold;")
        x_input_layout.addWidget(x_label)
        
        self.x_value_input = QLineEdit("5")
        self.x_value_input.setObjectName("xValueInput")
        self.x_value_input.setStyleSheet("""
            QLineEdit#xValueInput {
                background-color: #2e3440;
                border: 1px solid #4c566a;
                border-radius: 6px;
                color: #eceff4;
                font-size: 14px;
                padding: 4px;
                max-width: 100px;
            }
        """)
        x_input_layout.addWidget(self.x_value_input)
        x_input_layout.addStretch()
        
        calc_layout.addWidget(self.x_input_frame)
        
        # Toggles Row
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
        
        calc_layout.addLayout(toggles_layout)
        
        # Keyboard grid (Stack of Scientific Panel & Grid)
        self.buttons_widget = QWidget()
        self.buttons_layout = QVBoxLayout(self.buttons_widget)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(8)
        
        # Create Scientific/Symbolic Grid
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
        
        # Create Core Grid
        core_grid_widget = QWidget()
        core_grid = QGridLayout(core_grid_widget)
        core_grid.setContentsMargins(0, 0, 0, 0)
        core_grid.setSpacing(8)
        
        # Grid: row 0 to 4
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
        calc_layout.addWidget(self.buttons_widget)
        
        # Right Side (History Sidebar)
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
        clear_hist_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                min-height: 24px;
                min-width: 50px;
                background-color: #3b4252;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #4c566a; }
        """)
        clear_hist_btn.clicked.connect(self.clear_history)
        sidebar_header.addWidget(clear_hist_btn)
        sidebar_layout.addLayout(sidebar_header)
        
        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.itemDoubleClicked.connect(self.history_item_clicked)
        sidebar_layout.addWidget(self.history_list)
        
        self.splitter.addWidget(self.sidebar)
        self.sidebar.setVisible(False)
        
        # Initial splitter ratio
        self.splitter.setSizes([450, 200])

    def apply_styles(self):
        self.setStyleSheet(QSS_STYLESHEET)

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
            '\r': ('equals', '='),  # Enter key
            '\n': ('equals', '='),
        }
        for key, (action, val) in ops.items():
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda a=action, v=val: self.handle_action(a, v))
            
        # Clear/Delete
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
                return  # Skip multiple dots
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
            # Adjust spacing or insert operator
            if self.new_entry_started and self.expression and self.expression[-1] in ["+", "-", "*", "/"]:
                self.expression = self.expression[:-1] + op_map[action]
            else:
                # Add implicit multiply if entering digit/var next to operator
                self.expression += f" {self.current_input} {op_map[action]}"
            
            self.new_entry_started = True
            
        elif action == "percent":
            try:
                # Use SymPy to safely calculate percentage
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
                # Standardize arithmetic notation
                eval_expr = full_expr.replace("×", "*").replace("÷", "/")
                
                # Parse expression using sympy
                x = sympy.Symbol('x')
                sym_expr = sympy.sympify(eval_expr)
                
                # Check if x is present in the equation
                if x in sym_expr.free_symbols:
                    # Substitute the value of x
                    x_val_str = self.x_value_input.text().strip()
                    x_val = sympy.sympify(x_val_str)
                    result_val = sym_expr.subs(x, x_val).evalf()
                else:
                    result_val = sym_expr.evalf()
                
                formatted_res = self.format_number(result_val)
                
                # Add to history
                readable_expr = full_expr.replace("*", "×").replace("/", "÷").strip()
                self.add_history_item(readable_expr, formatted_res)
                
                self.current_input = formatted_res
                self.expression = ""
                self.new_entry_started = True
            except Exception as e:
                self.current_input = "Error"
                self.new_entry_started = True
                
        # Scientific/Symbolic Operations
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
            
        # Pure Symbolic Features
        elif action in ["diff", "integrate", "simplify", "solve"]:
            full_expr = f"{self.expression} {self.current_input}".strip()
            try:
                eval_expr = full_expr.replace("×", "*").replace("÷", "/")
                x = sympy.Symbol('x')
                sym_expr = sympy.sympify(eval_expr)
                
                if action == "diff":
                    result = sympy.diff(sym_expr, x)
                    readable_op = f"d/dx({sym_expr})"
                elif action == "integrate":
                    result = sympy.integrate(sym_expr, x)
                    readable_op = f"∫({sym_expr})dx"
                elif action == "simplify":
                    result = sympy.simplify(sym_expr)
                    readable_op = f"simplify({sym_expr})"
                elif action == "solve":
                    result = sympy.solve(sym_expr, x)
                    readable_op = f"solve({sym_expr} = 0)"
                    
                formatted_res = str(result)
                self.add_history_item(readable_op, formatted_res)
                self.current_input = formatted_res
                self.expression = ""
                self.new_entry_started = True
            except Exception as e:
                self.current_input = "Error"
                self.new_entry_started = True
                
        self.update_displays()

    def format_number(self, value):
        try:
            # If it's a sympy number/float, format it
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Premium theme font selection
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    
    window = Karhulaattori()
    window.show()
    sys.exit(app.exec())
