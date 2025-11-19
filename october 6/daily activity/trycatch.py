try:
    value=int(input('Enter a number: '))
    print(10/value)
except ValueError:
    print('Value is not an integer')
except ZeroDivisionError:
    print('Division by zero')
finally:
    print('execution finished')