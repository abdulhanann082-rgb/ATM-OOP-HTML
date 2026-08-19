# 30 Python Data Types Problem-Solving Questions - SOLUTIONS

# Q1. Integer
a = int(input("Enter first number: "))
b = int(input("Enter second number: "))
print("Sum:", a + b)
print("Difference:", a - b)
print("Multiplication:", a * b)
if b != 0:
    print("Division:", a / b)
else:
    print("Division: Cannot divide by zero")


# Q2. Float
marks = []
for i in range(5):
    marks.append(float(input(f"Enter marks for subject {i + 1}: ")))
total = sum(marks)
average = total / len(marks)
print("Total:", total)
print("Average:", average)


# Q3. String
word = input("Enter a word: ")
if len(word) > 5:
    print("Length is greater than 5")
else:
    print("Length is 5 or less")


# Q4. Boolean
age = int(input("Enter your age: "))
is_adult = age >= 18
print(is_adult)


# Q5. Type Conversion
age = input("Enter your age: ")
age = int(age)
print("Next year your age will be:", age + 1)


# Q6. String
sentence = input("Enter a sentence: ")
print("Total characters:", len(sentence))
print("Total spaces:", sentence.count(" "))


# Q7. String
word = input("Enter a word: ")
if word.lower() == word.lower()[::-1]:
    print("Palindrome")
else:
    print("Not Palindrome")


# Q8. Float + Integer
price = float(input("Enter product price: "))
quantity = int(input("Enter quantity: "))
bill = price * quantity

if bill > 5000:
    discount = bill * 0.10
    final_bill = bill - discount
    print("Original Bill:", bill)
    print("Discount:", discount)
    print("Final Bill:", final_bill)
else:
    print("Final Bill:", bill)


# Q9. List
numbers = [12, 5, 28, 3, 19, 8]
largest = numbers[0]
smallest = numbers[0]

for number in numbers:
    if number > largest:
        largest = number
    if number < smallest:
        smallest = number

print("Largest:", largest)
print("Smallest:", smallest)


# Q10. List
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
even_numbers = []

for number in numbers:
    if number % 2 == 0:
        even_numbers.append(number)

print("Even numbers:", even_numbers)


# Q11. List
numbers = [1, 2, 2, 3, 4, 4, 5, 5, 6]
unique_numbers = []

for number in numbers:
    if number not in unique_numbers:
        unique_numbers.append(number)

print("Without duplicates:", unique_numbers)


# Q12. List
numbers = [10, 20, 30, 40, 50]
total = 0

for number in numbers:
    total += number

average = total / len(numbers)
print("Sum:", total)
print("Average:", average)


# Q13. List
numbers = [-5, 0, 10, -2, 7, 0, 3, -8]
positive = 0
negative = 0
zero = 0

for number in numbers:
    if number > 0:
        positive += 1
    elif number < 0:
        negative += 1
    else:
        zero += 1

print("Positive:", positive)
print("Negative:", negative)
print("Zeros:", zero)


# Q14. List + String
names = ["Ali", "Ahmed", "Hassan", "Abdul Hannan", "Sara", "Usman"]

for name in names:
    if len(name) > 5:
        print(name)


# Q15. List
numbers = [1, 2, 3, 4, 5]
reversed_list = []

for i in range(len(numbers) - 1, -1, -1):
    reversed_list.append(numbers[i])

print("Original:", numbers)
print("Reversed:", reversed_list)


# Q16. List
list1 = [1, 2, 3, 4, 5]
list2 = [4, 5, 6, 7, 8]
common = []

for item in list1:
    if item in list2 and item not in common:
        common.append(item)

print("Common elements:", common)


# Q17. List
numbers = [10, 5, 20, 8, 20, 15]
unique = []

for number in numbers:
    if number not in unique:
        unique.append(number)

unique.sort()

if len(unique) >= 2:
    print("Second largest:", unique[-2])
else:
    print("Second largest does not exist")


# Q18. List
numbers = [2, 4, 6, 8, 10]
doubled = []

for number in numbers:
    doubled.append(number * 2)

print("Original:", numbers)
print("Doubled:", doubled)


# Q19. Tuple
marks = (85, 78, 92, 67, 88)
highest = marks[0]
lowest = marks[0]

for mark in marks:
    if mark > highest:
        highest = mark
    if mark < lowest:
        lowest = mark

print("Highest:", highest)
print("Lowest:", lowest)


# Q20. Tuple
values = (2, 5, 2, 8, 2, 9, 5, 2)
target = 2
count = 0

for value in values:
    if value == target:
        count += 1

print(f"{target} appears {count} times")


# Q21. Set
set1 = {1, 2, 3, 4, 5}
set2 = {4, 5, 6, 7, 8}

print("Union:", set1 | set2)
print("Intersection:", set1 & set2)
print("Difference:", set1 - set2)


# Q22. Set + List
numbers = [5, 2, 8, 2, 1, 5, 9, 8, 3]
unique_numbers = set(numbers)
print("Unique sorted numbers:", sorted(unique_numbers))


# Q23. Set + List
student1_courses = ["Python", "Database", "HTML", "Java"]
student2_courses = ["Python", "Java", "CSS", "JavaScript"]

