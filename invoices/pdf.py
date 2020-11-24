import os
import platform

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
        'footer-left': '[page]/[topage]',
    }
    if platform.system() == 'Windows':
        configuration = pdfkit.configuration(
            wkhtmltopdf=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'wkhtmltox', 'bin', 'wkhtmltopdf.exe'))
    elif platform.system() == 'Linux':
        configuration = pdfkit.configuration(
            wkhtmltopdf=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'wkhtmltopdf.sh'))
    else:
        configuration = pdfkit.configuration()

    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, filename), 'wb') as pdf_file:
        pdf_file.write(pdfkit.PDFKit(html, "string",
                                     options=pdfkit_settings,
                                     configuration=configuration).to_pdf())


def generate_html(values):
    path = os.path.join(os.path.dirname(__file__), 'templates')
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader(path)).get_template(
        'invoice.html')
    values['dateformat'] = "%d/%m/%Y" if platform.system() == 'Windows' else "%02d/%02m/%Y"
    return template.render(values)


if __name__ == '__main__':
    import datetime
    values = {
        'name': 'Name Surname',
        'date': datetime.date(2020, 10, 1),
        'invoices': [
            {
                'date': datetime.date(2020, 9, 2),
                'name': 'Name Surname',
                'task': ('Тест'),
                'comment': ('1. пункт 1.<br/>'
                            '2. пункт 2.<br/>'
                            '3. пункт 3<br/>'
                            '4. пункт 4.'),
                'time': 0.852,
                'cost': 8.52,
            },
        ] * 12
    }
    generate_pdf(generate_html(values), 'pdf_out', 'output.pdf')
