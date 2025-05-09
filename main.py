import sys
import os
import re
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QListWidget, QMessageBox, QCheckBox, QComboBox, QSpinBox, QListWidgetItem, QFrame
)
from PyQt6.QtCore import Qt

# 🔹 Get the correct base directory (whether running as a script or as an .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)  # When running from .exe
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # When running as a script

PRESET_FILE = os.path.join(BASE_DIR, 'preset.json')

def save_preset():
    """ Save preset settings to preset.json in the executable's directory. """
    preset = {
        'prefix': "example",
        'suffix': "test",
        'simulation_mode': True
    }
    with open(PRESET_FILE, 'w', encoding='utf-8') as f:
        json.dump(preset, f)

def load_preset():
    """ Load preset settings from preset.json in the executable's directory. """
    if os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


class ListItemWidget(QWidget):
    def __init__(self, original_name):
        super().__init__()
        self.original_name_label = QLabel(original_name)
        self.preview_name_label = QLabel()

        # Make labels selectable
        self.original_name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.preview_name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # Set fixed width for labels (adjust as needed)
        self.original_name_label.setFixedWidth(400)
        self.preview_name_label.setFixedWidth(400)

        # Create a vertical line separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        layout = QHBoxLayout()
        layout.addWidget(self.original_name_label)
        layout.addWidget(separator)
        layout.addWidget(self.preview_name_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setPreviewText(self, text):
        self.preview_name_label.setText(text)

    def getOriginalName(self):
        return self.original_name_label.text()

    def getPreviewName(self):
        return self.preview_name_label.text()

    def updateOriginalName(self, text):
        self.original_name_label.setText(text)
        self.preview_name_label.setText('')


class HeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.original_label = QLabel('Original')
        self.preview_label = QLabel('Preview')

        # Set fixed widths matching the ListItemWidget labels
        self.original_label.setFixedWidth(400)
        self.preview_label.setFixedWidth(400)

        # Create a vertical line separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        # Set bold font for header labels
        font = self.original_label.font()
        font.setBold(True)
        self.original_label.setFont(font)
        self.preview_label.setFont(font)

        layout = QHBoxLayout()
        layout.addWidget(self.original_label)
        layout.addWidget(separator)
        layout.addWidget(self.preview_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class REnamer(QWidget):
    def __init__(self):
        super().__init__()
        self.rename_history = []
        self.rename_history_stack = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('REnamer')
        self.setGeometry(100, 100, 900, 700)

        # Widgets
        self.folder_label = QLabel('Folder:')
        self.folder_line_edit = QLineEdit()
        self.browse_button = QPushButton('Browse')
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.extension_label = QLabel('Filter Extension:')
        self.extension_line_edit = QLineEdit()

        self.prefix_label = QLabel('Add Prefix:')
        self.prefix_line_edit = QLineEdit()
        self.skip_existing_prefix_checkbox = QCheckBox('Skip if Prefix Exists')

        self.suffix_label = QLabel('Add Suffix:')
        self.suffix_line_edit = QLineEdit()
        self.skip_existing_suffix_checkbox = QCheckBox('Skip if Suffix Exists')

        self.replace_label = QLabel('Replace Text:')
        self.replace_line_edit = QLineEdit()
        self.with_label = QLabel('With:')
        self.with_line_edit = QLineEdit()

        self.regex_checkbox = QCheckBox('Use Regular Expressions')

        self.case_label = QLabel('Case Conversion:')
        self.case_combo_box = QComboBox()
        self.case_combo_box.addItems(['None', 'lowercase', 'UPPERCASE', 'Title Case', 'Sentence case'])

        self.numbering_checkbox = QCheckBox('Add Numbering')
        self.numbering_start_label = QLabel('Start:')
        self.numbering_start_spinbox = QSpinBox()
        self.numbering_start_spinbox.setValue(1)
        self.numbering_increment_label = QLabel('Increment:')
        self.numbering_increment_spinbox = QSpinBox()
        self.numbering_increment_spinbox.setValue(1)
        self.numbering_padding_label = QLabel('Padding:')
        self.numbering_padding_spinbox = QSpinBox()
        self.numbering_padding_spinbox.setValue(1)
        self.numbering_position_label = QLabel('Position:')
        self.numbering_position_combo_box = QComboBox()
        self.numbering_position_combo_box.addItems(['Prefix', 'Suffix'])

        self.conflict_label = QLabel('On Conflict:')
        self.conflict_combo_box = QComboBox()
        self.conflict_combo_box.addItems(['Skip', 'Overwrite', 'Rename'])

        self.simulation_checkbox = QCheckBox('Simulation Mode')
        self.fix_checkbox = QCheckBox('Apply Fix')

        self.rename_button = QPushButton('Rename Files')
        self.undo_button = QPushButton('Undo Last Rename')
        self.undo_button.setEnabled(False)
        self.reset_button = QPushButton('Reset')

        self.save_preset_button = QPushButton('Save Preset')
        self.load_preset_button = QPushButton('Load Preset')

        # Adding Tooltips
        self.folder_line_edit.setToolTip('Enter or browse to the folder containing files to rename.')
        self.browse_button.setToolTip('Click to browse and select a folder.')
        self.extension_line_edit.setToolTip('Filter files by extension (e.g., .txt). Leave blank for all files.')

        self.prefix_line_edit.setToolTip('Enter text to add at the beginning of file names.')
        self.suffix_line_edit.setToolTip('Enter text to add at the end of file names (before extension).')

        self.replace_line_edit.setToolTip('Enter the text you want to replace in file names.')
        self.with_line_edit.setToolTip('Enter the text that will replace the specified text.')
        self.regex_checkbox.setToolTip('Check to use regular expressions for find and replace.')

        self.case_combo_box.setToolTip('Select case conversion for file names.')

        self.numbering_checkbox.setToolTip('Check to add numbering to file names.')
        self.numbering_start_spinbox.setToolTip('Set the starting number for numbering.')
        self.numbering_increment_spinbox.setToolTip('Set the increment between numbers.')
        self.numbering_padding_spinbox.setToolTip(
            'Set the number of digits for numbering (e.g., padding of 3 for 001).')
        self.numbering_position_combo_box.setToolTip('Choose whether to add numbering as a prefix or suffix.')

        self.conflict_combo_box.setToolTip('Select how to handle file name conflicts.')
        self.simulation_checkbox.setToolTip('Check to simulate renaming without making actual changes.')
        self.fix_checkbox.setToolTip('Apply predefined fix rules to file names.')

        self.rename_button.setToolTip('Click to rename files according to the specified options.')
        self.undo_button.setToolTip('Click to undo the last renaming action.')
        self.reset_button.setToolTip('Click to reset all fields to their default values.')

        self.save_preset_button.setToolTip('Click to save current settings as a preset.')
        self.load_preset_button.setToolTip('Click to load a previously saved preset.')

        self.file_list_widget.setToolTip('Displays the list of files to be renamed.')
        self.skip_existing_prefix_checkbox.setToolTip('Skip adding the prefix if the file name already starts with it.')
        self.skip_existing_suffix_checkbox.setToolTip('Skip adding the suffix if the file name already ends with it.')

        # Header Widget for Original and Preview labels
        self.header_widget = HeaderWidget()

        # Layouts
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_line_edit)
        folder_layout.addWidget(self.browse_button)

        extension_layout = QHBoxLayout()
        extension_layout.addWidget(self.extension_label)
        extension_layout.addWidget(self.extension_line_edit)

        # File list layout with header
        file_list_layout = QVBoxLayout()
        file_list_layout.addWidget(self.header_widget)
        file_list_layout.addWidget(self.file_list_widget)

        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_label)
        prefix_layout.addWidget(self.prefix_line_edit)
        prefix_layout.addWidget(self.skip_existing_prefix_checkbox)

        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(self.suffix_label)
        suffix_layout.addWidget(self.suffix_line_edit)
        suffix_layout.addWidget(self.skip_existing_suffix_checkbox)

        replace_layout = QHBoxLayout()
        replace_layout.addWidget(self.replace_label)
        replace_layout.addWidget(self.replace_line_edit)
        replace_layout.addWidget(self.with_label)
        replace_layout.addWidget(self.with_line_edit)
        replace_layout.addWidget(self.regex_checkbox)

        case_layout = QHBoxLayout()
        case_layout.addWidget(self.case_label)
        case_layout.addWidget(self.case_combo_box)

        numbering_layout = QHBoxLayout()
        numbering_layout.addWidget(self.numbering_checkbox)
        numbering_layout.addWidget(self.numbering_start_label)
        numbering_layout.addWidget(self.numbering_start_spinbox)
        numbering_layout.addWidget(self.numbering_increment_label)
        numbering_layout.addWidget(self.numbering_increment_spinbox)
        numbering_layout.addWidget(self.numbering_padding_label)
        numbering_layout.addWidget(self.numbering_padding_spinbox)
        numbering_layout.addWidget(self.numbering_position_label)
        numbering_layout.addWidget(self.numbering_position_combo_box)

        conflict_layout = QHBoxLayout()
        conflict_layout.addWidget(self.conflict_label)
        conflict_layout.addWidget(self.conflict_combo_box)

        options_layout = QHBoxLayout()
        options_layout.addWidget(self.simulation_checkbox)
        options_layout.addWidget(self.fix_checkbox)

        actions_layout = QHBoxLayout()
        actions_layout.addWidget(self.rename_button)
        actions_layout.addWidget(self.undo_button)
        actions_layout.addWidget(self.reset_button)
        actions_layout.addWidget(self.save_preset_button)
        actions_layout.addWidget(self.load_preset_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(folder_layout)
        main_layout.addLayout(extension_layout)
        main_layout.addLayout(file_list_layout)
        main_layout.addLayout(prefix_layout)
        main_layout.addLayout(suffix_layout)
        main_layout.addLayout(replace_layout)
        main_layout.addLayout(case_layout)
        main_layout.addLayout(numbering_layout)
        main_layout.addLayout(conflict_layout)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(actions_layout)

        self.setLayout(main_layout)

        # Signals and Slots
        self.browse_button.clicked.connect(self.browse_folder)
        self.rename_button.clicked.connect(self.rename_files)
        self.undo_button.clicked.connect(self.undo_rename)
        self.reset_button.clicked.connect(self.reset_fields)
        self.save_preset_button.clicked.connect(self.save_preset)
        self.load_preset_button.clicked.connect(self.load_preset)
        self.numbering_checkbox.stateChanged.connect(self.toggle_numbering_options)
        self.file_list_widget.itemSelectionChanged.connect(self.preview_changes)

        # Connect renaming option changes to preview update
        self.prefix_line_edit.textChanged.connect(self.preview_changes)
        self.suffix_line_edit.textChanged.connect(self.preview_changes)
        self.skip_existing_prefix_checkbox.stateChanged.connect(self.preview_changes)
        self.skip_existing_suffix_checkbox.stateChanged.connect(self.preview_changes)
        self.replace_line_edit.textChanged.connect(self.preview_changes)
        self.with_line_edit.textChanged.connect(self.preview_changes)
        self.regex_checkbox.stateChanged.connect(self.preview_changes)
        self.case_combo_box.currentIndexChanged.connect(self.preview_changes)
        self.numbering_checkbox.stateChanged.connect(self.preview_changes)
        self.numbering_start_spinbox.valueChanged.connect(self.preview_changes)
        self.numbering_increment_spinbox.valueChanged.connect(self.preview_changes)
        self.numbering_padding_spinbox.valueChanged.connect(self.preview_changes)
        self.numbering_position_combo_box.currentIndexChanged.connect(self.preview_changes)
        self.fix_checkbox.stateChanged.connect(self.preview_changes)
        self.extension_line_edit.textChanged.connect(self.load_files_from_extension)

        # Initialize numbering options state
        self.toggle_numbering_options()

    def toggle_numbering_options(self):
        enabled = self.numbering_checkbox.isChecked()
        self.numbering_start_label.setEnabled(enabled)
        self.numbering_start_spinbox.setEnabled(enabled)
        self.numbering_increment_label.setEnabled(enabled)
        self.numbering_increment_spinbox.setEnabled(enabled)
        self.numbering_padding_label.setEnabled(enabled)
        self.numbering_padding_spinbox.setEnabled(enabled)
        self.numbering_position_label.setEnabled(enabled)
        self.numbering_position_combo_box.setEnabled(enabled)
        self.preview_changes()  # Update preview when numbering options are toggled

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.folder_line_edit.setText(folder)
            self.load_files(folder)

    def load_files(self, folder):
        self.file_list_widget.clear()
        filter_ext = self.extension_line_edit.text()
        include_subfolders = False  # You can add a checkbox for recursive option
        if include_subfolders:
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    if not filter_ext or filename.endswith(filter_ext):
                        self.add_list_item(filename)
        else:
            files = os.listdir(folder)
            for file in files:
                if not filter_ext or file.endswith(filter_ext):
                    self.add_list_item(file)
        self.preview_changes()  # Update preview after loading files

    def load_files_from_extension(self):
        folder = self.folder_line_edit.text()
        if folder:
            self.load_files(folder)

    def add_list_item(self, text):
        item_widget = ListItemWidget(text)
        item = QListWidgetItem()
        item.setSizeHint(item_widget.sizeHint())
        self.file_list_widget.addItem(item)
        self.file_list_widget.setItemWidget(item, item_widget)

    def get_item_widget(self, index):
        item = self.file_list_widget.item(index)
        item_widget = self.file_list_widget.itemWidget(item)
        return item_widget

    def preview_changes(self):
        if not self.folder_line_edit.text():
            return

        # Get selected items
        selected_items = self.file_list_widget.selectedItems()
        apply_to_all = len(selected_items) == 0

        prefix = self.prefix_line_edit.text()
        suffix = self.suffix_line_edit.text()
        skip_existing_prefix = self.skip_existing_prefix_checkbox.isChecked()
        skip_existing_suffix = self.skip_existing_suffix_checkbox.isChecked()
        replace_text = self.replace_line_edit.text()
        with_text = self.with_line_edit.text()
        use_regex = self.regex_checkbox.isChecked()
        case_option = self.case_combo_box.currentText()
        add_numbering = self.numbering_checkbox.isChecked()
        numbering_start = self.numbering_start_spinbox.value()
        numbering_increment = self.numbering_increment_spinbox.value()
        numbering_padding = self.numbering_padding_spinbox.value()
        numbering_position = self.numbering_position_combo_box.currentText()

        numbering_counter = numbering_start

        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            item_widget = self.get_item_widget(i)

            if not apply_to_all and not item.isSelected():
                item_widget.setPreviewText('')  # Clear preview if not selected
                continue

            original_name = os.path.basename(item_widget.getOriginalName())
            new_name = self.get_new_name(
                original_name, prefix, suffix, skip_existing_prefix, skip_existing_suffix,
                replace_text, with_text, use_regex, case_option, add_numbering,
                numbering_counter, numbering_increment, numbering_padding,
                numbering_position
            )

            if new_name != original_name:
                item_widget.setPreviewText(new_name)
            else:
                item_widget.setPreviewText('')  # Clear preview if no change

            if add_numbering:
                numbering_counter += numbering_increment

    def get_new_name(self, original_name, prefix, suffix, skip_existing_prefix, skip_existing_suffix,
                     replace_text, with_text, use_regex, case_option, add_numbering,
                     numbering_current, numbering_increment, numbering_padding,
                     numbering_position):
        name, ext = os.path.splitext(original_name)
        new_name = name

        # Apply fix first
        if self.fix_checkbox.isChecked():
            new_name = self.apply_fix(new_name)

        # Apply replace
        if replace_text:
            if use_regex:
                try:
                    new_name = re.sub(replace_text, with_text, new_name)
                except re.error as e:
                    QMessageBox.critical(self, 'Regex Error', f'Invalid regular expression:\n{e}')
                    return original_name
            else:
                new_name = new_name.replace(replace_text, with_text)

        # Apply case conversion
        if case_option == 'lowercase':
            new_name = new_name.lower()
        elif case_option == 'UPPERCASE':
            new_name = new_name.upper()
        elif case_option == 'Title Case':
            new_name = new_name.title()
        elif case_option == 'Sentence case':
            new_name = new_name.capitalize()

        # Apply prefix
        if prefix:
            if skip_existing_prefix and new_name.startswith(prefix):
                pass  # Skip adding prefix
            else:
                new_name = prefix + new_name

        # Apply suffix
        if suffix:
            if skip_existing_suffix and new_name.endswith(suffix):
                pass  # Skip adding suffix
            else:
                new_name = new_name + suffix

        # Add numbering
        if add_numbering:
            number_str = str(numbering_current).zfill(numbering_padding)
            if numbering_position == 'Prefix':
                new_name = number_str + new_name
            else:
                new_name = new_name + number_str

        # Remove space before extension
        new_name = new_name.rstrip()

        return new_name + ext

    def apply_fix(self, name):
        # Remove leading and trailing spaces
        new_name = name.strip()

        # Replace ' - ' with placeholder to preserve it
        placeholder = 'PLACEHOLDERDASH'
        new_name = new_name.replace(' - ', placeholder)

        # Replace hyphens not surrounded by spaces with spaces
        new_name = re.sub(r'(?<!\s)-(?!\s)', ' ', new_name)

        # Replace multiple spaces with a single space
        new_name = re.sub(r'\s{2,}', ' ', new_name)

        # Restore ' - ' from placeholders
        new_name = new_name.replace(placeholder, ' - ')

        # Remove non-alphanumeric characters except spaces and hyphens
        new_name = re.sub(r'[^A-Za-z0-9\s\-]', '', new_name)

        # Insert spaces before capital letters that are after lowercase letters
        new_name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', new_name)

        # Replace multiple spaces again
        new_name = re.sub(r'\s{2,}', ' ', new_name)

        # Trim leading and trailing spaces
        new_name = new_name.strip()

        # Convert to Title Case
        new_name = new_name.title()

        return new_name

    def rename_files(self):
        folder = self.folder_line_edit.text()
        if not folder:
            QMessageBox.warning(self, 'Warning', 'Please select a folder.')
            return

        # Get selected items
        selected_items = self.file_list_widget.selectedItems()
        apply_to_all = len(selected_items) == 0

        simulation_mode = self.simulation_checkbox.isChecked()
        conflict_strategy = self.conflict_combo_box.currentText()

        self.rename_history = []
        self.rename_history_stack.append([])

        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            item_widget = self.get_item_widget(i)

            if not apply_to_all and not item.isSelected():
                continue  # Skip items not selected

            old_name = item_widget.getOriginalName()
            new_name = item_widget.getPreviewName()

            if not new_name or old_name == new_name:
                continue  # Skip if no changes

            old_path = os.path.join(folder, old_name)
            new_path = os.path.join(folder, new_name)

            if os.path.exists(new_path) and old_path != new_path:
                if conflict_strategy == 'Skip':
                    continue
                elif conflict_strategy == 'Overwrite':
                    pass  # Proceed to rename
                elif conflict_strategy == 'Rename':
                    base, ext = os.path.splitext(new_name)
                    counter = 1
                    while os.path.exists(new_path):
                        new_name = f"{base}_{counter}{ext}"
                        new_path = os.path.join(folder, new_name)
                        counter += 1

            try:
                if not simulation_mode and old_path != new_path:
                    os.rename(old_path, new_path)
                self.rename_history.append((old_path, new_path))
                self.rename_history_stack[-1].append((old_path, new_path))
                # Update the original name label to the new name
                item_widget.updateOriginalName(new_name)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to rename {old_name}:\n{e}')
                return

        if self.rename_history:
            self.undo_button.setEnabled(True)
            if simulation_mode:
                QMessageBox.information(self, 'Simulation Complete', 'Simulation mode is ON. No files were renamed.')
            else:
                QMessageBox.information(self, 'Success', 'Files renamed successfully!')
            self.preview_changes()  # Update preview after renaming
        else:
            QMessageBox.information(self, 'No Changes', 'No files were renamed.')

    def undo_rename(self):
        if self.rename_history_stack:
            rename_history = self.rename_history_stack.pop()
            for old_path, new_path in reversed(rename_history):
                try:
                    os.rename(new_path, old_path)
                except Exception as e:
                    QMessageBox.critical(self, 'Error', f'Failed to undo rename {new_path}:\n{e}')
                    return
            self.load_files(self.folder_line_edit.text())
            if not self.rename_history_stack:
                self.undo_button.setEnabled(False)
            QMessageBox.information(self, 'Success', 'Undo completed!')

    def reset_fields(self):
        # Clear input fields
        self.folder_line_edit.clear()
        self.extension_line_edit.clear()
        self.prefix_line_edit.clear()
        self.suffix_line_edit.clear()
        self.replace_line_edit.clear()
        self.with_line_edit.clear()

        # Uncheck checkboxes
        self.regex_checkbox.setChecked(False)
        self.numbering_checkbox.setChecked(False)
        self.simulation_checkbox.setChecked(False)
        self.skip_existing_prefix_checkbox.setChecked(False)
        self.skip_existing_suffix_checkbox.setChecked(False)
        self.fix_checkbox.setChecked(False)

        # Reset combo boxes
        self.case_combo_box.setCurrentIndex(0)
        self.numbering_position_combo_box.setCurrentIndex(0)
        self.conflict_combo_box.setCurrentIndex(0)

        # Reset spin boxes
        self.numbering_start_spinbox.setValue(1)
        self.numbering_increment_spinbox.setValue(1)
        self.numbering_padding_spinbox.setValue(1)

        # Clear file list and disable undo button
        self.file_list_widget.clear()
        self.undo_button.setEnabled(False)
        self.rename_history = []
        self.rename_history_stack.clear()

        # Reset numbering options state
        self.toggle_numbering_options()

    def save_preset(self):
        preset = {
            'prefix': self.prefix_line_edit.text(),
            'suffix': self.suffix_line_edit.text(),
            'skip_existing_prefix': self.skip_existing_prefix_checkbox.isChecked(),
            'skip_existing_suffix': self.skip_existing_suffix_checkbox.isChecked(),
            'replace_text': self.replace_line_edit.text(),
            'with_text': self.with_line_edit.text(),
            'use_regex': self.regex_checkbox.isChecked(),
            'case_option': self.case_combo_box.currentText(),
            'add_numbering': self.numbering_checkbox.isChecked(),
            'numbering_start': self.numbering_start_spinbox.value(),
            'numbering_increment': self.numbering_increment_spinbox.value(),
            'numbering_padding': self.numbering_padding_spinbox.value(),
            'numbering_position': self.numbering_position_combo_box.currentText(),
            'conflict_strategy': self.conflict_combo_box.currentText(),
            'simulation_mode': self.simulation_checkbox.isChecked(),
            'filter_extension': self.extension_line_edit.text(),
            'apply_fix': self.fix_checkbox.isChecked(),
        }
        preset_file, _ = QFileDialog.getSaveFileName(self, 'Save Preset', '', 'JSON Files (*.json)')
        if preset_file:
            try:
                with open(preset_file, 'w') as f:
                    json.dump(preset, f)
                QMessageBox.information(self, 'Success', 'Preset saved successfully!')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save preset:\n{e}')

    def load_preset(self):
        preset_file, _ = QFileDialog.getOpenFileName(self, 'Load Preset', '', 'JSON Files (*.json)')
        if preset_file:
            try:
                with open(preset_file, 'r') as f:
                    preset = json.load(f)
                self.prefix_line_edit.setText(preset.get('prefix', ''))
                self.suffix_line_edit.setText(preset.get('suffix', ''))
                self.skip_existing_prefix_checkbox.setChecked(preset.get('skip_existing_prefix', False))
                self.skip_existing_suffix_checkbox.setChecked(preset.get('skip_existing_suffix', False))
                self.replace_line_edit.setText(preset.get('replace_text', ''))
                self.with_line_edit.setText(preset.get('with_text', ''))
                self.regex_checkbox.setChecked(preset.get('use_regex', False))
                self.case_combo_box.setCurrentText(preset.get('case_option', 'None'))
                self.numbering_checkbox.setChecked(preset.get('add_numbering', False))
                self.numbering_start_spinbox.setValue(preset.get('numbering_start', 1))
                self.numbering_increment_spinbox.setValue(preset.get('numbering_increment', 1))
                self.numbering_padding_spinbox.setValue(preset.get('numbering_padding', 1))
                self.numbering_position_combo_box.setCurrentText(preset.get('numbering_position', 'Prefix'))
                self.conflict_combo_box.setCurrentText(preset.get('conflict_strategy', 'Skip'))
                self.simulation_checkbox.setChecked(preset.get('simulation_mode', False))
                self.extension_line_edit.setText(preset.get('filter_extension', ''))
                self.fix_checkbox.setChecked(preset.get('apply_fix', False))
                self.toggle_numbering_options()
                self.preview_changes()
                QMessageBox.information(self, 'Success', 'Preset loaded successfully!')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to load preset:\n{e}')


def main():
    app = QApplication(sys.argv)
    window = REnamer()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
