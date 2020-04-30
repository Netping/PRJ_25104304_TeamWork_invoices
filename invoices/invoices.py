import datetime
import logging
import configparser
import traceback
import requests

if __name__ == '__main__':
    try:
        # логгирование
        errors = logging.getLogger("errors")
        log = logging.getLogger("main")

        errors.setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)

        FH = logging.FileHandler("log.txt", encoding='utf8')
        ERRORS_FH = logging.FileHandler("errors.txt", encoding='utf8')
        log.addHandler(FH)
        errors.addHandler(ERRORS_FH)

        FORMATTER = logging.Formatter('%(name)s [%(asctime)s] - %(message)s')
        FH.setFormatter(FORMATTER)
        ERRORS_FH.setFormatter(FORMATTER)

        # константа
        HEADERS = {'Content-type': 'application/json'}

        # конфиг
        CONFIG = configparser.ConfigParser()
        CONFIG.read('config.ini')
        CONFIG = CONFIG['config']

        DOMAIN = CONFIG['domain']
        APIKEY = CONFIG['apikey']
        PROJECT_IDS = CONFIG['project_ids'].split(',')      # список проектов из которых получаются time entries
        START_DATE = CONFIG['start_date']
        END_DATE = CONFIG['end_date']

        START_DATE = datetime.datetime.strptime(START_DATE, '%Y-%m-%d')
        END_DATE = datetime.datetime.strptime(END_DATE, '%Y-%m-%d')

        for PROJECT in PROJECT_IDS:
            PROJECT = PROJECT.strip()

            log.info('Получаем time entries для проекта %s' % PROJECT)
            log.debug(f'{DOMAIN}/projects/{PROJECT}/time_entries.json -->')

            time = requests.get(DOMAIN + '/projects/' + PROJECT + '/time_entries.json',
                                {'billableType': 'billable', 'invoicedType': 'noninvoiced'},
                                headers=HEADERS,
                                auth=(APIKEY, '')).json()
            
            log.debug(f'<-- {time}')

            items = {}

            log.info('Сортируем time entries по сотрудникам')

            for entrie in time['time-entries']:
                entrie_time = entrie['dateUserPerspective']
                entrie_time = entrie_time.split('T')[0]
                entrie_time = datetime.datetime.strptime(entrie_time, '%Y-%m-%d')
                if (entrie['invoiceNo'] == '' and
                        entrie['invoiceStatus'] == '' and
                        entrie['isbillable'] == '1' and
                        START_DATE <= entrie_time and entrie_time <= END_DATE):

                    id = entrie['person-id'] + ';;' + entrie['person-first-name'] + ' ' + entrie['person-last-name']
                    if id in items:
                        items[id] += entrie['id'] + ','
                    else:
                        items[id] = ''
                        items[id] += entrie['id'] + ','

            log.debug(items)
            print(items)
            log.info('Начинаем формировать счета')

            for person in items:
                name = person.split(';;')[1]
                date = datetime.datetime.utcnow()
                date = datetime.datetime.strftime(date, '%Y%m%d')
                data = {"invoice":
                            {"number": name,
                             "currency-code": "USD",
                             "display-date": date,
                             "fixed-cost":"",
                             "description":"",
                             "po-number":""}
                        }
                log.debug(DOMAIN + '/projects/' + PROJECT + '/invoices.json')
                log.debug(f'{data} -->')
                invoice = requests.post(DOMAIN + '/projects/' + PROJECT + '/invoices.json',
                                        json=data,
                                        headers=HEADERS,
                                        auth=(APIKEY, '')).json()
                print(invoice)
                log.debug(f'<-- {invoice}')
                if invoice['STATUS'] == 'OK':
                    data = {"lineitems": {"add": {"timelogs": items[person].strip(',')}}}
                    req = requests.put(DOMAIN + '/invoices/' + invoice['id'] + '/lineitems.json',
                                       json=data,
                                       headers=HEADERS,
                                       auth=(APIKEY, '')).json()
                    print(req)
                else:
                    errors.error('Результат создания счёта отличен от OK')
    except Exception as e:
        print('При выполнении кода произошла ошибка - %s' % str(e))
        traceback.print_exc()
        errors.exception('При выполнении кода произошла ошибка - %s' % str(e))