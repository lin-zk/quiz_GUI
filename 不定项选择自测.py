# -*- coding: utf-8 -*-
# @Author: Lin_ZK
# @Email: 1751740699@qq.com
# @Date: 2025-07-04
# @Description: 工程伦理答题系统，使用 PyQt5 实现的 GUI
# @Version: 1.0
# @License: MIT License
# @Thanks: 感谢Copilot给予代码编辑支持
import sys
import os
import json
import random
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QCheckBox, QMessageBox, QGroupBox, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QBrush, QColor, QPalette


def load_questions():
    """
    从外部 JSON 文件加载题库数据
    
    Returns:
        list: 题库列表，如果加载失败则返回空列表
    """
    try:
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        questions_file = os.path.join(script_dir, '题库.json')
        
        # 检查文件是否存在
        if not os.path.exists(questions_file):
            raise FileNotFoundError(f'题库文件不存在：{questions_file}')
        
        # 读取 JSON 文件
        with open(questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 验证数据格式
        if 'questions' not in data:
            raise ValueError('题库文件格式错误：缺少 questions 字段')
        
        questions = data['questions']
        
        # 验证题目数据完整性
        for i, q in enumerate(questions):
            required_fields = ['id', 'question', 'options', 'answer']
            for field in required_fields:
                if field not in q:
                    raise ValueError(f'第{i+1}题缺少必要字段：{field}')
        
        print(f"成功加载 {len(questions)} 道题目")
        return questions
        
    except json.JSONDecodeError as e:
        raise ValueError(f'题库文件格式错误：{str(e)}')
    except Exception as e:
        raise RuntimeError(f'加载题库失败：{str(e)}')


class QuizWindow(QWidget):
    def __init__(self, questions):
        super().__init__()
        self.setWindowTitle('不定项选择自测')
        self.resize(1500, 1000)
        self.setStyleSheet('QWidget { background: #f6f8fa; }')
        self.quiz = questions.copy()  # 使用传入的题库数据
        self.reset_quiz()
        self.showMaximized()  # 默认最大化窗口

    def reset_quiz(self):
        random.shuffle(self.quiz)
        self.user_answers = [set() for _ in self.quiz]
        self.current_index = 0
        self.start_time = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_seconds = 0
        self.option_shuffle_map = []
        for q in self.quiz:
            indices = list(range(len(q['options'])))
            random.shuffle(indices)
            self.option_shuffle_map.append(indices)
        # 递归清理所有子控件和子布局
        def clear_layout(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    sublayout = item.layout()
                    if sublayout is not None:
                        clear_layout(sublayout)
                        sublayout.deleteLater()
        if self.layout() is not None:
            clear_layout(self.layout())
        # 重新创建主布局
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        self.init_ui()
        self.timer.start(1000)

    def init_ui(self):
        layout = self.layout()  # 不再新建QHBoxLayout(self)，直接用已有主布局
        # 左侧导航栏
        self.nav_list = QListWidget()
        font = QFont()
        font.setPointSize(18)
        self.nav_list.setFont(font)
        # 现代化滚动条样式
        self.nav_list.setStyleSheet('''
            QListWidget { border-radius: 12px; background: #fff; }
            QListWidget::item { height: 48px; }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 14px;
                margin: 4px 0 4px 0;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #1976d2;
                min-height: 36px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        ''')
        for i in range(len(self.quiz)):
            self.nav_list.addItem(f'第{i+1}题')
        self.nav_list.setFixedWidth(160)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.switch_question)
        layout.addWidget(self.nav_list, 1)
        # 右侧
        right = QVBoxLayout()
        # 顶部计时和提交
        top_bar = QHBoxLayout()
        self.timer_label = QLabel('用时: 00:00:00')
        self.timer_label.setFont(QFont('Arial', 18, QFont.Bold))
        top_bar.addWidget(self.timer_label)
        self.submit_btn_top = QPushButton('提交')
        self.submit_btn_top.setFont(QFont('Arial', 18, QFont.Bold))
        self.submit_btn_top.setStyleSheet('QPushButton { background: #1976d2; color: #fff; border-radius: 10px; padding: 8px 24px; } QPushButton:hover { background: #1565c0; }')
        self.submit_btn_top.clicked.connect(self.try_submit)
        top_bar.addWidget(self.submit_btn_top)
        top_bar.addStretch()
        right.addLayout(top_bar)
        # 间隔
        right.addSpacing(20)
        # 题目
        self.question_label = QLabel()
        self.question_label.setFont(QFont('Arial', 22, QFont.Bold))
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet('QLabel { color: #222; }')
        right.addWidget(self.question_label)
        # 选项
        self.options_group = QGroupBox('选项')
        self.options_group.setFont(QFont('Arial', 18, QFont.Bold))
        self.options_group.setStyleSheet('QGroupBox { border: 2px solid #1976d2; border-radius: 12px; margin-top: 12px; padding: 12px; }')
        self.options_layout = QVBoxLayout()
        self.options_group.setLayout(self.options_layout)
        right.addWidget(self.options_group)
        # 下一页/提交按钮
        self.next_btn = QPushButton('下一页')
        self.next_btn.setFont(QFont('Arial', 18, QFont.Bold))
        self.next_btn.setStyleSheet('QPushButton { background: #43a047; color: #fff; border-radius: 10px; padding: 10px 36px; } QPushButton:hover { background: #388e3c; }')
        self.next_btn.setFixedHeight(48)
        self.next_btn.clicked.connect(self.next_or_submit)
        right.addWidget(self.next_btn)
        right.addStretch()
        layout.addLayout(right, 4)
        self.setLayout(layout)
        self.show_question(0)
        self.update_nav_status()

    def update_timer(self):
        self.elapsed_seconds = int(time.time() - self.start_time)
        h = self.elapsed_seconds // 3600
        m = (self.elapsed_seconds % 3600) // 60
        s = self.elapsed_seconds % 60
        self.timer_label.setText(f'用时: {h:02d}:{m:02d}:{s:02d}')

    def show_question(self, idx):
        self.current_index = idx
        q = self.quiz[idx]
        self.question_label.setText(q["question"])
        # 清空旧选项
        for i in reversed(range(self.options_layout.count())):
            widget = self.options_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.checkboxes = []
        # 选项乱序映射
        indices = self.option_shuffle_map[idx]
        abcd = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        # 恢复已保存答案
        saved = self.user_answers[idx]
        for i, ab in enumerate(abcd[:len(q['options'])]):
            opt_idx = indices[i]
            content = q['options'][opt_idx][2:]  # 去掉前缀A.等
            # 创建一个横向布局，左侧是QCheckBox，右侧是自动换行的QLabel
            option_widget = QWidget()
            option_layout = QHBoxLayout(option_widget)
            option_layout.setContentsMargins(0, 0, 0, 0)
            cb = QCheckBox(f'{ab}.')
            cb.setFont(QFont('Arial', 18))
            cb.setStyleSheet('''
                QCheckBox { margin: 12px 0; spacing: 14px; }
                QCheckBox::indicator {
                    width: 28px; height: 28px;
                    border-radius: 8px;
                    border: 2px solid #1976d2;
                    background: #fff;
                }
                QCheckBox::indicator:checked {
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, stop:0 #1976d2, stop:1 #fff);
                    border: 2px solid #1976d2;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #1565c0;
                }
            ''')
            if ab in saved:
                cb.setChecked(True)
            cb.stateChanged.connect(self.save_answer)
            self.checkboxes.append(cb)
            label = QLabel(content)
            label.setFont(QFont('Arial', 18))
            label.setWordWrap(True)
            # 让label响应鼠标点击，点击时切换cb
            label.mousePressEvent = lambda e, c=cb: c.toggle()
            option_layout.addWidget(cb)
            option_layout.addWidget(label, 1)
            self.options_layout.addWidget(option_widget)
        # 按钮切换
        if idx == len(self.quiz) - 1:
            self.next_btn.setText('提交')
        else:
            self.next_btn.setText('下一页')
        self.update_nav_status()

    def switch_question(self, idx):
        if idx >= 0:
            self.show_question(idx)

    def save_answer(self):
        idx = self.current_index
        selected = set()
        for cb in self.checkboxes:
            if cb.isChecked():
                selected.add(cb.text()[0])
        # 只有用户主动更改时才更新答案
        if selected:
            self.user_answers[idx] = selected
        else:
            self.user_answers[idx] = set()  # 取消所有选项，视为未作答
        self.update_nav_status()

    def update_nav_status(self):
        # 已答题高亮/打勾
        for i in range(self.nav_list.count()):
            item = self.nav_list.item(i)
            if self.user_answers[i]:
                item.setBackground(QBrush(QColor(200, 255, 200)))
            else:
                item.setBackground(QBrush(QColor(255, 255, 255)))

    def next_or_submit(self):
        if self.current_index < len(self.quiz) - 1:
            self.nav_list.setCurrentRow(self.current_index + 1)
        else:
            self.try_submit()

    def try_submit(self):
        unanswered = sum(1 for ans in self.user_answers if not ans)
        if unanswered > 0:
            reply = QMessageBox.question(self, '确认提交', f'您有{unanswered}题未答，是否提交？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self.submit()

    def submit(self):
        self.timer.stop()
        wrong = []
        for i, q in enumerate(self.quiz):
            # 还原原始选项顺序
            right = set(q['answer'])
            user = set()
            # 用户选择的ABCD->原始选项
            indices = self.option_shuffle_map[i]
            abcd = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            for ab in self.user_answers[i]:
                idx_ab = abcd.index(ab)
                if idx_ab < len(indices):
                    orig_idx = indices[idx_ab]
                    user.add(q['options'][orig_idx][0])
            if user != right:
                wrong.append((q['id'], q['question'], q['options'], ''.join(sorted(right)), ''.join(sorted(user))))
        msg = f'用时: {self.timer_label.text().replace("用时: ", "")}\n错题数/总题数: {len(wrong)}/{len(self.quiz)}\n'
        if wrong:
            msg += '\n以下为错题及正确答案：\n'
            for id_, ques, opts, right, user in sorted(wrong):
                msg += f'{id_}. {ques}\n'
                for opt in opts:
                    msg += opt + '\n'
                msg += f'你的答案: {user}  正确答案: {right}\n\n'
        else:
            msg += '全部答对，太棒了！'
        # 结果弹窗，内容过多时可滚动
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QLabel, QPushButton, QHBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle('答题结果')
        dialog.resize(700, 600)
        vbox = QVBoxLayout(dialog)
        # 滚动内容区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        label = QLabel(msg)
        label.setWordWrap(True)
        label.setFont(QFont('Arial', 18))
        content_layout.addWidget(label)
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        vbox.addWidget(scroll, 1)
        # 按钮区
        btn_layout = QHBoxLayout()
        btn_retry = QPushButton('重新作答')
        btn_exit = QPushButton('退出')
        btn_retry.setFont(QFont('Arial', 18, QFont.Bold))
        btn_exit.setFont(QFont('Arial', 18, QFont.Bold))
        btn_retry.setStyleSheet('QPushButton { background: #1976d2; color: #fff; border-radius: 10px; padding: 8px 24px; } QPushButton:hover { background: #1565c0; }')
        btn_exit.setStyleSheet('QPushButton { background: #b71c1c; color: #fff; border-radius: 10px; padding: 8px 24px; } QPushButton:hover { background: #c62828; }')
        btn_layout.addStretch()
        btn_layout.addWidget(btn_retry)
        btn_layout.addWidget(btn_exit)
        btn_layout.addStretch()
        vbox.addLayout(btn_layout)
        # 绑定事件
        btn_retry.clicked.connect(lambda: (dialog.accept(), self.quiz.__init__(questions), self.reset_quiz()))
        btn_exit.clicked.connect(lambda: (dialog.accept(), self.close()))
        dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        questions = load_questions()
        win = QuizWindow(questions)
        win.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, '错误', str(e))
        sys.exit(1)
