# FIXME: add header

import sys
import traceback
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from qgis.core import Qgis, QgsMessageLog
from qgis.gui import QgsMessageBarItem
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import (
    QToolButton, QApplication, QVBoxLayout, QDialog, QTextBrowser)


def tr(message):
    """
    Leverage QApplication.translate to translate a message

    :param message: the message to be translated
    :returns: the return value of `QApplication.translate('HyBridge', message)`
    """
    return QApplication.translate('HyBridge', message)


def _on_tb_btn_clicked(message, tb_text):
    vbox = QVBoxLayout()
    dlg = QDialog()
    dlg.setWindowTitle('Traceback')
    text_browser = QTextBrowser()
    unformatted_msg = message
    formatted_msg = highlight(tb_text, PythonLexer(), HtmlFormatter(full=True))
    text_browser.setHtml(unformatted_msg + formatted_msg)
    vbox.addWidget(text_browser)
    dlg.setLayout(vbox)
    dlg.setMinimumSize(700, 500)
    dlg.exec_()


def log_msg(message, tag='GEM OpenQuake IRMT plugin', level='I',
            message_bar=None, duration=None, exception=None,
            print_to_stderr=False):
    """
    Add a message to the QGIS message log. If a messageBar is provided,
    the same message will be displayed also in the messageBar. In the latter
    case, warnings and critical messages will have no timeout, whereas
    info messages will have a duration of 5 seconds.

    :param message: the message
    :param tag: the log topic
    :param level:
        the importance level
        'I' -> Qgis.Info,
        'W' -> Qgis.Warning,
        'C' -> Qgis.Critical,
        'S' -> Qgis.Success,
    :param message_bar: a `QgsMessageBar` instance
    :param duration: how long (in seconds) the message will be displayed (use 0
        to keep the message visible indefinitely, or None to use
        the default duration of the chosen level
    :param exception: an optional exception, from which the traceback will be
        extracted and written in the log. When the exception is provided,
        an additional button in the `QgsMessageBar` allows to visualize the
        traceback in a separate window.
    :print_to_stderr: if True, the error message will be printed also to stderr
    """
    levels = {
              'I': Qgis.Info,
              'W': Qgis.Warning,
              'C': Qgis.Critical,
              'S': Qgis.Success,
              }
    if level not in levels:
        raise ValueError('Level must be one of %s' % levels.keys())
    tb_text = ''
    if exception is not None:
        tb_lines = traceback.format_exception(
            exception.__class__, exception, exception.__traceback__)
        tb_text = '\n' + ''.join(tb_lines)

    # if we are running nosetests, exit on critical errors
    if 'nose' in sys.modules and level == 'C':
        raise RuntimeError(message + tb_text)
    else:
        log_verbosity = QSettings().value('irmt/log_level', 'W')
        if (level == 'C'
                or level == 'W' and log_verbosity in ('S', 'I', 'W')
                or level in ('I', 'S') and log_verbosity in ('I', 'S')):
            QgsMessageLog.logMessage(
                tr(message) + tb_text, tr(tag), levels[level])
            if exception is not None:
                tb_btn = QToolButton(message_bar)
                tb_btn.setText('Show Traceback')
                tb_btn.clicked.connect(
                    lambda: _on_tb_btn_clicked(tr(message), tb_text))
        if message_bar is not None:
            if level == 'S':
                title = 'Success'
                duration = duration if duration is not None else 8
            elif level == 'I':
                title = 'Info'
                duration = duration if duration is not None else 8
            elif level == 'W':
                title = 'Warning'
                duration = duration if duration is not None else 0
            elif level == 'C':
                title = 'Error'
                duration = duration if duration is not None else 0
            max_msg_len = 200
            if len(message) > max_msg_len:
                display_text = ("%s[...]" % message[:max_msg_len])
                show_more = "[...]%s" % message[max_msg_len:]
            else:
                display_text = message
                show_more = None
            if exception is None:
                if show_more is not None:
                    message_bar.pushMessage(tr(title),
                                            tr(display_text),
                                            tr(show_more),
                                            levels[level],
                                            duration)
                else:
                    message_bar.pushMessage(tr(title),
                                            tr(display_text),
                                            levels[level],
                                            duration)
            else:
                mb_item = QgsMessageBarItem(
                    tr(title), tr(display_text), tb_btn, levels[level],
                    duration)
                message_bar.pushItem(mb_item)
        if print_to_stderr:
            print('\t\t%s' % message + tb_text, file=sys.stderr)
