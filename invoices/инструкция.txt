Установка:
Установить Python 3.8+
Установить зависимости через pip
Установить wkhtmltopdf https://wkhtmltopdf.org (проверено на версии 0.12.4 и 0.12.6)

Важно! wkhtmltopdf должен быть с патчами qt!
При запуске вывод примерно такой(должно быть "with patched qt"):

$ wkhtmltopdf 
You need to specify at least one input file, and exactly one output file
Use - for stdin or stdout

Name:
  wkhtmltopdf 0.12.6 (with patched qt)


Для Linux можно скачать скомпилированный https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
В таком случае нужно будет доустановить вручную: openssl build-essential libssl-dev libxrender-dev git-core libx11-dev libxext-dev libfontconfig1-dev libfreetype6-dev fontconfi
Для версий 0.12.5 и 0.12.6 готовых сборок нет.

Для запуска под Linux(рассматривается вариант сервера, без запущенного X-сервера) требуется xvfb.
в файле wkhtmltopdf.sh проверить путь к исполняемому файлу wkhtmltopdf, по умолчанию /usr/bin/wkhtmltopdf
Для Windows wkhtmltopdf.exe находится в каталоге wkhtmltox/bin, wkhtmltopdf.sh не используется.
Для MacOS используется системная установка без указания путей, wkhtmltopdf.sh не используется.

Запуск:
как обычный python скрипт

Пример запуска:
python ./main.py --domain https://netping.teamwork.com --apikey twp_****************** --project_ids all_projects --exclude_project_ids 442963 --start_date YYYYMMDD --end_date YYYYMMDD --logdir %path_to_logdir% --pdfdir %path_to_pdfdir% --check-lost
