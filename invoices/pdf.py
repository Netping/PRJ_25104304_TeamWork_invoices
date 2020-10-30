import os

import jinja2
import pdfkit


def generate_pdf(html, directory, filename):
    pdfkit_settings = {
        'dpi': '96',
        'image-dpi': '3500',
        'image-quality': '94',
        'page-size': 'A4',
        'encoding': "UTF-8",
        'margin-top': '1cm',
        'margin-bottom': '1cm',
        'margin-right': '1cm',
        'margin-left': '1cm',
        'quiet': '',
        'disable-smart-shrinking': '',
        'footer-left': '[page] of [topage]'
    }
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'wb') as pdf_file:
        configuration = pdfkit.configuration(
            wkhtmltopdf=os.path.join(
                os.path.dirname(__file__),
                'wkhtmltopdf.sh'))
        pdf_file.write(pdfkit.PDFKit(html, "string",
                                     options=pdfkit_settings,
                                     configuration=configuration).to_pdf())


def generate_html(values):
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./templates')).get_template(
        'invoice.html')
    return template.render(values)


if __name__ == '__main__':
    import datetime
    values = {
        'name': 'Alexey Nikolin',
        'date': datetime.date(2020, 10, 1),
        'invoices': [
            {
                'date': datetime.date(2020, 9, 2),
                'name': 'Alexey Nikolin',
                'task': ('#DKST 708 SOFTWARE development (softeware version '
                     '1.X is ready) - #DKST 708 SOFTWARE Сконфигурировать '
                     'сборку образа прошивки для DKST 708 на виртуальной '
                     'машине тестового стенда '),
                'comment': ('1. Настроил ssh на вм. <br/>'
                            '2. склонировал репозиторий <br/>'
                            '3. Запустил сборку и получил ошибки<br/>'
                            ' 4. чуть поразбирался, оставил.'),
                'time': 0.717,
                'cost': 7.17,
            },
        ] * 12
    }

    html = generate_html(values)
    with open('output.html', 'w') as html_file:
        html_file.write(html)
    generate_pdf(generate_html(values), 'pdf', 'output.pdf')
