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
    if vacancy['currency']:
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
    if vacancy['salary']:
        if vacancy['salary'].get('currency') == 'RUR':
            return predict_salary(vacancy['salary'].get('to'), vacancy['salary'].get('from'))


def predict_salary(salary_to, salary_from):
    if all((salary_to, salary_from)):
        return (salary_to + salary_from) / 2
    elif salary_to:
        return salary_to * 0.8
    elif salary_from:
        return salary_from * 1.2


def search_job_main(url, headers, params, prog_languages, get_vacancies_func, predict_rub_salary_func):
    programming_languages = {language: {} for language in prog_languages}
    for programming_language in programming_languages:
        vacancies, vacancy_total = get_vacancies_func(url, params, headers, programming_language)
        vacancy_salaries = []
        for vacancy in vacancies:
            salary = predict_rub_salary_func(vacancy)
            if salary:
                vacancy_salaries.append(salary)

        if not vacancy_salaries:
            average_salary = 0
        else:
            average_salary = int(sum(vacancy_salaries) / len(vacancy_salaries))

        programming_languages[programming_language] = {
            'vacancies_found': vacancy_total,
            'vacancies_processed': len(vacancy_salaries),
            'average_salary': average_salary
        }

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
