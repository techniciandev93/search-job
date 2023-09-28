import argparse
import os
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_vacancies_sj(url, params, headers=None, search_field=None):
    vacancies = []
    params['page'] = 0
    if search_field:
        params['keyword'] = search_field

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    page_vacancy = response.json()
    vacancies.extend(page_vacancy['objects'])

    params['page'] = 1
    while page_vacancy['more']:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        page_vacancy = response.json()
        vacancies.extend(page_vacancy['objects'])
        params['page'] += 1
    return vacancies


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] is not None:
        if vacancy.get('currency') == 'rub':
            if all((vacancy.get('payment_to'), vacancy.get('payment_from'))):
                return (vacancy.get('payment_to') + vacancy.get('payment_from')) / 2
            elif vacancy.get('payment_to'):
                return vacancy.get('payment_to') * 0.8
            elif vacancy.get('payment_from'):
                return vacancy.get('payment_from') * 1.2


def get_vacancies_hh(url, params, headers=None, search_field=None):
    vacancies = []
    params['page'] = 0
    if search_field:
        params['text'] = search_field

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    first_page_vacancies = response.json()
    vacancies.extend(first_page_vacancies['items'])

    for page in range(1, first_page_vacancies['pages']):
        params['page'] = page
        response = requests.get(url, params=params)
        response.raise_for_status()
        vacancies.extend(response.json()['items'])
    return vacancies


def predict_rub_salary_hh(vacancy):
    if vacancy['salary'] is not None:
        if vacancy['salary'].get('currency') == 'RUR':
            if all((vacancy['salary'].get('to'), vacancy['salary'].get('from'))):
                return (vacancy['salary'].get('to') + vacancy['salary'].get('from')) / 2
            elif vacancy['salary'].get('to'):
                return vacancy['salary'].get('to') * 0.8
            elif vacancy['salary'].get('from'):
                return vacancy['salary'].get('from') * 1.2


def search_job_main(url, headers, params, prog_languages, get_vacancies_func, predict_rub_salary_func):
    programming_languages = {language: {} for language in prog_languages}
    for programming_language in programming_languages:
        vacancies = get_vacancies_func(url, params, headers, programming_language)
        vacancy_salary = []
        for vacancy in vacancies:
            salary = predict_rub_salary_func(vacancy)
            if salary is not None:
                vacancy_salary.append(salary)

        if not vacancy_salary:
            average_salary = 0
        else:
            average_salary = int(sum(vacancy_salary) / len(vacancy_salary))

        programming_languages[programming_language].update(
            {
                'vacancies_found': len(vacancies),
                'vacancies_processed': len(vacancy_salary),
                'average_salary': average_salary
            }
        )
    return programming_languages


def create_table(programming_languages, title):
    top_hat = ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    for_table_vacancies = [[language, *[vacancy for vacancy in programming_languages[language].values()]]
                           for language in programming_languages]
    for_table_vacancies.insert(0, top_hat)
    table = AsciiTable(for_table_vacancies, title)
    return table


if __name__ == '__main__':
    load_dotenv()
    superjob_token = os.environ['SUPERJOB_TOKEN']
    sj_headers = {'X-Api-App-Id': superjob_token}
    sj_params = {'period': 30, 'town': 4, 'count': 100, 'catalogues': 48}
    sj_url = 'https://api.superjob.ru/2.0/vacancies'

    hh_params = {'professional_role': 96, 'area': 1, 'period': 30, 'per_page': 100}
    hh_url = 'https://api.hh.ru/vacancies'
    hh_headers = None

    parser = argparse.ArgumentParser(description="Запустите скрипт, указав несколько языков программирования через "
                                                 "пробел после ключа -l : python main.py -l Python Java GO, "
                                                 "по умолчанию произойдёт поиск по языку Python: python main.py")
    parser.add_argument('-l', '--list', type=str, help="Введите несколько языков программирования через пробел",
                        nargs='*', default=['Python'])
    args = parser.parse_args()

    sj_vacancies = search_job_main(
        sj_url,
        sj_headers,
        sj_params,
        args.list,
        get_vacancies_sj,
        predict_rub_salary_sj
    )

    hh_vacancies = search_job_main(
        hh_url,
        hh_headers,
        hh_params,
        args.list,
        get_vacancies_hh,
        predict_rub_salary_hh
    )

    sj_title = 'SuperJob Moscow'
    sj_table = create_table(sj_vacancies, sj_title)
    print(sj_table.table)

    hh_title = 'HH Moscow'
    hh_table = create_table(hh_vacancies, hh_title)
    print(hh_table.table)
