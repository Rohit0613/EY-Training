#even odd
'''def checknumber(num):
    if num % 2 == 0:
        return f"{num} is even"
    else:
        return f"{num} is odd"

number=int(input("Enter your number: "))
result=checknumber(number)
print (result) '''


#for loop
'''for i in range(1,6):
    print(i)'''

#table creation
'''def multiplicationtable(num):
    print(f'Multiplication table of {num}')
    for i in range(1,11):
        print(f'{num}*{i}={num*i}')


number=int(input("Enter your number: "))
multiplicationtable(number)'''

'''#creating a list
numbers=[10,20,30,40,50,60,70,80,90]

#accessing element
print(numbers[0]) #first element
print(numbers[-1]) #last element'''

fruits=['apple','banana','mango']
#add
fruits.append('orange') #adds at end
fruits.insert(1,'peach') #adds at index 1

print(fruits)

fruits.remove('orange')
print(fruits)

fruits.pop()
print(fruits)