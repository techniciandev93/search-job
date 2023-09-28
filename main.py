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

    page_vacancy = {'more': True}
    while page_vacancy['more']:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        page_vacancy = response.json()
        vacancies.extend(page_vacancy['objects'])
        params['page'] += 1
    vacancy_total = page_vacancy['total']
    return vacancies, vacancy_total


def predict_rub_salary_sj(vacancy):
    if not vacancy['currency']:
        return None
    if vacancy.get('currency') == 'rub':
        return predict_salary(vacancy.get('payment_to'), vacancy.get('payment_from'))


def get_vacancies_hh(url, params, headers=None, search_field=None):
    vacancies = []
    params['page'] = 0
    if search_field:
        params['text'] = search_field

    while True:
        response = requests.get(url, params=params, headers=None)
        response.raise_for_status()
        page_vacancy = response.json()
        vacancies.extend(page_vacancy['items'])
        params['page'] += 1
        if page_vacancy['pages'] == params['page']:
            break
    vacancy_total = page_vacancy['found']
    return vacancies, vacancy_total


def predict_rub_salary_hh(vacancy):
    if not vacancy['salary']:
        return None
    if vacancy['salary'].get('currency') == 'RUR':
        return predict_salary(vacancy['salary'].get('to'), vacancy['salary'].get('from'))


def predict_salary(salary_to, salary_from):
    if all((salary_to, salary_from)):
        return (salary_to + salary_from) / 2
    elif salary_to:
        return salary_to * 0.8
    elif salary_from:
        return salary_from * 1.2


def process_calculation_vacancies(programming_languages, programming_language, vacancies, predict_rub_salary_func,
                                  vacancy_total):
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
            'vacancies_found': vacancy_total,
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

    publication_period = 30
    page_vacancy_counts = 100
    sj_moscow_town_id = 4
    sj_programmer_position_id = 48

    superjob_token = os.environ['SUPERJOB_TOKEN']
    sj_headers = {'X-Api-App-Id': superjob_token}
    sj_params = {'period': publication_period,
                 'town': sj_moscow_town_id,
                 'count': page_vacancy_counts,
                 'catalogues': sj_programmer_position_id}
    sj_url = 'https://api.superjob.ru/2.0/vacancies'

    hh_programmer_position_id = 96
    hh_moscow_region_id = 1

    hh_params = {'professional_role': hh_programmer_position_id,
                 'area': hh_moscow_region_id,
                 'period': publication_period,
                 'per_page': page_vacancy_counts}
    hh_url = 'https://api.hh.ru/vacancies'
    hh_headers = None

    parser = argparse.ArgumentParser(description="Этот скрипт предназначен для поиска зарплаты по языкам "
                                                 "программирования на ресурсах superjob.ru и hh.ru используя их API. "
                                                 "Запустите скрипт, указав несколько языков программирования через "
                                                 "пробел после ключа -l : python main.py -l Python Java GO, "
                                                 "по умолчанию произойдёт поиск по языку Python: python main.py")
    parser.add_argument('-l', '--list', type=str, help="Введите несколько языков программирования через пробел",
                        nargs='*', default=['Python'])
    args = parser.parse_args()

    hh_programming_languages = {language: {} for language in args.list}
    sj_programming_languages = {language: {} for language in args.list}

    for language in args.list:
        sj_vacancies, sj_vacancy_total = get_vacancies_sj(sj_url, sj_params, sj_headers, language)
        hh_vacancies, hh_vacancy_total = get_vacancies_hh(hh_url, hh_params, hh_headers, language)

        process_calculation_vacancies(sj_programming_languages, language, sj_vacancies, predict_rub_salary_sj,
                                      sj_vacancy_total)
        process_calculation_vacancies(hh_programming_languages, language, hh_vacancies, predict_rub_salary_hh,
                                      hh_vacancy_total)

    sj_title = 'SuperJob Moscow'
    sj_table = create_table(sj_programming_languages, sj_title)
    print(sj_table.table)

    hh_title = 'HH Moscow'
    hh_table = create_table(hh_programming_languages, hh_title)
    print(hh_table.table)
