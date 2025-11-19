import logging

class InvalidMarkserrror(Exception):
    pass

def check_marks(marks):
    if marks<0 or marks>100:
        raise InvalidMarkserrror("Marks must be between 0 and 100")

try:
    check_marks(20)
except InvalidMarkserrror as e:
    logging.error(e)