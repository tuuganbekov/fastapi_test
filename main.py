import os
import json
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel
from mako.template import Template

app = FastAPI()
BASE_DIR = os.getcwd()


class Solution(BaseModel):
    solution: str
    tests: str


# Prepare processes that run code
def prepare_processes(process_path, test_file_path) -> str:
    """Prepare processes that run code"""
    with open(process_path, 'r') as f:
        lines = f.readlines()

    temp = '    p = multiprocessing.Process(target=run_test, args=('
    lines[1] = f"{temp}'{test_file_path}', ))"
    ready = '\n'.join(lines)
    return ready


# Create student-task submit file from template
def prepare_submit_file(solution: str, test_case: str):
    """
    Create test file with python tests and solution
    Returns submit file path
    """
    import_file_path = os.path.join(BASE_DIR, "helpers/imports")
    test_runner_file_path = os.path.join(BASE_DIR, "helpers/test_runner")
    processes_file_path = os.path.join(BASE_DIR, 'helpers/processes')
    submit_file_path = os.path.join(BASE_DIR, 'tests/test_task.py')
    print('submit_file_path', submit_file_path)
    print('type submit_file_path: ', type(submit_file_path))
    with open(submit_file_path, 'w') as f:
        process = prepare_processes(processes_file_path, submit_file_path)
        tmp_import_file = Template(filename=import_file_path)
        tmp_test_runner_file = Template(filename=test_runner_file_path)
        tmp_process = Template(f'{process}')
        student_task = Template(f"{tmp_import_file.source}\n\n{solution}\n\n{test_case}\n \
        \n{tmp_test_runner_file.source}\n\n{tmp_process.source}")

        f.write(student_task.render())
        return submit_file_path


# return result of tests from json
def get_result() -> tuple:
    """
    Parse .report.json which was
    generated after running pytest
    """
    with open('.report.json', 'r') as json_file:
        r = json.load(json_file)
        print('Ralsdlksajfd: ', r)
        result = r.get('exitcode')
        print("returncode:", result)
        if r.get('tests')[0].get('call').get('crash'):
            message = r.get('tests')[0].get('call').get('crash')['message']
        else:
            message = "Выполнено!"
        if result == 0:
            return 1, message
        return 2, message


@app.post("/api/check/")
async def root(data: Solution):
    data = data.dict()
    print("data", data)
    solution = data.get('solution')
    test_case = data.get('tests')
    # prepare test file and run tests
    # submit_file = prepare_submit_file(solution, test_case)
    cmd = f'pytest tests\\test_task.py --json-report --json-report-summary'
    syntax_test = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, universal_newlines=True)
    _, error_message = syntax_test.communicate()
    returncode = syntax_test.returncode
    final_result = get_result()
    final = {'returncode': final_result, 'success': True}
    return final