courses1 = set(student1_courses)
courses2 = set(student2_courses)

print("Common courses:", courses1 & courses2)
print("Only first student's courses:", courses1 - courses2)
print("Total unique courses:", len(courses1 | courses2))


# Q24. Dictionary
students = {
    "Ali": 78,
    "Ahmed": 92,
    "Hassan": 85,
    "Usman": 88
}

highest_student = None
highest_marks = -1

for name, marks in students.items():
    if marks > highest_marks:
        highest_marks = marks
        highest_student = name

print("Highest student:", highest_student)
print("Marks:", highest_marks)


# Q25. Dictionary
products = {
    "Laptop": 100000,
    "Mouse": 2000,
    "Keyboard": 5000,
    "Monitor": 30000
}

product_name = input("Enter product name: ")

if product_name in products:
    print("Price:", products[product_name])
else:
    print("Product not found")


# Q26. Dictionary
sentence = input("Enter a sentence: ").lower()
words = sentence.split()
frequency = {}

for word in words:
    frequency[word] = frequency.get(word, 0) + 1

print("Word frequency:", frequency)


# Q27. Dictionary
students = {
    "Ali": 78,
    "Ahmed": 92,
    "Hassan": 85,
    "Sara": 75,
    "Ayesha": 90
}

passed_students = {}

for name, marks in students.items():
    if marks >= 80:
        passed_students[name] = marks

print("Students with 80 or above:", passed_students)


# Q28. Dictionary + List
departments = {
    "IT": ["Ali", "Ahmed"],
    "HR": ["Sara", "Ayesha"],
    "Sales": ["Hassan", "Usman"]
}

employee = input("Enter employee name: ")
found = False

for department, employees in departments.items():
    if employee in employees:
        print(employee, "works in", department)
        found = True
        break

if not found:
    print("Employee not found")


# Q29. Shopping Cart
cart = [
    {"name": "Laptop", "price": 100000, "quantity": 1},
    {"name": "Mouse", "price": 2000, "quantity": 2},
    {"name": "Keyboard", "price": 5000, "quantity": 1}
]

total_bill = 0

for product in cart:
    product_total = product["price"] * product["quantity"]
    print(product["name"], "Total:", product_total)
    total_bill += product_total

print("Complete Bill:", total_bill)

if total_bill > 100000:
    discount = total_bill * 0.10
else:
    discount = 0

final_amount = total_bill - discount

print("Discount:", discount)
print("Final Payable Amount:", final_amount)


# ============================================================
# Q30. FINAL CHALLENGE: STUDENT MANAGEMENT SYSTEM
# ============================================================

students = [
    {
        "name": "Hassan",
        "age": 21,
        "courses": ["Python", "Database"],
        "marks": (85, 78, 92),
        "skills": {"Python", "SQL"},
        "fee_paid": True
    },
    {
        "name": "Ali",
        "age": 20,
        "courses": ["Python", "HTML"],
        "marks": (75, 88, 80),
        "skills": {"Python", "HTML"},
        "fee_paid": False
    }
]

# 1. Add a new student
new_student = {
    "name": "Ahmed",
    "age": 22,
    "courses": ["Python", "JavaScript"],
    "marks": (90, 85, 88),
    "skills": {"Python", "JavaScript"},
    "fee_paid": True
}

students.append(new_student)
print("New student added:", new_student["name"])


# 2. Search for a student
search_name = "Hassan"
found_student = None

for student in students:
    if student["name"].lower() == search_name.lower():
        found_student = student
        break

if found_student:
    print("Student found:", found_student)
else:
    print("Student not found")


# 3. Calculate average marks
for student in students:
    marks = student["marks"]
    average = sum(marks) / len(marks)
    print(student["name"], "Average:", average)


# 4. Find highest-scoring student
highest_student = None
highest_average = -1

for student in students:
    average = sum(student["marks"]) / len(student["marks"])

    if average > highest_average:
        highest_average = average
        highest_student = student

print("Highest-scoring student:", highest_student["name"])
print("Average:", highest_average)


# 5. Find all unique skills
all_skills = set()

for student in students:
    all_skills.update(student["skills"])

print("Unique skills:", all_skills)


# 6. Show paid/unpaid students
paid_students = []
unpaid_students = []

for student in students:
    if student["fee_paid"]:
        paid_students.append(student["name"])
    else:
        unpaid_students.append(student["name"])

print("Fee Paid:", paid_students)
print("Fee Unpaid:", unpaid_students)


# 7. Count students course-wise
course_count = {}

for student in students:
    for course in student["courses"]:
        course_count[course] = course_count.get(course, 0) + 1

print("Course-wise students:", course_count)


# 8. Delete a student
delete_name = "Ali"

for student in students[:]:
    if student["name"].lower() == delete_name.lower():
        students.remove(student)
        print(delete_name, "deleted successfully")
        break


# 9. Display all students
print("\nAll Students:")

for student in students:
    print("------------------------------")
    print("Name:", student["name"])
    print("Age:", student["age"])
    print("Courses:", student["courses"])
    print("Marks:", student["marks"])
    print("Skills:", student["skills"])
    print("Fee Paid:", student["fee_paid"])
