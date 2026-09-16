from mate import output
from mate import globals

def test_suggest_retry():
    report = [
        ("dir1", globals.SUCCESS_CODE),
        ("dir2", globals.ERROR_CODE),
        ("dir3", globals.SUCCESS_CODE),
        ("dir4", globals.ERROR_CODE),
        ("dir5", globals.SUCCESS_CODE),
        ("dir6", globals.ERROR_CODE)
    ]

    output.suggest_retry(report)


test_suggest_retry()