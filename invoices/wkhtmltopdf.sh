#!/bin/bash
# Необходим для запуска wkhtmltopdf в остсуствии запузенного графического сервера
/usr/bin/xvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf $*