#!/usr/bin/env python3.8

import datetime
import getopt
import logging
import os
import sys
import time as ttime
import traceback
from pathlib import Path

import requests
import requests.exceptions
from pdf import generate_html, generate_pdf

# prints error and usage instructions in situations when wrong arguments passed in console etc during script execution

def print_usage():
    script_name = os.path.basename(__file__)
    print('Error: wrong startup arguments')
    print('Usage:', script_name, ' --domain <domain> --apikey <apikey> --project_ids <project_ids_coma_separated> --exclude_project_ids <project_ids_coma_separated> --start_date <start_date_in_YYYYMMDD_format> --end_date <end_date_in_YYYYMMDD_format> --logdir <directory_for_logs> --pdfdir <directory_for_pdfs> --check-lost')
    print('Help:', script_name, ' --help')

# prints help for running with --help flag

def print_help():
    script_name = os.path.basename(__file__)

    sample_domain = 'https://test123.teamwork.com'
    sample_apikey = 'testkey123'
    sample_project_ids = '41230,112332'
    exclude_project_ids = '112332'
    sample_start_date = '20200501'
    sample_end_date = '20200603'
    sample_log_dir = '/var/log/scriptlogs/'
    sample_pdf_dir = 'pdf/'

    help = f'''
        {script_name} --domain <domain> --apikey <apikey> --project_ids <project_ids_coma_separated> --exclude_project_ids <project_ids_coma_separated> --start_date <start_date_in_YYYYMMDD_format> --end_date <end_date_in_YYYYMMDD_format> --logdir <directory_for_logs> --pdfdir <directory_for_pdfs> --check-lost

        Form Teamwork salaries invoices on the basis of time entries and fixed expenses for specifed projects.

        All arguments (except --help) are mandatory and required to run the script.

        Examples:

            Assuming that your arguments are:

                domain = {sample_domain}
                apikey = {sample_apikey}
                project_ids = {sample_project_ids}
                exclude_project_ids = {exclude_project_ids}
                start_date = {sample_start_date}
                end_date = {sample_end_date}
                logdir = {sample_log_dir}
                pdfdir = {sample_pdf_dir}
                check lost

            Then you have to execute the script this way:

            {script_name} --domain {sample_domain} --apikey {sample_apikey} --project_ids {sample_project_ids} --exclude_project_ids {exclude_project_ids} --start_date {sample_start_date} --end_date {sample_end_date} --logdir {sample_log_dir} --pdfdir {sample_pdf_dir} --check-lost

        Arguments:

            --domain domain_name
                URL to your Teamwork instance. For example, if your Teamwork site url is https://test123.teamwork.com (copy it from address bar of your browser, in any doubt check Teamwork support docs) then you have to pass it like:
                --domain https://test123.teamwork.com

            --apikey api_key
                Api key for access to your Teamwork instance (you can get it in the settings of Teamwork instance, see documentation for Teamwork in any doubt for that). For example, if your api key is 123key555example, then you have to pass it like:
                --apikey 123key555example

            --project_ids project_ids
                Ids of project on whom script execution should be based or 'all_projects' for process all projects on server. Must be coma separated without blank spaces. For example, if you have to proceed projects with ids 100555, 200777, 300999 then you have to pass them like:
                --project_ids 100555,200777,300999
                --project_ids all_projects

            --exclude_project_ids exclude_project_ids
                Ids of project which script should skip. Must be coma separated without blank spaces. For example, if you have to exculde projects with ids 100555, 200777, 300999 then you have to pass them like:
                --exclude_project_ids 100555,200777,300999

            --start_date start_date
                Start date of the period on which script execution should be based. Must be in YYYYMMDD format. For example, if your start date is 1 May 2020 then you have to pass it like:
                --start_date 20200501

            --end_date end_date
                End date of the period on which script execution should be based. Must be in YYYYMMDD format. For example, if your end date is 1 June 2020 then you have to pass it like:
                --end_date 20200601
                
            --logdir logdir
                Directory for logs - both for errors.txt and logs.txt. For example:
                --logdir /var/log/scriptlogs/
                --logdir ./logs
                --logdir .

            --pdfdir pdfdir
                Directory for pdf files. For example:
                --pdfdir ./pdf
                --pdfdir .

            --check-lost
                Check lost expenses and time entries for each person after invoice.

            --help
                print this message
    '''
    print(help)

# register error logger/handler (once, maybe another solution needed for not creating error.txt if no errors), prints error

def log_error(error_msg):

    global ERROR_LOG_INITIATED
    global ERROR_LOGGER
    global ERROR_LOGGER_FH
    global LOGS_PATH

    if not ERROR_LOG_INITIATED:
        
        ERROR_LOG_FULL_PATH = LOGS_PATH / "errors.txt"
        
        ERROR_LOGGER = logging.getLogger("errors")
        ERROR_LOGGER.setLevel(logging.DEBUG)
        ERROR_LOGGER_FH = logging.FileHandler(ERROR_LOG_FULL_PATH, encoding='utf8')
        ERROR_LOGGER.addHandler(ERROR_LOGGER_FH)
        FORMATTER = logging.Formatter('%(name)s [%(asctime)s] - %(message)s')
        ERROR_LOGGER_FH.setFormatter(FORMATTER)
        ERROR_LOG_INITIATED = True

    ERROR_LOGGER.error(error_msg)


if __name__ == '__main__':
    try:

        # version constant for logging

        SCRIPT_VERSION = "4.2"

        # constant for http header requests

        HEADERS = {'Content-type': 'application/json'}

        # console arguments parsing and validation (and maybe sanitization needed too? not sure)

        argv = sys.argv[1:]

        try:

            opts, args = getopt.getopt(argv, "", ["help", "check-lost", "domain=", "apikey=", "project_ids=", "exclude_project_ids=", "apikey=", "start_date=", "end_date=", "logdir=", "pdfdir="])

        except getopt.GetoptError:
            print_usage()
            sys.exit(2)

        required_arguments = ["domain", "apikey", "project_ids", "start_date", "end_date", "logdir"]

        if (len(opts) == 1 and opts[0][0] == '--help' and opts[0][1] == ''):
            print_help()
            sys.exit(2)

        if (len(opts) < len(required_arguments)):
            print_usage()
            sys.exit(2)

        DOMAIN = ''
        APIKEY = ''
        PROJECT_IDS = []
        PROJECT_IDS_NOT_SPLITED = ''  # for logging
        EXCLUDE_PROJECT_IDS = []
        START_DATE = ''
        END_DATE = ''
        LOGDIR = ''
        PDF_DIR = ''
        CHECK_LOST = False

        for opt, arg in opts:
            if opt == '--domain':
                DOMAIN = arg
            elif opt == '--apikey':
                APIKEY = arg
            elif opt == '--project_ids':
                PROJECT_IDS = arg.split(',')
                PROJECT_IDS_NOT_SPLITED = arg
            elif opt == '--exclude_project_ids':
                EXCLUDE_PROJECT_IDS = arg.split(',')
            elif opt == '--start_date':
                START_DATE = arg
            elif opt == '--end_date':
                END_DATE = arg
            elif opt == '--pdfdir':
                PDF_DIR = arg
            elif opt == '--check-lost':
                CHECK_LOST = True
            elif opt == '--logdir':
                LOGDIR = arg
                
                # check is LOGDIR exists
                if LOGDIR and not os.path.exists(LOGDIR):
                    os.makedirs(LOGDIR)
                
                p = Path(LOGDIR)
                if not p.is_dir():
                    print_usage()
                    sys.exit(2)
                
            else:
                print_usage()
                sys.exit(2)
                
        # initiate logging for runtime logs (not errors)

        ERROR_LOG_INITIATED = False
        ERROR_LOGGER = None
        ERROR_LOGGER_FH = None
        
        LOGS_PATH = Path(LOGDIR)
        
        RUNTIME_LOG_FULL_PATH = LOGS_PATH / 'log.txt'

        log = logging.getLogger("main")
        log.setLevel(logging.DEBUG)
        FH = logging.FileHandler(RUNTIME_LOG_FULL_PATH, encoding='utf8')
        log.addHandler(FH)

        FORMATTER = logging.Formatter('%(name)s [%(asctime)s] - %(message)s')
        FH.setFormatter(FORMATTER)

        # log bootstrap values

        log.info("== Script started (version {0}) with params: domain {1}, apikey ###, project_ids {2}, exclude_project_ids {6}, start_date {3}, end_date {4}, logdir {5}".format(SCRIPT_VERSION, DOMAIN, PROJECT_IDS_NOT_SPLITED, START_DATE, END_DATE, LOGDIR, EXCLUDE_PROJECT_IDS))

        # check for last_month argument
        
        if START_DATE == 'last_month' and END_DATE == 'last_month':
            
            today = datetime.datetime.today()
            
            last_day_previous_month = today - datetime.timedelta(days=today.day)
            
            first_day_previous_month = last_day_previous_month.replace(day=1)
            
            START_DATE = first_day_previous_month
                        
            END_DATE = last_day_previous_month
            
        else:

            # prepend date arguments for passing to API

            START_DATE = datetime.datetime.strptime(START_DATE, '%Y%m%d')
            END_DATE = datetime.datetime.strptime(END_DATE, '%Y%m%d')
            
            # check that end_date must be greater then start_date

            if START_DATE > END_DATE:
                log_error('Ошибка: START_DATE > END_DATE')
                sys.exit(2)

        # some additional prepend date arguments for passing to API

        START_DATE_FORMAT = START_DATE.strftime("%Y%m%d")
        END_DATE_FORMAT = END_DATE.strftime("%Y%m%d")
        
        # prepend dicts for report.txt

        expenses_cost_by_user = {}

        rates_for_users_per_project = {}

        time_for_users_per_project = {}

        cost_for_users_per_project = {}

        people_names_by_id = {}
        
        people_ids_by_name = {}
        
        # get projects if needed
        
        if ( len(PROJECT_IDS) == 1 ) and ( PROJECT_IDS[0] == 'all_projects' ):
            
            log.info('Получаем список проектов, так как указан ключ all_projects')
        
            response = requests.get(
                DOMAIN + '/projects.json',
                params={'status':'ACTIVE'},
                headers=HEADERS,
                auth=(APIKEY, '')
            )
            
            response.raise_for_status()

            all_projects = response.json()

            if 'projects' not in all_projects:
                log_error('Ошибка ответа от API (get all projects)! Аварийное завершение.')
                sys.exit(1)

            NEW_PROJECT_IDS = []

            for proj in all_projects['projects']:
                
                NEW_PROJECT_IDS.append(proj['id'])
                
            PROJECT_IDS = NEW_PROJECT_IDS
        
        PROJECT_IDS = [prj for prj in PROJECT_IDS if prj not in EXCLUDE_PROJECT_IDS]

        # iterate over projects

        for PROJECT in PROJECT_IDS:
            
            PROJECT = PROJECT.strip()
            
            log.info('Проект {}'.format(PROJECT))
            
            # getting array with persons id as a key, and persons name as a value - for report.txt
            
            log.info('Получаем список сотрудников для проекта')

            response = requests.get(
                DOMAIN + '/projects/' + PROJECT + '/people.json',
                params={},
                headers=HEADERS,
                auth=(APIKEY, '')
            )
            
            response.raise_for_status()
            
            peoples = response.json()
            
            if 'people' not in peoples:
                log_error('Ошибка ответа от API (get peoples for project, project {})! Аварийное завершение.'.format(PROJECT))
                sys.exit(1)
            
            for people in peoples['people']:
                
                full_name = people['first-name'] + ' ' + people['last-name']               
                
                if people['id'] not in people_names_by_id:
                   people_names_by_id[people['id']] = full_name
                   
                if full_name not in people_ids_by_name:
                   people_ids_by_name[full_name] = people['id']
                
            # get expenses for project
            
            log.info('Получаем все фиксированные затраты для проекта')

            response = requests.get(
                DOMAIN + '/projects/' + PROJECT + '/expenses.json',
                params={},
                headers=HEADERS,
                auth=(APIKEY, '')
            )
            
            response.raise_for_status()
            
            expenses = response.json()
            
            if 'expenses' not in expenses:
                log_error('Ошибка ответа от API (get fixed expenses for project, project {})! Аварийное завершение.'.format(PROJECT))
                sys.exit(1)
                        
            log.info('Начинаем формировать счет для фиксированных затрат')
            
            # separate expenses for current project by valid dates and only not yet invoiced, put them in one string coma separated
            # also calculate uninvoiced and date valid expenses cost per user across all projects for report.txt
            
            #fixed_expenses_to_invoice = ""
            
            fixed_expenses_by_user_id = {}

            for expense in expenses['expenses']:

                expence_invoice_id = expense['invoice-id']

                expense_date = expense['date']
                
                expense_date = datetime.datetime.strptime(expense_date, '%Y%m%d')
                
                if (expence_invoice_id == '' and
                        expense_date >= START_DATE  and
                        expense_date <= END_DATE):
                            
                    expense_name = expense['name']
                    
                    # check if user exists (because name of expense equals first name + list name of user)
                    # if there is no such user then make a record in errors.txt for manager who will check it manually
                    # if user exists then proceed expense automatically      

                    if expense_name not in people_ids_by_name:
                        
                        project_url = DOMAIN
                        
                        if project_url[len(project_url)-1] != '/':
                            
                            project_url += '/'
                            
                        project_url += '#/projects/'
                        
                        project_url += PROJECT
                            
                        log_error('Не удалось идентифицировать сотрудника при обработке фиксированных расходов. Проект {}. Параметры фиксированного расхода:  имя {}, дата создания {}, описание {}, создатель {}, сумма {}.'.format(project_url, expense['name'], expense['date'], expense['description'], expense['created-by-user-lastname'], expense['cost']))

                        continue

                    expense_cost = expense['cost']
                    expense_id = expense['id']

                    user_id_for_fixed_expense = people_ids_by_name[expense_name]

                    if user_id_for_fixed_expense not in fixed_expenses_by_user_id:
                        fixed_expenses_by_user_id[user_id_for_fixed_expense] = expense_id + ','
                    else:
                        fixed_expenses_by_user_id[user_id_for_fixed_expense] += expense_id + ','
                    
                    # summarazing expenses per user across all projects for report.txt

                    if expense_name in expenses_cost_by_user:

                        current = float(expenses_cost_by_user[expense_name])
                        add = float(expense['cost'])
                        new = current + add

                        expenses_cost_by_user[expense_name] = round(new, 2)

                    else:

                        expenses_cost_by_user[expense_name] = round(float(expense['cost']), 2)
                        
            # create invoice through API for uninvoiced fixed expenses (with valid date) for current project

            project_billing = True
            for key, val in fixed_expenses_by_user_id.items():

                user_id = key
                user_expenses = val

                invoice_name = 'Fix_' + people_names_by_id[user_id]
               
                date = datetime.datetime.utcnow()
                date = datetime.datetime.strftime(date, '%Y%m%d')
                data = {"invoice":
                        {"number": invoice_name,
                         "currency-code": "USD",
                         "display-date": date,
                         "fixed-cost": "",
                         "description": "",
                         "po-number": ""}
                        }
                
                try:
                    response = requests.post(
                        DOMAIN + '/projects/' + PROJECT + '/invoices.json',
                        json=data,
                        headers=HEADERS,
                        auth=(APIKEY, '')
                    )

                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    # Some projects may haven't billing option, skip them
                    log_error('Ошибка ответа от API (create invoice for fixed expenses for user name {} in project {})!'.format(invoice_name, PROJECT))
                    project_billing = False
                    break
                else:
                    invoice_expenses = response.json()
                    
                    if invoice_expenses['STATUS'] != 'OK':
                        log_error('Ошибка ответа от API (create invoice for fixed expenses for user name {} in project {})! Аварийное завершение.'.format(invoice_name, PROJECT))
                        sys.exit(1)

                    # attach selected fixed expenses to previously created invoice
                    
                    user_expenses = user_expenses.strip(',')
                    
                    data = {"lineitems":
                            {"add":
                             {"expenses": user_expenses}}
                            }
                            
                    response = requests.put(
                        DOMAIN + '/invoices/' + invoice_expenses['id'] + '/lineitems.json',
                        json=data,
                        headers=HEADERS,
                        auth=(APIKEY, '')
                    )
                    
                    response.raise_for_status()
                    
                    response_json = response.json()
                    
                    if response_json['STATUS'] != 'OK':
                        log_error('Ошибка ответа от API (create lineitems for invoice fixed expenses, project {}, user name {}, invoice {}, expenses {})! Аварийное завершение.'.format(PROJECT, invoice_name, invoice_expenses['id'], user_expenses))
                        sys.exit(1)

            if not project_billing:
                continue

            # get rates for people in all projects for report.txt needs

            response = requests.get(
                DOMAIN + '/projects/' + PROJECT + '/rates.json',
                params={},
                headers=HEADERS,
                auth=(APIKEY, '')
            )
            
            response.raise_for_status()
            
            rates = response.json()
            
            if rates['STATUS'] != 'OK':
                log_error('Ошибка ответа от API (get rates for people in project, project {})! Аварийное завершение.'.format(PROJECT))
                sys.exit(1)
                
            if 'rates' in rates:
                if 'users' in rates['rates']:    
                    for key, value in rates['rates']['users'].items():

                        if key not in rates_for_users_per_project:
                            rates_for_users_per_project[key] = {}
                            rates_for_users_per_project[key][PROJECT] = value['rate']
                        else:
                            rates_for_users_per_project[key][PROJECT] = value['rate']

            # get time entries

            log.info('Получаем time entries')
            # log.debug(f'{DOMAIN}/projects/{PROJECT}/time_entries.json -->')

            pageSize = 500  # param for getting 500 entries per API page

            # getting first page

            time_response = requests.get(
                DOMAIN + '/projects/' + PROJECT + '/time_entries.json',
                params={'billableType': 'billable',
                 'invoicedType': 'noninvoiced',
                 'fromdate': START_DATE_FORMAT,
                 'todate': END_DATE_FORMAT,
                 'pageSize': pageSize},
                headers=HEADERS,
                auth=(APIKEY, ''))
                
            time_response.raise_for_status()

            time = time_response.json()
            
            if time['STATUS'] != 'OK':
                log_error('Ошибка ответа от API (get time entries for project, project {}, page 1)! Аварийное завершение.'.format(PROJECT))
                sys.exit(1)

            time_page = int(time_response.headers['X-Page'])  # current API page
            time_pages = int(time_response.headers['X-Pages'])  # total API pages
            time_records = int(time_response.headers['X-Records'])  # total entries over all API pages - need to check if it > 0 and just continue to next project?

            # getting other pages if exist

            for i in range(time_page, time_pages):
                
                # sleep for not overwhelming API
                
                ttime.sleep(1)

                response = requests.get(
                    DOMAIN + '/projects/' + PROJECT + '/time_entries.json',
                    params={'billableType': 'billable',
                     'invoicedType': 'noninvoiced',
                     'fromdate': START_DATE_FORMAT,
                     'todate': END_DATE_FORMAT,
                     'page': i + 1,
                     'pageSize': pageSize},
                    headers=HEADERS,
                    auth=(APIKEY, '')
                )
                
                response.raise_for_status()
                
                time_temp = response.json()
                
                if time_temp['STATUS'] != 'OK':
                    log_error('Ошибка ответа от API (get time entries for project, project {}, page {})! Аварийное завершение.'.format(PROJECT, i+1))
                    sys.exit(1)

                time['time-entries'] = time['time-entries'] + time_temp['time-entries']

            # log.debug(f'<-- {time}')

            items = {}

            # log.info('Сортируем time entries по сотрудникам')

            for entrie in time['time-entries']:
                if (entrie['invoiceNo'] == '' and
                        entrie['invoiceStatus'] == '' and
                        entrie['isbillable'] == '1'):

                    # calculate summary time and summary cost for person overall projects for report.txt

                    minutes = int(entrie['minutes'])
                    hours = int(entrie['hours'])
                    total_minutes = 60*hours + minutes
                    # total_hours = round(float(entrie['hoursDecimal']), 2)
                    rate = float(rates_for_users_per_project[entrie['person-id']][PROJECT])
                    rate_per_minute = rate / 60
                    cost = round(total_minutes * rate_per_minute, 2)

                    # summary costs

                    if entrie['person-id'] not in cost_for_users_per_project:
                        cost_for_users_per_project[entrie['person-id']] = cost
                    else:
                        current = float(cost_for_users_per_project[entrie['person-id']])
                        add = cost
                        new = current + add
                        cost_for_users_per_project[entrie['person-id']] = new

                    # summary time

                    if entrie['person-id'] not in time_for_users_per_project:
                        time_for_users_per_project[entrie['person-id']] = total_minutes
                    else:
                        current = time_for_users_per_project[entrie['person-id']]
                        add = total_minutes
                        new = current + add
                        time_for_users_per_project[entrie['person-id']] = new

                    # then old code goes

                    id = entrie['person-id'] + ';;' + entrie['person-first-name'] + ' ' + entrie['person-last-name']
                    if id in items:
                        items[id] += entrie['id'] + ','
                    else:
                        items[id] = ''
                        items[id] += entrie['id'] + ','

            log.info('Начинаем формировать счета')

            for person in items:
                name = person.split(';;')[1]
                date = datetime.datetime.utcnow()
                date = datetime.datetime.strftime(date, '%Y%m%d')
                data = {"invoice":
                        {"number": name,
                         "currency-code": "USD",
                         "display-date": date,
                         "fixed-cost": "",
                         "description": "",
                         "po-number": ""}
                        }
                # log.debug(DOMAIN + '/projects/' + PROJECT + '/invoices.json')
                # log.debug(f'{data} -->')
                response = requests.post(
                    DOMAIN + '/projects/' + PROJECT + '/invoices.json',
                    json=data,
                    headers=HEADERS,
                    auth=(APIKEY, '')
                )
                
                response.raise_for_status()
                
                invoice = response.json()
                
                # log.debug(f'<-- {invoice}')
                if invoice['STATUS'] == 'OK':
                    data = {"lineitems":
                            {"add":
                             {"timelogs": items[person].strip(',')}}
                            }
                            
                    response = requests.put(
                        DOMAIN + '/invoices/' + invoice['id'] + '/lineitems.json',
                        json=data,
                        headers=HEADERS,
                        auth=(APIKEY, '')
                    )
                    
                    response.raise_for_status()
                    
                    response_json = response.json()
                    
                    if response_json['STATUS'] != 'OK':
                        log_error('Ошибка ответа от API (create lineitems for invoice time entries, project {}, invoice {}, timelogs {})! Аварийное завершение.'.format(PROJECT, invoice['id'], items[person].strip(',')))
                        sys.exit(1)

                    if PDF_DIR:
                        try:
                            time_ids = items[person].strip(',')
                            invoices =[{
                                'date': datetime.datetime.strptime(tm['date'], r'%Y-%m-%dT%H:%M:%SZ'),
                                'name': name,
                                'task': tm['todo-item-name'],
                                'comment': tm['description'],
                                'time': float(tm['hoursDecimal']),
                                'cost': float(tm['hoursDecimal']) * float(rates_for_users_per_project[tm['person-id']][tm['project-id']]),
                            } for tm in time['time-entries'] if tm['id'] in time_ids]
                            summ = round(sum(map(lambda x: x['cost'], invoices)), 2)
                            generate_pdf(
                                generate_html({
                                    'name': name,
                                    'date': datetime.datetime.utcnow(),
                                    'invoices': invoices,
                                    }),
                                PDF_DIR,
                                '({summ} usd) Invoice {project} {name}.pdf'.format(
                                    summ=str(summ).replace('.', ','),
                                    project=PROJECT,
                                    name=name,
                                    ))
                        except Exception as exp:
                            log_error('Ошибка сохранения PDF (project {}, person {}): {}'.format(PROJECT, name, exp))
                        
                else:
                    log_error('Ошибка ответа от API (create invoice for time entries, project {}, person )! Аварийное завершение.'.format(PROJECT, name))
                    sys.exit(1)
                    
                # sleep for not overwhelming API    
                    
                ttime.sleep(1)
                    
            # sleep for not overwhelming API
            
            ttime.sleep(1)
                    
        # generate report.txt
        
        log.info('Начинаем формировать файл с общим отчётом')
        
        x = []
        
        for key, val in people_names_by_id.items():

            person_id = key
            person_name = val
            person_time = 0.00
            person_cost = 0.00
            person_expenses = 0.00
            person_rates = ''
            
            if person_id in time_for_users_per_project:
                person_time = round(time_for_users_per_project[person_id]/60, 2)
                
            if person_id in cost_for_users_per_project:
                person_cost = round(cost_for_users_per_project[person_id], 2)

            if person_name in expenses_cost_by_user:
                person_expenses = round(expenses_cost_by_user[person_name], 2)
                
            if person_time == 0 and person_cost == 0 and person_expenses == 0:
                continue
                
            if person_id in rates_for_users_per_project:
                
                rates_for_person = rates_for_users_per_project[person_id]
                
                rates_for_person_values = list(rates_for_person.values())
                
                if len(set(rates_for_person_values)) == 1:
                    
                    person_rates = "all projects: {} usd/hour".format(rates_for_person_values[0])
                    
                else:
                
                    for key, val in rates_for_users_per_project[person_id].items():
                        
                        person_rates += ' project ID:{}: {} usd/hour,'.format(key, val)
                        
                    if person_rates[len(person_rates) - 1] == ',':
                        
                        person_rates = person_rates[:-1]
                        
                    if person_rates[0] == ' ':
                        
                        person_rates = person_rates[1:]
                
            person_id = str(person_id)
            person_name = str(person_name)
            person_time = str(person_time)
            person_cost = str(person_cost)
            person_expenses = str(person_expenses)
            person_rates = person_rates
            
            x.append([person_id, person_name, person_time, person_cost, person_expenses, person_rates])

        with open("report.txt", "w") as text_file:
            
            # common info
            
            now = datetime.datetime.now()
            
            created_at = '{:%Y-%m-%d %H:%M:%S}'.format(now)
            
            report_timestamp = "Created at {}".format(created_at)
            
            report_domain = "Domain {}".format(DOMAIN)
            
            report_dates = "Dates from {} to {}".format(START_DATE_FORMAT, END_DATE_FORMAT)
            
            report_projects_ids = "Projects {}".format(', '.join(PROJECT_IDS))
            
            print(report_timestamp, file=text_file)
            print(report_domain, file=text_file)
            print(report_dates, file=text_file)
            print(report_projects_ids, file=text_file)
            
            print("", file=text_file)
            
            # info about people
            
            table_headers = ['ID', 'NAME', 'HOURS', 'COST', 'EXPENSES', 'RATES']

            row_format ="{:<15} {:<30} {:<15} {:<15} {:<15} {:<15}"
            
            print(row_format.format(*table_headers), file=text_file)
            
            for row in x:
                print(row_format.format(*row), file=text_file)

        if CHECK_LOST:
            lost_expenses = list()
            lost_time_response = list()
            for PROJECT in PROJECT_IDS:
                response = requests.get(
                    DOMAIN + '/projects/' + PROJECT + '/expenses.json',
                    params={},
                    headers=HEADERS,
                    auth=(APIKEY, '')
                )
                
                response.raise_for_status()
                
                processed_expense_ids = [tid for _, ids in fixed_expenses_by_user_id.items() for tid in ids.strip(',')]
                
                lost_time_response = [entrie for entrie in response.json()['expenses'] if
                                      str(entrie['id']) not in processed_expense_ids]

                response = requests.get(
                    DOMAIN + '/projects/' + PROJECT + '/time_entries.json',
                    params={'billableType': 'billable',
                     'invoicedType': 'noninvoiced',
                     'fromdate': START_DATE_FORMAT,
                     'todate': END_DATE_FORMAT,
                     'pageSize': pageSize},
                    headers=HEADERS,
                    auth=(APIKEY, ''))
                    
                response.raise_for_status()

                processed_time_response_ids = [tid for _, ids in items.items() for tid in ids.strip(',')]
                lost_time_response = [entrie for entrie in response.json()['time-entries'] if
                                      str(entrie['id']) not in processed_time_response_ids]

            for person_id, person_name in people_names_by_id.items():
                person_expenses = [exp for exp in lost_time_response if
                                   str(people_ids_by_name[exp['name']]) == str(person_id)]
                person_time_responses = [exp for exp in lost_time_response if
                                         str(exp['person-id']) == str(person_id)]
                if person_expenses or person_time_responses:
                    for exp in person_expenses:
                        log_error("Не оплачено: person_id {} name {} expense_id {} date {} cost {}".format(
                            person_id, person_name, exp['id'], exp['date'], exp['cost']))
                    for tm in person_time_responses:
                        log_error("Не оплачено: time_entries {} name {} time_entrie_id {} date {} time {}".format(
                            person_id, person_name, tm['id'], tm['date'], tm['hoursDecimal']))

        # end script

        log.info('== Script ended')

    except Exception as e:  # maybe need to improve exceptions handling
        print('При выполнении кода произошла ошибка - %s' % str(e))
        traceback.print_exc()
        log_error('При выполнении кода произошла ошибка - %s' % str(e))
        log_error(traceback.format_exc())
